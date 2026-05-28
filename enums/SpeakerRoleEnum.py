from enum import Enum

"""
used to enumerate the different possible roles of speakers in a bill discussion
"""

class SpeakerRoleEnum(Enum):
    CHAIRMAN=   "committee chair"
    STAFF=      "committee staff"       # includes committee chair, secretary, and staff
    AUTHOR=     "bill author"
    PRESENTER=  "bill presenter"        # usually bill author
    LEGISLATOR= "legislator"
    EXPERT=     "expert witness"
    PUBLIC=     "member of the public"
    OTHER=      "uncategorized speaker"