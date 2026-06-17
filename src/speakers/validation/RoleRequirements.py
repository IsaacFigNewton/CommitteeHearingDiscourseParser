from typing import List, Tuple, Set, Union, Optional, FrozenSet
from dataclasses import dataclass

from ..enums.SpeakerPositionEnum import SpeakerPositionEnum
from ..interfaces.SpeakerProperties import RoleProperties

"""
Used to configure SpeakerRoleEnum items
"""

@dataclass
class RoleRequirements(RoleProperties):
    valid_speaker_position_intervals:       Optional[Set[Tuple[SpeakerPositionEnum, SpeakerPositionEnum]]]