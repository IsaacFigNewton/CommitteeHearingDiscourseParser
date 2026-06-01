from typing import List, Dict, Tuple, Union, Optional
from datetime import datetime
from dataclasses import dataclass

from .OralContribution import OralContribution
from .Speaker import Speaker

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
    utterances: List[OralContribution]