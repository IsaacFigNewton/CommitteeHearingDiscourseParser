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
            (SpeakerPositionEnum.VICE_CHAIRMAN.value, SpeakerPositionEnum.PRESIDING_CHAIR.value),
        },
        can_file_motions=               True,
        is_presenter=                   None,
        cmp_first_mention_first_uid=    None,
    )

    # bill description/introduction
    PRESENTATION=           RoleRequirements(
        valid_speaker_position_intervals=          {
            (SpeakerPositionEnum.BILL_AUTHOR.value, SpeakerPositionEnum.BILL_AUTHOR.value),
            (SpeakerPositionEnum.PRESIDING_CHAIR.value, SpeakerPositionEnum.PRESIDING_CHAIR.value),
        },
        can_file_motions=               None,
        is_presenter=                   True,
        cmp_first_mention_first_uid=    None,
    )

    # sequence of different discussion sections
    LEGISLATOR_DISCUSSION=  RoleRequirements(
        valid_speaker_position_intervals=          {
            (SpeakerPositionEnum.BILL_AUTHOR.value, SpeakerPositionEnum.SECRETARY.value),
        },
        can_file_motions=               True,
        is_presenter=                   None,
        cmp_first_mention_first_uid=    None,
    )
    # expert testimony goes from first expert utterance to last
    EXPERT_TESTIMONY=       RoleRequirements(
        valid_speaker_position_intervals=          {
            (SpeakerPositionEnum.EXPERT.value, SpeakerPositionEnum.EXPERT.value),
            (SpeakerPositionEnum.BILL_AUTHOR.value, SpeakerPositionEnum.SECRETARY.value),
        },
        can_file_motions=               None,
        is_presenter=                   None,
        cmp_first_mention_first_uid=    None,
    )
    # public comments never contain expert testimony
    PUBLIC_COMMENTS=        RoleRequirements(
        valid_speaker_position_intervals=          {
            (SpeakerPositionEnum.NONLEGISLATOR.value, SpeakerPositionEnum.NONLEGISLATOR.value),
            (SpeakerPositionEnum.PRESIDING_CHAIR.value, SpeakerPositionEnum.SECRETARY.value),
        },
        can_file_motions=               None,
        is_presenter=                   None,
        cmp_first_mention_first_uid=    None,
    )

    # closing remarks by committee chair XOR bill presenter, but not generic committee member
    CLOSING_REMARKS=        RoleRequirements(
        valid_speaker_position_intervals=          {
            (SpeakerPositionEnum.BILL_AUTHOR.value, SpeakerPositionEnum.BILL_AUTHOR.value),
            (SpeakerPositionEnum.PRESIDING_CHAIR.value, SpeakerPositionEnum.PRESIDING_CHAIR.value),
        },
        can_file_motions=               None,
        is_presenter=                   None,
        cmp_first_mention_first_uid=    None,
    )

    # voting section
    VOTE=                   RoleRequirements(
        valid_speaker_position_intervals=          {
            (SpeakerPositionEnum.BILL_AUTHOR.value, SpeakerPositionEnum.SECRETARY.value),
        },
        can_file_motions=               True,
        is_presenter=                   None,
        cmp_first_mention_first_uid=    None,
    )

    # catch-all category - allows any speaker/utterance configuration
    OTHER=                  RoleRequirements(
        valid_speaker_position_intervals=          None,  # No restrictions
        can_file_motions=               None,  # No restrictions
        is_presenter=                   None,  # No restrictions
        cmp_first_mention_first_uid=    None,
    )