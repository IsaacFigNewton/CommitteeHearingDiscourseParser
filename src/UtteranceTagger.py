from typing import Optional, Dict, Set, Tuple
import re
import spacy
from rapidfuzz import fuzz
from .interfaces.ITagger import ITagger
from .enums.SpeechActEnum import SpeechActEnum, SPEECH_ACT_CUES
from .enums.SectionEnum import SectionEnum, VoteSectionEnum, SECTION_CUE_PHRASES
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

        # substitute keyphrases with their group names
        text = self.substitute_keyphrases(text)
        normalized = self.normalize_text(text)

        # get cues for different speech acts
        speech_act_cues = self._get_speech_act_cues(normalized)

        # check for single-keyphrase-occurrence-based cues
        section_cues = self._get_section_cues(normalized)

        tagged_u = TaggedOralContribution(
            # metadata
            uid=                            utterance.uid,
            pid=                            utterance.pid,
            text=                           text,

            # mention features
            # metadata features
            relative_position=              None,
            sent_count=                     None,
            # match all capitalized bigrams that might be names
            pids_mentioned=                 pids_mentioned,
            bids_mentioned=                 re.findall(BILL_ID_PATTERN, text),

            # cues
            section_cues=                   section_cues,
            speech_act_cues=                speech_act_cues,
            
            # tags for evaluation
            section=                        None,
        )

        if speaker is not None:
            # if speaker provided
            return FlatTaggedOralContribution(
                **vars(tagged_u),
                # speaker features
                is_presenter=                   speaker.is_presenter,
                can_file_motions=               speaker.can_file_motions,
                speaker_position=               speaker.speaker_position,
            )
        
        return tagged_u


    def _match_entity_to_speaker(
        self,
        entity_text: str,
        speaker_names_pids: Dict[str, int],
        speakers: Dict[int, Speaker],
        fuzzy_threshold: int = 85
    ) -> Optional[int]:
        """
        Match an entity text to a speaker using fuzzy matching.

        Args:
            entity_text: The cleaned entity text to match
            speaker_names_pids: Dict mapping speaker names to their PIDs
            speakers: Dict mapping PIDs to Speaker objects
            fuzzy_threshold: Minimum fuzzy match score (0-100) to consider a match

        Returns:
            The PID of the best matching speaker, or None if no match found
        """
        # Stopwords to filter out from entity text
        STOPWORDS = {"senator", "member", "assembly", "assemblymember"}

        # Remove stopwords from entity text
        entity_tokens = [
            token for token in entity_text.split()
            if token.lower() not in STOPWORDS
        ]
        entity_text_cleaned = " ".join(entity_tokens).strip()

        if not entity_text_cleaned:
            return None

        # Try to fuzzy match against speaker names
        best_match_pid = None
        best_match_score = 0

        for speaker_name, pid in speaker_names_pids.items():
            speaker = speakers[pid]

            # Try matching against full name, first name, and last name
            candidates = [speaker_name]
            if speaker.first_name:
                candidates.append(speaker.first_name)
            if speaker.last_name:
                candidates.append(speaker.last_name)

            for candidate in candidates:
                score = fuzz.ratio(entity_text_cleaned.lower(), candidate.lower())

                if score > best_match_score and score >= fuzzy_threshold:
                    best_match_score = score
                    best_match_pid = pid

        return best_match_pid

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

        # Store matches: (start_char, end_char, position_name)
        replacements = []
        pids_mentioned = set()

        # Iterate through entities
        for ent in doc.ents:
            match ent.label_:
                case "PERSON":
                    matched_pid = self._match_entity_to_speaker(
                        ent.text, speaker_names_pids, speakers, fuzzy_threshold
                    )

                    # If we found a match
                    if matched_pid is not None:
                        pids_mentioned.add(matched_pid)
                        speaker = speakers[matched_pid]

                        # Get the position name if available
                        if speaker.speaker_position:
                            position_name = speaker.speaker_position.name
                            replacements.append((ent.start_char, ent.end_char, position_name))

                case "GPE":
                    # GPE (Geopolitical Entity) - replace with GPE
                    replacements.append((ent.start_char, ent.end_char, "GPE"))

                case "ORG":
                    # ORG (Organization) - replace with ORG
                    replacements.append((ent.start_char, ent.end_char, "ORG"))
                
                case _:
                    continue

        # Apply replacements in reverse order to maintain character positions
        modified_text = text
        for start_char, end_char, replacement in reversed(replacements):
            modified_text = modified_text[:start_char] + replacement + modified_text[end_char:]

        return modified_text, pids_mentioned

    def substitute_keyphrases(self, text: str) -> str:
        """
        Replace keyphrases from PHRASE_GROUPS with their phrase group names.

        Args:
            text: The utterance text to process

        Returns:
            Modified text with keyphrases replaced by their group names
        """
        if not text:
            return text

        # Normalize the input text for matching
        normalized_text = self.normalize_text(text)

        # Store matches: (start_pos, end_pos, group_name)
        replacements = []

        # Iterate through each phrase in PHRASE_TOKEN_MAP
        for phrase, group_name in PHRASE_TOKEN_MAP.items():
            # Find all occurrences of this phrase in the normalized text
            start_pos = 0
            while True:
                pos = normalized_text.find(phrase, start_pos)
                if pos == -1:
                    break

                # Record the replacement
                replacements.append((pos, pos + len(phrase), group_name))
                start_pos = pos + len(phrase)

        # Sort by start position and filter overlapping matches (keep longest/first)
        replacements.sort(key=lambda x: (x[0], -(x[1] - x[0])))

        # Remove overlapping replacements
        filtered_replacements = []
        last_end = -1
        for start, end, group_name in replacements:
            if start >= last_end:
                filtered_replacements.append((start, end, group_name))
                last_end = end

        # Apply replacements in reverse order to maintain character positions
        modified_text = normalized_text
        for start_pos, end_pos, group_name in reversed(filtered_replacements):
            modified_text = modified_text[:start_pos] + group_name + modified_text[end_pos:]

        return modified_text
    

    def _get_speech_act_cues(self, text: str) -> set:
        speech_act_cues = set()

        for cue_grp, cue_set in SPEECH_ACT_CUES.items():
            if self.contains_any_phrase(text, cue_set):
                speech_act_cues.add(cue_grp)
        
        # if there's some statement about a bill procedure
        if bool(BILL_ACTION_PATTERN.search(text)):
            speech_act_cues.add(SpeechActEnum.STATEMENT)

        return speech_act_cues
    
    
    def _get_section_cues(self, text: str) -> set:
        section_cues = set()
        
        for cue_grp, cue_set in SECTION_CUE_PHRASES.items():
            if self.contains_any_phrase(text, cue_set):
                section_cues.add(cue_grp)
        
        # if there's >1 aye, it's probably roll call
        if text.count(" aye ") > 1:
            section_cues.add(VoteSectionEnum.ROLL_CALL)

        return section_cues