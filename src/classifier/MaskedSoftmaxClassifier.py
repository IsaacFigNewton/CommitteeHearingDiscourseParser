import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.linear_model import LogisticRegression
from typing import Optional
from .MaskedSoftmaxHelper import MaskedSoftmaxHelper


class MaskedSoftmaxClassifier(BaseEstimator, ClassifierMixin):
    """
    A classifier that applies masked softmax based on speaker and utterance requirements.

    This classifier uses logistic regression internally but masks out invalid section predictions
    based on SectionSpeakerRequirementsEnum constraints. Invalid sections get -inf logits
    before softmax, ensuring they receive 0 probability.
    """

    def __init__(self,
            max_iter=2000,
            class_weight='balanced',
            solver='lbfgs',
            section_smoothing=False,
            section_smoothing_min_run_length=2
        ):
        self.max_iter = max_iter
        self.class_weight = class_weight
        self.solver = solver
        self.section_smoothing = section_smoothing
        self.section_smoothing_min_run_length = section_smoothing_min_run_length
        self.base_classifier = None
        self.classes_ = None
        self.mask_helper_ = None

    def fit(self, X, y):
        """
        Fit the underlying logistic regression model.

        Args:
            X: Feature matrix
            y: Target labels (section names as strings)
        """
        self.base_classifier = LogisticRegression(
            max_iter=self.max_iter,
            class_weight=self.class_weight,
            solver=self.solver
        )
        self.base_classifier.fit(X, y)
        self.classes_ = self.base_classifier.classes_
        self.mask_helper_ = MaskedSoftmaxHelper(
            classes_=self.classes_,
            section_smoothing=self.section_smoothing,
            section_smoothing_min_run_length=self.section_smoothing_min_run_length
        )

        return self

    def _normalize_logits_shape(self, logits: np.ndarray) -> np.ndarray:
        """
        Normalize sklearn decision_function output to shape (n_samples, n_classes).

        LogisticRegression.decision_function returns a 1D array for binary
        classification. This classifier expects one logit column per class so
        that masking and smoothing can be applied consistently.
        """
        if logits.ndim == 1:
            return np.column_stack([-logits, logits])
        return logits

    def _require_fitted(self):
        if self.base_classifier is None or self.mask_helper_ is None:
            raise ValueError("Classifier must be fitted before calling predict_proba")

    # Backward-compatible delegates for existing tests or callers that use the
    # previous private helper methods directly.
    def _get_mask_for_utterance(self,
            speaker_position: Optional[int],
            can_file_motion: bool,
            is_presenter: Optional[bool] = None
        ) -> np.ndarray:
        self._require_fitted()
        return self.mask_helper_.build_utterance_mask(
            speaker_position,
            can_file_motion,
            is_presenter
        )

    def _apply_mask_to_logits(self,
            logits: np.ndarray,
            masks: np.ndarray
        ) -> np.ndarray:
        return MaskedSoftmaxHelper.apply_mask_to_logits(logits, masks)

    def _masked_softmax(self, logits: np.ndarray) -> np.ndarray:
        return MaskedSoftmaxHelper.masked_softmax(logits)

    def _get_section_order(self, class_name: str) -> Optional[int]:
        self._require_fitted()
        return self.mask_helper_.get_section_order(class_name)

    def _build_section_order_masks(self,
            probas: np.ndarray,
            masks: np.ndarray
        ) -> np.ndarray:
        self._require_fitted()
        return self.mask_helper_.build_section_order_masks(probas, masks)

    def _apply_section_order_smoothing(self,
            logits: np.ndarray,
            masks: np.ndarray
        ) -> np.ndarray:
        self._require_fitted()
        return self.mask_helper_.apply_section_order_smoothing(logits, masks)

    def predict_proba(self,
            X,
            speaker_positions=None,
            can_file_motions=None,
            is_presenters=None
        ):
        """
        Predict class probabilities with masking.

        Args:
            X: Feature matrix
            speaker_positions: Array of speaker position values (or None)
            can_file_motions: Array of can_file_motion boolean values (or None)
            is_presenters: Array of is_presenter values (or None)

        Returns:
            Probability matrix (n_samples, n_classes)
        """
        self._require_fitted()

        # Get base logits from the underlying classifier.
        logits = self._normalize_logits_shape(self.base_classifier.decision_function(X))

        return self.mask_helper_.predict_proba_from_logits(
            logits,
            speaker_positions=speaker_positions,
            can_file_motions=can_file_motions,
            is_presenters=is_presenters
        )

    def predict(self,
            X,
            speaker_positions=None,
            can_file_motions=None,
            is_presenters=None
        ):
        """
        Predict class labels with masking.

        Args:
            X: Feature matrix
            speaker_positions: Array of speaker position values (or None)
            can_file_motions: Array of can_file_motion boolean values (or None)
            is_presenters: Array of is_presenter values (or None)

        Returns:
            Array of predicted class labels
        """
        probas = self.predict_proba(X, speaker_positions, can_file_motions, is_presenters)
        return self.classes_[np.argmax(probas, axis=1)]
