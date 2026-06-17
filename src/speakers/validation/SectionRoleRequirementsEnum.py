from enum import Enum
from .RoleRequirements import RoleRequirements
from ..enums.SpeakerPositionEnum import SpeakerPositionEnum

"""
describes the valid speaker roles associated with each section

note: make sure to update SectionEnum when modifying this

SpeakerRoleEnum.CHAIRMAN and SpeakerRoleEnum.SECRETARY are always allowed as speakers
"""
class SectionSpeakerRequirementsEnum(Enum):
    # introducing senators, pledge of allegiance, etc.
    INTRO=                  RoleRequirements(
        valid_speaker_position_intervals=          {
            (SpeakerPositionEnum.VICE_CHAIRMAN, SpeakerPositionEnum.PRESIDING_CHAIR),
        },
        can_file_motions=           True,
        is_secretary=               False,
        is_presenter=               None,
    )

    # bill description/introduction
    PRESENTATION=           RoleRequirements(
        valid_speaker_position_intervals=          {
            (SpeakerPositionEnum.BILL_AUTHOR, SpeakerPositionEnum.BILL_AUTHOR),
            (SpeakerPositionEnum.PRESIDING_CHAIR, SpeakerPositionEnum.PRESIDING_CHAIR),
        },
        can_file_motions=           None,
        is_secretary=               False,
        is_presenter=               True,
    )

    # sequence of different discussion sections
    LEGISLATOR_DISCUSSION=  RoleRequirements(
        valid_speaker_position_intervals=          {
            (SpeakerPositionEnum.BILL_AUTHOR, SpeakerPositionEnum.PRESIDING_CHAIR),
        },
        can_file_motions=           True,
        is_secretary=               None,
        is_presenter=               None,
    )
    # expert testimony goes from first expert utterance to last
    EXPERT_TESTIMONY=       RoleRequirements(
        valid_speaker_position_intervals=          {
            (SpeakerPositionEnum.EXPERT, SpeakerPositionEnum.EXPERT),
            (SpeakerPositionEnum.BILL_AUTHOR, SpeakerPositionEnum.PRESIDING_CHAIR),
        },
        can_file_motions=           None,
        is_secretary=               None,
        is_presenter=               None,
    )
    # public comments never contain expert testimony
    PUBLIC_COMMENTS=        RoleRequirements(
        valid_speaker_position_intervals=          {
            (SpeakerPositionEnum.NONLEGISLATOR, SpeakerPositionEnum.NONLEGISLATOR),
            (SpeakerPositionEnum.PRESIDING_CHAIR, SpeakerPositionEnum.PRESIDING_CHAIR),
        },
        can_file_motions=           None,
        is_secretary=               None,
        is_presenter=               None,
    )

    # closing remarks by committee chair XOR bill presenter, but not generic committee member
    CLOSING_REMARKS=        RoleRequirements(
        valid_speaker_position_intervals=          {
            (SpeakerPositionEnum.BILL_AUTHOR, SpeakerPositionEnum.BILL_AUTHOR),
            (SpeakerPositionEnum.PRESIDING_CHAIR, SpeakerPositionEnum.PRESIDING_CHAIR),
        },
        can_file_motions=           None,
        is_secretary=               False,
        is_presenter=               None,
    )

    # voting section
    VOTE=                   RoleRequirements(
        valid_speaker_position_intervals=          {
            (SpeakerPositionEnum.BILL_AUTHOR, SpeakerPositionEnum.PRESIDING_CHAIR),
        },
        can_file_motions=           True,
        is_secretary=               None,
        is_presenter=               None,
    )