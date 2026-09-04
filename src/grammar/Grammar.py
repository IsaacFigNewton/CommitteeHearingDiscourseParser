from typing import Tuple, Set, Dict, List, Union
from enum import Enum
from collections import defaultdict

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
#   then split the EXPERT_TESTIMONY or PUBLIC_COMMENTS into >=2 consecutive TerminalEnum tokens 
class SMOOTHING(Enum):
    EXPERT_TESTIMONY=       "SMOOTH_EXPERT_TESTIMONY"
    PUBLIC_COMMENTS=        "SMOOTH_PUBLIC_COMMENTS"
    LEGISLATOR_DISCUSSION=  "SMOOTH_LEGISLATOR_DISCUSSION"


class TerminalEnum(Enum):
    SECRETARY=          SpeakerPositionEnum.SECRETARY
    PRESIDING_CHAIR=    SpeakerPositionEnum.PRESIDING_CHAIR
    CHAIRMAN=           SpeakerPositionEnum.CHAIRMAN
    VICE_CHAIRMAN=      SpeakerPositionEnum.VICE_CHAIRMAN
    COMMITTEE_MEMBER=   SpeakerPositionEnum.COMMITTEE_MEMBER
    BILL_AUTHOR=        SpeakerPositionEnum.BILL_AUTHOR
    LEGISLATOR=         SpeakerPositionEnum.LEGISLATOR
    EXPERT=             SpeakerPositionEnum.EXPERT
    NONLEGISLATOR=      SpeakerPositionEnum.NONLEGISLATOR
    PUBLIC=             SpeakerPositionEnum.PUBLIC

# base types
Nonterminal = Union[
    TOP,
    SMOOTHING,
    SectionEnum,
    VoteSectionEnum,
    TerminalEnum
]

