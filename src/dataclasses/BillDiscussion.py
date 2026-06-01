from typing import List, Dict, Tuple, Union, Optional
from dataclasses import dataclass

from ..enums.SectionSpeakerEnum import SectionSpeakerEnum
from ..enums.MotionEnum import MotionEnum
from .OralContribution import OralContribution

"""
only want to parse hearings labelled as CA_201720180<AB/SB>7
    if it's got SR in the suffix, then it's a senate resolution,
    which we don't need to parse
tuples represent indices of starting line (inclusive), ending line (exclusive)
"""

@dataclass
class Section:
    # start and end uids (utterance indices) of form [start_uid, end_uid)
    span: Tuple[int, int]
    valid_speakers: SectionSpeakerEnum
    utterances: List[OralContribution]


@dataclass
class VoteSection(Section):
    motion_type: MotionEnum
    motion: OralContribution
    second: OralContribution
    roll_call: OralContribution
    results: List[OralContribution]
    discussion: Optional[List[OralContribution]]


@dataclass
class BillDiscussion:
    """
    Note: hearing transcript may contain a portion of the previous and/or following one
    """

    # introducing senators, pledge of allegiance, etc.
    intro: Optional[Section]

    # bill description/introduction
    #   generally presenter == author if an author is present
    presentation: Section

    # sequence of different discussion sections
    # bill discussion absent in only 5% of hearings, so just take the L there
    discussion: List[Section]
    
    # closing remarks by committee chair or bill author
    closing_remarks: Optional[Section]

    # voting section
    #   may include discussion by legislators
    vote: List[VoteSection]