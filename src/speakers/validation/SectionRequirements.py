from typing import List, Dict, Tuple, Union, Optional, FrozenSet
from dataclasses import dataclass

from .types import ValidRoles

@dataclass
class SectionRequirements:
    valid_speaker_roles:    Optional[ValidRoles]
