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
from .speakers.enums.SpeakerPositionEnum import SpeakerPositionEnum, TERMINAL_STR_TOK_MAP
from .grammar.Parser import Parser
"""
only want to parse hearings labelled as CA_201720180<AB/SB>7
    if it's got SR in the suffix, then it's a senate resolution,
    which we don't need to parse
"""


class ClassifierPipeline:
    parser = Parser()
    classes_ = np.array([s.value for s in list(SectionEnum)])

    def __init__(self,
            base_estimator=None,
            max_parses:int=2,
            masking:bool=True,
            smoothing: bool = True,
        ) -> None:
        self.hearing_tagger = HearingTagger()
        self.max_parses = max_parses
        self.masking = masking
        self.smoothing = smoothing
        
        if base_estimator is None:
            base_estimator = LogisticRegression(
                max_iter=2000,
                class_weight='balanced',
                solver='lbfgs'
            )

        self.model = Pipeline([
            ('features', ColumnTransformer([
                ('text', TfidfVectorizer(
                    ngram_range=(2, 5),
                    min_df=4,
                    max_features=2000
                ), TEXT_COL),
                ('categorical', OneHotEncoder(
                    handle_unknown='ignore'
                ), CAT_COLS + [TOKEN_COL]),
                ('numeric', StandardScaler(), NUM_COLS),
            ])),
            ('classifier', Classifier(
                base_estimator=base_estimator,
            )),
            ('masker', Masker()),
        ])

        # Get classifier classes and set them on the masker
        # Get classifier classes and set them on the masker
        self.model.named_steps['classifier'].classes_ = self.classes_
        self.classifier = self.model.named_steps['classifier']
        self.masking_helper = MaskedSoftmaxHelper(self.classes_)


    def fit(self,
            X: pd.DataFrame,
            y: pd.DataFrame | pd.Series
        ):
        """Train the section prediction model on labeled data.

        Args:
            train_df: DataFrame with utterance features and labels (accepts SectionEnum or string labels)
            label_col: Name of the column containing stage labels
        """

        self.model.fit(X, y)

        # Set masking parameters on the masker stage
        # CRITICAL: Use the fitted classifier's classes_ (sklearn sorts lexically)
        # rather than self.classes_ (SectionEnum declaration order) to ensure
        # the masker decodes argmax against the same label order as predict_proba
        self.model.set_params(
            masker__classes_=self.model.named_steps['classifier'].classes_,
        )


    def _predict_sections(self, X: pd.DataFrame) -> List[SectionEnum]:
        """
        predict labels for 1 hearing's utterances
            1. get sequence of token strings (List[str]) for each unique hearing (list of row["speaker.position"] entries)
            2. map List[str] to List[SpeakerPositionEnum]
            3. pass List[Optional[SpeakerPositionEnum]] to self.parser.get_all_parses_as_nltk_trees if needed
        """
        token_strings = [
            # if no speaker.position assigned, tok may be np.nan
            str(tok)
            for tok in X[TOKEN_COL].to_list()
        ]
        token_seq: List[Optional[SpeakerPositionEnum]] = [
            # if "np.nan" not in TERMINAL_STR_TOK_MAP, it will return None
            TERMINAL_STR_TOK_MAP.get(tok_str)
            for tok_str in token_strings
        ]
        
        # Generate parse trees for masking
        parse_trees = []
        try:
            parse_trees = list(
                self.parser.get_all_parses_as_nltk_trees(token_seq, max_parses=self.max_parses)
                or []
            )
        except Exception:
            parse_trees = []

        # Generate class mask using MaskedSoftmaxHelper directly
        class_mask = self.masking_helper.allowed_sections_for_hearing(
            token_seq=token_seq,
            parse_trees=parse_trees,
        )

        if self.masking:
            self.model.set_params(
                masker__class_mask=class_mask,
            )

        # Predict using the full pipeline (features -> classifier -> masker)
        labels = list(self.model.predict(X))
        
        if self.smoothing:
            # If a label is surrounded by identical labels, change it to match.
            for i, (prev_, curr, next_) in enumerate(zip(labels, labels[1:], labels[2:]), 1):
                if prev_ == next_ != curr:
                    labels[i] = prev_

        return labels


    def predict(
        self,
        X: pd.DataFrame
    ) -> np.ndarray:
        """Predict section labels for a collection of hearinsg.

        Args:
            hearing_df: DataFrame with pre-extracted features for multiple hearings,
                       sorted by uid. Should contain feature columns and metadata columns:
                       'speaker.position.value', 'can_file_motions', 'is_presenter'.
                       If provided, utterances_df is ignored.

        Returns:
            List of predicted SectionEnum labels, one per utterance
        """
        labels_to_stack = []

        for hearing_group in X["hearing_group"].unique():
            # group hearing_df rows by 'bid' and 'hid'
            hearing = X[
                X["hearing_group"] == hearing_group
            ].sort_values(by="uid")[FEATURE_COLS]

            # extract features for the pipeline
            labels_to_stack.append(self._predict_sections(hearing))

        # TODO: Convert List[List[SectionEnum]] to np.ndarray of shape (n_)
        return np.hstack(labels_to_stack)