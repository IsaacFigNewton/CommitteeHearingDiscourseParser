from typing import List, Dict, Tuple, Union, Optional
from dataclasses import dataclass

"""
only want to parse hearings labelled as CA_201720180<AB or SB>7
    if it's got SR in the suffix, then it's a senate resolution,
    which we don't need to parse
tuples represent indices of starting line (inclusive), ending line (exclusive)
"""

@dataclass
class LegislatorDiscussion:
    span: Tuple[int, int]
    # only legislator discussion
    speakers: List[str]

@dataclass
class ExpertTestimony:
    span: Tuple[int, int]
    # only legislator and expert testimony
    speakers: List[str]
    
@dataclass
class PublicComments:
    span: Tuple[int, int]
    # only legislator and expert testimony
    speakers: List[str]

@dataclass
class BillDiscussion:
    """
    Note: hearing transcript may contain a portion of the previous and/or following one
    """

    # introducing senators, pledge of allegiance, etc.
    intro: Optional[Tuple[int, int]]

    # bill description/introduction
    presentation: Tuple[int, int]

    # sequence of different discussion types
    discussion: List[
        LegislatorDiscussion
        | ExpertTestimony
        | PublicComments
    ]
    
    # closing remarks by committee chair or bill author
    closing_remarks: Tuple[int, int]
    # voting section
    vote: Tuple[int, int]
    # final remarks at end of session
    outro: Optional[Tuple[int, int]]