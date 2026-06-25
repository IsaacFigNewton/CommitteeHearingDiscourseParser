from typing import List, Optional, Tuple, Dict, Any, Set
from dataclasses import dataclass
from collections import defaultdict

try:
    from nltk.tree import Tree
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False

from .dataclasses.Hearing import TaggedHearing
from .speakers.enums.SpeakerPositionEnum import SpeakerPositionEnum
from .enums.SectionEnum import SectionEnum
from .Grammar import GRAMMAR, Terminal, TOP


@dataclass
class ParseNode:
    """Represents a node in the parse tree."""
    symbol: Any  # Can be ROOT, TOP, SectionEnum, or Terminal
    children: Optional[List['ParseNode']] = None
    utterance_indices: Optional[List[int]] = None  # Track which utterances this node covers

    def __repr__(self, level=0):
        indent = "  " * level
        if self.children:
            children_repr = "\n".join(child.__repr__(level + 1) for child in self.children)
            return f"{indent}{self.symbol}\n{children_repr}"
        else:
            return f"{indent}{self.symbol} (utterances: {self.utterance_indices})"

    def to_nltk_tree(self) -> 'Tree':
        """
        Convert this ParseNode to an NLTK Tree.

        Returns:
            NLTK Tree representation of this parse tree

        Raises:
            ImportError: If NLTK is not installed
        """
        if not NLTK_AVAILABLE:
            raise ImportError("NLTK is not installed. Install it with: pip install nltk")

        return self._to_nltk_tree_recursive()

    def _to_nltk_tree_recursive(self) -> 'Tree':
        """Recursively convert ParseNode to NLTK Tree."""
        # Format the label based on symbol type
        label = self._format_symbol_label(self.symbol)

        if self.children:
            # Non-terminal node: recursively convert children
            nltk_children = [child._to_nltk_tree_recursive() for child in self.children]
            return Tree(label, nltk_children)
        else:
            # Terminal node: use utterance indices as leaves
            if self.utterance_indices:
                return Tree(label, [f"utt_{idx}" for idx in self.utterance_indices])
            else:
                return Tree(label, [])

    @staticmethod
    def _format_symbol_label(symbol: Any) -> str:
        """Format a symbol for use as an NLTK Tree label."""
        if isinstance(symbol, str):
            # ROOT symbol or generated CNF symbols
            return symbol
        elif hasattr(symbol, 'name'):
            # Enum types (TOP, SectionEnum, SpeakerPositionEnum)
            return symbol.name
        else:
            return str(symbol)


