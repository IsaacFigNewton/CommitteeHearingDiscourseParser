from typing import Any, Dict, Iterator, List, Optional, Set, Tuple
from collections import defaultdict
from nltk.tree import Tree

from src.grammar.ParseNode import ParseNode
from ..dataclasses.Hearing import TaggedHearing
from .Grammar import GRAMMAR, SpeakerPositionEnum, TOP
from .Tokenizer import Tokenizer, Token


class Parser:
    """
    CYK parser over SpeakerPositionEnum token sequences.

    GRAMMAR is expected to contain only rules of the forms:
        A -> B C
        A -> B
        A -> epsilon
    where a unary RHS symbol that never appears on the left-hand side of a
    production is treated as a terminal.

    Unlike the previous implementation, backpointers now store *every*
    derivation of a (symbol, span) pair, so ambiguous grammars yield all
    parse trees (lazily, up to a caller-supplied limit).

    Binary rules must be strictly over nonterminals: terminals may only
    appear as the sole RHS of a unary rule (A -> terminal). A binary rule
    mentioning a terminal directly, e.g.
        CLOSING_REMARKS -> (PRESIDING_CHAIR, BILL_AUTHOR)
    would silently never fire in CYK (chart cells only ever contain
    nonterminals), so _index_rules raises a ValueError on such rules instead
    of letting them go dead. Route them through a preterminal instead.
    """

    def __init__(self,
            grammar_rules: List[Tuple] = GRAMMAR,
            tokenizer: Optional[Tokenizer] = None
        ):
        """Initialize the Parser with grammar rules in CNF and a tokenizer."""
        self.tokenizer = tokenizer or Tokenizer()
        self.grammar = self._parse_grammar(grammar_rules)

        # Separate CNF rules by type for efficient CYK parsing
        self.terminal_rules: Dict[Any, Set[Any]] = defaultdict(set)  # terminal -> {A | A -> terminal}
        self.binary_rules: Dict[Tuple[Any, Any], List[Any]] = defaultdict(list)  # (B, C) -> [A | A -> B C]
        self.unary_rules: Dict[Any, Set[Any]] = defaultdict(set)  # B -> {A | A -> B}
        self._index_rules()

    # ------------------------------------------------------------------ #
    # Grammar setup
    # ------------------------------------------------------------------ #

    @staticmethod
    def _parse_grammar(grammar_rules: List[Tuple]) -> Dict[Any, List[List[Any]]]:
        """
        Convert grammar rules into a dictionary mapping each left-hand symbol
        to a list of right-hand expansions (each expansion is a list).
        """
        grammar_dict: Dict[Any, List[List[Any]]] = {}
        for lhs, rhs in grammar_rules:
            grammar_dict.setdefault(lhs, [])
            grammar_dict[lhs].append(list(rhs) if isinstance(rhs, (list, tuple)) else [rhs])
        return grammar_dict

    def _is_terminal(self, symbol: Any) -> bool:
        """A symbol is a terminal if it never appears on the LHS of a production."""
        return symbol not in self.grammar

    def _index_rules(self) -> None:
        """Populate terminal/unary/binary rule indexes from the grammar."""
        for lhs, expansions in self.grammar.items():
            for rhs in expansions:
                # Epsilon productions: [] or [None]
                if len(rhs) == 0 or (len(rhs) == 1 and rhs[0] is None):
                    continue
                if len(rhs) == 1:
                    sym = rhs[0]
                    if self._is_terminal(sym):
                        self.terminal_rules[sym].add(lhs)
                    else:
                        self.unary_rules[sym].add(lhs)
                elif len(rhs) == 2:
                    self.binary_rules[(rhs[0], rhs[1])].append(lhs)
                else:
                    raise ValueError(
                        f"Grammar is not in CNF: {lhs} -> {rhs} has {len(rhs)} RHS symbols"
                    )

        # Strict CNF check: terminals may only appear as the sole RHS of a
        # unary rule. A terminal inside a binary RHS would silently never
        # fire (chart cells only ever contain nonterminals), so fail fast.
        bad_rules = [
            f"{lhs} -> ({b}, {c})"
            for (b, c), lhss in self.binary_rules.items()
            if self._is_terminal(b) or self._is_terminal(c)
            for lhs in lhss
        ]
        if bad_rules:
            raise ValueError(
                "Grammar is not in CNF: binary rules may not contain terminal "
                "RHS symbols (symbols that never appear on a LHS). Route them "
                "through a preterminal instead. Offending rules:\n  "
                + "\n  ".join(bad_rules)
            )

    @staticmethod
    def _matches_terminal(terminal: SpeakerPositionEnum, token: Token) -> bool:
        """
        Check if a token matches a terminal symbol.

        A token whose speaker position is None was unidentified and may match
        any terminal.
        """
        if terminal is None:
            return False

        if isinstance(terminal, SpeakerPositionEnum):
            token_speaker_position, _ = token
            return terminal == token_speaker_position or token_speaker_position is None

        return False

    # ------------------------------------------------------------------ #
    # Public parsing API
    # ------------------------------------------------------------------ #

    def parse(self, hearing: TaggedHearing) -> Optional[ParseNode]:
        """
        Construct a parse tree from the hearing's utterances using CYK.

        Returns:
            ParseNode for the root of the parse tree, or None if parsing fails
        """
        tokens = self.tokenizer.tokenize(hearing)
        return self.parse_tokens(tokens)

    def parse_tokens(self, tokens: List[Token]) -> Optional[ParseNode]:
        """Parse an already-tokenized sequence, returning the first parse found."""
        for tree in self.iter_parses_for_tokens(tokens, max_parses=1):
            return tree
        return None

    def get_all_parses(self, hearing: TaggedHearing, max_parses: int = 10) -> List[ParseNode]:
        """
        Get all possible parse trees for a hearing (up to max_parses).

        Ambiguous grammars can have exponentially many parses, so enumeration
        is lazy and stops as soon as max_parses trees have been produced.
        """
        tokens = self.tokenizer.tokenize(hearing)
        return list(self.iter_parses_for_tokens(tokens, max_parses=max_parses))

    def iter_parses_for_tokens(
        self, tokens: List[Token], max_parses: Optional[int] = None
    ) -> Iterator[ParseNode]:
        """
        Lazily yield parse trees for a token sequence, up to max_parses
        (or all of them if max_parses is None).
        """
        if not tokens:
            return

        table, backpointers = self._cyk_parse(tokens)
        n = len(tokens)

        if TOP.ROOT not in table[0][n - 1]:
            return

        count = 0
        for tree in self._enumerate_trees(backpointers, 0, n - 1, TOP.ROOT, tokens, frozenset()):
            yield tree
            count += 1
            if max_parses is not None and count >= max_parses:
                return

    # ------------------------------------------------------------------ #
    # CYK
    # ------------------------------------------------------------------ #

    def _cyk_parse(
        self, tokens: List[Token]
    ) -> Tuple[List[List[Set[Any]]], Dict[Tuple[Any, int, int], List[Tuple]]]:
        """
        CYK parsing algorithm.

        Returns:
            Tuple of (CYK table, backpointers for tree reconstruction).
            Each backpointer entry maps (symbol, i, j) to a *list* of all
            derivations of that symbol over that span.
        """
        n = len(tokens)

        # table[i][j] contains non-terminals that can derive tokens[i:j+1]
        table: List[List[Set[Any]]] = [[set() for _ in range(n)] for _ in range(n)]

        # (symbol, i, j) -> [(production_type, details...), ...]
        backpointers: Dict[Tuple[Any, int, int], List[Tuple]] = defaultdict(list)

        # Fill diagonal (single tokens)
        for i in range(n):
            token = tokens[i]
            for terminal, non_terminals in self.terminal_rules.items():
                if self._matches_terminal(terminal, token):
                    for nt in non_terminals:
                        table[i][i].add(nt)
                        self._add_backpointer(backpointers, nt, i, i, ('terminal', terminal, i))
            self._apply_unary_rules(table[i][i], backpointers, i, i)

        # Fill table bottom-up for spans of increasing length
        for length in range(2, n + 1):
            for i in range(n - length + 1):
                j = i + length - 1

                for k in range(i, j):
                    left_symbols = table[i][k]
                    right_symbols = table[k + 1][j]

                    for b in left_symbols:
                        for c in right_symbols:
                            if (b, c) in self.binary_rules:
                                for a in self.binary_rules[(b, c)]:
                                    table[i][j].add(a)
                                    self._add_backpointer(
                                        backpointers, a, i, j, ('binary', b, c, k)
                                    )

                self._apply_unary_rules(table[i][j], backpointers, i, j)

        return table, backpointers

    @staticmethod
    def _add_backpointer(
        backpointers: Dict[Tuple[Any, int, int], List[Tuple]],
        symbol: Any,
        i: int,
        j: int,
        derivation: Tuple,
    ) -> None:
        """Record a derivation for (symbol, i, j), skipping exact duplicates."""
        derivations = backpointers[(symbol, i, j)]
        if derivation not in derivations:
            derivations.append(derivation)

    def _apply_unary_rules(
        self,
        symbol_set: Set[Any],
        backpointers: Dict[Tuple[Any, int, int], List[Tuple]],
        i: int,
        j: int,
    ) -> None:
        """
        Apply unary rules (A -> B) to a cell.

        First computes the unary closure of the cell's symbol set, then records
        *every* applicable unary derivation as a backpointer — including ones
        whose parent symbol was already in the cell via another route. This is
        what preserves ambiguity across unary/binary derivations of the same
        symbol.
        """
        # 1. Closure over symbols
        changed = True
        while changed:
            changed = False
            new_symbols: Set[Any] = set()
            for b in symbol_set:
                for a in self.unary_rules.get(b, ()):
                    if a not in symbol_set and a not in new_symbols:
                        new_symbols.add(a)
                        changed = True
            symbol_set.update(new_symbols)

        # 2. Record all unary derivations among symbols now in the cell
        for b in symbol_set:
            for a in self.unary_rules.get(b, ()):
                self._add_backpointer(backpointers, a, i, j, ('unary', b))

    # ------------------------------------------------------------------ #
    # Tree enumeration
    # ------------------------------------------------------------------ #

    def _enumerate_trees(
        self,
        backpointers: Dict[Tuple[Any, int, int], List[Tuple]],
        i: int,
        j: int,
        symbol: Any,
        tokens: List[Token],
        unary_chain: frozenset,
    ) -> Iterator[ParseNode]:
        """
        Lazily yield every parse tree rooted at `symbol` over tokens[i:j+1].

        `unary_chain` holds the symbols already visited through unary rules at
        this same span; it guards against infinite loops when the grammar has
        unary cycles (A -> B, B -> A). It is reset whenever we descend through
        a terminal or binary derivation, since those change the span (or reach
        a leaf) and therefore cannot cycle.
        """
        for derivation in backpointers.get((symbol, i, j), ()):
            production_type = derivation[0]

            if production_type == 'terminal':
                _, terminal, token_idx_in_list = derivation
                _, utterance_idx = tokens[token_idx_in_list]
                yield ParseNode(
                    symbol=symbol,
                    children=[ParseNode(symbol=terminal, utterance_indices=[utterance_idx])],
                    utterance_indices=[utterance_idx],
                )

            elif production_type == 'unary':
                _, child_symbol = derivation
                if child_symbol in unary_chain:
                    continue  # unary cycle at this span; skip to avoid infinite recursion
                for child_node in self._enumerate_trees(
                    backpointers, i, j, child_symbol, tokens,
                    unary_chain | {symbol},
                ):
                    yield ParseNode(
                        symbol=symbol,
                        children=[child_node],
                        utterance_indices=child_node.utterance_indices,
                    )

            elif production_type == 'binary':
                _, left_symbol, right_symbol, k = derivation
                for left_node in self._enumerate_trees(
                    backpointers, i, k, left_symbol, tokens, frozenset()
                ):
                    for right_node in self._enumerate_trees(
                        backpointers, k + 1, j, right_symbol, tokens, frozenset()
                    ):
                        utterance_indices: List[int] = []
                        utterance_indices.extend(left_node.utterance_indices or [])
                        utterance_indices.extend(right_node.utterance_indices or [])
                        yield ParseNode(
                            symbol=symbol,
                            children=[left_node, right_node],
                            utterance_indices=utterance_indices or None,
                        )

    # ------------------------------------------------------------------ #
    # NLTK helpers
    # ------------------------------------------------------------------ #

    @staticmethod
    def parse_node_to_nltk_tree(parse_node: ParseNode) -> Tree:
        """Convert a ParseNode to an NLTK Tree."""
        return parse_node.to_nltk_tree()

    def parse_to_nltk_tree(self, hearing: TaggedHearing) -> Optional[Tree]:
        """Parse a hearing and return the result as an NLTK Tree, or None."""
        parse_node = self.parse(hearing)
        return parse_node.to_nltk_tree() if parse_node else None

    def get_all_parses_as_nltk_trees(self, hearing: TaggedHearing, max_parses: int = 3) -> List[Tree]:
        """Get all possible parse trees as NLTK Trees."""
        return [node.to_nltk_tree() for node in self.get_all_parses(hearing, max_parses)]