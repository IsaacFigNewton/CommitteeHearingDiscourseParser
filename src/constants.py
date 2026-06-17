import re

AB_BILL_REGEX = r'\bAB\s*\d+\b'
SB_BILL_REGEX = r'\bSB\s*\d+\b'
SJR_BILL_REGEX = r'\bSJR\s*\d+\b'
ASSEMBLY_BILL_REGEX = r'\bAssembly\s+Bill\s+\d+\b'
SENATE_BILL_REGEX = r'\bSenate\s+Bill\s+\d+\b'

PRESENTATION_HANDOFF_PHRASES = [
    'Please proceed',
    'please present',
    'feel free to present',
]

PRESENTATION_START_PHRASES = [
    'I would like to present',
    'I\'m pleased to present',
    'I\'m delighted to bring before you',
    'I\'m here to present',
    'I would appreciate your support on this bill',
    'ask for an aye vote',
    'request an aye vote',
    'I present',
]

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

VOTE_START_PHRASES = [
    'The motion is due pass',
    'The motion is do pass',
]

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