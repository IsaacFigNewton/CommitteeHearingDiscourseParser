import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.linear_model import LogisticRegression
from typing import Optional

from .speakers.validation.SectionRoleRequirementsEnum import SectionSpeakerRequirementsEnum
from .speakers.enums.SectionEnum import SectionEnum


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
            section_smoothing=True,
            section_smoothing_min_run_length=6
        ):
        self.max_iter = max_iter
        self.class_weight = class_weight
        self.solver = solver
        self.section_smoothing = section_smoothing
        self.section_smoothing_min_run_length = section_smoothing_min_run_length
        self.base_classifier = None
        self.classes_ = None
        self._section_to_idx = None
        self._section_order_by_name = None

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

        # Create a stable section ordering from SectionEnum. Classes outside
        # SectionEnum, such as OTHER, are intentionally excluded from ordering
        # constraints and remain available wherever the utterance mask allows them.
        self._section_order_by_name = {
            section.name: order for order, section in enumerate(SectionEnum)
        }

        return self

    def _get_mask_for_utterance(self,
            speaker_position: Optional[int],
            can_file_motion: bool,
            is_presenter: Optional[bool] = None
        ) -> np.ndarray:
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

    def _apply_mask_to_logits(self,
            logits: np.ndarray,
            masks: np.ndarray
        ) -> np.ndarray:
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

    def _get_section_order(self, class_name: str) -> Optional[int]:
        """Return SectionEnum order for a class, or None for unordered classes."""
        if self._section_order_by_name is None:
            return None
        return self._section_order_by_name.get(class_name)

    def _build_section_order_masks(self,
            probas: np.ndarray,
            masks: np.ndarray
        ) -> np.ndarray:
        """
        Build sequence-level masks that prevent backward section transitions.

        The smoother first looks at the utterance-level argmax sequence after
        speaker masking. When it sees a contiguous run of at least
        section_smoothing_min_run_length utterances assigned to a later
        SectionEnum value, it advances the minimum allowed section order from
        that point onward. Earlier SectionEnum sections are then masked out for
        subsequent utterances.

        This makes the ordering robust to isolated noisy predictions. For
        example, with the default threshold, a single PUBLIC_COMMENTS
        prediction will not block later EXPERT_TESTIMONY, but a sustained
        PUBLIC_COMMENTS block will. OTHER is not constrained by this
        ordering pass.
        """
        n_samples = probas.shape[0]
        order_masks = np.ones_like(masks, dtype=bool)

        if (not self.section_smoothing
                or self.section_smoothing_min_run_length is None
                or self.section_smoothing_min_run_length <= 0
                or n_samples == 0):
            return order_masks

        predicted_indices = np.argmax(probas, axis=1)
        predicted_labels = self.classes_[predicted_indices]

        # minimum_order_after[i] is the lowest SectionEnum order allowed at i.
        # It is updated only after a stable run has been observed.
        minimum_order_after = np.zeros(n_samples, dtype=int)
        current_min_order = 0
        run_label = None
        run_order = None
        run_start = 0
        run_length = 0

        for i, label in enumerate(predicted_labels):
            label_order = self._get_section_order(label)

            if label == run_label:
                run_length += 1
            else:
                run_label = label
                run_order = label_order
                run_start = i
                run_length = 1

            # Advance only on ordered section labels, never on OTHER/unordered.
            if (run_order is not None
                    and run_order > current_min_order
                    and run_length >= self.section_smoothing_min_run_length):
                current_min_order = run_order

                # Start enforcing at the beginning of the stable run, not only
                # after the threshold utterance, so the whole section block is
                # smoothed consistently.
                minimum_order_after[run_start:i + 1] = np.maximum(
                    minimum_order_after[run_start:i + 1],
                    current_min_order
                )

            minimum_order_after[i] = max(minimum_order_after[i], current_min_order)

        for i, min_order in enumerate(minimum_order_after):
            for class_name, class_idx in self._section_to_idx.items():
                class_order = self._get_section_order(class_name)
                if class_order is not None and class_order < min_order:
                    order_masks[i, class_idx] = False

        return order_masks

    def _apply_section_order_smoothing(self,
            logits: np.ndarray,
            masks: np.ndarray
        ) -> np.ndarray:
        """Apply SectionEnum ordering constraints to already utterance-masked logits."""
        initial_probas = self._masked_softmax(logits)
        order_masks = self._build_section_order_masks(initial_probas, masks)
        smoothed_masks = masks & order_masks

        # If speaker requirements plus ordering constraints remove every class
        # for a row, fall back to the utterance-level mask rather than returning
        # NaN probabilities from an all -inf softmax row.
        empty_rows = ~np.any(smoothed_masks, axis=1)
        if np.any(empty_rows):
            smoothed_masks[empty_rows] = masks[empty_rows]

        return self._apply_mask_to_logits(logits, smoothed_masks)

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
        if self.base_classifier is None:
            raise ValueError("Classifier must be fitted before calling predict_proba")

        # Get base logits from the underlying classifier
        logits = self._normalize_logits_shape(self.base_classifier.decision_function(X))

        # If no masking information provided, optionally still apply
        # SectionEnum sequence smoothing across the utterance batch.
        if speaker_positions is None and can_file_motions is None:
            masks = np.ones((X.shape[0], len(self.classes_)), dtype=bool)
            if self.section_smoothing:
                logits = self._apply_section_order_smoothing(logits, masks)
            return self._masked_softmax(logits)

        n_samples = X.shape[0]
        masks = np.ones((n_samples, len(self.classes_)), dtype=bool)

        # Generate mask for each sample
        for i in range(n_samples):
            speaker_pos = speaker_positions[i] if speaker_positions is not None else None
            can_file = can_file_motions[i] if can_file_motions is not None else False
            is_pres = is_presenters[i] if is_presenters is not None else None

            masks[i] = self._get_mask_for_utterance(speaker_pos, can_file, is_pres)

        # Apply utterance-level masks to logits
        masked_logits = self._apply_mask_to_logits(logits, masks)

        # Apply SectionEnum sequence smoothing so stable later sections prevent
        # later backward jumps to earlier sections.
        if self.section_smoothing:
            masked_logits = self._apply_section_order_smoothing(masked_logits, masks)

        # Compute masked softmax
        return self._masked_softmax(masked_logits)

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
