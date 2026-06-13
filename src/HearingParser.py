from .dataclasses.Hearing import ParsedHearing, RawHearing
from .parsing_constants import (
    PRESENTATION_HANDOFF_PHRASES,
    PRESENTATION_START_PHRASES,
    BILL_ACTION_PATTERN,
)
from .parsing_utils import match_regex_pattern, match_any_phrase

"""
only want to parse hearings labelled as CA_201720180<AB/SB>7
    if it's got SR in the suffix, then it's a senate resolution,
    which we don't need to parse
"""

class HearingParser:
    def __init__(self) -> None:
        pass

    def _detect_first_presentation_utterance(self, raw_hearing: RawHearing) -> int:
        """Returns the index of the first utterance that is believed to be a presenting a bill, or -1 if none found"""
        for i, u in enumerate(raw_hearing.utterances):
            # The presenter may say a phrase that indicates they are beginning to present or the chairperson is introducing them
            if match_any_phrase(u.text, PRESENTATION_START_PHRASES + PRESENTATION_HANDOFF_PHRASES):
                return i
            
            if match_regex_pattern(BILL_ACTION_PATTERN, u.text):
                return i

        return -1

    def parse_hearing(self, raw_hearing: RawHearing) -> ParsedHearing:
        pass

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
