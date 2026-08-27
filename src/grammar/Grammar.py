from typing import Tuple, Set, Dict, List, Union
from enum import Enum

from ..enums.SectionEnum import SectionEnum, VoteSectionEnum
from ..speakers.enums.SpeakerPositionEnum import SpeakerPositionEnum

# base symbols
class TOP(Enum):
    ROOT=                   "ROOT"
    START=                  "START"
    START_MIDDLE=           "START_MIDDLE"
    UPPER_MIDDLE=           "UPPER_MIDDLE"
    MIDDLE=                 "MIDDLE"
    LOWER_MIDDLE=           "LOWER_MIDDLE"
    END=                    "END"
    WRAPUP=                 "WRAPUP"

# if thee UPPER_MIDDLE or LOWER_MIDDLE has >= 2 SectionEnums of different types,
#   and the legislator discussion is >= 2 utterances long,
#   then split the EXPERT_TESTIMONY or PUBLIC_COMMENTS into >=2 consecutive SpeakerPositionEnum tokens 
class SMOOTHING(Enum):
    EXPERT_TESTIMONY=       "SMOOTH_EXPERT_TESTIMONY"
    PUBLIC_COMMENTS=        "SMOOTH_PUBLIC_COMMENTS"
    LEGISLATOR_DISCUSSION=  "SMOOTH_LEGISLATOR_DISCUSSION"

# base types
Terminal = Union[
    SpeakerPositionEnum
]
Nonterminal = Union[
    TOP,
    SectionEnum,
    VoteSectionEnum
]
Symbol = Union[
    Terminal,
    Nonterminal
]

# rule types
Terminal_Rule = Union[
    Tuple[Nonterminal, Tuple[Terminal, Terminal]],
    Tuple[Nonterminal, Terminal],
    Tuple[Nonterminal, None]
]
Nonterminal_Rule = Union[
    Tuple[Nonterminal, Tuple[Nonterminal, Nonterminal]],
    Tuple[Nonterminal, Nonterminal],
]
Rule = Union[
    Terminal_Rule,
    Nonterminal_Rule
]

