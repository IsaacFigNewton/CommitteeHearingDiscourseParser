from typing import List, Tuple, Optional
from dataclasses import dataclass

from ..speakers.validation.SectionRoleRequirementsEnum import SectionSpeakerRequirementsEnum
from ..enums.MotionEnum import MotionEnum
from .OralContribution import OralContribution


@dataclass
class Section:
    """
    interval given by start uid (inclusive) and end uid (exclusive)
        of form [start_uid, end_uid)
    """
    span: Tuple[int, int]
    valid_speakers: SectionSpeakerRequirementsEnum
    utterances: List[OralContribution]