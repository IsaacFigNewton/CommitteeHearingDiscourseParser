from typing import Tuple, Set, Dict, List
from enum import Enum

from .enums.SectionEnum import SectionEnum, VoteSectionEnum
from .speakers.enums.SpeakerPositionEnum import SpeakerPositionEnum

# base symbols
ROOT = "ROOT"

class TOP(Enum):
    START = "START"
    MIDDLE = "MIDDLE"
    LOWER_MIDDLE = "LOWER_MIDDLE"
    END = "END"

# base types
Terminal = Tuple[
    SectionEnum | VoteSectionEnum,
    SpeakerPositionEnum
] | SectionEnum | VoteSectionEnum | None
Level2_Predicate = List[TOP | SectionEnum]
Predicate = List["Predicate" | Terminal] | Terminal | None

Hearing_Grammar = [
    # broad hearing structures
    (ROOT, [TOP.START, TOP.MIDDLE, TOP.END]),
    (ROOT, [SectionEnum.OTHER, TOP.START, TOP.MIDDLE, TOP.END]),

    # fallback
    # (SectionEnum.OTHER, [SectionEnum.OTHER, SectionEnum.OTHER]),

    # different discussion starts
    (TOP.START,                         [SectionEnum.INTRO, SectionEnum.PRESENTATION]),
    (TOP.START,                         [SectionEnum.PRESENTATION]),

    # different middles
    (TOP.MIDDLE,                        [SectionEnum.LEGISLATOR_DISCUSSION, TOP.LOWER_MIDDLE]),
    (TOP.MIDDLE,                        TOP.LOWER_MIDDLE),
    (TOP.LOWER_MIDDLE,                  [SectionEnum.EXPERT_TESTIMONY, SectionEnum.PUBLIC_COMMENTS]),
    (TOP.LOWER_MIDDLE,                  [SectionEnum.EXPERT_TESTIMONY]),
    (TOP.LOWER_MIDDLE,                  [SectionEnum.PUBLIC_COMMENTS]),

    # different ends
    (TOP.END,                           [SectionEnum.CLOSING_REMARKS, SectionEnum.VOTE]),
    (TOP.END,                           [SectionEnum.VOTE]),

    # different SectionEnum expansions
    # TOP.START
    (SectionEnum.INTRO,                 [SectionEnum.INTRO, SectionEnum.OTHER]),
    (SectionEnum.INTRO,                 [SectionEnum.INTRO, SectionEnum.INTRO]),
    (SectionEnum.PRESENTATION,          [SectionEnum.PRESENTATION, SectionEnum.OTHER]),
    (SectionEnum.PRESENTATION,          [SectionEnum.PRESENTATION, SectionEnum.PRESENTATION]),

    # TOP.MIDDLE
    (SectionEnum.LEGISLATOR_DISCUSSION, [SectionEnum.LEGISLATOR_DISCUSSION, SectionEnum.OTHER]),
    (SectionEnum.LEGISLATOR_DISCUSSION, [SectionEnum.LEGISLATOR_DISCUSSION, SectionEnum.LEGISLATOR_DISCUSSION]),
    (SectionEnum.EXPERT_TESTIMONY,      [SectionEnum.EXPERT_TESTIMONY, SectionEnum.OTHER]),
    (SectionEnum.EXPERT_TESTIMONY,      [SectionEnum.EXPERT_TESTIMONY, SectionEnum.EXPERT_TESTIMONY]),
    (SectionEnum.EXPERT_TESTIMONY,      [SectionEnum.EXPERT_TESTIMONY, SectionEnum.LEGISLATOR_DISCUSSION]),
    (SectionEnum.EXPERT_TESTIMONY,      [SectionEnum.LEGISLATOR_DISCUSSION, SectionEnum.EXPERT_TESTIMONY]),
    (SectionEnum.PUBLIC_COMMENTS,       [SectionEnum.PUBLIC_COMMENTS, SectionEnum.OTHER]),
    (SectionEnum.PUBLIC_COMMENTS,       [SectionEnum.PUBLIC_COMMENTS, SectionEnum.PUBLIC_COMMENTS]),
    (SectionEnum.PUBLIC_COMMENTS,       [SectionEnum.PUBLIC_COMMENTS, SectionEnum.LEGISLATOR_DISCUSSION]),
    (SectionEnum.PUBLIC_COMMENTS,       [SectionEnum.LEGISLATOR_DISCUSSION, SectionEnum.PUBLIC_COMMENTS]),

    # TOP.END
    (SectionEnum.CLOSING_REMARKS,       [SectionEnum.CLOSING_REMARKS, SectionEnum.OTHER]),
    (SectionEnum.CLOSING_REMARKS,       [SectionEnum.CLOSING_REMARKS, SectionEnum.CLOSING_REMARKS]),
    (SectionEnum.VOTE,                  [SectionEnum.VOTE, SectionEnum.OTHER]),
    (SectionEnum.VOTE,                  [SectionEnum.VOTE, SectionEnum.VOTE]),

    # valid role expansions
    (SectionEnum.OTHER,                 (SectionEnum.OTHER, SpeakerPositionEnum.NONLEGISLATOR)),
    (SectionEnum.OTHER,                 (SectionEnum.OTHER, SpeakerPositionEnum.LEGISLATOR)),
    (SectionEnum.OTHER,                 (SectionEnum.OTHER, SpeakerPositionEnum.COMMITTEE_MEMBER)),
    (SectionEnum.OTHER,                 (SectionEnum.OTHER, SpeakerPositionEnum.PRESIDING_CHAIR)),
    (SectionEnum.OTHER,                 (SectionEnum.OTHER, SpeakerPositionEnum.SECRETARY)),
    (SectionEnum.INTRO,                 (SectionEnum.INTRO, SpeakerPositionEnum.PRESIDING_CHAIR)),
    (SectionEnum.INTRO,                 (SectionEnum.INTRO, SpeakerPositionEnum.SECRETARY)),
    (SectionEnum.PRESENTATION,          (SectionEnum.PRESENTATION, SpeakerPositionEnum.PRESIDING_CHAIR)),
    (SectionEnum.PRESENTATION,          (SectionEnum.PRESENTATION, SpeakerPositionEnum.BILL_AUTHOR)),
    (SectionEnum.LEGISLATOR_DISCUSSION, (SectionEnum.LEGISLATOR_DISCUSSION, SpeakerPositionEnum.BILL_AUTHOR)),
    (SectionEnum.LEGISLATOR_DISCUSSION, (SectionEnum.LEGISLATOR_DISCUSSION, SpeakerPositionEnum.COMMITTEE_MEMBER)),
    (SectionEnum.LEGISLATOR_DISCUSSION, (SectionEnum.LEGISLATOR_DISCUSSION, SpeakerPositionEnum.PRESIDING_CHAIR)),
    (SectionEnum.LEGISLATOR_DISCUSSION, (SectionEnum.LEGISLATOR_DISCUSSION, SpeakerPositionEnum.SECRETARY)),
    (SectionEnum.EXPERT_TESTIMONY,      (SectionEnum.EXPERT_TESTIMONY, SpeakerPositionEnum.EXPERT)),
    (SectionEnum.EXPERT_TESTIMONY,      (SectionEnum.EXPERT_TESTIMONY, SpeakerPositionEnum.BILL_AUTHOR)),
    (SectionEnum.EXPERT_TESTIMONY,      (SectionEnum.EXPERT_TESTIMONY, SpeakerPositionEnum.COMMITTEE_MEMBER)),
    (SectionEnum.EXPERT_TESTIMONY,      (SectionEnum.EXPERT_TESTIMONY, SpeakerPositionEnum.PRESIDING_CHAIR)),
    (SectionEnum.EXPERT_TESTIMONY,      (SectionEnum.EXPERT_TESTIMONY, SpeakerPositionEnum.SECRETARY)),
    (SectionEnum.PUBLIC_COMMENTS,       (SectionEnum.PUBLIC_COMMENTS, SpeakerPositionEnum.PUBLIC)),
    (SectionEnum.PUBLIC_COMMENTS,       (SectionEnum.PUBLIC_COMMENTS, SpeakerPositionEnum.BILL_AUTHOR)),
    (SectionEnum.PUBLIC_COMMENTS,       (SectionEnum.PUBLIC_COMMENTS, SpeakerPositionEnum.COMMITTEE_MEMBER)),
    (SectionEnum.PUBLIC_COMMENTS,       (SectionEnum.PUBLIC_COMMENTS, SpeakerPositionEnum.PRESIDING_CHAIR)),
    (SectionEnum.PUBLIC_COMMENTS,       (SectionEnum.PUBLIC_COMMENTS, SpeakerPositionEnum.SECRETARY)),
    (SectionEnum.CLOSING_REMARKS,       (SectionEnum.CLOSING_REMARKS, SpeakerPositionEnum.BILL_AUTHOR)),
    (SectionEnum.CLOSING_REMARKS,       (SectionEnum.CLOSING_REMARKS, SpeakerPositionEnum.PRESIDING_CHAIR)),
    (SectionEnum.VOTE,                  (SectionEnum.VOTE, SpeakerPositionEnum.BILL_AUTHOR)),
    (SectionEnum.VOTE,                  (SectionEnum.VOTE, SpeakerPositionEnum.COMMITTEE_MEMBER)),
    (SectionEnum.VOTE,                  (SectionEnum.VOTE, SpeakerPositionEnum.PRESIDING_CHAIR)),
    (SectionEnum.VOTE,                  (SectionEnum.VOTE, SpeakerPositionEnum.SECRETARY)),
]