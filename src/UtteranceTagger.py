from typing import Optional, Dict
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
        speaker_names_pids: Dict[str, int],
        speakers: Dict[int, Speaker],
        speaker: Optional[Speaker] = None,
    ) -> TaggedOralContribution | FlatTaggedOralContribution:
        # use empty text as default
        text = ""
        if utterance.text:
            text = utterance.text

        # build a set of the pids of speakers mentioned
        pids_mentioned = set()
        for s in speakers_mentioned:
            # just try strict name matching for now
            matched_pid = speaker_names_pids.get(s)
            # if a speaker was matched
            if matched_pid:
                # add their pid to the set of speakers mentioned
                pids_mentioned.add(matched_pid)
                
        normalized_text = self.normalize_text(text)
        tagged_u = TaggedOralContribution(
            # metadata
            uid=                            utterance.uid,
            pid=                            utterance.pid,
            text=                           text,

            # mention features
            # match all capitalized bigrams that might be names
            mentions_speakers=              None,
            pids_mentioned=                 pids_mentioned,
            mentions_bills=                 re.findall(BILL_ID_PATTERN, normalized_text),
            bids_mentioned=                 None,
            has_bill_action=                bool(BILL_ACTION_PATTERN.search(normalized_text)),
            has_presentation_cue=           self.contains_any_phrase(normalized_text, PRESENTATION_CUES),
            has_vote_cue=                   bool(self.has_vote_cue(normalized_text)),
            has_closing_cue=                self.contains_any_phrase(normalized_text, DISPOSITION_CUES),

            # tags for evaluation
            is_motion=self.contains_any_phrase(normalized_text, VOTE_START_PHRASES + MOTION_CUES),
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