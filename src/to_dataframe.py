from typing import Optional, List
import pandas as pd

from .dataclasses.Hearing import TaggedHearing


def build_utterance_rows(hearings: Optional[List[TaggedHearing]]) -> pd.DataFrame:
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
