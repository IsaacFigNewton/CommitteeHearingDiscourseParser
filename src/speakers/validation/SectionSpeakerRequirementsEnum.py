from enum import Enum
from ..enums.SpeakerRoleEnum import SpeakerRoleEnum
from .SectionRequirements import SectionRequirements

"""
describes the valid speaker roles associated with each section

SpeakerRoleEnum.CHAIRMAN and SpeakerRoleEnum.SECRETARY are always allowed as speakers
"""
class SectionSpeakerRequirementsEnum(Enum):
    # introducing senators, pledge of allegiance, etc.
    INTRO=                  SectionRequirements(frozenset({
        SpeakerRoleEnum.PRESIDING_CHAIR
    }))

    # bill description/introduction
    PRESENTATION=           SectionRequirements(frozenset({
        SpeakerRoleEnum.PRESENTER
    }))

    # sequence of different discussion sections
    LEGISLATOR_DISCUSSION=  SectionRequirements(frozenset({
        SpeakerRoleEnum.PRESIDING_CHAIR,
        SpeakerRoleEnum.SECRETARY,
        SpeakerRoleEnum.COMMITTEE_MEMBER
    }))
    EXPERT_TESTIMONY=       SectionRequirements(frozenset({
        SpeakerRoleEnum.PRESIDING_CHAIR,
        SpeakerRoleEnum.SECRETARY,
        SpeakerRoleEnum.COMMITTEE_MEMBER,
        SpeakerRoleEnum.EXPERT
    }))
    PUBLIC_COMMENTS=        SectionRequirements(frozenset({
        SpeakerRoleEnum.PRESIDING_CHAIR,
        SpeakerRoleEnum.SECRETARY,
        SpeakerRoleEnum.PUBLIC
    }))

    # closing remarks by committee chair or bill presenter
    CLOSING_REMARKS=        SectionRequirements(frozenset({
        SpeakerRoleEnum.PRESIDING_CHAIR,
        SpeakerRoleEnum.PRESENTER
    }))

    # voting section
    VOTE=                   SectionRequirements(frozenset({
        SpeakerRoleEnum.PRESIDING_CHAIR,
        SpeakerRoleEnum.SECRETARY,
        SpeakerRoleEnum.COMMITTEE_MEMBER
    }))