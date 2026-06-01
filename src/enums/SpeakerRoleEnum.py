from enum import Enum

"""
used to enumerate the different possible roles of speakers in a bill discussion
"""

class SpeakerRoleEnum(Enum):
    CHAIRMAN=   "CHAIRMAN"
    STAFF=      "STAFF"             # includes committee chair, secretary, and staff
    AUTHOR=     "AUTHOR"
    PRESENTER=  "PRESENTER"         # usually bill author
    LEGISLATOR= "ASSEMBLYMEMBER"
    EXPERT=     "EXPERT"
    PUBLIC=     "PUBLIC"
    OTHER=      "UNKNOWN"