from enum import Enum

"""
used to enumerate the different possible roles of speakers in a bill discussion
"""

class SpeakerRoleEnum(Enum):
    CHAIRMAN=   "committee chair"
    SECRETARY=  "committee secretary"
    AUTHOR=     "bill author"
    LEGISLATOR= "legislator"
    EXPERT=     "expert witness"
    PUBLIC=     "member of the public"
    OTHER=      "uncategorized speaker"