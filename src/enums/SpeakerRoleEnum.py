from enum import Enum
from .SpeakerTypeEnum import SpeakerTypeEnum

class SpeakerRoleEnum(Enum):
    # procedural roles
    PRESIDING_CHAIR=           frozenset({
        SpeakerTypeEnum.CHAIRMAN
        SpeakerTypeEnum.VICE_CHAIRMAN,
    })
    STAFF=              frozenset({
        SpeakerTypeEnum.CHAIRMAN,
        SpeakerTypeEnum.VICE_CHAIRMAN,
        SpeakerTypeEnum.SECRETARY,
    })

    # legislator roles
    PRESENTER=          frozenset({SpeakerTypeEnum.PRESENTER})
    LEGISLATOR=         frozenset({
        SpeakerTypeEnum.CHAIRMAN,
        SpeakerTypeEnum.VICE_CHAIRMAN,
        SpeakerTypeEnum.AUTHOR,
        SpeakerTypeEnum.PRESENTER,
        SpeakerTypeEnum.MEMBER,
        SpeakerTypeEnum.NONMEMBER,
    })

    # other roles
    EXPERT=             frozenset({SpeakerTypeEnum.EXPERT})
    PUBLIC=             frozenset({SpeakerTypeEnum.PUBLIC})
    UNKNOWN=            frozenset({SpeakerTypeEnum.UNKNOWN})