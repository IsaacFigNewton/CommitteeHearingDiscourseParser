from enum import Enum
from .SpeakerRoleEnum import SpeakerRoleEnum

"""
describes the valid speaker roles associated with each section

SpeakerRoleEnum.CHAIRMAN and SpeakerRoleEnum.SECRETARY are always allowed as speakers
"""
class SectionSpeakerEnum(Enum):
    ANY_SECTION=            [SpeakerRoleEnum.CHAIRMAN, SpeakerRoleEnum.STAFF, SpeakerRoleEnum.OTHER]

    # introducing senators, pledge of allegiance, etc.
    INTRO=                  [SpeakerRoleEnum.CHAIRMAN]

    # bill description/introduction
    PRESENTATION=           [SpeakerRoleEnum.PRESENTER]

    # sequence of different discussion sections
    LEGISLATOR_DISCUSSION=  [SpeakerRoleEnum.LEGISLATOR]
    EXPERT_TESTIMONY=       [SpeakerRoleEnum.LEGISLATOR, SpeakerRoleEnum.EXPERT]
    PUBLIC_COMMENTS=        [SpeakerRoleEnum.PUBLIC]

    # closing remarks by committee chair or bill presenter
    CLOSING_REMARKS=        [SpeakerRoleEnum.CHAIRMAN, SpeakerRoleEnum.PRESENTER]

    # voting section
    VOTE=                   [SpeakerRoleEnum.STAFF]