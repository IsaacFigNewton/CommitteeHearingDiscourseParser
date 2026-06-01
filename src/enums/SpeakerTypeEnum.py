from enum import Enum

"""
used to enumerate the different possible roles of speakers in a bill discussion
"""

class SpeakerTypeEnum(Enum):
    # procedural roles
    CHAIRMAN=           "CHAIRMAN"
    VICE_CHAIRMAN=      "VICE_CHAIRMAN"
    SECRETARY=          "SECRETARY"
    # legislator roles
    AUTHOR=             "AUTHOR"
    PRESENTER=          "PRESENTER"         # usually bill author
    MEMBER=             "MEMBER"            # committee member
    NONMEMBER=          "NONMEMBER"         # legislator that is not a committee member
    # other roles
    EXPERT=             "EXPERT"
    PUBLIC=             "PUBLIC"
    UNKNOWN=              "UNKNOWN"


COMMITTEE_POSITION_MAP = {
    "Chair":        SpeakerTypeEnum.CHAIRMAN,
    "Co-Chair":     SpeakerTypeEnum.CHAIRMAN,
    "Vice-Chair":   SpeakerTypeEnum.VICE_CHAIRMAN,
    "Member":       SpeakerTypeEnum.MEMBER
}