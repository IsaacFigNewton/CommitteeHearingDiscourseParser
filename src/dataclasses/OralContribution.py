from typing import List, Dict, Tuple, Union, Optional
from dataclasses import dataclass


"""
Based on the UK Parliament's oral contribution ontology
    here: https://ukparliament.github.io/ontologies/oral-contribution/oral-contribution-ontology

Since transcripts' metadata will always include partial or complete speaker information,
    it's simpler to just make a dataclass with optional fields
"""

@dataclass
class OralContribution:
    # utterance id within the hearing
    #   indicates utterance index within hearing transcript
    uid: int
    # pid of speaker
    pid: int
    # utterance text
    text: str

    # if it's a motion
    is_motion: Optional[bool]
    # if it's just a transitional utterance
    is_transition: Optional[bool]
    
    # pids of any speakers (including the speaker themself) that were mentioned
    mentions: Optional[List[int]]
    