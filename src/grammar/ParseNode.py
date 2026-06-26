from nltk.tree import Tree


from dataclasses import dataclass
from typing import Any, List, Optional


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
        """Recursively convert ParseNode to NLTK Tree."""
        # Format the label based on symbol type
        label = self._format_symbol_label(self.symbol)

        if self.children:
            # Non-terminal node: recursively convert children
            nltk_children = [child.to_nltk_tree() for child in self.children]
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