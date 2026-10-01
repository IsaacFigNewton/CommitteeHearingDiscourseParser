from enum import Enum

"""
used to enumerate the different kinds of speech acts/utterances
    valid motions listed here: 
"""

class SpeechActEnum(Enum):
    STATEMENT=  "STATEMENT"
    ARGUMENT=   "ARGUMENT"

SPEECH_ACT_CUES = {
    SpeechActEnum.STATEMENT: {

    },

    SpeechActEnum.ARGUMENT: {
        "ask for your aye vote"
    }
}