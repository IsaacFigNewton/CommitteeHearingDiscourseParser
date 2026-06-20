from typing import Tuple, Set, Dict, List
from enum import Enum

from .enums.SectionEnum import SectionEnum, VoteSectionEnum
from .speakers.enums.SpeakerPositionEnum import SpeakerPositionEnum

# base symbols
ROOT = "ROOT"

class TOP(Enum):
    START = "START"
    MIDDLE = "MIDDLE"
    END = "END"

# base types
Terminal = Tuple[
    SectionEnum | VoteSectionEnum | None,
    SpeakerPositionEnum | None
] | SectionEnum | VoteSectionEnum | None
Level2_Predicate = List[TOP | SectionEnum]
Predicate = List["Predicate" | Terminal] | Terminal | None

Hearing_Grammar = {
    # broad hearing structures
    ROOT:       [TOP.START, TOP.MIDDLE, TOP.END],
    ROOT:       [SectionEnum.OTHER, TOP.START, TOP.MIDDLE, TOP.END],

    # fallback
    SectionEnum.OTHER: [SectionEnum.OTHER, SectionEnum.OTHER],

    # different discussion starts
    TOP.START:  [SectionEnum.INTRO, SectionEnum.PRESENTATION],
    TOP.START:  [SectionEnum.PRESENTATION],

    # different middles
    TOP.MIDDLE: [SectionEnum.LEGISLATOR_DISCUSSION, SectionEnum.EXPERT_TESTIMONY, SectionEnum.PUBLIC_COMMENTS],
    TOP.MIDDLE: [SectionEnum.EXPERT_TESTIMONY, SectionEnum.PUBLIC_COMMENTS],
    TOP.MIDDLE: [SectionEnum.EXPERT_TESTIMONY],
    TOP.MIDDLE: [SectionEnum.PUBLIC_COMMENTS],

    # different ends
    TOP.END:    [SectionEnum.CLOSING_REMARKS, SectionEnum.VOTE],
    TOP.END:    [SectionEnum.VOTE],

    # different SectionEnum expansions
    # TOP.START
    SectionEnum.INTRO: [SectionEnum.INTRO, SectionEnum.OTHER],
    SectionEnum.INTRO: [SectionEnum.INTRO, SectionEnum.INTRO],
    SectionEnum.PRESENTATION: [SectionEnum.PRESENTATION, SectionEnum.OTHER],
    SectionEnum.PRESENTATION: [SectionEnum.PRESENTATION, SectionEnum.PRESENTATION],
    
    # TOP.MIDDLE
    SectionEnum.LEGISLATOR_DISCUSSION: [SectionEnum.LEGISLATOR_DISCUSSION, SectionEnum.OTHER],
    SectionEnum.LEGISLATOR_DISCUSSION: [SectionEnum.LEGISLATOR_DISCUSSION, SectionEnum.LEGISLATOR_DISCUSSION],
    SectionEnum.EXPERT_TESTIMONY: [SectionEnum.EXPERT_TESTIMONY, SectionEnum.OTHER],
    SectionEnum.EXPERT_TESTIMONY: [SectionEnum.EXPERT_TESTIMONY, SectionEnum.EXPERT_TESTIMONY],
    SectionEnum.EXPERT_TESTIMONY: [SectionEnum.EXPERT_TESTIMONY, SectionEnum.LEGISLATOR_DISCUSSION],
    SectionEnum.EXPERT_TESTIMONY: [SectionEnum.LEGISLATOR_DISCUSSION, SectionEnum.EXPERT_TESTIMONY],
    SectionEnum.PUBLIC_COMMENTS: [SectionEnum.PUBLIC_COMMENTS, SectionEnum.OTHER],
    SectionEnum.PUBLIC_COMMENTS: [SectionEnum.PUBLIC_COMMENTS, SectionEnum.PUBLIC_COMMENTS],
    SectionEnum.PUBLIC_COMMENTS: [SectionEnum.PUBLIC_COMMENTS, SectionEnum.LEGISLATOR_DISCUSSION],
    SectionEnum.PUBLIC_COMMENTS: [SectionEnum.LEGISLATOR_DISCUSSION, SectionEnum.PUBLIC_COMMENTS],

    # TOP.END
    SectionEnum.CLOSING_REMARKS: [SectionEnum.CLOSING_REMARKS, SectionEnum.OTHER],
    SectionEnum.CLOSING_REMARKS: [SectionEnum.CLOSING_REMARKS, SectionEnum.CLOSING_REMARKS],
    SectionEnum.VOTE: [SectionEnum.VOTE, SectionEnum.OTHER],
    SectionEnum.VOTE: [SectionEnum.VOTE, SectionEnum.VOTE]

}