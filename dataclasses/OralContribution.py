from typing import List, Dict, Tuple, Union, Optional
from dataclasses import dataclass

from .Speaker import Speaker

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

    # keep speaker role information separate for modularity
    speaker: Speaker

    # utterance text
    reported_speech: str

    # most recent utterance id that is being continued
    resumes_from: Optional[int]
    
    # most recent utterance id that this utterance is responding to
    in_reply_to: Optional[int]