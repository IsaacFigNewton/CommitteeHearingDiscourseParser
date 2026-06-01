"""
Configuration constants for the TranscriptLoader
"""

# Valid state abbreviations in the corpus
VALID_STATES = ["CA", "FL", "NY", "TX"]

# Available CSV filenames in the corpus
CSV_FILENAMES = [
    'bills',
    'committeeHearings',
    'committeeRosters',
    'committees',
    'hearings',
    'legislature',
    'people',
    'speeches',
    'videos'
]

# Default corpus path
DEFAULT_CORPUS_PATH = 'DH2024_Corpus_Release/'

# Year ranges for different states
CA_VALID_YEARS = ["2015-2016", "2017-2018"]
OTHER_STATES_VALID_YEARS = ["2017-2018"]

# CSV column indices for speeches
SPEECH_HID_IDX = 3
SPEECH_BID_IDX = 4
SPEECH_SESSION_IDX = 7
SPEECH_DATE_IDX = 6
SPEECH_PID_IDX = 1
SPEECH_VID_START_IDX = 9
SPEECH_VID_END_IDX = 10
SPEECH_LAST_NAME_IDX = 14
SPEECH_FIRST_NAME_IDX = 15
SPEECH_TEXT_IDX = 16
SPEECH_STARTING_TIME_IDX = 11

# CSV column indices for hearings
HEARING_HID_IDX = 0
HEARING_CID_IDX = 4
HEARING_CNAME_IDX = 8
HEARING_HDATE_IDX = 1
HEARING_STATE_IDX = 3

# Time format
TIME_FORMAT = '%H:%M:%S'
