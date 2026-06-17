from enum import Enum

"""
used to enumerate the different possible roles of speakers in a bill discussion
"""

# secretary doesn't have a speaker position
class SpeakerPositionEnum(Enum):
    PRESIDING_CHAIR=    7
    CHAIRMAN=           6
    VICE_CHAIRMAN=      5
    COMMITTEE_MEMBER=   4
    BILL_AUTHOR=        3   # subdivided by can_file_motions
    LEGISLATOR=         2
    EXPERT=             1   # subdivided by is_presenter
    NONLEGISLATOR=      0


COMMITTEE_POSITION_MAP = {
    "Chair":        SpeakerPositionEnum.CHAIRMAN,
    "Co-Chair":     SpeakerPositionEnum.CHAIRMAN,
    "Vice-Chair":   SpeakerPositionEnum.VICE_CHAIRMAN,
    "Member":       SpeakerPositionEnum.LEGISLATOR
}