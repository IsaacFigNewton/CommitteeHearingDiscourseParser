from enum import Enum

class SpeakerRoleEnum(Enum):
    """
    each SpeakerRoleEnum denotes a different speaker role
    """

    # procedural roles
    PRESIDING_CHAIR=    "PRESIDING_CHAIR"
    SECRETARY=          "SECRETARY"

    # legislator roles
    PRESENTER=          "PRESENTER"
    COMMITTEE_MEMBER=   "COMMITTEE_MEMBER"

    # other roles
    EXPERT=             "EXPERT"
    PUBLIC=             "PUBLIC"
    UNKNOWN=            "UNKNOWN"