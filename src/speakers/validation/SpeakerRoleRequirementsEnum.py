from enum import Enum
from ..types.SpeakerPositionEnum import SpeakerPositionEnum
from .RoleRequirements import RoleRequirements

class SpeakerRoleRequirementsEnum(Enum):
    """
    each SpeakerRoleRequirementsEnum is defined by:
        valid_speaker_positions:    a set of the types of speakers that may hold the role
        is_committee_member:    whether the speaker with this role must be a committee member,
        is_bill_author:         whether the speaker with this role must be a primary bill author
    """

    # procedural roles
    PRESIDING_CHAIR=        RoleRequirements(
        is_legislator=              True,
        is_committee_member=        True,
        is_bill_author=             None,
        # only chairmen or vicechairmen can preside
        valid_speaker_positions=    frozenset({
            SpeakerPositionEnum.CHAIRMAN,
            SpeakerPositionEnum.VICE_CHAIRMAN,
        }),
    )
    SECRETARY=              RoleRequirements(
        is_legislator=              False,
        is_committee_member=        False,
        is_bill_author=             False,
        valid_speaker_positions=    frozenset({
            SpeakerPositionEnum.SECRETARY,
        }),
    )

    # legislator roles
    PRESENTER=              RoleRequirements(
        is_legislator=              True,
        is_committee_member=        None,
        is_bill_author=             None,
        # presiding chair cannot present bill
        valid_speaker_positions=    frozenset({
            SpeakerPositionEnum.LEGISLATOR,
        }),
    )
    COMMITTEE_MEMBER=       RoleRequirements(
        is_legislator=              True,
        is_committee_member=        True,
        is_bill_author=             None,
        # anyone who's a committee member can have this role
        valid_speaker_positions=    None,
    )

    # other roles
    EXPERT=             RoleRequirements(
        is_legislator=              None,
        is_committee_member=        False,
        is_bill_author=             False,
        # experts can be legislators or nonlegislators
        valid_speaker_positions=    None,
    )
    PUBLIC=             RoleRequirements(
        is_legislator=              False,
        is_committee_member=        False,
        is_bill_author=             False,
        valid_speaker_positions=    frozenset({
            SpeakerPositionEnum.NONLEGISLATOR
        }),
    )
    UNKNOWN=            RoleRequirements(
        is_legislator=              False,
        is_committee_member=        False,
        is_bill_author=             False,
        valid_speaker_positions=    frozenset({
            SpeakerPositionEnum.UNKNOWN
        }),
    )