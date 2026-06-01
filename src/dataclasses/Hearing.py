from typing import List, Dict, Tuple, Union, Optional
from datetime import datetime
from dataclasses import dataclass

@dataclass
class Hearing:
    hid: int
    bid: int
    cid: int
    cname: str
    hearing_date: datetime
    state: str