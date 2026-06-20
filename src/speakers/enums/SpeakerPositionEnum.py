from enum import Enum

"""
used to enumerate the different possible roles of speakers in a bill discussion
"""

class SpeakerPositionEnum(Enum):
    SECRETARY=          8
    PRESIDING_CHAIR=    7
    CHAIRMAN=           6
    VICE_CHAIRMAN=      5
    COMMITTEE_MEMBER=   4
    BILL_AUTHOR=        3   # subdivided by can_file_motions, determines is_presenter
    LEGISLATOR=         2
    EXPERT=             1
    NONLEGISLATOR=      0



COMMITTEE_POSITION_MAP = {
    "Chair":        SpeakerPositionEnum.CHAIRMAN,
    "Co-Chair":     SpeakerPositionEnum.CHAIRMAN,
    "Vice-Chair":   SpeakerPositionEnum.VICE_CHAIRMAN,
    "Member":       SpeakerPositionEnum.COMMITTEE_MEMBER
}