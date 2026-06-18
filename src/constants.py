import re

AB_BILL_REGEX = r'\bAB\s*\d+\b'
SB_BILL_REGEX = r'\bSB\s*\d+\b'
SJR_BILL_REGEX = r'\bSJR\s*\d+\b'
ASSEMBLY_BILL_REGEX = r'\bAssembly\s+Bill\s+\d+\b'
SENATE_BILL_REGEX = r'\bSenate\s+Bill\s+\d+\b'
NAME_BIGRAM_REGEX = r'(?<![A-Z][a-z] )\b[A-Z][a-z]+ [A-Z][a-z]+\b(?! [A-Z][a-z])'

PHRASE_GROUPS = {
    "PRESENTING": {
        "please proceed",
        "please present",
        "feel free to present",
        "i would like to present",
        "i'm pleased to present",
        "i'm delighted to bring before you",
        "i'm here to present",
        "i would appreciate your support on this bill",
        "ask for an aye vote",
        "request an aye vote",
        "i present",
    },

    "BILL_PREFIXES": {
        'AB', 'SB', 'SJR'
    },

    "BILL": {
        "this bill",
        "this measure",
        "the bill contains",
        "this is the",
        "includes the following changes",
        "bill",
        "measure",
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

    "START_VOTE": {
        "is due pass",
        "is do pass",
        "is so moved",
        "is seconded",
    },

    "MOTION": {
        "refer to the committee",
        "re-refer to the committee",
    },

    "DISPOSITION": {
        "'s out",
        "is out",
        "passes",
        "the measure's out",
        "the measure is out",
        "the bill is out",
        "the bill passes",
        "the measure passes",
        "without objection",
    },
}

PHRASE_TOKEN_MAP = {
    phrase: token
    for token, phrases in PHRASE_GROUPS.items()
    for phrase in phrases
}

DISPOSITION_SUFFIXES = {
    "'s out",
    'is out',
    'passes',
}


prefix_pattern = '|'.join(PHRASE_GROUPS["BILL_PREFIXES"])
verb_pattern = '|'.join(PHRASE_GROUPS["BILL_ACTION_VERBS"])

BILL_ID_PATTERN = re.compile(
    rf'\b(?:{prefix_pattern})\s*\d+\b',
    re.IGNORECASE,
)

BILL_ACTION_PATTERN = re.compile(
    rf'\b(?:{prefix_pattern})\s*\d+\b[\s,;:]*would\s+(?:also\s+)?(?:{verb_pattern})\b',
    re.IGNORECASE,
)
