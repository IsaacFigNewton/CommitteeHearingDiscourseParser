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
    CLOSING=                "CLOSING"
    WRAPUP=                 "WRAPUP"

# if thee UPPER_MIDDLE or LOWER_MIDDLE has >= 2 SectionEnums of different types,
#   and the legislator discussion is >= 2 utterances long,
#   then split the EXPERT_TESTIMONY or PUBLIC_COMMENTS into >=2 consecutive TerminalEnum tokens 
class SMOOTHING(Enum):
    EXPERT_TESTIMONY=       "SMOOTH_EXPERT_TESTIMONY"
    PUBLIC_COMMENTS=        "SMOOTH_PUBLIC_COMMENTS"
    LEGISLATOR_DISCUSSION=  "SMOOTH_LEGISLATOR_DISCUSSION"


class TerminalEnum(Enum):
    SECRETARY=          9
    PRESIDING_CHAIR=    8
    CHAIRMAN=           7
    VICE_CHAIRMAN=      6
    COMMITTEE_MEMBER=   5
    BILL_AUTHOR=        4   # subdivided by can_file_motions, determines is_presenter
    LEGISLATOR=         3
    EXPERT=             2
    NONLEGISLATOR=      1
    PUBLIC=             0

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
GRAMMAR = [
    # broad hearing structures
    (TOP.ROOT,                          (TOP.START_MIDDLE, TOP.END)),
    (TOP.START_MIDDLE,                  (TOP.START, TOP.END)),

    # fallback for OTHER sections
    (SectionEnum.OTHER_PROCEDURAL,      (SectionEnum.OTHER_PROCEDURAL, SectionEnum.OTHER_PROCEDURAL)),
    (SectionEnum.OTHER_NONPROCEDURAL,   (SectionEnum.OTHER_NONPROCEDURAL, SectionEnum.OTHER_NONPROCEDURAL)),


    # TOP.START
    (TOP.START,                         (SectionEnum.INTRO, SectionEnum.PRESENTATION)),
    (TOP.START,                         (SectionEnum.INTRO)),
    # 1-line presentation
    (TOP.START,                         (TerminalEnum.BILL_AUTHOR)),
    (TOP.START,                         (TerminalEnum.COMMITTEE_MEMBER)),
    (TOP.START,                         (TerminalEnum.PRESIDING_CHAIR)),

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
    # a testimony run of any length may be followed by a discussion
    (TOP.UPPER_MIDDLE,                  (TOP.UPPER_MIDDLE, TOP.UPPER_MIDDLE)),
    # a comment run of any length may be followed by a discussion
    (TOP.UPPER_MIDDLE,                  (TOP.UPPER_MIDDLE, SMOOTHING.LEGISLATOR_DISCUSSION)),
    (TOP.UPPER_MIDDLE,                  (SMOOTHING.EXPERT_TESTIMONY, TOP.UPPER_MIDDLE)),
    (TOP.UPPER_MIDDLE,                  (SMOOTHING.EXPERT_TESTIMONY, SMOOTHING.LEGISLATOR_DISCUSSION)),
    (TOP.UPPER_MIDDLE,                  (SMOOTHING.EXPERT_TESTIMONY, SMOOTHING.EXPERT_TESTIMONY)),
    (TOP.UPPER_MIDDLE,                  (SMOOTHING.EXPERT_TESTIMONY, SectionEnum.EXPERT_TESTIMONY)),
    # TOP.LOWER_MIDDLE
    # allow public comment runs of any length >= 3 (previously only multiples of 3 parsed)
    (TOP.LOWER_MIDDLE,                  (TOP.LOWER_MIDDLE, TOP.LOWER_MIDDLE)),
    # a comment run of any length may be followed by a discussion
    (TOP.LOWER_MIDDLE,                  (TOP.LOWER_MIDDLE, SMOOTHING.LEGISLATOR_DISCUSSION)),
    (TOP.LOWER_MIDDLE,                  (SMOOTHING.PUBLIC_COMMENTS, TOP.LOWER_MIDDLE)),
    (TOP.LOWER_MIDDLE,                  (SMOOTHING.PUBLIC_COMMENTS, SMOOTHING.LEGISLATOR_DISCUSSION)),
    (TOP.LOWER_MIDDLE,                  (SMOOTHING.PUBLIC_COMMENTS, SMOOTHING.PUBLIC_COMMENTS)),
    (TOP.LOWER_MIDDLE,                  (SMOOTHING.PUBLIC_COMMENTS, SectionEnum.PUBLIC_COMMENTS)),

    # TOP.END
    (TOP.END,                           (TOP.CLOSING, SectionEnum.VOTE)),
    (TOP.END,                           TOP.CLOSING),
    (TOP.END,                           SectionEnum.VOTE),
    # post-vote / post-close wrap-up; WRAPUP deliberately excludes SECRETARY so it can never reach past a vote
    (TOP.END,                           (TOP.END, TOP.WRAPUP)),
    (TOP.WRAPUP,                        SectionEnum.OTHER_HEARING),        # OTHER_HEARING self-recurses below


    # different SectionEnum expansions
    # TOP.START
    (SectionEnum.INTRO,                 (SectionEnum.OTHER_HEARING, SectionEnum.INTRO)),
    # (SectionEnum.INTRO,                 (SectionEnum.INTRO, SectionEnum.OTHER_NONPROCEDURAL)),
    # (SectionEnum.INTRO,                 (SectionEnum.INTRO, SectionEnum.INTRO)),
    (SectionEnum.PRESENTATION,          (SectionEnum.PRESENTATION, SectionEnum.OTHER_NONPROCEDURAL)),
    (SectionEnum.PRESENTATION,          (SectionEnum.PRESENTATION, SectionEnum.PRESENTATION)),

    # TOP.MIDDLE
    # Smoothing
    (SMOOTHING.EXPERT_TESTIMONY,        (SectionEnum.EXPERT_TESTIMONY, SectionEnum.EXPERT_TESTIMONY)),
    (SMOOTHING.EXPERT_TESTIMONY,        (SectionEnum.EXPERT_TESTIMONY, SectionEnum.OTHER_PROCEDURAL)),
    (SMOOTHING.PUBLIC_COMMENTS,         (SectionEnum.PUBLIC_COMMENTS, SectionEnum.PUBLIC_COMMENTS)),
    (SMOOTHING.PUBLIC_COMMENTS,         (SectionEnum.PUBLIC_COMMENTS, SectionEnum.OTHER_PROCEDURAL)),
    (SMOOTHING.LEGISLATOR_DISCUSSION,   (SectionEnum.LEGISLATOR_DISCUSSION, SectionEnum.LEGISLATOR_DISCUSSION)),
    # Semi-terminals
    # (SectionEnum.LEGISLATOR_DISCUSSION, (SectionEnum.LEGISLATOR_DISCUSSION, SectionEnum.OTHER_NONPROCEDURAL)),
    (SectionEnum.LEGISLATOR_DISCUSSION, (SectionEnum.LEGISLATOR_DISCUSSION, SectionEnum.LEGISLATOR_DISCUSSION)),
    # (SectionEnum.EXPERT_TESTIMONY,      (SectionEnum.EXPERT_TESTIMONY, SectionEnum.EXPERT_TESTIMONY)),
    # (SectionEnum.PUBLIC_COMMENTS,       (SectionEnum.PUBLIC_COMMENTS, SectionEnum.PUBLIC_COMMENTS)),

    # TOP.END
    # (SectionEnum.CLOSING_REMARKS,       (SectionEnum.CLOSING_REMARKS, SectionEnum.OTHER_NONPROCEDURAL)),
    # max 4 closing remarks
    (TOP.CLOSING,                       (SectionEnum.CLOSING_REMARKS, SectionEnum.CLOSING_REMARKS)),
    (SectionEnum.CLOSING_REMARKS,       (SectionEnum.CLOSING_REMARKS, SectionEnum.OTHER_NONPROCEDURAL)),
    (SectionEnum.VOTE,                  (SectionEnum.VOTE, SectionEnum.VOTE)),
    (SectionEnum.VOTE,                  (SectionEnum.VOTE, SectionEnum.OTHER_NONPROCEDURAL)),
    (SectionEnum.OTHER_HEARING,         (SectionEnum.OTHER_HEARING, SectionEnum.OTHER_HEARING)),


    # Leaf rule expansions
    # OTHER
    # OTHER_NONPROCEDURAL
    # (SectionEnum.OTHER_NONPROCEDURAL,   (TerminalEnum.PRESIDING_CHAIR, TerminalEnum.BILL_AUTHOR)),
    (SectionEnum.OTHER_NONPROCEDURAL,   TerminalEnum.LEGISLATOR),
    # (SectionEnum.OTHER_NONPROCEDURAL,   TerminalEnum.PUBLIC),
    (SectionEnum.OTHER_NONPROCEDURAL,   TerminalEnum.BILL_AUTHOR),
    # (SectionEnum.OTHER_NONPROCEDURAL,   TerminalEnum.COMMITTEE_MEMBER),
    # OTHER_PROCEDURAL
    (SectionEnum.OTHER_PROCEDURAL,      (TerminalEnum.COMMITTEE_MEMBER, TerminalEnum.SECRETARY)),
    (SectionEnum.OTHER_PROCEDURAL,      (TerminalEnum.PRESIDING_CHAIR, TerminalEnum.SECRETARY)),
    (SectionEnum.OTHER_PROCEDURAL,      TerminalEnum.SECRETARY),


    # TOP.START
    # INTRO
    (SectionEnum.INTRO,                 TerminalEnum.PRESIDING_CHAIR),
    (SectionEnum.INTRO,                 (TerminalEnum.SECRETARY, TerminalEnum.PRESIDING_CHAIR)),
    # PRESENTATION
    (SectionEnum.PRESENTATION,          (TerminalEnum.EXPERT, TerminalEnum.PRESIDING_CHAIR)),
    (SectionEnum.PRESENTATION,          (TerminalEnum.BILL_AUTHOR, TerminalEnum.BILL_AUTHOR)),
    (SectionEnum.PRESENTATION,          (TerminalEnum.BILL_AUTHOR, TerminalEnum.PRESIDING_CHAIR)),
    (SectionEnum.PRESENTATION,          (TerminalEnum.COMMITTEE_MEMBER, TerminalEnum.PRESIDING_CHAIR)),

    # TOP.MIDDLE
    # LEGISLATOR_DISCUSSION
    (SectionEnum.LEGISLATOR_DISCUSSION, (TerminalEnum.COMMITTEE_MEMBER, TerminalEnum.PUBLIC)),
    (SectionEnum.LEGISLATOR_DISCUSSION, (TerminalEnum.COMMITTEE_MEMBER, TerminalEnum.NONLEGISLATOR)),
    (SectionEnum.LEGISLATOR_DISCUSSION, (TerminalEnum.COMMITTEE_MEMBER, TerminalEnum.EXPERT)),
    (SectionEnum.LEGISLATOR_DISCUSSION, (TerminalEnum.COMMITTEE_MEMBER, TerminalEnum.BILL_AUTHOR)),
    (SectionEnum.LEGISLATOR_DISCUSSION, (TerminalEnum.COMMITTEE_MEMBER, TerminalEnum.COMMITTEE_MEMBER)),
    (SectionEnum.LEGISLATOR_DISCUSSION, (TerminalEnum.COMMITTEE_MEMBER, TerminalEnum.PRESIDING_CHAIR)),
    (SectionEnum.LEGISLATOR_DISCUSSION, (TerminalEnum.PRESIDING_CHAIR, TerminalEnum.PUBLIC)),
    (SectionEnum.LEGISLATOR_DISCUSSION, (TerminalEnum.PRESIDING_CHAIR, TerminalEnum.NONLEGISLATOR)),
    (SectionEnum.LEGISLATOR_DISCUSSION, (TerminalEnum.PRESIDING_CHAIR, TerminalEnum.EXPERT)),
    (SectionEnum.PUBLIC_COMMENTS,       TerminalEnum.PUBLIC),
    (SectionEnum.EXPERT_TESTIMONY,      TerminalEnum.EXPERT),
    (SectionEnum.LEGISLATOR_DISCUSSION, TerminalEnum.COMMITTEE_MEMBER),
    (SectionEnum.LEGISLATOR_DISCUSSION, TerminalEnum.PRESIDING_CHAIR),
    # EXPERT_TESTIMONY
    (SectionEnum.EXPERT_TESTIMONY,       (TerminalEnum.NONLEGISLATOR, TerminalEnum.COMMITTEE_MEMBER)),
    (SectionEnum.EXPERT_TESTIMONY,       (TerminalEnum.NONLEGISLATOR, TerminalEnum.PRESIDING_CHAIR)),
    (SectionEnum.EXPERT_TESTIMONY,       (TerminalEnum.PUBLIC, TerminalEnum.COMMITTEE_MEMBER)),
    (SectionEnum.EXPERT_TESTIMONY,       (TerminalEnum.PUBLIC, TerminalEnum.PRESIDING_CHAIR)),
    (SectionEnum.EXPERT_TESTIMONY,       (TerminalEnum.EXPERT, TerminalEnum.COMMITTEE_MEMBER)),
    (SectionEnum.EXPERT_TESTIMONY,       (TerminalEnum.EXPERT, TerminalEnum.PRESIDING_CHAIR)),
    (SectionEnum.EXPERT_TESTIMONY,       (TerminalEnum.PRESIDING_CHAIR, TerminalEnum.EXPERT)),
    (SectionEnum.EXPERT_TESTIMONY,       TerminalEnum.EXPERT),
    (SectionEnum.EXPERT_TESTIMONY,       TerminalEnum.PRESIDING_CHAIR),
    # PUBLIC_COMMENTS
    # (SectionEnum.PUBLIC_COMMENTS,       (TerminalEnum.NONLEGISLATOR, TerminalEnum.COMMITTEE_MEMBER)),
    (SectionEnum.PUBLIC_COMMENTS,       (TerminalEnum.PUBLIC, TerminalEnum.COMMITTEE_MEMBER)),
    # (SectionEnum.PUBLIC_COMMENTS,       (TerminalEnum.NONLEGISLATOR, TerminalEnum.PRESIDING_CHAIR)),
    (SectionEnum.PUBLIC_COMMENTS,       (TerminalEnum.PUBLIC, TerminalEnum.PRESIDING_CHAIR)),
    (SectionEnum.PUBLIC_COMMENTS,       TerminalEnum.PUBLIC),
    (SectionEnum.PUBLIC_COMMENTS,       TerminalEnum.PRESIDING_CHAIR),
    # CLOSING_REMARKS
    (SectionEnum.CLOSING_REMARKS,       (TerminalEnum.PRESIDING_CHAIR, TerminalEnum.LEGISLATOR)),
    (SectionEnum.CLOSING_REMARKS,       (TerminalEnum.PRESIDING_CHAIR, TerminalEnum.COMMITTEE_MEMBER)),
    (SectionEnum.CLOSING_REMARKS,       (TerminalEnum.PRESIDING_CHAIR, TerminalEnum.BILL_AUTHOR)),
    (SectionEnum.CLOSING_REMARKS,       TerminalEnum.PRESIDING_CHAIR),
    # VOTE
    (SectionEnum.VOTE,                  (TerminalEnum.PRESIDING_CHAIR, TerminalEnum.SECRETARY)),
    (SectionEnum.VOTE,                  (TerminalEnum.SECRETARY, TerminalEnum.PRESIDING_CHAIR)),
    (SectionEnum.VOTE,                  (TerminalEnum.SECRETARY, TerminalEnum.COMMITTEE_MEMBER)),
    (SectionEnum.VOTE,                  TerminalEnum.SECRETARY),
    # OTHER_HEARING
    # (SectionEnum.OTHER_HEARING,         (TerminalEnum.PUBLIC, TerminalEnum.PRESIDING_CHAIR)),
    (SectionEnum.OTHER_HEARING,         (TerminalEnum.PRESIDING_CHAIR, TerminalEnum.SECRETARY)),
    (SectionEnum.OTHER_HEARING,         (TerminalEnum.PRESIDING_CHAIR, TerminalEnum.COMMITTEE_MEMBER)),
    (SectionEnum.OTHER_HEARING,         TerminalEnum.PUBLIC),
    (SectionEnum.OTHER_HEARING,         TerminalEnum.EXPERT),


    # Terminal expansions
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