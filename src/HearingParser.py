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
    def __init__(self, return_type:str = 'dataframe') -> None:
        self.hearing_tagger = HearingTagger()
        # return_type == 'dataframe' or 'json'
        #   if return_type == 'json', parse the hearing into a ParsedHearing instance and serialize its contents as JSON
        #   if return_type == 'dataframe', just
        self.return_type = return_type
        self.model = None
        self.feature_cols = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the section prediction model pipeline."""
        text_feature = 'text'

        categorical_features = [
            'speaker_position',
        ]

        numeric_features = [
            'is_legislator',
            'is_committee_member',
            'relative_position',
            'word_count',
            'mentions_bills',
            'has_bill_action',
            'has_presentation_cue',
            'has_motion_cue',
            'has_vote_cue',
            'has_disposition_cue',
        ]

        self.feature_cols = [text_feature] + categorical_features + numeric_features

        self.model = Pipeline([
            ('features', ColumnTransformer([
                ('text', TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=1,
                    max_features=20000,
                ), text_feature),

                ('categorical', OneHotEncoder(
                    handle_unknown='ignore',
                ), categorical_features),

                ('numeric', StandardScaler(), numeric_features),
            ])),

            ('classifier', LogisticRegression(
                max_iter=2000,
                class_weight='balanced',
                solver='lbfgs',
            )),
        ])

    def train_model(self, train_df: pd.DataFrame, label_col: str = 'stage_label'):
        """Train the section prediction model on labeled data.

        Args:
            train_df: DataFrame with utterance features and labels
            label_col: Name of the column containing stage labels
        """
        # Fill missing values
        text_cols = ['text']
        for col in text_cols:
            train_df[col] = train_df[col].fillna('')

        categorical_features = ['speaker_position']
        for col in categorical_features:
            train_df[col] = train_df[col].fillna('unknown')

        numeric_features = [
            'is_legislator', 'is_committee_member', 'relative_position',
            'word_count', 'mentions_bills', 'has_bill_action',
            'has_presentation_cue', 'has_motion_cue', 'has_vote_cue',
            'has_disposition_cue'
        ]
        for col in numeric_features:
            train_df[col] = train_df[col].fillna(0)

        train_df[label_col] = train_df[label_col].fillna('unknown')

        X_train = train_df[self.feature_cols]
        y_train = train_df[label_col]

        self.model.fit(X_train, y_train)

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

        for i in range(1, len(labels) - 1):
            prev_label = labels[i - 1]
            curr_label = labels[i]
            next_label = labels[i + 1]

            if prev_label == next_label and curr_label != prev_label:
                labels[i] = prev_label

        return labels

    def predict_hearing_sections(
        self,
        hearing: TaggedHearing,
        utterances_df: pd.DataFrame,
        smooth: bool = True
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
        ].copy()

        if hearing_df.empty:
            raise ValueError(
                f'No rows found for hid={hearing.hid}, bid={hearing.bid}'
            )

        hearing_df = hearing_df.sort_values('uid').copy()

        # Fill missing values
        text_cols = ['text']
        for col in text_cols:
            hearing_df[col] = hearing_df[col].fillna('')

        categorical_features = ['speaker_position']
        for col in categorical_features:
            hearing_df[col] = hearing_df[col].fillna('unknown')

        numeric_features = [
            'is_legislator', 'is_committee_member', 'relative_position',
            'word_count', 'mentions_bills', 'has_bill_action',
            'has_presentation_cue', 'has_motion_cue', 'has_vote_cue',
            'has_disposition_cue'
        ]
        for col in numeric_features:
            hearing_df[col] = hearing_df[col].fillna(0)

        X = hearing_df[self.feature_cols]

        labels = list(self.model.predict(X))

        if smooth:
            labels = self.smooth_label_list(labels)

        return labels

    def predict_hearings_batch(
        self,
        hearings: List[TaggedHearing],
        smooth: bool = True
    ) -> dict:
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
            try:
                labels = self.predict_hearing_sections(
                    hearing=hearing,
                    utterances_df=utterances_df,
                    smooth=smooth
                )
                results[(hearing.hid, hearing.bid)] = labels
            except ValueError as e:
                print(f"Warning: Could not predict sections for hearing {hearing.hid}/{hearing.bid}: {e}")
                results[(hearing.hid, hearing.bid)] = []

        return results

    def parse_hearing(self, raw_hearing: RawHearing) -> Optional[ParsedHearing]:
        tagged_hearing = self.hearing_tagger(raw_hearing)
        # TODO: insert section tagging, assignment pipeline
        # return ParsedHearing()


    def _build_utterance_rows(self, hearings: Optional[List[TaggedHearing]]) -> pd.DataFrame:
        if not hearings:
            return pd.DataFrame()

        rows = []

        for hearing in hearings:
            for u in hearing.utterances:
                speaker = hearing.speakers[u.pid]
                rows.append({
                    'hid':                  hearing.hid,
                    'bid':                  hearing.bid,
                    'state':                hearing.state,
                    'uid':                  u.uid,
                    'pid':                  u.pid,

                    'text':                 u.text,

                    'speaker_position':     speaker.speaker_position.value if speaker and speaker.speaker_position else None,
                    'is_legislator':        int(bool(getattr(speaker, 'is_legislator', False))),
                    'is_committee_member':  int(bool(getattr(speaker, 'is_committee_member', False))),

                    'relative_position':    u.relative_position,
                    'word_count':           u.relative_len,

                    'mentions_speakers':    int(bool(len(u.mentions_speakers or []) > 0)),
                    'mentions_bills':       int(bool(len(u.mentions_bills or []) > 0)),
                    'has_bill_action':      int(u.has_bill_action),
                    'has_presentation_cue': int(u.has_presentation_cue),
                    'has_vote_cue':         int(u.has_vote_cue),
                    'has_disposition_cue':  int(u.has_disposition_cue),

                    # manual label
                    'has_motion_cue':       int(u.is_motion or False),
                    'is_transition':        int(u.is_transition or False),
                    'stage_label':          None,
                })

        return pd.DataFrame(rows)

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
        for contribution in hearing.utterances:
            speaker = hearing.speakers[contribution.pid]
            first_name = speaker.first_name or "UNKNOWN"
            last_name = speaker.last_name or "UNKNOWN"
            name = f"{first_name} {last_name}:"
            print(f"{name:<20} {contribution.text}")
        print()
