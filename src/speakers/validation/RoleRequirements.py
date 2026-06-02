from typing import List, Dict, Tuple, Union, Optional, FrozenSet
from dataclasses import dataclass

from ..roles.RoleProperties import RoleProperties
from ..types.SpeakerTypeEnum import SpeakerTypeEnum

"""
Used to configure SpeakerRoleEnum items
"""

@dataclass
class RoleRequirements(RoleProperties):
    valid_speaker_types:    FrozenSet[SpeakerTypeEnum]