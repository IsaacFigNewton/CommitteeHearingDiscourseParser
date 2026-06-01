from .dataclasses.Hearing import ParsedHearing

"""
only want to parse hearings labelled as CA_201720180<AB/SB>7
    if it's got SR in the suffix, then it's a senate resolution,
    which we don't need to parse
"""

class HearingParser:
    def __init__(self) -> None:
        pass