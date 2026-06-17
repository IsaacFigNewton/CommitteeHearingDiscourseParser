from typing import List, Dict, Tuple, Union, Optional
from dataclasses import dataclass

from ..speakers.interfaces.RoleProperties import RoleProperties
from ..speakers.enums.SpeakerPositionEnum import SpeakerPositionEnum
from ..speakers.enums.SpeakerRoleEnum import SpeakerRoleEnum
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
    section: Optional[SectionEnum]

    speaker_position: Optional[SpeakerPositionEnum]
    speaker_is_legislator: bool
    speaker_is_committee_member: bool
    speaker_role: Optional[SpeakerRoleEnum]

    # pids of any speakers (including the current one) that were mentioned
    mentions_speakers: Optional[List[int]]
    # bids of any bills (including the current one) that were mentioned
    mentions_bills: Optional[List[str]]
    has_bill_action: bool
    has_presentation_cue: bool
    has_vote_cue: bool
    has_disposition_cue: bool

    # metadata features
    relative_position: Optional[float]
    relative_len: Optional[float]

    # tags for evaluation
    # if it's a motion
    is_motion: Optional[bool]
    # if it's just a transitional utterance
    is_transition: Optional[bool]