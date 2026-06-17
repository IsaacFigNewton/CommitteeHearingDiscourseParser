from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass

from .OralContribution import OralContribution, TaggedOralContribution
from ..speakers.Speaker import Speaker
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
class TaggedHearing(Hearing):
    utterances: List[TaggedOralContribution]