class Tokenizer:
    """
    Tokenizes utterances from a TaggedHearing into a sequence of SpeakerPositionEnums
    and constructs parse trees using CYK parsing algorithm.
    """

    def __init__(self):
        """Initialize the Tokenizer with the grammar rules converted to CNF."""
        self.original_grammar = self._parse_grammar(GRAMMAR)

        # Separate CNF rules by type for efficient CYK parsing
        self.terminal_rules = {}  # Maps terminals to set of non-terminals
        self.binary_rules = defaultdict(list)  # Maps (B, C) to list of A where A -> BC
        self.unary_rules = defaultdict(set)  # Maps B to set of A where A -> B

        # Convert grammar to Chomsky Normal Form (CNF)
        self.cnf_grammar, self.reverse_cnf = self._convert_to_cnf(self.original_grammar)

    @staticmethod
    def _parse_grammar(grammar_rules: List[Tuple]) -> Dict[Any, List[Any]]:
        """
        Convert grammar rules into a more accessible dictionary format.

        Args:
            grammar_rules: List of (lhs, rhs) tuples from Hearing_Grammar

        Returns:
            Dictionary mapping left-hand symbols to lists of possible right-hand expansions
        """
        grammar_dict = {}
        for lhs, rhs in grammar_rules:
            if lhs not in grammar_dict:
                grammar_dict[lhs] = []
            # Ensure rhs is always a list
            if isinstance(rhs, list):
                grammar_dict[lhs].append(rhs)
            else:
                grammar_dict[lhs].append([rhs])
        return grammar_dict

    def _convert_to_cnf(self, grammar: Dict[Any, List[Any]]) -> Tuple[Dict[Any, List[Any]], Dict[Any, Any]]:
        """
        Convert grammar to Chomsky Normal Form (CNF).

        CNF rules are:
        - A -> BC (two non-terminals)
        - A -> a (single terminal)
        - S -> ε (only for start symbol, we don't handle empty strings)

        Args:
            grammar: Original grammar dictionary

        Returns:
            Tuple of (CNF grammar dict, reverse mapping for generated symbols)
        """
        cnf_grammar = {}
        reverse_cnf = {}  # Maps generated symbols back to original productions
        generated_symbol_counter = [0]  # Use list to make it mutable in nested function

        def generate_symbol(original_lhs: Any, production: List[Any]) -> Any:
            """Generate a unique symbol for intermediate productions."""
            generated_symbol_counter[0] += 1
            symbol = f"_GEN_{generated_symbol_counter[0]}"
            reverse_cnf[symbol] = (original_lhs, production)
            return symbol

        # Process each production rule
        for lhs, productions in grammar.items():
            if lhs not in cnf_grammar:
                cnf_grammar[lhs] = []

            for production in productions:
                if len(production) == 1:
                    # Unary rule or terminal - already in CNF form
                    rhs = production[0]
                    if self._is_terminal(rhs):
                        # Terminal rule: A -> a
                        if rhs not in self.terminal_rules:
                            self.terminal_rules[rhs] = set()
                        self.terminal_rules[rhs].add(lhs)
                    else:
                        # Unary rule: A -> B
                        self.unary_rules[rhs].add(lhs)
                    cnf_grammar[lhs].append(production)

                elif len(production) == 2:
                    # Binary rule: A -> BC (already in CNF)
                    b, c = production
                    self.binary_rules[(b, c)].append(lhs)
                    cnf_grammar[lhs].append(production)

                else:
                    # Production with > 2 symbols: A -> B C D ...
                    # Convert to binary by introducing intermediate symbols
                    # A -> B X1, X1 -> C X2, X2 -> D ...
                    symbols = production[:]
                    current_lhs = lhs

                    while len(symbols) > 2:
                        # Take first symbol and group the rest
                        first = symbols[0]
                        rest = symbols[1:]

                        # Generate intermediate symbol for the rest
                        intermediate = generate_symbol(current_lhs, symbols)

                        # Add binary rule: current_lhs -> first intermediate
                        if current_lhs not in cnf_grammar:
                            cnf_grammar[current_lhs] = []
                        cnf_grammar[current_lhs].append([first, intermediate])
                        self.binary_rules[(first, intermediate)].append(current_lhs)

                        # Continue with the intermediate symbol
                        current_lhs = intermediate
                        symbols = rest

                    # Final binary rule for last two symbols
                    if current_lhs not in cnf_grammar:
                        cnf_grammar[current_lhs] = []
                    cnf_grammar[current_lhs].append(symbols)
                    self.binary_rules[tuple(symbols)].append(current_lhs)

        return cnf_grammar, reverse_cnf

    def _is_terminal(self, symbol: Any) -> bool:
        """Check if a symbol is a terminal (has no grammar expansions)."""
        if isinstance(symbol, tuple):
            # Terminals are (SectionEnum, SpeakerPositionEnum) tuples
            return True
        if symbol not in self.original_grammar and not isinstance(symbol, str):
            # If not in grammar and not a generated symbol, it's a terminal
            return True
        return False

    def tokenize_utterances(self, hearing: TaggedHearing) -> List[Tuple[SpeakerPositionEnum, int]]:
        """
        Extract SpeakerPositionEnum tokens from hearing utterances.

        Args:
            hearing: TaggedHearing with speakers and utterances

        Returns:
            List of (SpeakerPositionEnum, utterance_index) tuples
        """
        tokens = []
        for idx, utterance in enumerate(hearing.utterances):
            speaker = hearing.speakers.get(utterance.pid)
            if speaker and speaker.speaker_position:
                tokens.append((speaker.speaker_position, idx))
        return tokens

    def _matches_terminal(self, terminal: Terminal, token: Tuple[SpeakerPositionEnum, int]) -> bool:
        """
        Check if a token matches a terminal symbol.

        Args:
            terminal: Terminal from grammar (SpeakerPositionEnum)
            token: (SpeakerPositionEnum, utterance_index) tuple

        Returns:
            True if token matches terminal
        """
        if terminal is None:
            return False

        # Terminal is now just a SpeakerPositionEnum
        if isinstance(terminal, SpeakerPositionEnum):
            token_speaker_position, _ = token
            return terminal == token_speaker_position

        return False

    def parse(self, hearing: TaggedHearing) -> Optional[ParseNode]:
        """
        Construct a parse tree from the hearing's utterances using CYK algorithm.

        Args:
            hearing: TaggedHearing to parse

        Returns:
            ParseNode representing the root of the parse tree, or None if parsing fails
        """
        tokens = self.tokenize_utterances(hearing)

        if not tokens:
            return None

        # Run CYK algorithm
        table, backpointers = self._cyk_parse(tokens)
        n = len(tokens)

        # Check if ROOT symbol spans the entire input
        if TOP.ROOT in table[0][n - 1]:
            # Reconstruct parse tree
            return self._reconstruct_parse_tree(table, backpointers, 0, n - 1, TOP.ROOT, tokens)

        return None

    def _cyk_parse(self, tokens: List[Tuple[SpeakerPositionEnum, int]]) -> Tuple[List[List[Set[Any]]], Dict]:
        """
        CYK parsing algorithm.

        Args:
            tokens: List of (SpeakerPositionEnum, utterance_index) tuples

        Returns:
            Tuple of (CYK table, backpointers for tree reconstruction)
        """
        n = len(tokens)

        # Initialize CYK table: table[i][j] contains non-terminals that can derive tokens[i:j+1]
        table = [[set() for _ in range(n)] for _ in range(n)]

        # Backpointers for tree reconstruction: (symbol, i, j) -> (production_type, details)
        backpointers = {}

        # Fill diagonal (single tokens)
        for i in range(n):
            token = tokens[i]

            # Find all terminals that match this token
            for terminal, non_terminals in self.terminal_rules.items():
                if self._matches_terminal(terminal, token):
                    for nt in non_terminals:
                        table[i][i].add(nt)
                        backpointers[(nt, i, i)] = ('terminal', terminal, i)

        # Apply unary rules to diagonal
        for i in range(n):
            self._apply_unary_rules(table[i][i], backpointers, i, i)

        # Fill table bottom-up for spans of increasing length
        for length in range(2, n + 1):  # length of span
            for i in range(n - length + 1):  # start position
                j = i + length - 1  # end position

                # Try all possible split points
                for k in range(i, j):  # k is the split point
                    # Get symbols that can derive left and right parts
                    left_symbols = table[i][k]
                    right_symbols = table[k + 1][j]

                    # Try all combinations
                    for b in left_symbols:
                        for c in right_symbols:
                            # Check if there's a rule A -> BC
                            if (b, c) in self.binary_rules:
                                for a in self.binary_rules[(b, c)]:
                                    table[i][j].add(a)
                                    backpointers[(a, i, j)] = ('binary', b, c, k)

                # Apply unary rules
                self._apply_unary_rules(table[i][j], backpointers, i, j)

        return table, backpointers

    def _apply_unary_rules(self, symbol_set: Set[Any], backpointers: Dict, i: int, j: int):
        """
        Apply unary rules (A -> B) until no new symbols can be added.

        Args:
            symbol_set: Set of symbols to expand
            backpointers: Backpointer dictionary to update
            i: Start position
            j: End position
        """
        # Keep applying unary rules until no new symbols are added
        changed = True
        while changed:
            changed = False
            new_symbols = set()

            for b in symbol_set:
                if b in self.unary_rules:
                    for a in self.unary_rules[b]:
                        if a not in symbol_set and a not in new_symbols:
                            new_symbols.add(a)
                            backpointers[(a, i, j)] = ('unary', b)
                            changed = True

            symbol_set.update(new_symbols)

    def _reconstruct_parse_tree(
        self,
        table: List[List[Set[Any]]],
        backpointers: Dict,
        i: int,
        j: int,
        symbol: Any,
        tokens: List[Tuple[SpeakerPositionEnum, int]]
    ) -> Optional[ParseNode]:
        """
        Reconstruct parse tree from CYK table and backpointers.

        Args:
            table: CYK parse table
            backpointers: Backpointer dictionary
            i: Start position
            j: End position
            symbol: Non-terminal symbol to reconstruct
            tokens: Original token list

        Returns:
            ParseNode for this subtree
        """
        if (symbol, i, j) not in backpointers:
            return None

        production_info = backpointers[(symbol, i, j)]
        production_type = production_info[0]

        if production_type == 'terminal':
            # Terminal: (production_type, terminal, token_index)
            terminal = production_info[1]
            token_idx_in_list = production_info[2]
            _, utterance_idx = tokens[token_idx_in_list]

            return ParseNode(
                symbol=symbol,
                children=[ParseNode(
                    symbol=terminal,
                    utterance_indices=[utterance_idx]
                )],
                utterance_indices=[utterance_idx]
            )

        elif production_type == 'unary':
            # Unary rule: (production_type, child_symbol)
            child_symbol = production_info[1]
            child_node = self._reconstruct_parse_tree(table, backpointers, i, j, child_symbol, tokens)

            if child_node:
                return ParseNode(
                    symbol=symbol,
                    children=[child_node],
                    utterance_indices=child_node.utterance_indices
                )

        elif production_type == 'binary':
            # Binary rule: (production_type, left_symbol, right_symbol, split_point)
            left_symbol = production_info[1]
            right_symbol = production_info[2]
            k = production_info[3]

            left_node = self._reconstruct_parse_tree(table, backpointers, i, k, left_symbol, tokens)
            right_node = self._reconstruct_parse_tree(table, backpointers, k + 1, j, right_symbol, tokens)

            if left_node and right_node:
                utterance_indices = []
                if left_node.utterance_indices:
                    utterance_indices.extend(left_node.utterance_indices)
                if right_node.utterance_indices:
                    utterance_indices.extend(right_node.utterance_indices)

                return ParseNode(
                    symbol=symbol,
                    children=[left_node, right_node],
                    utterance_indices=utterance_indices if utterance_indices else None
                )

        return None

    def get_all_parses(self, hearing: TaggedHearing, max_parses: int = 10) -> List[ParseNode]:
        """
        Get all possible parse trees for a hearing (up to max_parses).

        Note: CYK naturally finds all parses. This implementation returns the first parse
        and can be extended to enumerate all parse trees by tracking all backpointers.

        Args:
            hearing: TaggedHearing to parse
            max_parses: Maximum number of parse trees to return

        Returns:
            List of ParseNode objects representing different parse trees
        """
        tokens = self.tokenize_utterances(hearing)

        if not tokens:
            return []

        # For now, return single parse (can be extended to enumerate all)
        result = self.parse(hearing)
        return [result] if result else []

    @staticmethod
    def parse_node_to_nltk_tree(parse_node: ParseNode) -> 'Tree':
        """
        Convert a ParseNode to an NLTK Tree.

        Args:
            parse_node: ParseNode to convert

        Returns:
            NLTK Tree representation

        Raises:
            ImportError: If NLTK is not installed
        """
        return parse_node.to_nltk_tree()

    def parse_to_nltk_tree(self, hearing: TaggedHearing) -> Optional['Tree']:
        """
        Parse a hearing and return the result as an NLTK Tree.

        Args:
            hearing: TaggedHearing to parse

        Returns:
            NLTK Tree if parsing succeeds, None otherwise

        Raises:
            ImportError: If NLTK is not installed
        """
        parse_node = self.parse(hearing)
        if parse_node:
            return parse_node.to_nltk_tree()
        return None

    def get_all_parses_as_nltk_trees(
        self,
        hearing: TaggedHearing,
        max_parses: int = 10
    ) -> List['Tree']:
        """
        Get all possible parse trees as NLTK Trees.

        Args:
            hearing: TaggedHearing to parse
            max_parses: Maximum number of parse trees to return

        Returns:
            List of NLTK Tree objects

        Raises:
            ImportError: If NLTK is not installed
        """
        parse_nodes = self.get_all_parses(hearing, max_parses)
        return [node.to_nltk_tree() for node in parse_nodes]
