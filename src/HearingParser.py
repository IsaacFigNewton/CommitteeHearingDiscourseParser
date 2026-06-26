from typing import Optional, List, Union
import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .constants.constants import *
from .dataclasses.Hearing import TaggedHearing
from .HearingTagger import HearingTagger
from .classifier.MaskedSoftmaxClassifier import MaskedSoftmaxClassifier
from .enums.SectionEnum import SectionEnum
from .grammar.Tokenizer import Tokenizer
"""
only want to parse hearings labelled as CA_201720180<AB/SB>7
    if it's got SR in the suffix, then it's a senate resolution,
    which we don't need to parse
"""


class HearingParser:
    TEXT_COL = 'text'
    CAT_COLS = [
        'speaker.position',
        'section_cues',
        'speech_act_cues'
    ]
    NUM_COLS = [
        'relative_position', 'sent_count',
        'mentions_speaker', 'mentions_bill',
    ]
    FEATURE_COLS = [TEXT_COL, *CAT_COLS, *NUM_COLS]

    def __init__(self) -> None:
        self.hearing_tagger = HearingTagger()
        self.tokenizer = Tokenizer()
        # return the row-level parsed hearing dataframe
        self.feature_cols = self.FEATURE_COLS
        self.model = self._make_model()

    @classmethod
    def _make_model(cls):
        """Initialize the section prediction model pipeline."""
        return Pipeline([
            ('features', ColumnTransformer([
                ('text', TfidfVectorizer(
                    ngram_range=(2, 5),
                    min_df=3,
                    max_features=2000
                ), cls.TEXT_COL),
                ('categorical', OneHotEncoder(
                    handle_unknown='ignore'
                ), cls.CAT_COLS),
                ('numeric', StandardScaler(), cls.NUM_COLS),
            ])),
            ('classifier', MaskedSoftmaxClassifier(
                max_iter=2000,
                class_weight='balanced',
                solver='lbfgs'
            )),
        ])

    @classmethod
    def _fill_missing(cls, df: pd.DataFrame, label_col: Optional[str] = None) -> pd.DataFrame:
        """Fill missing feature values before training or prediction."""
        df = df.copy()
        df[cls.TEXT_COL] = df[cls.TEXT_COL].fillna('')
        df[cls.CAT_COLS] = df[cls.CAT_COLS].fillna('unknown')
        df[cls.NUM_COLS] = df[cls.NUM_COLS].fillna(0)
        if label_col:
            df[label_col] = df[label_col].fillna('unknown')
        return df

    def train_model(self, train_df: pd.DataFrame, label_col: str = 'stage_label'):
        """Train the section prediction model on labeled data.

        Args:
            train_df: DataFrame with utterance features and labels (accepts SectionEnum or string labels)
            label_col: Name of the column containing stage labels
        """
        train_df = self._fill_missing(train_df, label_col)

        # Convert labels to SectionEnum first (handles legacy labels), then to string for sklearn
        labels = train_df[label_col].copy()

        self.model.fit(train_df[self.feature_cols], labels)

    @staticmethod
    def smooth_label_list(labels: List[SectionEnum]) -> List[SectionEnum]:
        """Smooth label predictions by fixing single outlier labels.

        If a label is surrounded by identical labels, change it to match.

        Args:
            labels: List of predicted SectionEnum labels

        Returns:
            Smoothed list of SectionEnum labels
        """
        labels = list(labels)
        for i, (prev_, curr, next_) in enumerate(zip(labels, labels[1:], labels[2:]), 1):
            if prev_ == next_ != curr:
                labels[i] = prev_
        return labels

    def predict_hearing_sections(
        self,
        hearing: TaggedHearing,
        utterances_df: pd.DataFrame,
        smooth: bool = True,
    ) -> List[SectionEnum]:
        """Predict section labels for a single hearing.

        Args:
            hearing: Tagged hearing to predict sections for
            utterances_df: DataFrame containing utterance features for all hearings
            smooth: Whether to apply label smoothing

        Returns:
            List of predicted SectionEnum labels, one per utterance
        """
        hearing_df = utterances_df[
            (utterances_df['hid'] == hearing.hid)
            & (utterances_df['bid'].astype(str) == str(hearing.bid))
        ].sort_values('uid')

        if hearing_df.empty:
            raise ValueError(f'No rows found for hid={hearing.hid}, bid={hearing.bid}')

        filled_df = self._fill_missing(hearing_df)

        # Extract features for the pipeline
        X = filled_df[self.feature_cols]

        # Extract masking information for the classifier
        speaker_positions = filled_df['speaker.position_value'].values
        can_file_motions = filled_df['can_file_motions'].values
        is_presenters = filled_df['is_presenter'].values

        # Generate parse tree for this hearing
        parse_tree = None
        try:
            parse_tree = self.tokenizer.parse(hearing)
        except Exception as e:
            # If parsing fails, fall back to grammar rules
            print(f"Warning: Parse tree generation failed for hearing {hearing.hid}/{hearing.bid}: {e}")

        # Transform features through the pipeline's feature transformer
        X_transformed = self.model.named_steps['features'].transform(X)

        # Get predictions from classifier with masking (returns string labels)
        labels = list(self.model.named_steps['classifier'].predict(
            X_transformed,
            speaker_positions=speaker_positions,
            can_file_motions=can_file_motions,
            is_presenters=is_presenters,
            parse_tree=parse_tree,
        ))

        return self.smooth_label_list(labels) if smooth else labels

    def predict_hearings_batch(self, hearings: List[TaggedHearing], smooth: bool = True) -> dict:
        """Predict section labels for multiple hearings.

        Args:
            hearings: List of tagged hearings to predict sections for
            smooth: Whether to apply label smoothing

        Returns:
            Dictionary mapping (hid, bid) tuples to lists of predicted SectionEnum labels
        """
        # Build utterances dataframe for all hearings
        utterances_df = self._build_utterance_rows(hearings)
        results = {}

        for hearing in hearings:
            key = (hearing.hid, hearing.bid)
            try:
                results[key] = self.predict_hearing_sections(hearing, utterances_df, smooth)
            except ValueError as e:
                print(f"Warning: Could not predict sections for hearing {hearing.hid}/{hearing.bid}: {e}")
                results[key] = []

        return results

    def _build_utterance_rows(self, hearings: Optional[List[TaggedHearing]]) -> pd.DataFrame:
        return pd.DataFrame([
            {
                # metadata
                'state':                h.state,
                'bid':                  h.bid,
                'hid':                  h.hid,
                'uid':                  u.uid,
                'pid':                  u.pid,

                # speaker features
                'speaker.position':         s.speaker_position.name if s and s.speaker_position else None,
                'speaker.position_value':   s.speaker_position.value if s and s.speaker_position else None,
                'can_file_motions':         s.can_file_motions if s else None,
                'is_presenter':             s.is_presenter if s else None,

                # metadata features
                'relative_position':    u.relative_position,
                'sent_count':           u.sent_count,
                'mentions_speaker':     int(bool(u.pids_mentioned)),
                'mentions_bill':        int(bool(u.bids_mentioned)),
                'speech_act_cues':      ','.join([s.name for s in u.speech_act_cues]) if u.speech_act_cues else '',
                'section_cues':         ','.join([s.name for s in u.section_cues]) if u.section_cues else '',

                # output label
                'section':              None,

                # text
                'text':                 u.text,
            }
            for h in hearings or []
            for u in h.utterances
            for s in [h.speakers[u.pid]]
        ])