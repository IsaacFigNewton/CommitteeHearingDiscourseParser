from typing import Optional
from abc import ABC
import re
from rapidfuzz import fuzz


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
        
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @classmethod
    def simple_match(cls, text: str, phrase: str) -> bool:
        return cls.normalize_text(phrase) in cls.normalize_text(text)

    @classmethod
    def fuzzy_substring_match(cls, text: str, phrase: str, threshold: int = 80) -> bool:
        normalized_text = cls.normalize_text(text)
        normalized_phrase = cls.normalize_text(phrase)

        score = fuzz.partial_ratio(normalized_phrase, normalized_text)
        return score > threshold


    @classmethod
    def contains_any_phrase(cls, text: Optional[str], phrases: list[str]) -> bool:
        normalized = cls.normalize_text(text)

        return any(
            phrase in normalized
            for phrase in phrases
        )