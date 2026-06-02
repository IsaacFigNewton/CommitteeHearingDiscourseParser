from enum import Enum

"""
used to enumerate the different possible roles of speakers in a bill discussion
"""

class SpeakerTypeEnum(Enum):
    CHAIRMAN=           "CHAIRMAN"
    VICE_CHAIRMAN=      "VICE_CHAIRMAN"
    SECRETARY=          "SECRETARY"
    LEGISLATOR=         "LEGISLATOR"
    NONLEGISLATOR=      "NONLEGISLATOR"
    UNKNOWN=            "UNKNOWN"


COMMITTEE_POSITION_MAP = {
    "Chair":        SpeakerTypeEnum.CHAIRMAN,
    "Co-Chair":     SpeakerTypeEnum.CHAIRMAN,
    "Vice-Chair":   SpeakerTypeEnum.VICE_CHAIRMAN,
    "Member":       SpeakerTypeEnum.LEGISLATOR
}