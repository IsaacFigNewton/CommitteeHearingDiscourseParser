import re

BILL_ID_REGEX = "|".join(
    sorted(
        map(re.escape, {
            "AB",
            "SB",
            "SJR",
            "Assembly Bill",
            "Senate Bill",
            "this bill",
            "this measure",
            "the bill",
            "the measure",
        }),
        key=len,
        reverse=True,
    )
)

# Used for normalizing bill references to "BILL"
BILL_ID_REGEX = rf"""
    \b
    (?:
        {BILL_ID_REGEX}
    )
    \s+
    \d+
    \b
"""

BILL_ID_PATTERN = re.compile(
    BILL_ID_REGEX,
    re.IGNORECASE | re.VERBOSE,
)

NORMALIZED_BILL_REGEX = re.compile(
    r"\bBILL\b",
    re.IGNORECASE
)