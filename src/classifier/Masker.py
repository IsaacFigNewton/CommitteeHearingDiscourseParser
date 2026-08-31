from __future__ import annotations

from typing import Any, Iterable, Optional, Sequence, Tuple

import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin

from src.dataclasses.Hearing import TaggedHearing
from src.grammar.Parser import Parser
from src.classifier.MaskedSoftmaxHelper import MaskedSoftmaxHelper


class Masker(BaseEstimator, ClassifierMixin):
    """Applies grammar/parser-constrained masking to classifier probabilities.

    This component takes probability matrices from a classifier and applies
    masking based on grammar rules and parsing. It stores masking context
    (hearing, parser, etc.) as estimator parameters that can be set via
    set_params() before transformation.

    The Masker:
    1. Calls MaskedSoftmaxHelper.allowed_sections_for_hearing() to get allowed sections
    2. Applies masking to zero out probabilities for disallowed sections
    3. Renormalizes the probabilities
    4. Returns (masked_probs, parse_success_flag)

    Typical usage in a Pipeline:
        Pipeline([
            ('features', feature_transformer),
            ('classifier', Classifier(base_estimator=LogisticRegression(max_iter=2000))),
            ('masker', Masker(parser=parser)),
        ])

    Then before prediction:
        pipeline.set_params(
            masker__hearing=hearing,
            masker__speaker_positions=speaker_positions,
            masker__can_file_motions=can_file_motions,
            masker__is_presenters=is_presenters,
        )
        masked_probs, parse_success = pipeline.predict_proba(X)
    """

    helper_class = MaskedSoftmaxHelper

    def __init__(
        self,
        parser: Parser,
        hearing: Optional[TaggedHearing] = None,
        grammar: Any = None,
        speaker_positions: Optional[Sequence[Any]] = None,
        can_file_motions: Optional[Sequence[Any]] = None,
        is_presenters: Optional[Sequence[Any]] = None,
        max_parses: int = 2,
        classes_: Optional[np.ndarray] = None,
        parse_trees: Optional[list] = None,
        class_mask: Optional[Tuple[list, bool]] = None,
    ) -> None:
        """Initialize the masker.

        Args:
            parser: Parser for generating parse trees (kept for backwards compatibility)
            hearing: TaggedHearing object for context
            grammar: Grammar for fallback masking
            speaker_positions: Array of speaker position values per row
            can_file_motions: Array of can_file_motions flags per row
            is_presenters: Array of is_presenter flags per row
            max_parses: Maximum number of parses to consider
            classes_: Array of class labels (set automatically by pipeline)
            parse_trees: Pre-generated parse trees from parser (passed via set_params)
            class_mask: Optional pre-built class mask tuple (allowed_sections, parse_successful).
                       If provided, overrides allowed_sections_for_hearing() call.
        """
        self.parser = parser
        self.hearing = hearing
        self.grammar = grammar
        self.speaker_positions = speaker_positions
        self.can_file_motions = can_file_motions
        self.is_presenters = is_presenters
        self.max_parses = max_parses
        self.classes_ = classes_
        self.parse_trees = parse_trees
        self.class_mask = class_mask

    def fit(self, X: Any, y: Any = None, **fit_params: Any) -> "Masker":
        """Fit method (no-op for masker, just for sklearn compatibility).

        Args:
            X: Input data (ignored)
            y: Target labels (ignored)
            **fit_params: Additional parameters (ignored)

        Returns:
            self
        """
        return self

    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, bool]:
        """Predict labels from probability matrix after masking.

        Args:
            X: Probability matrix of shape (n_samples, n_classes) from previous pipeline stage

        Returns:
            Tuple of (labels, parse_success) where:
            - labels: Array of predicted class labels
            - parse_success: bool indicating if CYK parsing succeeded
        """
        masked_probs, parse_successful = self._get_masked_probs(X)

        if self.classes_ is None:
            raise ValueError("classes_ not set on Masker. Ensure the pipeline classifier stage sets this.")

        labels = self.classes_[np.argmax(masked_probs, axis=1)]
        return labels, parse_successful

    def predict_proba(self, X: np.ndarray) -> Tuple[np.ndarray, bool]:
        """Return masked probabilities.

        Args:
            X: Probability matrix of shape (n_samples, n_classes) from previous pipeline stage

        Returns:
            Tuple of (masked_probs, parse_success)
        """
        return self._get_masked_probs(X)

    def _get_masked_probs(self, X: np.ndarray) -> Tuple[np.ndarray, bool]:
        """Apply masking to probability matrix.

        Args:
            X: Probability matrix of shape (n_samples, n_classes)

        Returns:
            Tuple of (masked_probs, parse_success) where:
            - masked_probs: Masked and renormalized probability matrix
            - parse_success: bool indicating if CYK parsing succeeded
        """
        # X is expected to be probability matrix from classifier
        probs = X

        # If no masking context, return unmasked probabilities
        if self.hearing is None:
            return probs, False
        
        # If class_mask is provided, use it directly
        if self.class_mask is not None:
            allowed_sections, parse_successful = self.class_mask
            masked_probs = self._apply_masking(probs, allowed_sections)
            return masked_probs, parse_successful

        raise ValueError("self.class_mask was not provided to Masker for _get_masked_probs")

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

        if self.classes_ is None:
            raise ValueError("classes_ not set on Masker. Cannot apply masking without class labels.")

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
