from typing import List, Dict, Tuple, Union, Optional
from datetime import datetime
from dataclasses import dataclass

from .OralContribution import OralContribution
from .Speaker import Speaker
from .Section import Section, VoteSection


@dataclass
class Hearing:
    hid: int
    bid: str
    cid: int
    cname: str
    hearing_date: datetime
    state: str

    # index speakers by their pids
    speakers: Dict[int, Speaker]
    

@dataclass
class RawHearing(Hearing):
    utterances: List[OralContribution]


@dataclass
class ParsedHearing(Hearing):
    """
    Note: hearing transcript may contain a portion of the previous and/or following one
        these remain uncategorized
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