from enum import Enum
from ..enums.SpeakerPositionEnum import SpeakerPositionEnum
from ..enums.UtilEnums import RelativePositionEnum
from .RoleRequirements import RoleRequirements

class SpeakerRoleRequirementsEnum(Enum):
    """
    each SpeakerRoleRequirementsEnum denotes the speaker properties
        required for setting a particular attribute to "True"
    if SpeakerRoleRequirementsEnum.speaker_position <= speaker.speaker_position and speaker.speaker_position <= SpeakerRoleRequirementsEnum.max_speaker_position:
        check relevant role classification rules

    TODO: organize the rules below into an interval tree for faster, simpler lookup
    """

    # legislator roles
    is_presenter=       RoleRequirements(
        valid_speaker_position_intervals=          {
            (SpeakerPositionEnum.BILL_AUTHOR.value, SpeakerPositionEnum.BILL_AUTHOR.value),
            (SpeakerPositionEnum.PRESIDING_CHAIR.value, SpeakerPositionEnum.PRESIDING_CHAIR.value),
        },
        can_file_motions=               None,
        is_presenter=                   None,
        cmp_first_mention_first_uid=    RelativePositionEnum.BEFORE,
    )

    # other roles
    is_expert=          RoleRequirements(
        # experts can be legislators or nonlegislators but not committee members
        valid_speaker_position_intervals=          {
            (SpeakerPositionEnum.NONLEGISLATOR.value, SpeakerPositionEnum.EXPERT.value),
        },
        can_file_motions=               False,
        is_presenter=                   False,
        # if expert's name is mentioned before their first utterance
        cmp_first_mention_first_uid=    RelativePositionEnum.BEFORE,
    )
    is_public=          RoleRequirements(
        valid_speaker_position_intervals=          {
            (SpeakerPositionEnum.NONLEGISLATOR.value, SpeakerPositionEnum.NONLEGISLATOR.value),
        },
        can_file_motions=               False,
        is_presenter=                   False,
        cmp_first_mention_first_uid=    RelativePositionEnum.DURING,
    )