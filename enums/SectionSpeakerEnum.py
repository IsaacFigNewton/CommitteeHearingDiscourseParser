from enum import Enum
from .SpeakerRoleEnum import SpeakerRoleEnum

"""
describes the valid speaker roles associated with each section

SpeakerRoleEnum.CHAIRMAN and SpeakerRoleEnum.SECRETARY are always allowed as speakers
"""
class SectionSpeakerEnum(Enum):
    ANY_SECTION=            [SpeakerRoleEnum.CHAIRMAN, SpeakerRoleEnum.SECRETARY, SpeakerRoleEnum.OTHER]

    # introducing senators, pledge of allegiance, etc.
    INTRO=                  [SpeakerRoleEnum.CHAIRMAN]

    # bill description/introduction
    PRESENTATION=           [SpeakerRoleEnum.AUTHOR]

    # sequence of different discussion sections
    LEGISLATOR_DISCUSSION=  [SpeakerRoleEnum.AUTHOR, SpeakerRoleEnum.LEGISLATOR]
    EXPERT_TESTIMONY=       [SpeakerRoleEnum.AUTHOR, SpeakerRoleEnum.LEGISLATOR, SpeakerRoleEnum.EXPERT]
    PUBLIC_COMMENTS=        [SpeakerRoleEnum.PUBLIC]

    # closing remarks by committee chair or bill author
    CLOSING_REMARKS=        [SpeakerRoleEnum.CHAIRMAN, SpeakerRoleEnum.AUTHOR]

    # voting section
    VOTE=                   [SpeakerRoleEnum.CHAIRMAN]

    # final remarks at end of session
    OUTRO=                  [SpeakerRoleEnum.CHAIRMAN]