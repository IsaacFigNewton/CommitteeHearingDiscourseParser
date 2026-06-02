from enum import Enum
from ..types.SpeakerTypeEnum import SpeakerTypeEnum
from .RoleRequirements import RoleRequirements

class SpeakerRoleRequirementsEnum(Enum):
    """
    each SpeakerRoleRequirementsEnum is defined by:
        valid_speaker_types:    a set of the types of speakers that may hold the role
        is_committee_member:    whether the speaker with this role must be a committee member,
        is_bill_author:         whether the speaker with this role must be a primary bill author
    """

    # procedural roles
    PRESIDING_CHAIR=        RoleRequirements(
        is_committee_member=    True,
        is_bill_author=         None,
        valid_speaker_types=    frozenset({
            SpeakerTypeEnum.CHAIRMAN,
            SpeakerTypeEnum.VICE_CHAIRMAN,
        }),
    )
    SECRETARY=              RoleRequirements(
        is_committee_member=    False,
        is_bill_author=         False,
        valid_speaker_types=    frozenset({
            SpeakerTypeEnum.SECRETARY,
        }),
    )

    # legislator roles
    PRESENTER=              RoleRequirements(
        is_committee_member=    None,
        is_bill_author=         None,
        valid_speaker_types=    frozenset({
            SpeakerTypeEnum.LEGISLATOR,
        }),
    )
    COMMITTEE_MEMBER=       RoleRequirements(
        is_committee_member=    True,
        is_bill_author=         None,
        valid_speaker_types=    frozenset({
            SpeakerTypeEnum.CHAIRMAN,
            SpeakerTypeEnum.VICE_CHAIRMAN,
            SpeakerTypeEnum.LEGISLATOR,
        }),
    )

    # other roles
    EXPERT=             RoleRequirements(
        is_committee_member=    False,
        is_bill_author=         False,
        valid_speaker_types=    frozenset({
            SpeakerTypeEnum.LEGISLATOR,
            SpeakerTypeEnum.NONLEGISLATOR
        }),
    )
    PUBLIC=             RoleRequirements(
        is_committee_member=    False,
        is_bill_author=         False,
        valid_speaker_types=    frozenset({
            SpeakerTypeEnum.NONLEGISLATOR
        }),
    )
    UNKNOWN=            RoleRequirements(
        is_committee_member=    False,
        is_bill_author=         False,
        valid_speaker_types=    frozenset({
            SpeakerTypeEnum.UNKNOWN
        }),
    )