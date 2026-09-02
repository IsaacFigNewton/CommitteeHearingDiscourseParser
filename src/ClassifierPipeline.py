from typing import Optional, List, Union
import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .constants.constants import *
from .dataclasses.Hearing import TaggedHearing
from .HearingTagger import HearingTagger
from .classifier.Classifier import Classifier
from .classifier.Masker import Masker
from .classifier.MaskedSoftmaxHelper import MaskedSoftmaxHelper
from .enums.SectionEnum import SectionEnum
from .grammar.Parser import Parser
"""
only want to parse hearings labelled as CA_201720180<AB/SB>7
    if it's got SR in the suffix, then it's a senate resolution,
    which we don't need to parse
"""


class ClassifierPipeline:
    TOKEN_COL = 'speaker.position'
    TEXT_COL = 'text'
    CAT_COLS = [
        'section_cues',
        'speech_act_cues'
    ]
    NUM_COLS = [
        'relative_position', 'sent_count', 'token_count',
        'mentions_speaker', 'mentions_bill',
    ]
    FEATURE_COLS = [TOKEN_COL, TEXT_COL, *CAT_COLS, *NUM_COLS]
    
    parser = Parser()

    def __init__(self,
            base_estimator=None,
            max_parses:int=2,
            do_grammar_masking:bool=True
        ) -> None:
        self.hearing_tagger = HearingTagger()
        # return the row-level parsed hearing dataframe
        self.feature_cols = self.FEATURE_COLS
        self.model = self._make_model(base_estimator)
        self.max_parses = max_parses
        self.do_grammar_masking = do_grammar_masking

    @classmethod
    def _make_model(cls, base_estimator=None):
        """Initialize the section prediction model pipeline.

        The pipeline has two stages:
        1. Feature extraction (TF-IDF, one-hot encoding, scaling)
        2. Masked classification (classifier + grammar-constrained masking)

        Args:
            base_estimator: Optional sklearn classifier to use. If None, defaults to LogisticRegression.

        The MaskedClassifier separates the base estimator from the masking logic,
        allowing masking parameters to be set via set_params() before prediction.
        """
        if base_estimator is None:
            base_estimator = LogisticRegression(
                max_iter=2000,
                class_weight='balanced',
                solver='lbfgs'
            )

        return Pipeline([
            ('features', ColumnTransformer([
                ('text', TfidfVectorizer(
                    ngram_range=(2, 5),
                    min_df=4,
                    max_features=2000
                ), cls.TEXT_COL),
                ('categorical', OneHotEncoder(
                    handle_unknown='ignore'
                ), cls.CAT_COLS + [cls.TOKEN_COL]),
                ('numeric', StandardScaler(), cls.NUM_COLS),
            ])),
            ('classifier', Classifier(
                base_estimator=base_estimator,
            )),
            ('masker', Masker()),
        ])

    @classmethod
    def _build_utterances_dataframe(cls, hearings: List[TaggedHearing]) -> pd.DataFrame:
        """Build a DataFrame of utterance features from a list of tagged hearings.

        Builds raw utterance rows without filling missing values.
        Missing values are automatically filled.

        Args:
            hearings: List of TaggedHearing instances to convert to DataFrame

        Returns:
            DataFrame with utterance features, sorted by state, bid, hid, uid
        """
        df = pd.DataFrame([
            {
                # metadata
                'state':                    h.state,
                'bid':                      h.bid,
                'hid':                      h.hid,
                'uid':                      u.uid,
                'pid':                      u.pid,

                # speaker features
                'speaker.position':         s.speaker_position.name if s and s.speaker_position else None,
                'speaker.position.value':   s.speaker_position.value if s and s.speaker_position else None,
                'can_file_motions':         s.can_file_motions if s else None,
                'is_presenter':             s.is_presenter if s else None,

                # metadata features
                'relative_position':        u.relative_position,
                'token_count':              u.token_count,
                'sent_count':               u.sent_count,
                'mentions_speaker':         int(bool(u.pids_mentioned)),
                'mentions_bill':            int(bool(u.bill_mentioned)),
                'speech_act_cues':          ','.join([s.name for s in u.speech_act_cues]) if u.speech_act_cues else '',
                'section_cues':             ','.join([s.name for s in u.section_cues]) if u.section_cues else '',

                # output label
                'section':                  None,

                # text
                'text':                     u.text,
            }
            for h in hearings or []
            for u in h.utterances
            for s in [h.speakers[u.pid]]
        ])

        # Sort by state, bid, hid, uid for consistent ordering
        df = df.sort_values(by=['state', 'bid', 'hid', 'uid']).reset_index(drop=True)

        # Fill missing values
        df = cls._fill_missing(df)

        return df
    
    @classmethod
    def _fill_missing(cls, df: pd.DataFrame, label_col: Optional[str] = None) -> pd.DataFrame:
        """Fill missing feature values before training or prediction."""
        df = df.copy()
        df[cls.TEXT_COL] = df[cls.TEXT_COL].fillna('')
        df[cls.CAT_COLS] = df[cls.CAT_COLS].fillna(UNKNOWN)
        df[cls.NUM_COLS] = df[cls.NUM_COLS].fillna(0)
        if label_col:
            df[label_col] = df[label_col].fillna(UNKNOWN)
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
        hearing_df: pd.DataFrame,
        smooth: bool = True,
    ) -> List[SectionEnum]:
        """Predict section labels for a single hearing.

        Args:
            hearing: Tagged hearing to predict sections for
            hearing_df: Optional DataFrame with pre-extracted features for this hearing only,
                       sorted by uid. Should contain feature columns and metadata columns:
                       'speaker.position.value', 'can_file_motions', 'is_presenter'.
                       If provided, utterances_df is ignored.
            smooth: Whether to apply label smoothing

        Returns:
            List of predicted SectionEnum labels, one per utterance
        """
        if hearing_df.empty:
            raise ValueError(f'Empty hearing_df provided for hid={hearing.hid}, bid={hearing.bid}')
        filled_df = self._fill_missing(hearing_df)

        # Extract features for the pipeline
        X = filled_df[self.feature_cols]

        # Extract masking information for the masker stage
        speaker_positions = filled_df['speaker.position.value'].values
        can_file_motions = filled_df['can_file_motions'].values
        is_presenters = filled_df['is_presenter'].values

        # Get classifier classes and set them on the masker
        classifier = self.model.named_steps['classifier']
        classes_ = classifier.classes_

        # Generate parse trees for masking
        parse_trees = []
        try:
            parse_trees = list(
                self.parser.get_all_parses_as_nltk_trees(hearing, max_parses=self.max_parses)
                or []
            )
        except Exception:
            parse_trees = []

        # Generate class mask using MaskedSoftmaxHelper directly
        class_mask, parse_success = MaskedSoftmaxHelper.allowed_sections_for_hearing(
            hearing=hearing,
            parser=self.parser,
            speaker_positions=speaker_positions,
            can_file_motions=can_file_motions,
            is_presenters=is_presenters,
            max_parses=self.max_parses,
            parse_trees=parse_trees,
        )

        # Set masking parameters on the masker stage
        self.model.set_params(
            masker__classes_=classes_,
        )
        if self.do_grammar_masking:
            self.model.set_params(
                masker__class_mask=class_mask if parse_success else None,
            )

        # Predict using the full pipeline (features -> classifier -> masker)
        labels, parse_success = self.model.predict(X)
        labels = list(labels)

        return self.smooth_label_list(labels) if smooth else labels