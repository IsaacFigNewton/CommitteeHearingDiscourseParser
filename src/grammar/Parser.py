from typing import List, Optional, Tuple, Dict, Any, Set
from collections import defaultdict
from nltk.tree import Tree

from src.grammar.ParseNode import ParseNode
from ..dataclasses.Hearing import TaggedHearing
from ..speakers.enums.SpeakerPositionEnum import SpeakerPositionEnum
from .Grammar import GRAMMAR, Terminal, TOP
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

    @staticmethod
    def _matches_terminal(terminal: Terminal, token: Token) -> bool:
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
        """Parse an already-tokenized sequence."""
        if not tokens:
            return None

        table, backpointers = self._cyk_parse(tokens)
        n = len(tokens)

        if TOP.ROOT in table[0][n - 1]:
            return self._reconstruct_parse_tree(table, backpointers, 0, n - 1, TOP.ROOT, tokens)

        return None

    def get_all_parses(self, hearing: TaggedHearing, max_parses: int = 10) -> List[ParseNode]:
        """
        Get all possible parse trees for a hearing (up to max_parses).

        Note: this implementation currently returns at most one parse. It can be
        extended to enumerate all trees by tracking every backpointer.
        """
        result = self.parse(hearing)
        return [result] if result else []

    # ------------------------------------------------------------------ #
    # CYK
    # ------------------------------------------------------------------ #

    def _cyk_parse(self, tokens: List[Token]) -> Tuple[List[List[Set[Any]]], Dict]:
        """
        CYK parsing algorithm.

        Returns:
            Tuple of (CYK table, backpointers for tree reconstruction)
        """
        n = len(tokens)

        # table[i][j] contains non-terminals that can derive tokens[i:j+1]
        table: List[List[Set[Any]]] = [[set() for _ in range(n)] for _ in range(n)]

        # (symbol, i, j) -> (production_type, details...)
        backpointers: Dict[Tuple[Any, int, int], Tuple] = {}

        # Fill diagonal (single tokens)
        for i in range(n):
            token = tokens[i]
            for terminal, non_terminals in self.terminal_rules.items():
                if self._matches_terminal(terminal, token):
                    for nt in non_terminals:
                        table[i][i].add(nt)
                        backpointers[(nt, i, i)] = ('terminal', terminal, i)
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
                                    backpointers[(a, i, j)] = ('binary', b, c, k)

                self._apply_unary_rules(table[i][j], backpointers, i, j)

        return table, backpointers

    def _apply_unary_rules(self, symbol_set: Set[Any], backpointers: Dict, i: int, j: int) -> None:
        """Apply unary rules (A -> B) to a cell until no new symbols can be added."""
        changed = True
        while changed:
            changed = False
            new_symbols: Set[Any] = set()

            for b in symbol_set:
                for a in self.unary_rules.get(b, ()):
                    if a not in symbol_set and a not in new_symbols:
                        new_symbols.add(a)
                        backpointers[(a, i, j)] = ('unary', b)
                        changed = True

            symbol_set.update(new_symbols)

    # ------------------------------------------------------------------ #
    # Tree reconstruction
    # ------------------------------------------------------------------ #

    def _reconstruct_parse_tree(
        self,
        table: List[List[Set[Any]]],
        backpointers: Dict,
        i: int,
        j: int,
        symbol: Any,
        tokens: List[Token],
    ) -> Optional[ParseNode]:
        """Reconstruct a parse tree from the CYK table and backpointers."""
        if (symbol, i, j) not in backpointers:
            return None

        production_info = backpointers[(symbol, i, j)]
        production_type = production_info[0]

        if production_type == 'terminal':
            _, terminal, token_idx_in_list = production_info
            _, utterance_idx = tokens[token_idx_in_list]

            return ParseNode(
                symbol=symbol,
                children=[ParseNode(symbol=terminal, utterance_indices=[utterance_idx])],
                utterance_indices=[utterance_idx],
            )

        if production_type == 'unary':
            _, child_symbol = production_info
            child_node = self._reconstruct_parse_tree(table, backpointers, i, j, child_symbol, tokens)
            if child_node:
                return ParseNode(
                    symbol=symbol,
                    children=[child_node],
                    utterance_indices=child_node.utterance_indices,
                )

        if production_type == 'binary':
            _, left_symbol, right_symbol, k = production_info
            left_node = self._reconstruct_parse_tree(table, backpointers, i, k, left_symbol, tokens)
            right_node = self._reconstruct_parse_tree(table, backpointers, k + 1, j, right_symbol, tokens)

            if left_node and right_node:
                utterance_indices: List[int] = []
                utterance_indices.extend(left_node.utterance_indices or [])
                utterance_indices.extend(right_node.utterance_indices or [])

                return ParseNode(
                    symbol=symbol,
                    children=[left_node, right_node],
                    utterance_indices=utterance_indices or None,
                )

        return None

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

    def get_all_parses_as_nltk_trees(self, hearing: TaggedHearing, max_parses: int = 10) -> List[Tree]:
        """Get all possible parse trees as NLTK Trees."""
        return [node.to_nltk_tree() for node in self.get_all_parses(hearing, max_parses)]
