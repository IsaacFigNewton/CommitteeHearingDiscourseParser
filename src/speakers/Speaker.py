from typing import List, Dict, Tuple, Union, Optional
from dataclasses import dataclass

from .interfaces.SpeakerProperties import SpeakerPositionRoleProperties

"""
Inspired by the UK Parliament's agent ontology
    here: https://ukparliament.github.io/ontologies/agency/agency-ontology
"""

@dataclass
class Speaker(SpeakerPositionRoleProperties):
    pid: int

    # first and last name not always available
    first_name: Optional[str]
    last_name: Optional[str]