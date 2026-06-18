from typing import Optional
import re
from .interfaces.ITagger import ITagger
from .dataclasses.OralContribution import OralContribution, TaggedOralContribution, FlatTaggedOralContribution
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
    ) -> TaggedOralContribution | FlatTaggedOralContribution:
        # use empty text as default
        text = ""
        if utterance.text:
            text = utterance.text
            text = self.normalize_text(text)

        tagged_u = TaggedOralContribution(
            # metadata
            uid=                            utterance.uid,
            pid=                            utterance.pid,
            text=                           text,

            # mention features
            # match all capitalized bigrams that might be names
            mentions_speakers=              set(re.findall(NAME_BIGRAM_REGEX, utterance.text)),
            pids_mentioned=                 None,
            mentions_bills=                 re.findall(BILL_ID_PATTERN, text),
            bids_mentioned=                 None,
            has_bill_action=                bool(BILL_ACTION_PATTERN.search(text)),
            has_presentation_cue=           self.contains_any_phrase(text, PRESENTATION_CUES),
            has_vote_cue=                   bool(self.has_vote_cue(text)),
            has_closing_cue=            self.contains_any_phrase(text, DISPOSITION_CUES),

            # tags for evaluation
            is_motion=self.contains_any_phrase(text, VOTE_START_PHRASES + MOTION_CUES),
            is_transition=None,
            section=None,
        )

        if speaker is not None:
            # if speaker provided
            return FlatTaggedOralContribution(
                **vars(tagged_u),
                # speaker features
                is_presenter=                   speaker.is_presenter,
                can_file_motions=               speaker.can_file_motions,
                speaker_position=               speaker.speaker_position,

                # metadata features
                relative_position=              None,
                relative_len=                   None,
            )
        
        return tagged_u

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