# rule types
Terminal_Rule = Union[
    Tuple[Nonterminal, SpeakerPositionEnum],
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

# TerminalEnum should be disambiguated by now
#   some rules included below for ambiguous positions in case they were missed
GRAMMAR_TOP_EXPANSIONS = [
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
]

GRAMMAR_SECTION_EXPANSIONS = [
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
    # (SectionEnum.LEGISLATOR_DISCUSSION, (SectionEnum.LEGISLATOR_DISCUSSION, SectionEnum.OTHER_NONPROCEDURAL)),
    (SectionEnum.LEGISLATOR_DISCUSSION, (SectionEnum.LEGISLATOR_DISCUSSION, SectionEnum.LEGISLATOR_DISCUSSION)),
    # (SectionEnum.EXPERT_TESTIMONY,      (SectionEnum.EXPERT_TESTIMONY, SectionEnum.EXPERT_TESTIMONY)),
    # (SectionEnum.PUBLIC_COMMENTS,       (SectionEnum.PUBLIC_COMMENTS, SectionEnum.PUBLIC_COMMENTS)),

    # TOP.END
    (SectionEnum.CLOSING_REMARKS,       (SectionEnum.CLOSING_REMARKS, SectionEnum.OTHER_NONPROCEDURAL)),
    (SectionEnum.CLOSING_REMARKS,       (SectionEnum.CLOSING_REMARKS, SectionEnum.CLOSING_REMARKS)),
    (SectionEnum.VOTE,                  (SectionEnum.VOTE, SectionEnum.OTHER_NONPROCEDURAL)),
    (SectionEnum.VOTE,                  (SectionEnum.VOTE, SectionEnum.VOTE)),
    (SectionEnum.OTHER_HEARING,         (SectionEnum.OTHER_HEARING, SectionEnum.OTHER_HEARING)),
]

GRAMMAR_LEAF_EXPANSIONS = [
    # OTHER
    # OTHER_NONPROCEDURAL
    (SectionEnum.OTHER_NONPROCEDURAL,   TerminalEnum.LEGISLATOR),
    # (SectionEnum.OTHER_NONPROCEDURAL,   TerminalEnum.PUBLIC),
    (SectionEnum.OTHER_NONPROCEDURAL,   (TerminalEnum.PRESIDING_CHAIR, TerminalEnum.BILL_AUTHOR)),
    # (SectionEnum.OTHER_NONPROCEDURAL,   TerminalEnum.COMMITTEE_MEMBER),
    # OTHER_PROCEDURAL
    (SectionEnum.OTHER_PROCEDURAL,      (TerminalEnum.COMMITTEE_MEMBER, TerminalEnum.SECRETARY)),
    (SectionEnum.OTHER_PROCEDURAL,      TerminalEnum.PRESIDING_CHAIR),
    (SectionEnum.OTHER_PROCEDURAL,      TerminalEnum.SECRETARY),


    # TOP.START
    # INTRO
    (SectionEnum.INTRO,                 TerminalEnum.PRESIDING_CHAIR),
    (SectionEnum.INTRO,                 TerminalEnum.SECRETARY),
    # PRESENTATION
    (SectionEnum.PRESENTATION,          (TerminalEnum.EXPERT, TerminalEnum.PRESIDING_CHAIR)),
    (SectionEnum.PRESENTATION,          TerminalEnum.BILL_AUTHOR),
    (SectionEnum.PRESENTATION,          TerminalEnum.COMMITTEE_MEMBER),
    (SectionEnum.PRESENTATION,          TerminalEnum.PRESIDING_CHAIR),

    # TOP.MIDDLE
    # LEGISLATOR_DISCUSSION
    (SectionEnum.LEGISLATOR_DISCUSSION, (TerminalEnum.COMMITTEE_MEMBER, TerminalEnum.PUBLIC)),
    (SectionEnum.LEGISLATOR_DISCUSSION, (TerminalEnum.COMMITTEE_MEMBER, TerminalEnum.NONLEGISLATOR)),
    (SectionEnum.LEGISLATOR_DISCUSSION, (TerminalEnum.PRESIDING_CHAIR, TerminalEnum.PUBLIC)),
    (SectionEnum.LEGISLATOR_DISCUSSION, (TerminalEnum.PRESIDING_CHAIR, TerminalEnum.NONLEGISLATOR)),
    # (SectionEnum.LEGISLATOR_DISCUSSION, TerminalEnum.PUBLIC),
    (SectionEnum.LEGISLATOR_DISCUSSION, TerminalEnum.EXPERT),
    (SectionEnum.LEGISLATOR_DISCUSSION, TerminalEnum.BILL_AUTHOR),
    (SectionEnum.LEGISLATOR_DISCUSSION, TerminalEnum.LEGISLATOR),            # fallback for ambiguous TerminalEnum
    (SectionEnum.LEGISLATOR_DISCUSSION, TerminalEnum.COMMITTEE_MEMBER),
    (SectionEnum.LEGISLATOR_DISCUSSION, TerminalEnum.PRESIDING_CHAIR),
    # EXPERT_TESTIMONY
    (SectionEnum.EXPERT_TESTIMONY,      TerminalEnum.NONLEGISLATOR),
    (SectionEnum.EXPERT_TESTIMONY,      TerminalEnum.EXPERT),
    (SectionEnum.EXPERT_TESTIMONY,      TerminalEnum.LEGISLATOR),            # fallback for ambiguous TerminalEnum
    # (SectionEnum.EXPERT_TESTIMONY,      TerminalEnum.BILL_AUTHOR),
    (SectionEnum.EXPERT_TESTIMONY,      TerminalEnum.COMMITTEE_MEMBER),
    (SectionEnum.EXPERT_TESTIMONY,      TerminalEnum.PRESIDING_CHAIR),
    # (SectionEnum.EXPERT_TESTIMONY,      TerminalEnum.SECRETARY),
    # PUBLIC_COMMENTS
    (SectionEnum.PUBLIC_COMMENTS,       TerminalEnum.PUBLIC),
    # (SectionEnum.PUBLIC_COMMENTS,       TerminalEnum.NONLEGISLATOR),
    (SectionEnum.PUBLIC_COMMENTS,       TerminalEnum.COMMITTEE_MEMBER),
    (SectionEnum.PUBLIC_COMMENTS,       TerminalEnum.PRESIDING_CHAIR),
    # CLOSING_REMARKS
    (SectionEnum.CLOSING_REMARKS,       (TerminalEnum.PRESIDING_CHAIR, TerminalEnum.LEGISLATOR)),
    (SectionEnum.CLOSING_REMARKS,       (TerminalEnum.PRESIDING_CHAIR, TerminalEnum.BILL_AUTHOR)),
    (SectionEnum.CLOSING_REMARKS,       TerminalEnum.PRESIDING_CHAIR),
    # VOTE
    (SectionEnum.VOTE,                  (TerminalEnum.PRESIDING_CHAIR, TerminalEnum.SECRETARY)),
    (SectionEnum.VOTE,                  TerminalEnum.SECRETARY),
    # OTHER_HEARING
    (SectionEnum.OTHER_HEARING,         (TerminalEnum.PUBLIC, TerminalEnum.PRESIDING_CHAIR)),
    (SectionEnum.OTHER_HEARING,         (TerminalEnum.PUBLIC, TerminalEnum.SECRETARY)),
    (SectionEnum.OTHER_HEARING,         (TerminalEnum.PRESIDING_CHAIR, TerminalEnum.PUBLIC)),
    (SectionEnum.OTHER_HEARING,         (TerminalEnum.SECRETARY, TerminalEnum.PUBLIC)),
    (SectionEnum.OTHER_HEARING,         (TerminalEnum.SECRETARY, TerminalEnum.BILL_AUTHOR)),
    (SectionEnum.OTHER_HEARING,         TerminalEnum.COMMITTEE_MEMBER),
    # (SectionEnum.OTHER_HEARING,         TerminalEnum.BILL_AUTHOR),
    (SectionEnum.OTHER_HEARING,         TerminalEnum.PRESIDING_CHAIR),
    # (SectionEnum.OTHER_HEARING,         TerminalEnum.SECRETARY),   # a secretary utterance after the vote is still VOTE
]

GRAMMAR_TERMINAL_EXPANSIONS = [
    (TerminalEnum.PUBLIC,               SpeakerPositionEnum.PUBLIC),
    (TerminalEnum.NONLEGISLATOR,        SpeakerPositionEnum.NONLEGISLATOR),
    (TerminalEnum.EXPERT,               SpeakerPositionEnum.EXPERT),
    (TerminalEnum.LEGISLATOR,           SpeakerPositionEnum.LEGISLATOR),
    (TerminalEnum.BILL_AUTHOR,          SpeakerPositionEnum.BILL_AUTHOR),
    (TerminalEnum.COMMITTEE_MEMBER,     SpeakerPositionEnum.COMMITTEE_MEMBER),
    (TerminalEnum.VICE_CHAIRMAN,        SpeakerPositionEnum.VICE_CHAIRMAN),
    (TerminalEnum.CHAIRMAN,             SpeakerPositionEnum.CHAIRMAN),
    (TerminalEnum.PRESIDING_CHAIR,      SpeakerPositionEnum.PRESIDING_CHAIR),
    (TerminalEnum.SECRETARY,            SpeakerPositionEnum.SECRETARY),
]

GRAMMAR = GRAMMAR_TOP_EXPANSIONS\
        + GRAMMAR_SECTION_EXPANSIONS\
        + GRAMMAR_LEAF_EXPANSIONS\
        + GRAMMAR_TERMINAL_EXPANSIONS

SPEAKER_REACHABLE_SECTIONS: Dict[SpeakerPositionEnum, Set[SectionEnum]] = defaultdict(set[SectionEnum])
for (lhs, rhs) in GRAMMAR_LEAF_EXPANSIONS:
    if isinstance(rhs, TerminalEnum):
        SPEAKER_REACHABLE_SECTIONS[rhs.value].add(lhs)
    if isinstance(rhs, tuple):
        SPEAKER_REACHABLE_SECTIONS[rhs[0].value].add(lhs)
        SPEAKER_REACHABLE_SECTIONS[rhs[1].value].add(lhs)