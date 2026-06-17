from enum import Enum
from ..enums.SpeakerPositionEnum import SpeakerPositionEnum
from .RoleRequirements import RoleRequirements

class SpeakerRoleRequirementsEnum(Enum):
    """
    each SpeakerRoleRequirementsEnum denotes the speaker properties
        required for setting a particular attribute to "True"
    if SpeakerRoleRequirementsEnum.speaker_position <= speaker.speaker_position and speaker.speaker_position <= SpeakerRoleRequirementsEnum.max_speaker_position:
        check relevant role classification rules

    TODO: organize the rules below into an interval tree for faster, simpler lookup
    """

    # procedural roles
    is_presiding=        RoleRequirements(
        # only vicechairmen or chairmen can preside
        valid_speaker_position_intervals=          {
            (SpeakerPositionEnum.VICE_CHAIRMAN, SpeakerPositionEnum.PRESIDING_CHAIR),
        },
        can_file_motions=           True,
        is_presenter=               None,
    )

    # legislator roles
    is_presenter=       RoleRequirements(
        valid_speaker_position_intervals=          {
            (SpeakerPositionEnum.BILL_AUTHOR, SpeakerPositionEnum.BILL_AUTHOR),
            (SpeakerPositionEnum.PRESIDING_CHAIR, SpeakerPositionEnum.PRESIDING_CHAIR),
        },
        can_file_motions=           None,
        is_presenter=               None,
    )

    # other roles
    is_expert=          RoleRequirements(
        # experts can be legislators or nonlegislators but not committee members
        valid_speaker_position_intervals=          {
            (SpeakerPositionEnum.NONLEGISLATOR, SpeakerPositionEnum.EXPERT),
        },
        can_file_motions=           False,
        is_presenter=               False,
    )
    is_public=          RoleRequirements(
        valid_speaker_position_intervals=          {
            (SpeakerPositionEnum.NONLEGISLATOR, SpeakerPositionEnum.NONLEGISLATOR),
        },
        can_file_motions=           False,
        is_presenter=               False,
    )