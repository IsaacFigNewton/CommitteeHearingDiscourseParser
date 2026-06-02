from enum import Enum
from ..roles.SpeakerRoleEnum import SpeakerRoleEnum

"""
describes the valid speaker roles associated with each section

SpeakerRoleEnum.CHAIRMAN and SpeakerRoleEnum.SECRETARY are always allowed as speakers
"""
class SectionSpeakerEnum(Enum):
    # introducing senators, pledge of allegiance, etc.
    INTRO=                  {SpeakerRoleEnum.PRESIDING_CHAIR}

    # bill description/introduction
    PRESENTATION=           {SpeakerRoleEnum.PRESENTER}

    # sequence of different discussion sections
    LEGISLATOR_DISCUSSION=  {SpeakerRoleEnum.PRESIDING_CHAIR, SpeakerRoleEnum.SECRETARY, SpeakerRoleEnum.COMMITTEE_MEMBER}
    EXPERT_TESTIMONY=       {SpeakerRoleEnum.PRESIDING_CHAIR, SpeakerRoleEnum.SECRETARY, SpeakerRoleEnum.COMMITTEE_MEMBER, SpeakerRoleEnum.EXPERT}
    PUBLIC_COMMENTS=        {SpeakerRoleEnum.PRESIDING_CHAIR, SpeakerRoleEnum.SECRETARY, SpeakerRoleEnum.PUBLIC}

    # closing remarks by committee chair or bill presenter
    CLOSING_REMARKS=        {SpeakerRoleEnum.PRESIDING_CHAIR, SpeakerRoleEnum.PRESENTER}

    # voting section
    VOTE=                   {SpeakerRoleEnum.PRESIDING_CHAIR, SpeakerRoleEnum.SECRETARY}