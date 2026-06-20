import numpy as np
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.linear_model import LogisticRegression
from typing import Optional, Dict, Set, List, TYPE_CHECKING

from ..Grammar import Hearing_Grammar
from ..enums.SectionEnum import SectionEnum
from ..speakers.enums.SpeakerPositionEnum import SpeakerPositionEnum

if TYPE_CHECKING:
    from ..Tokenizer import ParseNode


class MaskedSoftmaxHelper:
    """
    Helper responsible for section masks, masked logits, masked softmax, and
    SectionEnum sequence-order smoothing.
    """

    def __init__(self,
            classes_: np.ndarray,
        ):
        self.classes_ = classes_

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

    @staticmethod
    def extract_valid_sections_from_parse_tree(
        parse_tree: Optional['ParseNode'],
        n_utterances: int
    ) -> Optional[Dict[int, Set[str]]]:
        """
        Extract valid section tags for each utterance from a parse tree.

        Args:
            parse_tree: ParseNode from Tokenizer.parse() or None
            n_utterances: Total number of utterances in the hearing

        Returns:
            Dict mapping utterance index to set of valid section names, or None if no parse tree
        """
        if parse_tree is None:
            return None

        utterance_to_sections = {i: set() for i in range(n_utterances)}

        def traverse(node: 'ParseNode'):
            """Recursively traverse parse tree to find section-utterance mappings."""
            # Check if this node is a SectionEnum
            if isinstance(node.symbol, SectionEnum):
                section_name = node.symbol.name
                # Add this section as valid for all utterances under this node
                if node.utterance_indices:
                    for utt_idx in node.utterance_indices:
                        utterance_to_sections[utt_idx].add(section_name)

            # Recurse on children
            if node.children:
                for child in node.children:
                    traverse(child)

        traverse(parse_tree)

        # Add OTHER as always available (fallback category)
        for section_set in utterance_to_sections.values():
            section_set.add('OTHER')

        return utterance_to_sections

    def build_utterance_mask(self,
            speaker_position: Optional[int],
            can_file_motion: bool,
            is_presenter: Optional[bool] = None,
            valid_sections: Optional[Set[str]] = None
        ) -> np.ndarray:
        """
        Generate a boolean mask indicating which sections are valid for one utterance.

        The 'OTHER' section is always available as a catch-all category.

        If valid_sections is provided (from parse tree), only those sections are allowed.
        Otherwise, uses Hearing_Grammar expansion rules to determine valid section-speaker combinations.

        Args:
            speaker_position: Speaker position enum value
            can_file_motion: Whether speaker can file motions
            is_presenter: Whether speaker is a presenter
            valid_sections: Set of valid section names from parse tree (optional)

        Returns:
            Boolean mask array indicating valid sections
        """
        mask = np.ones(len(self.classes_), dtype=bool)

        # If parse tree sections are provided, use them as primary constraint
        if valid_sections is not None:
            for section_name, idx in self.section_to_idx.items():
                if section_name not in valid_sections:
                    mask[idx] = False
            # Still apply speaker-based rules on top of parse tree constraints
            if speaker_position is not None:
                speaker_enum = None
                for sp in SpeakerPositionEnum:
                    if sp.value == speaker_position:
                        speaker_enum = sp
                        break

                if speaker_enum is not None:
                    for section_name, idx in self.section_to_idx.items():
                        # Skip if already masked out by parse tree
                        if not mask[idx]:
                            continue
                        # OTHER is always available
                        if section_name == 'OTHER':
                            continue
                        # Check speaker validity
                        if section_name in self.section_valid_speakers:
                            valid_speakers = self.section_valid_speakers[section_name]
                            if speaker_enum not in valid_speakers:
                                mask[idx] = False
            return mask

        # Fallback to grammar-based validation when no parse tree is available
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
            is_presenters=None,
            parse_tree: Optional['ParseNode'] = None
        ) -> np.ndarray:
        """
        Generate one mask per sample using the available utterance metadata.

        Args:
            n_samples: Number of samples (utterances)
            speaker_positions: Array of speaker position values
            can_file_motions: Array of can_file_motion booleans
            is_presenters: Array of is_presenter values
            parse_tree: Optional ParseNode from Tokenizer.parse()

        Returns:
            Boolean mask array of shape (n_samples, n_classes)
        """
        masks = np.ones((n_samples, len(self.classes_)), dtype=bool)

        # Extract valid sections from parse tree if available
        utterance_to_sections = self.extract_valid_sections_from_parse_tree(parse_tree, n_samples)

        if speaker_positions is None and can_file_motions is None and utterance_to_sections is None:
            return masks

        for i in range(n_samples):
            speaker_pos = speaker_positions[i] if speaker_positions is not None else None
            can_file = can_file_motions[i] if can_file_motions is not None else False
            is_pres = is_presenters[i] if is_presenters is not None else None
            valid_sections = utterance_to_sections[i] if utterance_to_sections is not None else None

            masks[i] = self.build_utterance_mask(speaker_pos, can_file, is_pres, valid_sections)

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

    def predict_proba_from_logits(self,
            logits: np.ndarray,
            speaker_positions=None,
            can_file_motions=None,
            is_presenters=None,
            parse_tree: Optional['ParseNode'] = None
        ) -> np.ndarray:
        """
        Apply utterance masking, optional smoothing, and masked softmax.

        Args:
            logits: Logit scores from classifier
            speaker_positions: Array of speaker position values
            can_file_motions: Array of can_file_motion booleans
            is_presenters: Array of is_presenter values
            parse_tree: Optional ParseNode from Tokenizer.parse()

        Returns:
            Probability matrix after masked softmax
        """
        masks = self.build_utterance_masks(
            n_samples=logits.shape[0],
            speaker_positions=speaker_positions,
            can_file_motions=can_file_motions,
            is_presenters=is_presenters,
            parse_tree=parse_tree
        )

        masked_logits = self.apply_mask_to_logits(logits, masks)

        return self.masked_softmax(masked_logits)
