from typing import Optional, Set
from abc import ABC
import re
from rapidfuzz import fuzz

from ..constants.bill_ref_normalization import BILL_ID_PATTERN


class ITagger(ABC):
    def __init__(self) -> None:
        pass

    @classmethod
    def match_regex_pattern(cls, pattern, text: str, ignore_case: bool = True) -> bool:
        if isinstance(pattern, str):
            return bool(re.search(pattern, text, re.IGNORECASE if ignore_case else 0))
        else:
            # in case pattern is an already compiled pattern, flags can't be used
            return bool(re.search(pattern, text))

    @classmethod
    def matches_any_regex_pattern(cls, patterns, text: str, ignore_case: bool = True) -> bool:
        return any([cls.match_regex_pattern(p, text, ignore_case) for p in patterns])

    @classmethod
    def normalize_text(cls, text: Optional[str]) -> str:
        if not text:
            return ''

        # Remove punctuation symbols
        text = re.sub(r'[.,!?:]', '', text)

        # Replace bill references BEFORE splitting into words
        # (so multi-word phrases like "this bill 123" are matched)
        text = BILL_ID_PATTERN.sub("BILL", text)

        # Convert words to lowercase only if not ALL_CAPS
        normalized_words = []
        for word in text.split():
            # Check if word (without punctuation) is ALL_CAPS
            alpha_only = re.sub(r'[^\w]', '', word)
            if alpha_only and alpha_only.isupper():
                # Keep ALL_CAPS words as is
                normalized_words.append(word)
            else:
                # Convert to lowercase
                normalized_words.append(word.lower())

        text = ' '.join(normalized_words)
        return text.strip()

    @classmethod
    def fuzzy_substring_match(cls, text: str, phrase: str, threshold: int = 80) -> bool:
        score = fuzz.partial_ratio(phrase, text)
        return score > threshold


    @classmethod
    def contains_any_phrase(cls, text: str, phrases: Set[str]) -> bool:
        return any(
            phrase in text
            for phrase in phrases
        )