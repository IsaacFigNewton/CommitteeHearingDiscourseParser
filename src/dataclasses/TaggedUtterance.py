from typing import Optional
from dataclasses import dataclass
from ..speakers.interfaces.RoleProperties import RoleProperties
from ..speakers.enums.SpeakerPositionEnum import SpeakerPositionEnum
from ..speakers.enums.SpeakerRoleEnum import SpeakerRoleEnum
from ..speakers.enums.SectionEnum import SectionEnum

@dataclass
class TaggedUtterance(RoleProperties):
    hid: int
    pid: int
    uid: int
    position: Optional[SpeakerPositionEnum]
    role: Optional[SpeakerRoleEnum]
    section: Optional[SectionEnum]