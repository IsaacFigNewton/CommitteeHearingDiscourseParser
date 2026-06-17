import pandas as pd

from .dataclasses.Hearing import RawHearing
from .feature_extraction import (
    has_bill_id,
    has_bill_action,
    has_presentation_cue,
    has_motion_cue,
    has_vote_cue,
    has_disposition_cue,
    aye_count,
    no_count,
    word_count,
)


def build_utterance_rows(hearings: list[RawHearing]) -> pd.DataFrame:
    rows = []

    for hearing in hearings:
        n = len(hearing.utterances)

        for i, utterance in enumerate(hearing.utterances):
            speaker = hearing.speakers.get(utterance.pid)

            rows.append({
                'hid': hearing.hid,
                'bid': hearing.bid,
                'state': hearing.state,
                'uid': utterance.uid,
                'pid': utterance.pid,

                'text': utterance.text,

                'speaker_position': speaker.speaker_position.value if speaker and speaker.speaker_position else None,
                'is_legislator': int(bool(getattr(speaker, 'is_legislator', False))),
                'is_committee_member': int(bool(getattr(speaker, 'is_committee_member', False))),

                'relative_position': i / max(n - 1, 1),
                'word_count': word_count(utterance.text),

                'has_bill_id': has_bill_id(utterance.text),
                'has_bill_action': has_bill_action(utterance.text),
                'has_presentation_cue': has_presentation_cue(utterance.text),
                'has_motion_cue': has_motion_cue(utterance.text),
                'has_vote_cue': has_vote_cue(utterance.text),
                'has_disposition_cue': has_disposition_cue(utterance.text),
                'aye_count': aye_count(utterance.text),
                'no_count': no_count(utterance.text),

                # manual label
                'stage_label': None,
            })

    return pd.DataFrame(rows)
