from typing import List, Dict, Tuple, Union, Optional
from dataclasses import dataclass

from .interfaces.RoleProperties import RoleProperties
from .enums.SpeakerPositionEnum import SpeakerPositionEnum
from .enums.SpeakerRoleEnum import SpeakerRoleEnum

"""
Inspired by the UK Parliament's agent ontology
    here: https://ukparliament.github.io/ontologies/agency/agency-ontology
"""

@dataclass
class Speaker(RoleProperties):
    pid: int

    # first and last name not always available
    first_name: Optional[str]
    last_name: Optional[str]

    # speaker position (if available)
    speaker_position: Optional[SpeakerPositionEnum]
    
    # speaker role
    speaker_role: Optional[SpeakerRoleEnum]