from enum import Enum

"""
used to enumerate the different kinds of motions
    valid motions listed here: 
"""

class MotionEnum(Enum):
    DUE_PASS=           "due pass"
    RECONSIDERATION=    "reconsideration"
    AMENDMENT=          "amendment"