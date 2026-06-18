from typing import List, Dict, Tuple, Union, Optional, FrozenSet
from dataclasses import dataclass
from ..enums.SpeakerPositionEnum import SpeakerPositionEnum

@dataclass
class RoleProperties:
    # can file motions?
    #   committee secretary can file motions
    can_file_motions:       Optional[bool]

    # context-derived role features
    # is the speaker presenting the current bill?
    is_presenter:           Optional[bool]

@dataclass
class PositionRoleProperties(RoleProperties):
    # speaker's level of legislative authority
    speaker_position:       Optional[SpeakerPositionEnum]

@dataclass
class SpeakerPositionRoleProperties(PositionRoleProperties):
    # first uid in which speaker is mentioned
    first_mention_uid:      Optional[int]
    # uid of speaker's first utterance
    first_uid:              int
    # uid of speaker's last utterance
    last_uid:               int