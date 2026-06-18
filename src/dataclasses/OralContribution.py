from typing import List, Dict, Tuple, Union, Optional, Set
from dataclasses import dataclass

from ..speakers.interfaces.SpeakerProperties import PositionRoleProperties
from ..speakers.enums.SectionEnum import SectionEnum

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


@dataclass
class TaggedOralContribution(OralContribution):
    # names of any speakers (including the current one) that were mentioned
    mentions_speakers: Optional[Set[str]]
    # pids of any speakers (including the current one) that were mentioned
    pids_mentioned: Optional[Set[int]]
    # names of any bills (including the current one) that were mentioned
    mentions_bills: Optional[Set[str]]
    # bids of any speakers (including the current one) that were mentioned
    bids_mentioned: Optional[Set[int]]
    
    has_bill_action: bool
    has_presentation_cue: bool
    has_vote_cue: bool
    has_disposition_cue: bool

    # tags for evaluation
    # if it's a motion
    is_motion: Optional[bool]
    # if it's just a transitional utterance
    is_transition: Optional[bool]
    # section for classification
    section: Optional[SectionEnum]


@dataclass
class FlatTaggedOralContribution(PositionRoleProperties, TaggedOralContribution):
    # metadata features
    relative_position: Optional[float]
    relative_len: Optional[float]