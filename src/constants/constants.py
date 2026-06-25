import re
from .bill_ref_normalization import NORMALIZED_BILL_REGEX

BILL_KEYPHRASES = {
    0: {
        "take up",
    },

    1: {
        "would",
        "would also",
    },

    2: {
        "require",
        "authorize",
        "prohibit",
        "allow",
        "establish",
        "create",
        "extend",
        "impose",
    },
}

DISPOSITION_SUFFIXES = {
    "'s out",
    "is out",
    "passes",
}

def regex_or(items):
    return "|".join(
        sorted(
            map(re.escape, items),
            key=len,
            reverse=True,
        )
    )

BILL_MODAL_REGEX = regex_or(BILL_KEYPHRASES[1])
BILL_ACTION_VERB_REGEX = regex_or(BILL_KEYPHRASES[2])
BILL_TAKE_UP_REGEX = regex_or(BILL_KEYPHRASES[0])
DISPOSITION_SUFFIX_REGEX = regex_or(DISPOSITION_SUFFIXES)

# These assume bill references may already have been normalized to "BILL"
BILL_ACTION_REGEX = rf"""
    {NORMALIZED_BILL_REGEX}
    [\s,;:]*
    (?:
        {BILL_MODAL_REGEX}
    )?
    \s*
    (?:
        {BILL_ACTION_VERB_REGEX}
    )
    \b
"""

BILL_TAKE_UP_REGEX = rf"""
    \b
    (?:
        {BILL_TAKE_UP_REGEX}
    )
    \s+
    {NORMALIZED_BILL_REGEX}
"""

BILL_DISPOSITION_REGEX = rf"""
    {NORMALIZED_BILL_REGEX}
    \s*
    (?:
        {DISPOSITION_SUFFIX_REGEX}
    )
    \b
"""

BILL_ACTION_PATTERN = re.compile(
    BILL_ACTION_REGEX,
    re.IGNORECASE | re.VERBOSE,
)

BILL_TAKE_UP_PATTERN = re.compile(
    BILL_TAKE_UP_REGEX,
    re.IGNORECASE | re.VERBOSE,
)

BILL_DISPOSITION_PATTERN = re.compile(
    BILL_DISPOSITION_REGEX,
    re.IGNORECASE | re.VERBOSE,
)