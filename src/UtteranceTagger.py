from typing import Optional, Dict, Set, Tuple
import re
import spacy
from rapidfuzz import fuzz
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
        self.nlp = spacy.load("en_core_web_sm")

    def __call__(
        self,
        utterance: OralContribution,
        speaker_names_pids: Dict[str, int],
        speakers: Dict[int, Speaker],
        speaker: Optional[Speaker] = None,
    ) -> TaggedOralContribution | FlatTaggedOralContribution:
        # use empty text as default
        text = utterance.text
        if not utterance.text:
            text = ""

        # build a set of the pids of speakers mentioned
        text, pids_mentioned = self.substitute_named_entities(
            text,
            speaker_names_pids,
            speakers,
        )
                
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


    def substitute_named_entities(
        self,
        text: str,
        speaker_names_pids: Dict[str, int],
        speakers: Dict[int, Speaker],
        fuzzy_threshold: int = 85
    ) -> Tuple[str, Set[int]]:
        """
        Replace speaker name mentions with their position names using spaCy NER.

        Args:
            text: The utterance text to process
            speaker_names_pids: Dict mapping speaker names to their PIDs
            speakers: Dict mapping PIDs to Speaker objects
            fuzzy_threshold: Minimum fuzzy match score (0-100) to consider a match

        Returns:
            Tuple of (modified_text, pids_mentioned)
        """
        if not text:
            return text, set()

        # Tokenize and extract named entities
        doc = self.nlp(text)

        # Store matches: (start_char, end_char, pid, position_name)
        replacements = []
        pids_mentioned = set()

        # Iterate through PERSON entities
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                entity_text = ent.text

                # Try to fuzzy match against speaker names
                best_match_pid = None
                best_match_score = 0

                for speaker_name, pid in speaker_names_pids.items():
                    # Calculate fuzzy match score
                    score = fuzz.ratio(entity_text.lower(), speaker_name.lower())

                    if score > best_match_score and score >= fuzzy_threshold:
                        best_match_score = score
                        best_match_pid = pid

                # If we found a match
                if best_match_pid is not None:
                    pids_mentioned.add(best_match_pid)
                    speaker = speakers[best_match_pid]

                    # Get the position name if available
                    if speaker.speaker_position:
                        position_name = speaker.speaker_position.name
                        replacements.append((ent.start_char, ent.end_char, position_name))

        # Apply replacements in reverse order to maintain character positions
        modified_text = text
        for start_char, end_char, replacement in reversed(replacements):
            modified_text = modified_text[:start_char] + replacement + modified_text[end_char:]

        return modified_text, pids_mentioned