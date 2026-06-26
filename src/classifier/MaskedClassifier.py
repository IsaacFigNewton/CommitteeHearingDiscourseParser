from __future__ import annotations

from typing import Any, Iterable, List, Optional, Sequence

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin

from src.classifier.MaskedSoftmaxHelper import MaskedSoftmaxHelper


class MaskedClassifier(BaseEstimator, ClassifierMixin):
    """Classifier wrapper that applies grammar/parser-constrained masking.

    This classifier wraps any base classifier (typically LogisticRegression)
    and applies softmax masking during prediction. It stores masking context
    (hearing, tokenizer, etc.) as estimator parameters that can be set via
    set_params() before prediction.

    Unlike SoftmaxMaskingTransformer, this classifier integrates masking
    directly into predict() and predict_proba(), making it work seamlessly
    in pipelines without requiring a separate transformation step.

    Typical usage in a Pipeline:
        Pipeline([
            ('features', feature_transformer),
            ('classifier', MaskedClassifier(
                base_estimator=LogisticRegression(max_iter=2000),
            )),
        ])

    Then in HearingParser:
        self.model.set_params(
            classifier__hearing=hearing,
            classifier__tokenizer=self.tokenizer,
            classifier__grammar=GRAMMAR,
            classifier__speaker_positions=speaker_positions,
            classifier__can_file_motions=can_file_motions,
            classifier__is_presenters=is_presenters,
        )
        predictions = self.model.predict(X)
    """

    helper_class = MaskedSoftmaxHelper

    def __init__(
        self,
        base_estimator: Any = None,
        hearing: Any = None,
        tokenizer: Any = None,
        grammar: Any = None,
        speaker_positions: Optional[Sequence[Any]] = None,
        can_file_motions: Optional[Sequence[Any]] = None,
        is_presenters: Optional[Sequence[Any]] = None,
        max_parses: int = 2,
    ) -> None:
        """Initialize the masked classifier.

        Args:
            base_estimator: Underlying classifier (e.g., LogisticRegression)
            hearing: TaggedHearing object for context
            tokenizer: Tokenizer for parsing
            grammar: Grammar for fallback masking
            speaker_positions: Array of speaker position values per row
            can_file_motions: Array of can_file_motions flags per row
            is_presenters: Array of is_presenter flags per row
            max_parses: Maximum number of parses to consider
        """
        self.base_estimator = base_estimator
        self.hearing = hearing
        self.tokenizer = tokenizer
        self.grammar = grammar
        self.speaker_positions = speaker_positions
        self.can_file_motions = can_file_motions
        self.is_presenters = is_presenters
        self.max_parses = max_parses

    def fit(self, X: Any, y: Any, **fit_params: Any) -> "MaskedClassifier":
        """Fit the base classifier.

        Args:
            X: Training data
            y: Target labels
            **fit_params: Additional parameters for base estimator's fit

        Returns:
            self
        """
        from sklearn.linear_model import LogisticRegression

        if self.base_estimator is None:
            self.base_estimator_ = LogisticRegression()
        else:
            from sklearn.base import clone
            self.base_estimator_ = clone(self.base_estimator)

        self.base_estimator_.fit(X, y, **fit_params)
        self.classes_ = self.base_estimator_.classes_
        return self

    def predict(self, X: Any) -> np.ndarray:
        """Predict labels after applying grammar-constrained masking.

        Args:
            X: Input data

        Returns:
            Predicted class labels
        """
        probs = self.predict_proba(X)
        return self.classes_[np.argmax(probs, axis=1)]

    def predict_proba(self, X: Any) -> np.ndarray:
        """Return class probabilities after masking and renormalizing.

        Args:
            X: Input data

        Returns:
            Masked probability matrix
        """
        # Get base probabilities
        probs = self.base_estimator_.predict_proba(X)

        # If no masking context, return unmasked probabilities
        if self.hearing is None or self.tokenizer is None:
            return probs

        # Build allowed sections for this hearing
        allowed_sections = self.helper_class.allowed_sections_for_hearing(
            hearing=self.hearing,
            tokenizer=self.tokenizer,
            grammar=self.grammar,
            speaker_positions=self.speaker_positions,
            can_file_motions=self.can_file_motions,
            is_presenters=self.is_presenters,
            max_parses=self.max_parses,
        )

        # Apply masking
        return self._apply_masking(probs, allowed_sections)

    def _apply_masking(
        self,
        probs: np.ndarray,
        allowed_sections: Optional[Sequence[Iterable[Any]]] = None,
    ) -> np.ndarray:
        """Apply masking and renormalization to probabilities.

        Args:
            probs: Probability matrix of shape (n_samples, n_classes)
            allowed_sections: List of allowed sections per row

        Returns:
            Masked and renormalized probability matrix
        """
        if allowed_sections is None:
            return probs

        if len(allowed_sections) != probs.shape[0]:
            raise ValueError(
                f"allowed_sections length ({len(allowed_sections)}) must match "
                f"number of rows in probs ({probs.shape[0]})."
            )

        masked = probs.copy()
        class_keys = [self.helper_class._section_key(c) for c in self.classes_]

        for row_idx, allowed in enumerate(allowed_sections):
            allowed_keys = {self.helper_class._section_key(s) for s in allowed if s is not None}

            # Empty/unknown mask means "do not constrain this row".
            if not allowed_keys:
                continue

            keep = np.array([key in allowed_keys for key in class_keys], dtype=bool)

            # If the grammar/parser produced labels that are not in the trained
            # classifier classes, keep the unmasked classifier distribution.
            if not keep.any():
                continue

            masked[row_idx, ~keep] = 0.0
            denom = masked[row_idx].sum()

            # Guard against numerical/degenerate cases by falling back to a
            # uniform distribution over allowed trained classes.
            if denom > 0:
                masked[row_idx] /= denom
            else:
                masked[row_idx, keep] = 1.0 / keep.sum()

        return masked

    @classmethod
    def allowed_sections_for_hearing(
        cls,
        hearing: Any,
        tokenizer: Any,
        grammar: Any = None,
        speaker_positions: Optional[Sequence[Any]] = None,
        can_file_motions: Optional[Sequence[Any]] = None,
        is_presenters: Optional[Sequence[Any]] = None,
        max_parses: int = 2,
    ) -> List[List[Any]]:
        """Delegate hearing-mask construction to MaskedSoftmaxHelper."""
        return cls.helper_class.allowed_sections_for_hearing(
            hearing=hearing,
            tokenizer=tokenizer,
            grammar=grammar,
            speaker_positions=speaker_positions,
            can_file_motions=can_file_motions,
            is_presenters=is_presenters,
            max_parses=max_parses,
        )

    @classmethod
    def _section_key(cls, value: Any) -> str:
        """Return a stable section key for backward compatibility."""
        return cls.helper_class._section_key(value)
