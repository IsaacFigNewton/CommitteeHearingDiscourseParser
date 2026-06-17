from enum import Enum
from .MotionEnum import MotionEnum

"""
used to enumerate the different kinds of sections and subsections
"""

class SectionEnum(Enum):
    """
    Note: hearing transcript may contain a portion of the previous and/or following one
        these remain uncategorized
    """

    # introducing senators, pledge of allegiance, etc.
    INTRO=                  "INTRO"

    # bill description/introduction
    #   generally presenter == author if an author is present
    PRESENTATION=           "PRESENTATION"

    # sequence of different discussion sections
    LEGISLATOR_DISCUSSION=  "LEGISLATOR_DISCUSSION"
    
    # expert testimony will always come before public discussion
    EXPERT_TESTIMONY=       "EXPERT_TESTIMONY"
    
    # sequence of different discussion sections
    # bill discussion absent in only 5% of hearings, so just take the L there
    # will only ever include legislators or members of the public - never experts
    PUBLIC_COMMENTS=        "PUBLIC_COMMENTS"

    # closing remarks by committee chair or bill author
    CLOSING_REMARKS=        "CLOSING_REMARKS"
    
    # voting section
    #   may include discussion by legislators
    VOTE=                   "VOTE"


class VoteSectionEnum(Enum):
    MOTION=             "MOTION"
    SECOND=             "SECOND"
    ROLL_CALL=          "ROLL_CALL"
    RESULTS=            "RESULTS"
    DISCUSSION=         "DISCUSSION"