from typing import List, Optional, Tuple

from ..dataclasses.Hearing import TaggedHearing
from ..speakers.enums.SpeakerPositionEnum import SpeakerPositionEnum

# A token is (speaker_position, utterance_index). A None speaker position means
# the speaker was unidentified and may fill any role during parsing.
Token = Tuple[Optional[SpeakerPositionEnum], int]


class Tokenizer:
    """
    Converts the utterances of a TaggedHearing into a sequence of
    (SpeakerPositionEnum, utterance_index) tokens for the Parser.
    """

    def tokenize(self, hearing: TaggedHearing) -> List[Token]:
        """
        Extract SpeakerPositionEnum tokens from hearing utterances.

        Args:
            hearing: TaggedHearing with speakers and utterances

        Returns:
            List of (SpeakerPositionEnum, utterance_index) tuples
        """
        tokens: List[Token] = []
        for idx, utterance in enumerate(hearing.utterances):
            speaker = hearing.speakers.get(utterance.pid)
            if speaker and speaker.speaker_position:
                tokens.append((speaker.speaker_position, idx))
        return tokens

    # Backwards-compatible alias for the old method name.
    tokenize_utterances = tokenize