# SpeakerPositionEnum should be disambiguated by now
#   some rules included below for ambiguous positions in case they were missed
GRAMMAR = [
    # broad hearing structures
    (TOP.ROOT,                          (TOP.START_MIDDLE, TOP.END)),
    (TOP.START_MIDDLE,                  (TOP.START, TOP.MIDDLE)),

    # fallback for OTHER sections
    (SectionEnum.OTHER_PROCEDURAL,      (SectionEnum.OTHER_PROCEDURAL, SectionEnum.OTHER_PROCEDURAL)),
    (SectionEnum.OTHER_NONPROCEDURAL,   (SectionEnum.OTHER_NONPROCEDURAL, SectionEnum.OTHER_NONPROCEDURAL)),


    # TOP.START
    (TOP.START,                         (SectionEnum.INTRO, SectionEnum.PRESENTATION)),
    (TOP.START,                         (SectionEnum.INTRO)),
    (TOP.START,                         (SectionEnum.PRESENTATION)),

    # TOP.MIDDLE
    (TOP.MIDDLE,                        (TOP.UPPER_MIDDLE, TOP.LOWER_MIDDLE)),
    (TOP.MIDDLE,                        TOP.UPPER_MIDDLE),
    (TOP.MIDDLE,                        TOP.LOWER_MIDDLE),
    (TOP.MIDDLE,                        None),
    # if there is only 1 EXPERT_TESTIMONY, PUBLIC_COMMENTS, or LEGISLATOR_DISCUSSION utterance,
    #   then ensure that there is only 1 of the other utterance section
    (TOP.MIDDLE,                        (SectionEnum.EXPERT_TESTIMONY, SectionEnum.LEGISLATOR_DISCUSSION)),
    (TOP.MIDDLE,                        (SectionEnum.PUBLIC_COMMENTS, SectionEnum.LEGISLATOR_DISCUSSION)),
    (TOP.MIDDLE,                        SMOOTHING.EXPERT_TESTIMONY),
    (TOP.MIDDLE,                        SMOOTHING.PUBLIC_COMMENTS),
    (TOP.MIDDLE,                        SMOOTHING.LEGISLATOR_DISCUSSION),
    (TOP.MIDDLE,                        SectionEnum.EXPERT_TESTIMONY),
    (TOP.MIDDLE,                        SectionEnum.PUBLIC_COMMENTS),
    # legislator discussion sections must involve >= 2 utterances
    (SMOOTHING.LEGISLATOR_DISCUSSION,   (SMOOTHING.LEGISLATOR_DISCUSSION, SectionEnum.LEGISLATOR_DISCUSSION)),

    # TOP.UPPER_MIDDLE
    (TOP.UPPER_MIDDLE,                  (TOP.UPPER_MIDDLE, TOP.UPPER_MIDDLE)),
    (TOP.UPPER_MIDDLE,                  (SMOOTHING.EXPERT_TESTIMONY, SMOOTHING.LEGISLATOR_DISCUSSION)),
    (TOP.UPPER_MIDDLE,                  (SMOOTHING.EXPERT_TESTIMONY, SectionEnum.EXPERT_TESTIMONY)),
    # allow testimony runs of any length >= 3
    (TOP.UPPER_MIDDLE,                  (SMOOTHING.EXPERT_TESTIMONY, SMOOTHING.EXPERT_TESTIMONY)),
    (TOP.UPPER_MIDDLE,                  (SMOOTHING.EXPERT_TESTIMONY, TOP.UPPER_MIDDLE)),
    # a testimony run of any length may be followed by a discussion
    (TOP.UPPER_MIDDLE,                  (TOP.UPPER_MIDDLE, SMOOTHING.LEGISLATOR_DISCUSSION)),
    # TOP.LOWER_MIDDLE
    (TOP.LOWER_MIDDLE,                  (TOP.LOWER_MIDDLE, TOP.LOWER_MIDDLE)),
    (TOP.LOWER_MIDDLE,                  (SMOOTHING.PUBLIC_COMMENTS, SMOOTHING.LEGISLATOR_DISCUSSION)),
    (TOP.LOWER_MIDDLE,                  (SMOOTHING.PUBLIC_COMMENTS, SectionEnum.PUBLIC_COMMENTS)),
    # allow public comment runs of any length >= 3 (previously only multiples of 3 parsed)
    (TOP.LOWER_MIDDLE,                  (SMOOTHING.PUBLIC_COMMENTS, SMOOTHING.PUBLIC_COMMENTS)),
    (TOP.LOWER_MIDDLE,                  (SMOOTHING.PUBLIC_COMMENTS, TOP.LOWER_MIDDLE)),
    # a comment run of any length may be followed by a discussion (not just exactly 2 utterances)
    (TOP.LOWER_MIDDLE,                  (TOP.LOWER_MIDDLE, SMOOTHING.LEGISLATOR_DISCUSSION)),

    # TOP.END
    (TOP.END,                           (SectionEnum.CLOSING_REMARKS, SectionEnum.VOTE)),
    (TOP.END,                           SectionEnum.CLOSING_REMARKS),
    (TOP.END,                           SectionEnum.VOTE),
    # post-vote / post-close wrap-up; WRAPUP deliberately excludes SECRETARY so it can never reach past a vote
    (TOP.END,                           (TOP.END, TOP.WRAPUP)),
    (TOP.WRAPUP,                        SectionEnum.OTHER_HEARING),        # OTHER_HEARING self-recurses below


    # different SectionEnum expansions
    # TOP.START
    (SectionEnum.INTRO,                 (SectionEnum.OTHER_PROCEDURAL, SectionEnum.INTRO)),
    # (SectionEnum.INTRO,                 (SectionEnum.INTRO, SectionEnum.OTHER_NONPROCEDURAL)),
    (SectionEnum.INTRO,                 (SectionEnum.INTRO, SectionEnum.INTRO)),
    (SectionEnum.PRESENTATION,          (SectionEnum.PRESENTATION, SectionEnum.OTHER_NONPROCEDURAL)),
    (SectionEnum.PRESENTATION,          (SectionEnum.PRESENTATION, SectionEnum.PRESENTATION)),

    # TOP.MIDDLE
    # Smoothing
    (SMOOTHING.EXPERT_TESTIMONY,        (SectionEnum.EXPERT_TESTIMONY, SectionEnum.EXPERT_TESTIMONY)),
    (SMOOTHING.PUBLIC_COMMENTS,         (SectionEnum.PUBLIC_COMMENTS, SectionEnum.PUBLIC_COMMENTS)),
    (SMOOTHING.LEGISLATOR_DISCUSSION,   (SectionEnum.LEGISLATOR_DISCUSSION, SectionEnum.LEGISLATOR_DISCUSSION)),
    # Semi-terminals
    (SectionEnum.LEGISLATOR_DISCUSSION, (SectionEnum.LEGISLATOR_DISCUSSION, SectionEnum.OTHER_NONPROCEDURAL)),
    (SectionEnum.LEGISLATOR_DISCUSSION, (SectionEnum.LEGISLATOR_DISCUSSION, SectionEnum.LEGISLATOR_DISCUSSION)),
    # (SectionEnum.EXPERT_TESTIMONY,      (SectionEnum.EXPERT_TESTIMONY, SectionEnum.EXPERT_TESTIMONY)),
    # (SectionEnum.PUBLIC_COMMENTS,       (SectionEnum.PUBLIC_COMMENTS, SectionEnum.PUBLIC_COMMENTS)),

    # TOP.END
    (SectionEnum.CLOSING_REMARKS,       (SectionEnum.CLOSING_REMARKS, SectionEnum.OTHER_NONPROCEDURAL)),
    (SectionEnum.CLOSING_REMARKS,       (SectionEnum.CLOSING_REMARKS, SectionEnum.CLOSING_REMARKS)),
    (SectionEnum.VOTE,                  (SectionEnum.VOTE, SectionEnum.VOTE)),
    (SectionEnum.OTHER_HEARING,         (SectionEnum.OTHER_HEARING, SectionEnum.OTHER_HEARING)),


    # Terminal rule expansions (terminals are just SpeakerPositionEnum instances)
    # OTHER
    # OTHER_NONPROCEDURAL
    (SectionEnum.OTHER_NONPROCEDURAL,   SpeakerPositionEnum.LEGISLATOR),
    # (SectionEnum.OTHER_NONPROCEDURAL,   SpeakerPositionEnum.PUBLIC),
    # (SectionEnum.OTHER_NONPROCEDURAL,   SpeakerPositionEnum.BILL_AUTHOR),
    # (SectionEnum.OTHER_NONPROCEDURAL,   SpeakerPositionEnum.COMMITTEE_MEMBER),
    # OTHER_PROCEDURAL
    (SectionEnum.OTHER_PROCEDURAL,      (SpeakerPositionEnum.COMMITTEE_MEMBER, SpeakerPositionEnum.SECRETARY)),
    (SectionEnum.OTHER_PROCEDURAL,      SpeakerPositionEnum.PRESIDING_CHAIR),
    (SectionEnum.OTHER_PROCEDURAL,      SpeakerPositionEnum.SECRETARY),


    # TOP.START
    # INTRO
    (SectionEnum.INTRO,                 SpeakerPositionEnum.PRESIDING_CHAIR),
    (SectionEnum.INTRO,                 SpeakerPositionEnum.SECRETARY),
    # PRESENTATION
    (SectionEnum.PRESENTATION,          SpeakerPositionEnum.BILL_AUTHOR),
    (SectionEnum.PRESENTATION,          SpeakerPositionEnum.COMMITTEE_MEMBER),
    (SectionEnum.PRESENTATION,          SpeakerPositionEnum.PRESIDING_CHAIR),

    # TOP.MIDDLE
    # LEGISLATOR_DISCUSSION
    (SectionEnum.LEGISLATOR_DISCUSSION, (SpeakerPositionEnum.COMMITTEE_MEMBER, SpeakerPositionEnum.NONLEGISLATOR)),
    (SectionEnum.LEGISLATOR_DISCUSSION, (SpeakerPositionEnum.COMMITTEE_MEMBER, SpeakerPositionEnum.PUBLIC)),        # member questions a PUBLIC-tagged witness
    (SectionEnum.LEGISLATOR_DISCUSSION, (SpeakerPositionEnum.PRESIDING_CHAIR, SpeakerPositionEnum.NONLEGISLATOR)),
    (SectionEnum.LEGISLATOR_DISCUSSION, SpeakerPositionEnum.EXPERT),
    (SectionEnum.LEGISLATOR_DISCUSSION, SpeakerPositionEnum.BILL_AUTHOR),
    (SectionEnum.LEGISLATOR_DISCUSSION, SpeakerPositionEnum.LEGISLATOR),            # fallback for ambiguous SpeakerPositionEnum
    (SectionEnum.LEGISLATOR_DISCUSSION, SpeakerPositionEnum.COMMITTEE_MEMBER),
    (SectionEnum.LEGISLATOR_DISCUSSION, SpeakerPositionEnum.PRESIDING_CHAIR),
    # EXPERT_TESTIMONY
    (SectionEnum.EXPERT_TESTIMONY,      SpeakerPositionEnum.NONLEGISLATOR),
    (SectionEnum.EXPERT_TESTIMONY,      SpeakerPositionEnum.EXPERT),
    (SectionEnum.EXPERT_TESTIMONY,      SpeakerPositionEnum.LEGISLATOR),            # fallback for ambiguous SpeakerPositionEnum
    # (SectionEnum.EXPERT_TESTIMONY,      SpeakerPositionEnum.BILL_AUTHOR),
    (SectionEnum.EXPERT_TESTIMONY,      SpeakerPositionEnum.COMMITTEE_MEMBER),
    (SectionEnum.EXPERT_TESTIMONY,      SpeakerPositionEnum.PRESIDING_CHAIR),
    # (SectionEnum.EXPERT_TESTIMONY,      SpeakerPositionEnum.SECRETARY),
    # PUBLIC_COMMENTS
    (SectionEnum.PUBLIC_COMMENTS,       SpeakerPositionEnum.PUBLIC),
    (SectionEnum.PUBLIC_COMMENTS,       SpeakerPositionEnum.NONLEGISLATOR),
    (SectionEnum.PUBLIC_COMMENTS,       SpeakerPositionEnum.COMMITTEE_MEMBER),
    (SectionEnum.PUBLIC_COMMENTS,       SpeakerPositionEnum.PRESIDING_CHAIR),
    # CLOSING_REMARKS
    (SectionEnum.CLOSING_REMARKS,       SpeakerPositionEnum.LEGISLATOR),            # fallback for ambiguous SpeakerPositionEnum
    (SectionEnum.CLOSING_REMARKS,       (SpeakerPositionEnum.PRESIDING_CHAIR, SpeakerPositionEnum.BILL_AUTHOR)),
    (SectionEnum.CLOSING_REMARKS,       SpeakerPositionEnum.PRESIDING_CHAIR),
    # VOTE
    (SectionEnum.VOTE,                  SpeakerPositionEnum.PRESIDING_CHAIR),
    (SectionEnum.VOTE,                  SpeakerPositionEnum.SECRETARY),
    # OTHER_HEARING
    (SectionEnum.OTHER_HEARING,         SpeakerPositionEnum.COMMITTEE_MEMBER),
    (SectionEnum.OTHER_HEARING,         SpeakerPositionEnum.BILL_AUTHOR),
    (SectionEnum.OTHER_HEARING,         SpeakerPositionEnum.PRESIDING_CHAIR),
    # (SectionEnum.OTHER_HEARING,         SpeakerPositionEnum.SECRETARY),   # a secretary utterance after the vote is still VOTE
]