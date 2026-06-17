from typing import Optional, List
import pandas as pd

from .constants import *
from .dataclasses.Hearing import RawHearing, TaggedHearing, ParsedHearing
from .HearingTagger import HearingTagger
"""
only want to parse hearings labelled as CA_201720180<AB/SB>7
    if it's got SR in the suffix, then it's a senate resolution,
    which we don't need to parse
"""

class HearingParser:
    def __init__(self, return_type:str = 'dataframe') -> None:
        self.hearing_tagger = HearingTagger()
        # return_type == 'dataframe' or 'json'
        #   if return_type == 'json', parse the hearing into a ParsedHearing instance and serialize its contents as JSON
        #   if return_type == 'dataframe', just 
        self.return_type = return_type
    
    
    def parse_hearing(self, raw_hearing: RawHearing) -> Optional[ParsedHearing]:
        tagged_hearing = self.hearing_tagger(raw_hearing)
        # TODO: insert section tagging, assignment pipeline
        # return ParsedHearing()


    def _build_utterance_rows(self, hearings: Optional[List[TaggedHearing]]) -> pd.DataFrame:
        if not hearings:
            return pd.DataFrame()

        rows = []

        for hearing in hearings:
            for u in hearing.utterances:
                speaker = hearing.speakers[u.pid]
                rows.append({
                    'hid':                  hearing.hid,
                    'bid':                  hearing.bid,
                    'state':                hearing.state,
                    'uid':                  u.uid,
                    'pid':                  u.pid,

                    'text':                 u.text,

                    'speaker_position':     speaker.speaker_position.value if speaker and speaker.speaker_position else None,
                    'is_legislator':        int(bool(getattr(speaker, 'is_legislator', False))),
                    'is_committee_member':  int(bool(getattr(speaker, 'is_committee_member', False))),

                    'relative_position':    u.relative_position,
                    'word_count':           u.relative_len,

                    'mentions_speakers':    int(bool(len(u.mentions_speakers or []) > 0)),
                    'mentions_bills':       int(bool(len(u.mentions_bills or []) > 0)),
                    'has_bill_action':      int(u.has_bill_action),
                    'has_presentation_cue': int(u.has_presentation_cue),
                    'has_vote_cue':         int(u.has_vote_cue),
                    'has_disposition_cue':  int(u.has_disposition_cue),

                    # manual label
                    'has_motion_cue':       int(u.is_motion or False),
                    'is_transition':        int(u.is_transition or False),
                    'stage_label':          None,
                })

        return pd.DataFrame(rows)

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
