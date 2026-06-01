from enum import Enum
from .SpeakerRoleEnum import SpeakerRoleEnum

"""
describes the valid speaker roles associated with each section

SpeakerRoleEnum.CHAIRMAN and SpeakerRoleEnum.SECRETARY are always allowed as speakers
"""
class SectionSpeakerEnum(Enum):
    # introducing senators, pledge of allegiance, etc.
    INTRO=                  SpeakerRoleEnum.PRESIDING_CHAIR.value

    # bill description/introduction
    PRESENTATION=           SpeakerRoleEnum.PRESENTER.value

    # sequence of different discussion sections
    LEGISLATOR_DISCUSSION=  SpeakerRoleEnum.LEGISLATOR.value
    EXPERT_TESTIMONY=       frozenset(set.union(
        set(),
        SpeakerRoleEnum.STAFF.value,
        SpeakerRoleEnum.EXPERT.value
    ))
    PUBLIC_COMMENTS=        frozenset(set.union(
        set(),
        SpeakerRoleEnum.STAFF.value,
        SpeakerRoleEnum.PUBLIC.value
    ))

    # closing remarks by committee chair or bill presenter
    CLOSING_REMARKS=        frozenset(set.union(
        set(),
        SpeakerRoleEnum.PRESIDING_CHAIR.value,
        SpeakerRoleEnum.PRESENTER.value
    ))

    # voting section
    VOTE=                   SpeakerRoleEnum.STAFF.value