import re

AB_BILL_REGEX = r'\bAB\s*\d+\b'
SB_BILL_REGEX = r'\bSB\s*\d+\b'
SJR_BILL_REGEX = r'\bSJR\s*\d+\b'
ASSEMBLY_BILL_REGEX = r'\bAssembly\s+Bill\s+\d+\b'
SENATE_BILL_REGEX = r'\bSenate\s+Bill\s+\d+\b'
NAME_BIGRAM_REGEX = r'(?<![A-Z][a-z] )\b[A-Z][a-z]+ [A-Z][a-z]+\b(?! [A-Z][a-z])'

BILL_KEYPHRASES = {
    "BILL_PREFIXES": {
        'AB', 'SB', 'SJR'
    },

    "BILL_ACTION_VERBS": {
        'require',
        'authorize',
        'prohibit',
        'allow',
        'establish',
        'create',
        'extend',
        'impose',
    },
}

DISPOSITION_SUFFIXES = {
    "'s out",
    'is out',
    'passes',
}

TOKEN_PHRASE_MAP = {
    "BILL": {
        "this bill",
        "this measure",
        "the bill",
        "the measure",
    },
}
PHRASE_TOKEN_MAP = {
    phrase: token
    for token, phrases in TOKEN_PHRASE_MAP.items()
    for phrase in phrases
}

prefix_pattern = '|'.join(BILL_KEYPHRASES["BILL_PREFIXES"])
verb_pattern = '|'.join(BILL_KEYPHRASES["BILL_ACTION_VERBS"])

BILL_ID_PATTERN = re.compile(
    rf'\b(?:{prefix_pattern})\s*\d+\b',
    re.IGNORECASE,
)

BILL_ACTION_PATTERN = re.compile(
    rf'\b(?:{prefix_pattern})\s*\d+\b[\s,;:]*would\s+(?:also\s+)?(?:{verb_pattern})\b',
    re.IGNORECASE,
)
