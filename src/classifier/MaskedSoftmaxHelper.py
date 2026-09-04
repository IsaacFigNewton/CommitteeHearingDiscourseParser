from collections import defaultdict, deque
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Set, Optional, Tuple
from nltk.tree import Tree

from src.grammar.Grammar import Rule, GRAMMAR, SPEAKER_REACHABLE_SECTIONS
from src.enums.SectionEnum import SectionEnum
from src.speakers.enums.SpeakerPositionEnum import SpeakerPositionEnum
from src.dataclasses.Hearing import TaggedHearing
from src.dataclasses.OralContribution import TaggedOralContribution


class MaskedSoftmaxHelper:
    """Utilities for building and applying grammar/parser-constrained masks.

    This helper owns the non-estimator logic used by masking components:
    - building per-utterance allowed SectionEnum masks for a hearing
    - reading SectionEnum ancestors from parser trees
    - deriving fallback masks from grammar terminal rules and speaker metadata
    - normalizing enum/name/value-like section labels into stable keys

    Used by:
    - MaskedClassifier (new pipeline-based approach)
    - SoftmaxMaskingTransformer (alternative transformer-based approach)
    - MaskedSoftmaxClassifier (deprecated, backward compatibility only)
    """

    @classmethod
    def allowed_sections_for_hearing(
        cls,
        hearing: TaggedHearing,
        parse_trees: Optional[List[Tree]] = None,
    ) -> List[Optional[List[SectionEnum]]]:
        """Build allowed SectionEnums for each utterance in a hearing.

        1. Prefer all parse trees provided via parse_trees parameter.
        2. If no parse trees are provided, infer the allowed sections from the
           speaker type plus SectionEnums reachable from GRAMMAR terminal rules.

        params:
            hearing: TaggedHearing object
            parser: Parser instance (kept for backwards compatibility but not used for parsing here)
            speaker_positions: Sequence of speaker positions
            can_file_motions: Sequence of can_file_motions flags
            is_presenters: Sequence of is_presenter flags
            max_parses: Maximum number of parses (kept for backwards compatibility)
            parse_trees: Pre-generated parse trees from parser.get_all_parses_as_nltk_trees()
        returns:
            masks:              list of lists of valid section tags associated with each utterance
            parse_successful:   whether >=1 parse tree was generated with the grammar
        """
        utterances = list(getattr(hearing, "utterances", []) or [])
        n = len(utterances)

        # Use provided parse trees if available
        if parse_trees is None:
            parse_trees = []

        # If we got at least one valid parse tree, use it
        if len(parse_trees) > 0:
            masks: List[Set[SectionEnum]] = [set() for _ in range(n)]

            # Collect allowed sections from all parse trees
            # Multiple parses can provide different section possibilities
            for tree in parse_trees:
                for idx, section in cls._sections_by_utterance_from_tree(tree, utterances).items():
                    if 0 <= idx < n:
                        masks[idx].update(section)

            # Only use parser-derived masks if at least one utterance was aligned
            # Empty masks mean the parse trees didn't help, so fall back
            if any(masks):
                return [list(s) for s in masks]
    
        # Fallback to Nonterminal -> TerminalEnum rules to constrain predictions
        #   based on speaker attributes without requiring a full parse
        masks: List[Optional[List[SectionEnum]]] = []
        for utt in utterances:
            pid = utt.pid
            speaker = hearing.speakers.get(pid)
            if speaker is not None and speaker.speaker_position is not None:
                masks.append(list(SPEAKER_REACHABLE_SECTIONS.get(speaker.speaker_position, [])))
            # if no speaker position available
            else:
                masks.append(None)
        return masks

    @classmethod
    def _sections_by_utterance_from_tree(
        cls,
        tree: Tree,
        utterances: Sequence[TaggedOralContribution],
    ) -> Dict[int, Set[SectionEnum]]:
        """Extract SectionEnums for utterance leaves from an nltk Tree.

        The method supports two common tree shapes:
        - leaves are utterance-like objects or uid values
        - leaves are in the same order as hearing.utterances
        """
        n = len(utterances)
        uid_to_idx = {getattr(u, "uid", None): i for i, u in enumerate(utterances)}
        out: Dict[int, Set[SectionEnum]] = defaultdict(set)

        leaf_records = list(cls._iter_leaf_records(tree))
        positional_alignment_ok = len(leaf_records) == n

        for pos, leaf, ancestor_labels in leaf_records:
            section = cls._first_section_label(ancestor_labels)
            if section is None:
                continue

            idx = cls._leaf_to_utterance_index(leaf, uid_to_idx)
            if idx is None and positional_alignment_ok:
                idx = pos

            if idx is not None and 0 <= idx < n:
                out[idx].add(section)

        return out

    @classmethod
    def _iter_leaf_records(
        cls,
        node: Tree,
        ancestors: List[SectionEnum] = list(),
    ) -> Iterable[tuple[int, Tree, Sequence[SectionEnum]]]:
        """Yield (leaf_position, leaf_value, ancestor_labels) for a Tree."""
        counter = 0

        def walk(cur: Tree, labels: Sequence[SectionEnum]) -> Iterable[tuple[Tree, Sequence[SectionEnum]]]:
            if isinstance(cur, Tree):
                next_labels = (*labels, cur.label())
                for child in cur:
                    yield from walk(child, next_labels)
            else:
                yield cur, labels

        for leaf, labels in walk(node, ancestors):
            yield counter, leaf, labels
            counter += 1

    @classmethod
    def _first_section_label(cls, labels: Sequence[SectionEnum]) -> Any:
        for section in reversed(labels):
            if section is not None:
                return section
        return None

    @staticmethod
    def _leaf_to_utterance_index(leaf: Any, uid_to_idx: Mapping[Any, int]) -> Optional[int]:
        if hasattr(leaf, "uid") and getattr(leaf, "uid") in uid_to_idx:
            return uid_to_idx[getattr(leaf, "uid")]
        if leaf in uid_to_idx:
            return uid_to_idx[leaf]
        if isinstance(leaf, str) and leaf.isdigit():
            numeric = int(leaf)
            if numeric in uid_to_idx:
                return uid_to_idx[numeric]
        return None


    @staticmethod
    def _merge_graphs(*graphs: Mapping[str, Set[str]]) -> Dict[str, Set[str]]:
        merged: Dict[str, Set[str]] = defaultdict(set)
        for graph in graphs:
            for src, dsts in graph.items():
                merged[src].update(dsts)
        return merged

    @staticmethod
    def _looks_like_nonterminal(symbol: Any) -> bool:
        return hasattr(symbol, "symbol") or not isinstance(symbol, (str, bytes, int, float, bool))

    @staticmethod
    def _symbol_name(symbol: Any) -> str:
        if hasattr(symbol, "symbol"):
            return str(symbol.symbol())
        return str(symbol)