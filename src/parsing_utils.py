import re
from rapidfuzz import fuzz

def match_regex_pattern(pattern, text: str, ignore_case: bool = True) -> bool:
    if isinstance(pattern, str):
        return bool(re.search(pattern, text, re.IGNORECASE if ignore_case else 0))
    else:
        # in case pattern is an already compiled pattern, flags can't be used
        return bool(re.search(pattern, text))

def matches_any_regex_pattern(patterns, text: str, ignore_case: bool = True) -> bool:
    return any([match_regex_pattern(p, text, ignore_case) for p in patterns])

def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def simple_match(text: str, phrase: str) -> bool:
    return normalize_text(phrase) in normalize_text(text)

def fuzzy_substring_match(text: str, phrase: str, threshold: int = 80) -> bool:
    normalized_text = normalize_text(text)
    normalized_phrase = normalize_text(phrase)

    score = fuzz.partial_ratio(normalized_phrase, normalized_text)
    return score > threshold

def match_any_phrase(text: str, phrases: list[str], fuzzy_threshold: int = 80) -> bool:
    for p in phrases:
        if len(p.split()) <= 2:
            # for short phrases, just use direct substring matching
            if simple_match(text, p):
                return True
        else:
            # for long phrases, use fuzzy matching to catch slight variants
            if fuzzy_substring_match(text, p, fuzzy_threshold):
                return True
    
    return False
        