from typing import Optional, List, Union
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .constants import *
from .dataclasses.Hearing import RawHearing, TaggedHearing, ParsedHearing
from .HearingTagger import HearingTagger
"""
only want to parse hearings labelled as CA_201720180<AB/SB>7
    if it's got SR in the suffix, then it's a senate resolution,
    which we don't need to parse
"""


class HearingParser:
    TEXT_COL = 'text'
    CAT_COLS = ['speaker_position']
    NUM_COLS = [
    'is_legislator', 'is_committee_member', 'relative_position', 'word_count',
    'mentions_bills', 'has_bill_action', 'has_presentation_cue',
    'has_motion_cue', 'has_vote_cue', 'has_disposition_cue',
    ]
    FEATURE_COLS = [TEXT_COL, *CAT_COLS, *NUM_COLS]

    def __init__(self, return_type: str = 'dataframe') -> None:
        self.hearing_tagger = HearingTagger()
        # return_type == 'dataframe' or 'json'
        #   if return_type == 'json', parse the hearing into a ParsedHearing instance and serialize its contents as JSON
        #   if return_type == 'dataframe', just return the row-level parsed hearing dataframe
        self.return_type = return_type
        self.feature_cols = self.FEATURE_COLS
        self.model = self._make_model()

    @classmethod
    def _make_model(cls):
        """Initialize the section prediction model pipeline."""
        return Pipeline([
            ('features', ColumnTransformer([
                ('text', TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=1,
                    max_features=20000
                ), cls.TEXT_COL),
                ('categorical', OneHotEncoder(
                    handle_unknown='ignore'
                ), cls.CAT_COLS),
                ('numeric', StandardScaler(), cls.NUM_COLS),
            ])),
            ('classifier', LogisticRegression(
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
            train_df: DataFrame with utterance features and labels
            label_col: Name of the column containing stage labels
        """
        train_df = self._fill_missing(train_df, label_col)
        self.model.fit(train_df[self.feature_cols], train_df[label_col])

    @staticmethod
    def smooth_label_list(labels: List[str]) -> List[str]:
        """Smooth label predictions by fixing single outlier labels.

        If a label is surrounded by identical labels, change it to match.

        Args:
            labels: List of predicted labels

        Returns:
            Smoothed list of labels
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
    ) -> List[str]:
        """Predict section labels for a single hearing.

        Args:
            hearing: Tagged hearing to predict sections for
            utterances_df: DataFrame containing utterance features for all hearings
            smooth: Whether to apply label smoothing

        Returns:
            List of predicted section labels, one per utterance
        """
        hearing_df = utterances_df[
            (utterances_df['hid'] == hearing.hid)
            & (utterances_df['bid'].astype(str) == str(hearing.bid))
        ].sort_values('uid')

        if hearing_df.empty:
            raise ValueError(f'No rows found for hid={hearing.hid}, bid={hearing.bid}')

        labels = list(self.model.predict(self._fill_missing(hearing_df)[self.feature_cols]))
        return self.smooth_label_list(labels) if smooth else labels

    def predict_hearings_batch(self, hearings: List[TaggedHearing], smooth: bool = True) -> dict:
        """Predict section labels for multiple hearings.

        Args:
            hearings: List of tagged hearings to predict sections for
            smooth: Whether to apply label smoothing

        Returns:
            Dictionary mapping (hid, bid) tuples to lists of predicted labels
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
                'hid':                  h.hid,
                'bid':                  h.bid,
                'state':                h.state,
                'uid':                  u.uid,
                'pid':                  u.pid,
                'text':                 u.text,
                'speaker_position':     s.speaker_position.value if s and s.speaker_position else None,
                'is_legislator':        int(bool(getattr(s, 'is_legislator', False))),
                'is_committee_member':  int(bool(getattr(s, 'is_committee_member', False))),
                'relative_position':    u.relative_position,
                'word_count':           u.relative_len,
                'mentions_speakers':    int(bool(u.mentions_speakers)),
                'mentions_bills':       int(bool(u.mentions_bills)),
                'has_bill_action':      int(u.has_bill_action),
                'has_presentation_cue': int(u.has_presentation_cue),
                'has_vote_cue':         int(u.has_vote_cue),
                'has_disposition_cue':  int(u.has_disposition_cue),

                # manual label
                'has_motion_cue':       int(u.is_motion or False),
                'is_transition':        int(u.is_transition or False),
                'stage_label':          None,
            }
            for h in hearings or []
            for u in h.utterances
            for s in [h.speakers[u.pid]]
        ])

    @staticmethod
    def pprint_hearing(hearing: RawHearing):
        """Print formatted transcript."""
        print()
        print(f"State:\t\t{hearing.state}")
        print(f"Committee:\t{hearing.cname}")
        print(f"Bill:\t\t{hearing.bid}")
        print(f"Date:\t\t{hearing.hearing_date.strftime('%Y-%m-%d')}")
        print()
        print("Transcript:")
        for u in hearing.utterances:
            speaker = hearing.speakers[u.pid]
            name = f"{speaker.first_name or 'UNKNOWN'} {speaker.last_name or 'UNKNOWN'}:"
            print(f"{name:<20} {u.text}")
        print()