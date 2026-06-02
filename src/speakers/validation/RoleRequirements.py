from typing import List, Dict, Tuple, Union, Optional, FrozenSet
from dataclasses import dataclass

from ..roles.RoleProperties import RoleProperties
from ..types.SpeakerPositionEnum import SpeakerPositionEnum

"""
Used to configure SpeakerRoleEnum items
"""

@dataclass
class RoleRequirements(RoleProperties):
    valid_speaker_positions:    Optional[FrozenSet[SpeakerPositionEnum]]