import re

BILL_ID_TERMS = "|".join([
    r"AB",
    r"SB",
    r"SJR",
    r"Assembly\s+Bill",
    r"Senate\s+Bill",
    r"this\s+bill",
    r"this\s+measure",
    r"this\s+proposal",
    r"the\s+bill",
    r"the\s+measure",
    r"the\s+proposal",
    r"item\s+number",
    r"issue\s+number",
])

BILL_ID_REGEX = rf"""
    \b
    (?:
        {BILL_ID_TERMS}
    )
    (?:\s+\d+)?
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