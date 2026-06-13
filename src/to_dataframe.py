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


def speaker_position_as_string(speaker) -> str:
    if speaker is None:
        return 'unknown'

    position = getattr(speaker, 'speaker_position', None)

    if position is None:
        return 'unknown'

    return str(position)


def build_utterance_rows(hearings: list[RawHearing]) -> pd.DataFrame:
    rows = []

    for hearing in hearings:
        n = len(hearing.utterances)

        for i, utterance in enumerate(hearing.utterances):
            speaker = hearing.speakers.get(utterance.pid)

            prev_utterance = hearing.utterances[i - 1] if i > 0 else None
            next_utterance = hearing.utterances[i + 1] if i < n - 1 else None

            prev_speaker = (
                hearing.speakers.get(prev_utterance.pid)
                if prev_utterance is not None
                else None
            )

            next_speaker = (
                hearing.speakers.get(next_utterance.pid)
                if next_utterance is not None
                else None
            )

            text = utterance.text or ''
            prev_text = prev_utterance.text if prev_utterance else ''
            next_text = next_utterance.text if next_utterance else ''

            rows.append({
                'hid': hearing.hid,
                'bid': hearing.bid,
                'state': hearing.state,
                'uid': utterance.uid,
                'pid': utterance.pid,

                'text': text,
                'prev_text': prev_text,
                'next_text': next_text,
                'context_text': (
                    'PREV: ' + prev_text +
                    ' CURR: ' + text +
                    ' NEXT: ' + next_text
                ),

                'speaker_position': speaker_position_as_string(speaker),
                'prev_speaker_position': speaker_position_as_string(prev_speaker),
                'next_speaker_position': speaker_position_as_string(next_speaker),

                'is_legislator': int(bool(getattr(speaker, 'is_legislator', False))),
                'is_committee_member': int(bool(getattr(speaker, 'is_committee_member', False))),

                'relative_position': i / max(n - 1, 1),
                'word_count': word_count(text),

                'has_bill_id': has_bill_id(text),
                'has_bill_action': has_bill_action(text),
                'has_presentation_cue': has_presentation_cue(text),
                'has_motion_cue': has_motion_cue(text),
                'has_vote_cue': has_vote_cue(text),
                'has_disposition_cue': has_disposition_cue(text),
                'aye_count': aye_count(text),
                'no_count': no_count(text),

                # manual label
                'stage_label': None,
            })

    return pd.DataFrame(rows)
