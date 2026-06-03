from enum import Enum

class SectionEnum(Enum):
    # introducing senators, pledge of allegiance, etc.
    INTRO=                  "INTRO"

    # bill description/introduction
    PRESENTATION=           "PRESENTATION"

    # sequence of different discussion sections
    LEGISLATOR_DISCUSSION=  "LEGISLATOR_DISCUSSION"
    EXPERT_TESTIMONY=       "EXPERT_TESTIMONY"
    PUBLIC_COMMENTS=        "PUBLIC_COMMENTS"

    # closing remarks by committee chair or bill presenter
    CLOSING_REMARKS=        "CLOSING_REMARKS"

    # voting section
    VOTE=                   "VOTE"