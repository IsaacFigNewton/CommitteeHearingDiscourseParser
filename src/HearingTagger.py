from typing import Optional, List, Dict, Any
from .interfaces.ITagger import ITagger
from .enums.SectionEnum import SectionEnum, SECTION_CUE_PHRASES
from .dataclasses.OralContribution import FlatTaggedOralContribution
from .dataclasses.Hearing import Hearing, TaggedHearing
from .speakers.enums.SpeakerPositionEnum import SpeakerPositionEnum, SPEAKER_POSITION_CUES
from .speakers.Speaker import Speaker

from .constants.constants import *
from .constants.bill_ref_normalization import SECTION_END_FLAGS
from .UtteranceTagger import UtteranceTagger
"""
only want to parse hearings labelled as CA_201720180<AB/SB>7
    if it's got SR in the suffix, then it's a senate resolution,
    which we don't need to parse
"""

class HearingTagger(ITagger):
    def __init__(self) -> None:
        self.utterance_tagger = UtteranceTagger()

    def __call__(self, raw_hearing: Hearing) -> Optional[TaggedHearing]:
        speaker_names_pids = {
            f"{s.first_name} {s.last_name}": pid
            for pid, s in raw_hearing.speakers.items()
        }

        unknown_speaker_count = sum([
            1 for s in raw_hearing.speakers.values()
            if s.speaker_position is None
        ])

        if unknown_speaker_count > 0:
            print(f"WARNING: Data annotation error for hearing {raw_hearing.hid}. Unidentified speakers: {unknown_speaker_count}")
        
        # subclassify each speaker
        raw_hearing.speakers = self._assign_presiding_chair(raw_hearing.speakers)

        # tag utterances
        tagged_utterances = []
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

            # if the utterance includes a public speaker keyphrase AND the speaker hasn't been
            # assigned a more specific role (e.g., BILL_AUTHOR, LEGISLATOR, COMMITTEE_MEMBER),
            # then mark them as PUBLIC
            if (speaker.speaker_position == SpeakerPositionEnum.NONLEGISLATOR):
                for position, cues in SPEAKER_POSITION_CUES.items():
                    if self.contains_any_phrase(tagged_u.text, cues):
                        raw_hearing.speakers[tagged_u.pid].speaker_position = position

            # if the speaker was mentioned
            if tagged_u.pids_mentioned:
                for matched_pid in tagged_u.pids_mentioned:
                    # update the associated speaker's mention metadata (as needed)
                    if raw_hearing.speakers[matched_pid].first_mention_uid is None:
                        raw_hearing.speakers[matched_pid].first_mention_uid = u.uid
            
            # add hearing contextual features
            tagged_u.relative_position = i / len(raw_hearing.utterances)

            # append to list of tagged utterances
            tagged_utterances.append(tagged_u)

        def first_uid(s: Speaker):
            return tagged_utterances[s.first_uid]

        # detect section end flags and re-tag speakers accordingly
        expert_testimony_end_uid = None
        if SectionEnum.EXPERT_TESTIMONY in SECTION_END_FLAGS:
            end_flags = SECTION_END_FLAGS[SectionEnum.EXPERT_TESTIMONY]
            for i, u in enumerate(tagged_utterances):
                normalized_text = self.normalize_text(u.text)
                if self.contains_any_phrase(normalized_text, end_flags):
                    expert_testimony_end_uid = u.uid
                    break

        # re-tag PUBLIC/NONLEGISLATOR speakers that precede the expert testimony section end as EXPERT
        if expert_testimony_end_uid is not None:
            for pid, s in raw_hearing.speakers.items():
                if s.speaker_position in [SpeakerPositionEnum.PUBLIC, SpeakerPositionEnum.NONLEGISLATOR]:
                    # if all their utterances are before the section end flag
                    if s.last_uid < expert_testimony_end_uid:
                        raw_hearing.speakers[pid].speaker_position = SpeakerPositionEnum.EXPERT

        # resolve ambiguous nonlegislator speakers' roles
        ambiguous_speakers = {
            pid: s for pid, s in raw_hearing.speakers.items()
            if s.speaker_position == SpeakerPositionEnum.NONLEGISLATOR
        }
        for pid, s in ambiguous_speakers.items():
            # if they're a nonlegislator that was mentioned (introduced)
            #   before their first utterance,
            #   or they have > 1 utterance and those utterances are nonconsecutive
            #   then they must be an expert
            if (
                (s.first_mention_uid and s.first_mention_uid < s.first_uid)
                # or first_uid(s).sent_count > 5
                or s.last_uid - s.first_uid > 2
            ):
                raw_hearing.speakers[pid].speaker_position = SpeakerPositionEnum.EXPERT
            
            elif (
                (s.first_mention_uid and s.first_mention_uid == s.first_uid)
                # or first_uid(s).sent_count < 5
            ):
                raw_hearing.speakers[pid].speaker_position = SpeakerPositionEnum.PUBLIC
            
        # if there is not an assigned presenter
        if not any([s.is_presenter for s in raw_hearing.speakers.values()]):
            #   assign the first legislator with an utterance longer than 10 tokens that mentions the bill the role
            for u in tagged_utterances:
                if (
                    u.speaker_position\
                        and u.speaker_position.value >= 3\
                        and u.token_count > 10\
                        and u.bill_mentioned
                ):
                    raw_hearing.speakers[u.pid].is_presenter = True
                    break

        # if the first utterance by a nonlegislator labelled as an EXPERT
        #   follows one by a member of the PUBLIC,
        #   reassign the speaker labelled as EXPERT to PUBLIC
        public_speakers = [
            s.first_uid for s in raw_hearing.speakers.values()
            if s.speaker_position == SpeakerPositionEnum.PUBLIC
        ]
        if len(public_speakers) > 0:
            earliest_public_uid = min(public_speakers)
            for pid in speaker_names_pids.values():
                s = raw_hearing.speakers[pid]
                if (    
                        s.speaker_position is not None\
                        and s.speaker_position.value <= SpeakerPositionEnum.EXPERT.value\
                        and earliest_public_uid < s.first_uid
                    ):
                    raw_hearing.speakers[pid].speaker_position = SpeakerPositionEnum.PUBLIC

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
        
        # if there's no chair or vice chair designated in the committee roster data
        else:
            # assign the committee member with the first utterance the role of presiding chair
            committee = [
                s for s in speakers.values()
                if s.speaker_position == SpeakerPositionEnum.COMMITTEE_MEMBER
            ]
            presiding_chair = min(committee, key=lambda s: s.first_uid)
            speakers[presiding_chair.pid].speaker_position = SpeakerPositionEnum.PRESIDING_CHAIR

        return speakers


    @staticmethod
    def pprint_hearing(hearing: Hearing):
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
