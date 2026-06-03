from enum import Enum

"""
used to enumerate the different possible roles of speakers in a bill discussion
"""

class SpeakerPositionEnum(Enum):
    CHAIRMAN=           "CHAIRMAN"
    VICE_CHAIRMAN=      "VICE_CHAIRMAN"
    SECRETARY=          "SECRETARY"
    LEGISLATOR=         "LEGISLATOR"
    NONLEGISLATOR=      "NONLEGISLATOR"
    UNKNOWN=            "UNKNOWN"


COMMITTEE_POSITION_MAP = {
    "Chair":        SpeakerPositionEnum.CHAIRMAN,
    "Co-Chair":     SpeakerPositionEnum.CHAIRMAN,
    "Vice-Chair":   SpeakerPositionEnum.VICE_CHAIRMAN,
    "Member":       SpeakerPositionEnum.LEGISLATOR
}