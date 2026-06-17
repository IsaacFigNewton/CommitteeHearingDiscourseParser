from typing import Optional
import re
from .interfaces.ITagger import ITagger
from .dataclasses.OralContribution import OralContribution, TaggedOralContribution
from .speakers.Speaker import Speaker
from .constants import *

"""
only want to parse hearings labelled as CA_201720180<AB/SB>7
    if it's got SR in the suffix, then it's a senate resolution,
    which we don't need to parse
"""

class UtteranceTagger(ITagger):
    def __init__(self) -> None:
        pass

    def __call__(
        self,
        utterance: OralContribution,
        speaker: Optional[Speaker] = None,
    ) -> TaggedOralContribution | OralContribution:
        # use empty text as default
        text = ""
        if utterance.text:
            text = utterance.text
            text = self.normalize_text(text)

        return TaggedOralContribution(
            # metadata
            uid=                            utterance.uid,
            pid=                            utterance.pid,
            text=                           text,

            # speaker features
            speaker_position=               (
                speaker.speaker_position
                if speaker and speaker.speaker_position
                else None
            ),
            speaker_is_legislator=          bool(getattr(speaker, "is_legislator", False)),
            speaker_is_committee_member=    bool(getattr(speaker, "is_committee_member", False)),
            speaker_role=                   None,

            # mention features
            mentions_bills=                 re.findall(BILL_ID_PATTERN, text),
            mentions_speakers=              None,
            has_bill_action=                bool(BILL_ACTION_PATTERN.search(text)),
            has_presentation_cue=           self.contains_any_phrase(text, PRESENTATION_CUES),
            has_vote_cue=                   bool(self.has_vote_cue(text)),
            has_disposition_cue=            self.contains_any_phrase(text, DISPOSITION_CUES),

            # metadata features
            relative_position=              None,
            relative_len=                   None,

            # tags for evaluation
            is_motion=self.contains_any_phrase(text, VOTE_START_PHRASES + MOTION_CUES),
            is_transition=None,
            section=None,
        )

    def has_vote_cue(self, text: Optional[str]) -> int:
        if not text:
            return 0

        normalized = self.normalize_text(text)

        vote_phrase_found = (
            "roll call" in normalized
            or "call the roll" in normalized
            or "please call the roll" in normalized
        )

        aye_count = len(re.findall(r"\baye\b", text.lower()))
        nay_count = len(re.findall(r"\bno\b", text.lower()))
        repeated_votes_found = aye_count + nay_count >= 2

        return int(vote_phrase_found or repeated_votes_found)