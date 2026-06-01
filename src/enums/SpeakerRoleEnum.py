from enum import Enum

"""
used to enumerate the different possible roles of speakers in a bill discussion
"""

class SpeakerRoleEnum(Enum):
    # procedural roles
    CHAIRMAN=           "CHAIRMAN"
    VICE_CHAIRMAN=      "VICE_CHAIRMAN"
    SECRETARY=          "SECRETARY"

    AUTHOR=             "AUTHOR"
    PRESENTER=          "PRESENTER"         # usually bill author
    MEMBER=             "MEMBER"            # committee member
    NONMEMBER=          "NONMEMBER"         # legislator that is not a committee member
    EXPERT=             "EXPERT"
    PUBLIC=             "PUBLIC"
    OTHER=              "UNKNOWN"


COMMITTEE_POSITION_MAP = {
    "Chair":        SpeakerRoleEnum.CHAIRMAN,
    "Co-Chair":     SpeakerRoleEnum.CHAIRMAN,
    "Vice-Chair":   SpeakerRoleEnum.VICE_CHAIRMAN,
    "Member":       SpeakerRoleEnum.MEMBER
}