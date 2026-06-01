from typing import List, Dict, Tuple, Union, Optional
from dataclasses import dataclass

from ..enums.SpeakerTypeEnum import SpeakerTypeEnum
from ..enums.SpeakerRoleEnum import SpeakerRoleEnum

"""
Inspired by the UK Parliament's agent ontology
    here: https://ukparliament.github.io/ontologies/agency/agency-ontology
"""

@dataclass
class Speaker:
    pid: int

    # first and last name not always available
    first_name: Optional[str]
    last_name: Optional[str]

    # speaker type
    speaker_type: Optional[SpeakerTypeEnum]
    # speaker role
    speaker_role: Optional[SpeakerRoleEnum]