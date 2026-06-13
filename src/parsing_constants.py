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

BILL_ACTION_VERBS = ['require']

prefix_pattern = '|'.join(BILL_PREFIXES)
verb_pattern = '|'.join(BILL_ACTION_VERBS)

BILL_ACTION_PATTERN = re.compile(
  rf'\b(?:{prefix_pattern})\s+\d+\s+would\s+(?:{verb_pattern})',
  re.IGNORECASE
)

VOTE_START_PHRASES = [
    'The motion is due pass',
    'The motion is do pass',
]
