import re
from typing import Optional


BILL_PREFIXES = ['AB', 'SB', 'SJR']
BILL_ACTION_VERBS = [
    'require',
    'authorize',
    'prohibit',
    'allow',
    'establish',
    'create',
    'extend',
    'impose',
]

prefix_pattern = '|'.join(BILL_PREFIXES)
verb_pattern = '|'.join(BILL_ACTION_VERBS)

BILL_ID_PATTERN = re.compile(
    rf'\b(?:{prefix_pattern})\s*\d+\b',
    re.IGNORECASE,
)

BILL_ACTION_PATTERN = re.compile(
    rf'\b(?:{prefix_pattern})\s*\d+\b[\s,;:]*would\s+(?:also\s+)?(?:{verb_pattern})\b',
    re.IGNORECASE,
)


MOTION_CUES = [
    'motion is do pass',
    'motion is due pass',
    'do pass',
    'due pass',
    'do pass as amended',
    'due pass as amended',
    'so moved',
    'second',
    'refer to the committee',
    're-refer to the committee',
]


DISPOSITION_CUES = [
    "the measure's out",
    'the measure is out',
    'the bill is out',
    'the bill passes',
    'the measure passes',
    'without objection',
]


PRESENTATION_CUES = [
    'i would like to present',
    "i'm pleased to present",
    "i'm here to present",
    'this bill',
    'this measure',
    'the bill contains',
    'this is the',
    'includes the following changes',
]


def normalize_text(text: Optional[str]) -> str:
    if not text:
        return ''

    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def contains_any_phrase(text: Optional[str], phrases: list[str]) -> bool:
    normalized = normalize_text(text)

    return any(
        normalize_text(phrase) in normalized
        for phrase in phrases
    )


def has_bill_id(text: Optional[str]) -> int:
    return int(bool(text and BILL_ID_PATTERN.search(text)))


def has_bill_action(text: Optional[str]) -> int:
    return int(bool(text and BILL_ACTION_PATTERN.search(text)))


def has_presentation_cue(text: Optional[str]) -> int:
    return int(contains_any_phrase(text, PRESENTATION_CUES))


def has_motion_cue(text: Optional[str]) -> int:
    return int(contains_any_phrase(text, MOTION_CUES))


def has_disposition_cue(text: Optional[str]) -> int:
    return int(contains_any_phrase(text, DISPOSITION_CUES))


def aye_count(text: Optional[str]) -> int:
    if not text:
        return 0

    return len(re.findall(r'\baye\b', text.lower()))


def no_count(text: Optional[str]) -> int:
    if not text:
        return 0

    return len(re.findall(r'\bno\b', text.lower()))


def has_vote_cue(text: Optional[str]) -> int:
    if not text:
        return 0

    normalized = normalize_text(text)

    vote_phrase_found = (
        'roll call' in normalized
        or 'call the roll' in normalized
        or 'please call the roll' in normalized
    )

    repeated_votes_found = aye_count(text) + no_count(text) >= 2

    return int(vote_phrase_found or repeated_votes_found)


def word_count(text: Optional[str]) -> int:
    return len(normalize_text(text).split())
