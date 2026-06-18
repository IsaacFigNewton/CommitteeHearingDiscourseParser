from typing import Optional, List, Dict, Any
from .interfaces.ITagger import ITagger
from .dataclasses.OralContribution import FlatTaggedOralContribution
from .dataclasses.Hearing import RawHearing, TaggedHearing
from .speakers.enums.SpeakerPositionEnum import SpeakerPositionEnum
from .speakers.Speaker import Speaker

from .constants import *
from .UtteranceTagger import UtteranceTagger
"""
only want to parse hearings labelled as CA_201720180<AB/SB>7
    if it's got SR in the suffix, then it's a senate resolution,
    which we don't need to parse
"""

class HearingTagger(ITagger):
    def __init__(self) -> None:
        self.utterance_tagger = UtteranceTagger()

    def __call__(self, raw_hearing: RawHearing) -> Optional[TaggedHearing]:
        tagged_utterances = []
        word_counts = [len(u.text.split(" ")) for u in raw_hearing.utterances]
        max_word_count = max(word_counts)
        speaker_names_pids = {
            f"{s.first_name} {s.last_name}": pid
            for pid, s in raw_hearing.speakers.items()
        }

        unknown_speaker_count = sum([
            1 for s in raw_hearing.speakers.values()
            if s.speaker_position is None and not s.can_file_motions
        ])

        # if all speakers are accounted for (i.e. no data annotation errors),
        #   try subdividing them
        if unknown_speaker_count == 0:
            raw_hearing.speakers = self._assign_presiding_chair(raw_hearing.speakers)

        # tag utterances
        for i, u in enumerate(raw_hearing.utterances):
            speaker = raw_hearing.speakers[u.pid]

            # update the current speaker's first and last utterance ids
            raw_hearing.speakers[u.pid].first_uid = min(raw_hearing.speakers[u.pid].first_uid, u.uid)
            raw_hearing.speakers[u.pid].last_uid = max(raw_hearing.speakers[u.pid].last_uid, u.uid)
            
            # tag the utterance using utterance and speaker data only
            tagged_u = self.utterance_tagger(
                u,
                speaker_names_pids,
                raw_hearing.speakers,
                speaker
            )
            if not isinstance(tagged_u, FlatTaggedOralContribution):
                raise ValueError(f"expected flattened, tagged utterance of type FlatTaggedOralContribution, received {type(tagged_u)}")

            if tagged_u.pids_mentioned:
                for matched_pid in tagged_u.pids_mentioned:
                    # update the associated speaker's mention metadata (as needed)
                    if raw_hearing.speakers[matched_pid].first_mention_uid is None:
                        raw_hearing.speakers[matched_pid].first_mention_uid = u.uid
            
            # add hearing contextual features
            tagged_u.relative_position = i / max(len(word_counts) - 1, 1)
            tagged_u.relative_len = word_counts[i] / max_word_count
            
            # append to list of tagged utterances
            tagged_utterances.append(tagged_u)

        return TaggedHearing(
            **{
                **vars(raw_hearing),
                "utterances": tagged_utterances,
            }
        )

    @classmethod
    def _assign_presiding_chair(cls, speakers: Dict[int, Speaker]) -> Dict[int, Speaker]:
        chairs = [
            (pid, s) for pid, s in speakers.items()
            if s.speaker_position == SpeakerPositionEnum.CHAIRMAN
        ]
        vice_chairs = [
            (pid, s) for pid, s in speakers.items()
            if s.speaker_position == SpeakerPositionEnum.VICE_CHAIRMAN
        ]

        # if there's at least 1 chair
        if len(chairs) > 0:

            # if there's 1 main chair, they preside
            if len(chairs) == 1:
                speakers[chairs[0][0]].speaker_position = SpeakerPositionEnum.PRESIDING_CHAIR
            # otherwise, presiding chair must be determined by context
            #   as a heuristic, just take the first available
            #   TODO: REPLACE
            else:
                speakers[chairs[0][0]].speaker_position = SpeakerPositionEnum.PRESIDING_CHAIR
                # reassign all other chairs to committee member positions
                for c in chairs[1:]:
                    speakers[c[0]].speaker_position = SpeakerPositionEnum.COMMITTEE_MEMBER

            # reassign all vice chairs to committee member positions
            for vc in vice_chairs:
                speakers[vc[0]].speaker_position = SpeakerPositionEnum.COMMITTEE_MEMBER

        # if there's at least 1 vice chair
        elif len(vice_chairs) > 0:
            # if there's 1 vice chair, they preside
            if len(vice_chairs) == 1:
                speakers[vice_chairs[0][0]].speaker_position = SpeakerPositionEnum.PRESIDING_CHAIR
            # otherwise, presiding chair must be determined by context
            #   as a heuristic, just take the first available
            #   TODO: REPLACE
            else:
                speakers[vice_chairs[0][0]].speaker_position = SpeakerPositionEnum.PRESIDING_CHAIR
                # reassign all other chairs to committee member positions
                for vc in vice_chairs[1:]:
                    speakers[vc[0]].speaker_position = SpeakerPositionEnum.COMMITTEE_MEMBER
        
        return speakers


    @classmethod
    def _detect_first_presentation_utterance(cls, raw_hearing: RawHearing) -> int:
        """Returns the index of the first utterance that is believed to be a presenting a bill, or -1 if none found"""
        for i, u in enumerate(raw_hearing.utterances):
            # The presenter may say a phrase that indicates they are beginning to present or the chairperson is introducing them
            if cls.contains_any_phrase(u.text, PRESENTATION_START_PHRASES + PRESENTATION_HANDOFF_PHRASES):
                return i
            
            if cls.match_regex_pattern(BILL_ACTION_PATTERN, u.text):
                return i

        return -1
    

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
