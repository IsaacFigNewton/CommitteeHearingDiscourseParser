from typing import List, Tuple, Set, Union, Optional, FrozenSet
from dataclasses import dataclass

from ..enums.UtilEnums import RelativePositionEnum
from ..interfaces.SpeakerProperties import RoleProperties

"""
Used to configure SpeakerRoleEnum items
"""

@dataclass
class RoleRequirements(RoleProperties):
    valid_speaker_position_intervals:       Optional[Set[Tuple[int, int]]]
    cmp_first_mention_first_uid:            Optional[RelativePositionEnum]