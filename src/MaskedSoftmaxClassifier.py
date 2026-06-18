import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.linear_model import LogisticRegression
from typing import Optional, List

from .speakers.validation.SectionRoleRequirementsEnum import SectionSpeakerRequirementsEnum
from .speakers.enums.SectionEnum import SectionEnum


class MaskedSoftmaxClassifier(BaseEstimator, ClassifierMixin):
    """
    A classifier that applies masked softmax based on speaker and utterance requirements.

    This classifier uses logistic regression internally but masks out invalid section predictions
    based on SectionSpeakerRequirementsEnum constraints. Invalid sections get -inf logits
    before softmax, ensuring they receive 0 probability.
    """

    def __init__(self, max_iter=2000, class_weight='balanced', solver='lbfgs'):
        self.max_iter = max_iter
        self.class_weight = class_weight
        self.solver = solver
        self.base_classifier = None
        self.classes_ = None
        self._section_to_idx = None

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

        # Create mapping from section name to index in the classes array
        self._section_to_idx = {cls: idx for idx, cls in enumerate(self.classes_)}

        return self

    def _get_mask_for_utterance(self, speaker_position: Optional[int],
                                 can_file_motion: bool,
                                 is_presenter: Optional[bool] = None) -> np.ndarray:
        """
        Generate a boolean mask indicating which sections are valid for this utterance.

        The 'OTHER' section is always available as a catch-all category.

        Args:
            speaker_position: Numeric speaker position value (or None)
            can_file_motion: Whether the speaker can file motions
            is_presenter: Whether the speaker is presenting (or None if unknown)

        Returns:
            Boolean array where True indicates the section is valid for this utterance
        """
        mask = np.ones(len(self.classes_), dtype=bool)

        for section_enum in SectionSpeakerRequirementsEnum:
            section_name = section_enum.name

            # Skip if this section is not in our trained classes
            if section_name not in self._section_to_idx:
                continue

            idx = self._section_to_idx[section_name]

            # OTHER is always available (has no restrictions)
            if section_name == 'OTHER':
                continue

            requirements = section_enum.value

            # Check speaker position constraints
            if requirements.valid_speaker_position_intervals is not None and speaker_position is not None:
                position_valid = False
                for min_pos, max_pos in requirements.valid_speaker_position_intervals:
                    if min_pos <= speaker_position <= max_pos:
                        position_valid = True
                        break
                if not position_valid:
                    mask[idx] = False
                    continue

            # Check can_file_motions constraint
            if requirements.can_file_motions is not None:
                if requirements.can_file_motions != can_file_motion:
                    mask[idx] = False
                    continue

            # Check is_presenter constraint
            if requirements.is_presenter is not None and is_presenter is not None:
                if requirements.is_presenter != is_presenter:
                    mask[idx] = False
                    continue

        return mask

    def _apply_mask_to_logits(self, logits: np.ndarray, masks: np.ndarray) -> np.ndarray:
        """
        Apply masks to logits by setting invalid positions to -inf.

        Args:
            logits: Decision function outputs (n_samples, n_classes)
            masks: Boolean masks (n_samples, n_classes) - True means valid

        Returns:
            Masked logits array
        """
        masked_logits = logits.copy()
        masked_logits[~masks] = -np.inf
        return masked_logits

    def _masked_softmax(self, logits: np.ndarray) -> np.ndarray:
        """
        Compute softmax with numerical stability.

        Args:
            logits: Logit array (n_samples, n_classes)

        Returns:
            Probability distribution over classes
        """
        # Subtract max for numerical stability (handles -inf properly)
        exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
        return exp_logits / np.sum(exp_logits, axis=1, keepdims=True)

    def predict_proba(self, X, speaker_positions=None, can_file_motions=None, is_presenters=None):
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
        if self.base_classifier is None:
            raise ValueError("Classifier must be fitted before calling predict_proba")

        # Get base logits from the underlying classifier
        logits = self.base_classifier.decision_function(X)

        # If no masking information provided, return standard probabilities
        if speaker_positions is None and can_file_motions is None:
            return self._masked_softmax(logits)

        n_samples = X.shape[0]
        masks = np.ones((n_samples, len(self.classes_)), dtype=bool)

        # Generate mask for each sample
        for i in range(n_samples):
            speaker_pos = speaker_positions[i] if speaker_positions is not None else None
            can_file = can_file_motions[i] if can_file_motions is not None else False
            is_pres = is_presenters[i] if is_presenters is not None else None

            masks[i] = self._get_mask_for_utterance(speaker_pos, can_file, is_pres)

        # Apply masks to logits
        masked_logits = self._apply_mask_to_logits(logits, masks)

        # Compute masked softmax
        return self._masked_softmax(masked_logits)

    def predict(self, X, speaker_positions=None, can_file_motions=None, is_presenters=None):
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
