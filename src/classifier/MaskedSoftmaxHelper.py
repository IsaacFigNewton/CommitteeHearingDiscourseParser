import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.linear_model import LogisticRegression
from typing import Optional, Dict, Set

from ..Grammar import Hearing_Grammar
from ..enums.SectionEnum import SectionEnum
from ..speakers.enums.SpeakerPositionEnum import SpeakerPositionEnum


class MaskedSoftmaxHelper:
    """
    Helper responsible for section masks, masked logits, masked softmax, and
    SectionEnum sequence-order smoothing.
    """

    def __init__(self,
            classes_: np.ndarray,
            section_smoothing: bool = True,
            section_smoothing_min_run_length: Optional[int] = 8
        ):
        self.classes_ = classes_
        self.section_smoothing = section_smoothing
        self.section_smoothing_min_run_length = section_smoothing_min_run_length

        # Create mapping from section name to index in the classes array.
        self.section_to_idx = {cls: idx for idx, cls in enumerate(self.classes_)}

        # Create a stable section ordering from SectionEnum. Classes outside
        # SectionEnum, such as OTHER, are intentionally excluded from ordering
        # constraints and remain available wherever the utterance mask allows them.
        self.section_order_by_name = {
            section.name: order for order, section in enumerate(SectionEnum)
        }

        # Extract valid speaker positions for each section from Hearing_Grammar
        self.section_valid_speakers = self._extract_valid_speakers_from_grammar()

    @staticmethod
    def _extract_valid_speakers_from_grammar() -> Dict[str, Set[SpeakerPositionEnum]]:
        """
        Extract valid speaker positions for each section from Hearing_Grammar.

        Returns a mapping from section name to set of valid SpeakerPositionEnum values.
        """
        valid_speakers = {}

        for key, value in Hearing_Grammar:
            # Check if value is a tuple of (SectionEnum, SpeakerPositionEnum)
            if isinstance(value, tuple) and len(value) == 2:
                section, speaker = value
                if isinstance(section, SectionEnum) and isinstance(speaker, SpeakerPositionEnum):
                    section_name = section.name
                    if section_name not in valid_speakers:
                        valid_speakers[section_name] = set()
                    valid_speakers[section_name].add(speaker)

        return valid_speakers

    def build_utterance_mask(self,
            speaker_position: Optional[int],
            can_file_motion: bool,
            is_presenter: Optional[bool] = None
        ) -> np.ndarray:
        """
        Generate a boolean mask indicating which sections are valid for one utterance.

        The 'OTHER' section is always available as a catch-all category.
        Uses Hearing_Grammar expansion rules to determine valid section-speaker combinations.
        """
        mask = np.ones(len(self.classes_), dtype=bool)

        # If no speaker position provided, return full mask
        if speaker_position is None:
            return mask

        # Convert speaker_position integer to SpeakerPositionEnum
        speaker_enum = None
        for sp in SpeakerPositionEnum:
            if sp.value == speaker_position:
                speaker_enum = sp
                break

        if speaker_enum is None:
            return mask

        # Apply grammar-based validation
        for section_name, idx in self.section_to_idx.items():
            # OTHER is always available (has no restrictions from grammar)
            if section_name == 'OTHER':
                continue

            # Check if this section has valid speakers defined in grammar
            if section_name in self.section_valid_speakers:
                valid_speakers = self.section_valid_speakers[section_name]
                if speaker_enum not in valid_speakers:
                    mask[idx] = False

        return mask

    def build_utterance_masks(self,
            n_samples: int,
            speaker_positions=None,
            can_file_motions=None,
            is_presenters=None
        ) -> np.ndarray:
        """Generate one mask per sample using the available utterance metadata."""
        masks = np.ones((n_samples, len(self.classes_)), dtype=bool)

        if speaker_positions is None and can_file_motions is None:
            return masks

        for i in range(n_samples):
            speaker_pos = speaker_positions[i] if speaker_positions is not None else None
            can_file = can_file_motions[i] if can_file_motions is not None else False
            is_pres = is_presenters[i] if is_presenters is not None else None

            masks[i] = self.build_utterance_mask(speaker_pos, can_file, is_pres)

        return masks

    @staticmethod
    def apply_mask_to_logits(logits: np.ndarray, masks: np.ndarray) -> np.ndarray:
        """Apply masks to logits by setting invalid positions to -inf."""
        masked_logits = logits.copy()
        masked_logits[~masks] = -np.inf
        return masked_logits

    @staticmethod
    def masked_softmax(logits: np.ndarray) -> np.ndarray:
        """Compute softmax with numerical stability."""
        exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
        return exp_logits / np.sum(exp_logits, axis=1, keepdims=True)

    def get_section_order(self, class_name: str) -> Optional[int]:
        """Return SectionEnum order for a class, or None for unordered classes."""
        return self.section_order_by_name.get(class_name)

    def build_section_order_masks(self,
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

        OTHER and any classes outside SectionEnum are not constrained by this
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
            label_order = self.get_section_order(label)

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
            for class_name, class_idx in self.section_to_idx.items():
                class_order = self.get_section_order(class_name)
                if class_order is not None and class_order < min_order:
                    order_masks[i, class_idx] = False

        return order_masks

    def apply_section_order_smoothing(self,
            logits: np.ndarray,
            masks: np.ndarray
        ) -> np.ndarray:
        """Apply SectionEnum ordering constraints to already utterance-masked logits."""
        initial_probas = self.masked_softmax(logits)
        order_masks = self.build_section_order_masks(initial_probas, masks)
        smoothed_masks = masks & order_masks

        # If speaker requirements plus ordering constraints remove every class
        # for a row, fall back to the utterance-level mask rather than returning
        # NaN probabilities from an all -inf softmax row.
        empty_rows = ~np.any(smoothed_masks, axis=1)
        if np.any(empty_rows):
            smoothed_masks[empty_rows] = masks[empty_rows]

        return self.apply_mask_to_logits(logits, smoothed_masks)

    def predict_proba_from_logits(self,
            logits: np.ndarray,
            speaker_positions=None,
            can_file_motions=None,
            is_presenters=None
        ) -> np.ndarray:
        """Apply utterance masking, optional smoothing, and masked softmax."""
        masks = self.build_utterance_masks(
            n_samples=logits.shape[0],
            speaker_positions=speaker_positions,
            can_file_motions=can_file_motions,
            is_presenters=is_presenters
        )

        masked_logits = self.apply_mask_to_logits(logits, masks)

        if self.section_smoothing:
            masked_logits = self.apply_section_order_smoothing(masked_logits, masks)

        return self.masked_softmax(masked_logits)
