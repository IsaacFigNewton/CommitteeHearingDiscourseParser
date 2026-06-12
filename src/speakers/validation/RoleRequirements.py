from typing import List, Dict, Tuple, Union, Optional, FrozenSet
from dataclasses import dataclass

from .types import ValidPositions
from ..interfaces.RoleProperties import RoleProperties

"""
Used to configure SpeakerRoleEnum items
"""

@dataclass
class RoleRequirements(RoleProperties):
    valid_speaker_positions:    Optional[ValidPositions]