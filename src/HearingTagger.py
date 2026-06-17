from typing import Optional, List, Dict, Any
from .interfaces.ITagger import ITagger
from .dataclasses.Hearing import RawHearing, TaggedHearing

from .constants import *
from .UtteranceTagger import UtteranceTagger
"""
only want to parse hearings labelled as CA_201720180<AB/SB>7
    if it's got SR in the suffix, then it's a senate resolution,
    which we don't need to parse
"""

class HearingTagger(ITagger):
    def __init__(self) -> None:
        self.utterance_tagger = UtteranceTagger()

    def __call__(self, raw_hearing: RawHearing) -> Optional[TaggedHearing]:
        tagged_utterances = []
        word_counts = [len(u.text.split(" ")) for u in raw_hearing.utterances]
        max_word_count = max(word_counts)

        for i, u in enumerate(raw_hearing.utterances):
            # tag the utterance using utterance and speaker data only
            tagged_u = self.utterance_tagger(u, raw_hearing.speakers[u.pid])

            # add hearing contextual features
            tagged_u.relative_position = i / max(len(word_counts) - 1, 1)
            tagged_u.relative_len = word_counts[i] / max_word_count
            
            # append to list of tagged utterances
            tagged_utterances.append(tagged_u)

        return TaggedHearing(
            **{
                **vars(raw_hearing),
                "utterances": tagged_utterances,
            }
        )


    @classmethod
    def _detect_first_presentation_utterance(cls, raw_hearing: RawHearing) -> int:
        """Returns the index of the first utterance that is believed to be a presenting a bill, or -1 if none found"""
        for i, u in enumerate(raw_hearing.utterances):
            # The presenter may say a phrase that indicates they are beginning to present or the chairperson is introducing them
            if cls.contains_any_phrase(u.text, PRESENTATION_START_PHRASES + PRESENTATION_HANDOFF_PHRASES):
                return i
            
            if cls.match_regex_pattern(BILL_ACTION_PATTERN, u.text):
                return i

        return -1
    

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
