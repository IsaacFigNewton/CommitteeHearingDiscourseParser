from collections import defaultdict, deque
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Set, Optional, Tuple

from src.grammar.Grammar import Rule
from src.grammar.Tokenizer import Tokenizer
from src.grammar.Parser import Parser
from src.enums.SectionEnum import SectionEnum
from src.speakers.enums.SpeakerPositionEnum import SpeakerPositionEnum
from src.dataclasses.Hearing import TaggedHearing


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
        parser: Parser,
        grammar: Optional[List[Rule]] = None,
        speaker_positions: Optional[Sequence[SpeakerPositionEnum|None]] = None,
        can_file_motions: Optional[Sequence[bool|None]] = None,
        is_presenters: Optional[Sequence[bool|None]] = None,
        max_parses: int = 2,
    ) -> Tuple[List[List[Any]], bool]:
        """Build allowed SectionEnums for each utterance in a hearing.

        1. Prefer all parse trees returned by
           Tokenizer.get_all_parses_as_nltk_trees(hearing, max_parses=2).
        2. If no parse trees are returned, infer the allowed sections from the
           speaker type plus SectionEnums reachable from GRAMMAR terminal rules.
        
        params:
            see code
        returns:
            masks:              list of lists of valid section tags associated with each utterance
            parse_successful:   whether >=1 parse tree was generated with the grammar
        """
        utterances = list(getattr(hearing, "utterances", []) or [])
        n = len(utterances)

        parse_trees: List[Any] = []
        try:
            parse_trees = list(
                parser.get_all_parses_as_nltk_trees(hearing, max_parses=max_parses)
                or []
            )
        except Exception:
            parse_trees = []
        
        # if there was at least 1 successful parse
        if len(parse_trees) > 0:
            masks: List[Set[Any]] = [set() for _ in range(n)]
            for tree in parse_trees:
                for idx, section in cls._sections_by_utterance_from_tree(tree, utterances).items():
                    if 0 <= idx < n:
                        masks[idx].update(section)

            # Only use parser-derived masks if at least one utterance was aligned.
            if any(masks):
                return [list(s) for s in masks], True

        return cls._allowed_sections_from_grammar_fallback(
            grammar=grammar,
            hearing=hearing,
            speaker_positions=speaker_positions,
            can_file_motions=can_file_motions,
            is_presenters=is_presenters,
        ), False

    @classmethod
    def _sections_by_utterance_from_tree(
        cls,
        tree: Any,
        utterances: Sequence[Any],
    ) -> Dict[int, Set[Any]]:
        """Extract SectionEnums for utterance leaves from an nltk Tree.

        The method supports two common tree shapes:
        - leaves are utterance-like objects or uid values
        - leaves are in the same order as hearing.utterances
        """
        n = len(utterances)
        uid_to_idx = {getattr(u, "uid", None): i for i, u in enumerate(utterances)}
        out: Dict[int, Set[Any]] = defaultdict(set)

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
        node: Any,
        ancestors: Sequence[Any] = (),
    ) -> Iterable[tuple[int, Any, Sequence[Any]]]:
        """Yield (leaf_position, leaf_value, ancestor_labels) for a Tree."""
        counter = 0

        def walk(cur: Any, labels: Sequence[Any]) -> Iterable[tuple[Any, Sequence[Any]]]:
            if cls._is_tree(cur):
                next_labels = (*labels, cur.label())
                for child in cur:
                    yield from walk(child, next_labels)
            else:
                yield cur, labels

        for leaf, labels in walk(node, ancestors):
            yield counter, leaf, labels
            counter += 1

    @staticmethod
    def _is_tree(value: Any) -> bool:
        return hasattr(value, "label") and hasattr(value, "__iter__") and not isinstance(value, (str, bytes))

    @classmethod
    def _first_section_label(cls, labels: Sequence[Any]) -> Any:
        for label in reversed(labels):
            section = cls._coerce_section(label)
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

    @classmethod
    def _allowed_sections_from_grammar_fallback(
        cls,
        grammar: Any,
        hearing: Any,
        speaker_positions: Optional[Sequence[Any]],
        can_file_motions: Optional[Sequence[Any]],
        is_presenters: Optional[Sequence[Any]],
    ) -> List[List[Any]]:
        """Fallback masks using terminal grammar rules and speaker type."""
        utterances = list(getattr(hearing, "utterances", []) or [])

        if grammar is None:
            try:
                from ..grammar.Grammar import GRAMMAR as grammar  # type: ignore
            except Exception:
                grammar = None

        terminal_to_sections = cls._terminal_to_reachable_sections(grammar)

        masks: List[List[Any]] = []
        for i, utt in enumerate(utterances):
            candidates = cls._speaker_terminal_candidates(
                utterance=utt,
                hearing=hearing,
                speaker_position=(speaker_positions[i] if speaker_positions is not None and i < len(speaker_positions) else None),
                can_file_motion=(can_file_motions[i] if can_file_motions is not None and i < len(can_file_motions) else None),
                is_presenter=(is_presenters[i] if is_presenters is not None and i < len(is_presenters) else None),
            )

            allowed: Set[Any] = set()
            for candidate in candidates:
                allowed.update(terminal_to_sections.get(candidate, set()))
                allowed.update(terminal_to_sections.get(str(candidate), set()))
                allowed.update(terminal_to_sections.get(str(candidate).upper(), set()))
                allowed.update(terminal_to_sections.get(str(candidate).lower(), set()))

            masks.append(list(allowed))

        return masks

    @classmethod
    def _terminal_to_reachable_sections(cls, grammar: Any) -> Dict[Any, Set[Any]]:
        """Map each terminal token in GRAMMAR to SectionEnums reachable from it."""
        if grammar is None or not hasattr(grammar, "productions"):
            return {}

        productions = list(grammar.productions())
        forward: Dict[str, Set[str]] = defaultdict(set)
        reverse: Dict[str, Set[str]] = defaultdict(set)
        terminal_lhs: Dict[Any, Set[str]] = defaultdict(set)

        for prod in productions:
            lhs = cls._symbol_name(prod.lhs())
            rhs = list(prod.rhs())

            has_nonterminal_rhs = False
            for sym in rhs:
                if cls._looks_like_nonterminal(sym):
                    rhs_name = cls._symbol_name(sym)
                    forward[lhs].add(rhs_name)
                    reverse[rhs_name].add(lhs)
                    has_nonterminal_rhs = True

            if not has_nonterminal_rhs:
                for terminal in rhs:
                    terminal_lhs[terminal].add(lhs)
                    terminal_lhs[str(terminal)].add(lhs)
                    terminal_lhs[str(terminal).upper()].add(lhs)
                    terminal_lhs[str(terminal).lower()].add(lhs)

        out: Dict[Any, Set[Any]] = defaultdict(set)
        graph = cls._merge_graphs(forward, reverse)

        for terminal, starts in terminal_lhs.items():
            seen: Set[str] = set()
            queue: deque[str] = deque(starts)

            while queue:
                symbol = queue.popleft()
                if symbol in seen:
                    continue
                seen.add(symbol)

                section = cls._coerce_section(symbol)
                if section is not None:
                    out[terminal].add(section)

                queue.extend(graph.get(symbol, set()) - seen)

        return out

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

    @classmethod
    def _speaker_terminal_candidates(
        cls,
        utterance: Any,
        hearing: Any,
        speaker_position: Any,
        can_file_motion: Any,
        is_presenter: Any,
    ) -> Set[Any]:
        candidates: Set[Any] = set()

        for value in (speaker_position, getattr(speaker_position, "name", None), getattr(speaker_position, "value", None)):
            if value is not None:
                candidates.add(value)
                candidates.add(str(value))

        pid = getattr(utterance, "pid", None)
        speaker = None
        try:
            speaker = getattr(hearing, "speakers", {}).get(pid)
        except Exception:
            speaker = None

        if speaker is not None:
            sp = getattr(speaker, "speaker_position", None)
            for value in (sp, getattr(sp, "name", None), getattr(sp, "value", None)):
                if value is not None:
                    candidates.add(value)
                    candidates.add(str(value))
            can_file_motion = getattr(speaker, "can_file_motions", can_file_motion)
            is_presenter = getattr(speaker, "is_presenter", is_presenter)

        if bool(can_file_motion):
            candidates.update({"can_file_motions", "CAN_FILE_MOTIONS", "motion_speaker", "MOTION_SPEAKER"})
        if bool(is_presenter):
            candidates.update({"is_presenter", "IS_PRESENTER", "presenter", "PRESENTER"})

        return candidates

    @classmethod
    def _coerce_section(cls, value: Any) -> Any:
        """Return a SectionEnum member for enum/name/value-like inputs."""
        if SectionEnum is None or value is None:
            return None

        if isinstance(value, SectionEnum):
            return value

        raw = cls._symbol_name(value)
        candidates = {
            raw,
            raw.strip(),
            raw.strip().upper(),
            raw.strip().lower(),
            raw.strip().replace("SectionEnum.", ""),
        }

        for candidate in candidates:
            try:
                return SectionEnum[candidate]
            except Exception:
                pass
            try:
                return SectionEnum(candidate)
            except Exception:
                pass

        return None

    @classmethod
    def _section_key(cls, value: Any) -> str:
        section = cls._coerce_section(value)
        if section is not None:
            return str(getattr(section, "name", section))
        if hasattr(value, "name"):
            return str(value.name)
        return str(value)