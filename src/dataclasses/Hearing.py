from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass

from .OralContribution import OralContribution, TaggedOralContribution
from ..speakers.Speaker import Speaker


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
    
    def __str__(self):
        """Print formatted transcript."""
        strings = list()
        strings.append("\n")
        strings.append(f"State:\t\t{self.state}")
        strings.append(f"Committee:\t{self.cname}")
        strings.append(f"Bill:\t\t{self.bid}")
        strings.append(f"Date:\t\t{self.hearing_date.strftime('%Y-%m-%d')}")
        strings.append("\n")
        strings.append("Transcript:")
        for u in self.utterances:
            speaker = self.speakers[u.pid]
            name = f"{speaker.first_name or 'UNKNOWN'} {speaker.last_name or 'UNKNOWN'}:"
            role = "UNKNOWN"
            if speaker.speaker_position:
                role = speaker.speaker_position.name
            strings.append(f"{name} [{role}]:")
            strings.append(f"{u.text}")
            strings.append("\n")
        return "\n".join(strings)

@dataclass
class TaggedHearing(Hearing):
    utterances: List[TaggedOralContribution]