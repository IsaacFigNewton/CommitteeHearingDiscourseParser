from typing import List, Dict, Tuple, Union, Optional, Set
from dataclasses import dataclass

from ..speakers.interfaces.SpeakerProperties import RoleProperties
from ..enums.SectionEnum import SectionEnum
from ..enums.SpeechActEnum import SpeechActEnum

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
    # pids of any speakers (including the current one) that were mentioned
    pids_mentioned: Optional[Set[int]]
    # bids of any bills (including the current one) that were mentioned
    bids_mentioned: Optional[Set[str]]

    # metadata features
    # relative position of the utterance within the hearing transcript
    relative_position: Optional[float]
    # total # sentences in the utterance
    sent_count: Optional[int]
    
    # cues
    speech_act_cues: Optional[Set[SpeechActEnum]]
    section_cues: Optional[Set[SectionEnum]]

    # tags for evaluation
    # section for classification
    section: Optional[SectionEnum]


@dataclass
class FlatTaggedOralContribution(RoleProperties, TaggedOralContribution):
    pass