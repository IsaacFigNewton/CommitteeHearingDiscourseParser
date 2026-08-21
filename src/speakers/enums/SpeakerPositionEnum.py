from enum import Enum

"""
used to enumerate the different possible roles of speakers in a bill discussion
"""

class SpeakerPositionEnum(Enum):
    SECRETARY=          9
    PRESIDING_CHAIR=    8
    CHAIRMAN=           7
    VICE_CHAIRMAN=      6
    COMMITTEE_MEMBER=   5
    BILL_AUTHOR=        4   # subdivided by can_file_motions, determines is_presenter
    LEGISLATOR=         3
    EXPERT=             2
    NONLEGISLATOR=      1
    PUBLIC=             0



COMMITTEE_POSITION_MAP = {
    "Chair":        SpeakerPositionEnum.CHAIRMAN,
    "Co-Chair":     SpeakerPositionEnum.CHAIRMAN,
    "Vice-Chair":   SpeakerPositionEnum.VICE_CHAIRMAN,
    "Member":       SpeakerPositionEnum.COMMITTEE_MEMBER
}


SPEAKER_POSITION_CUES = {
    SpeakerPositionEnum.PUBLIC: {
        "on behalf of",
        "NONLEGISLATOR representing ORG",
        "NONLEGISLATOR with ORG",
        "i'm with ORG"
    },
}