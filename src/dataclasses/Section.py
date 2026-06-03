from typing import List, Tuple, Optional
from dataclasses import dataclass

from ..speakers.validation.SectionSpeakerRequirementsEnum import SectionSpeakerRequirementsEnum
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


@dataclass
class VoteSection(Section):
    motion_type: MotionEnum
    motion: OralContribution
    second: OralContribution
    roll_call: OralContribution
    results: List[OralContribution]
    discussion: Optional[List[OralContribution]]