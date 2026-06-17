from typing import Optional
from .dataclasses.Hearing import ParsedHearing, RawHearing

from .constants import *
from .HearingTagger import HearingTagger
"""
only want to parse hearings labelled as CA_201720180<AB/SB>7
    if it's got SR in the suffix, then it's a senate resolution,
    which we don't need to parse
"""

class HearingParser:
    def __init__(self) -> None:
        self.hearing_tagger = HearingTagger()
    
    
    def parse_hearing(self, raw_hearing: RawHearing) -> Optional[ParsedHearing]:
        tagged_hearing = self.hearing_tagger(raw_hearing)
        # TODO: insert section tagging, assignment pipeline
        # return ParsedHearing()

    @staticmethod
    def pprint_hearing(hearing: RawHearing):
        """Print formatted transcript."""
        print()
        print(f"State:\t\t{hearing.state}")
        print(f"Committee:\t{hearing.cname}")
        print(f"Bill:\t\t{hearing.bid}")
        print(f"Date:\t\t{hearing.hearing_date.strftime('%Y-%m-%d')}")
        print()
        print("Transcript:")
        for contribution in hearing.utterances:
            speaker = hearing.speakers[contribution.pid]
            first_name = speaker.first_name or "UNKNOWN"
            last_name = speaker.last_name or "UNKNOWN"
            name = f"{first_name} {last_name}:"
            print(f"{name:<20} {contribution.text}")
        print()
