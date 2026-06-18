import sys
import csv
from collections import defaultdict
from datetime import datetime
from typing import Optional, List, Dict, Any
import pandas as pd

from .config import *
from .dataclasses.Hearing import RawHearing
from .speakers.Speaker import Speaker
from .dataclasses.OralContribution import OralContribution

from .speakers.enums.SpeakerPositionEnum import SpeakerPositionEnum, COMMITTEE_POSITION_MAP

class HearingLoader:
    """
    A class to load and query committee hearing transcripts from the Digital Democracy Corpus.

    This class provides methods to:
    - Load CSV data from the corpus
    - Search for people by name or ID
    - Find bills and hearings
    - Retrieve and format hearing transcripts
    """

    def __init__(self, corpus_path: str = DEFAULT_CORPUS_PATH):
        """
        Initialize the TranscriptLoader with the path to the corpus.

        Args:
            corpus_path: Path to the extracted corpus directory
        """
        self.corpus_path = corpus_path
        # set up csv field limit
        try:
            csv.field_size_limit(sys.maxsize)
        except OverflowError:
            # Windows workaround
            maxInt = int(2**31 - 1)
            csv.field_size_limit(maxInt)

        self.hearings: pd.DataFrame =           self.load_csv("hearings", method="pandas")
        self.speeches: Dict[str, Any] =         self.load_csv("speeches", method="custom")
        self.committeeRosters: pd.DataFrame =   self.load_csv("committeeRosters", method="pandas")[["pid", "cid", "position"]]
        self.people: pd.DataFrame =             self.load_csv("people", method="pandas")
        
        # get a set of all the cids
        self.cids = set(self.committeeRosters["cid"].unique().tolist())
        # ignore the assembly and senate floors
        self.cids = self.cids.difference({536, 577})
        
        # get a set of all tracked pids
        #   if a pid is missing from here, it's probably a data cleanliness issue
        self.all_pids = set(self.people["pid"].unique().tolist())
        # get a set of all the legislators' pids
        #   if a pid is not in this set, then the person is not a legislator
        self.pids = set(self.committeeRosters["pid"].unique().tolist())

        self.cid_pid_pos = dict()
        for _, row in self.committeeRosters.iterrows():
            cid = row["cid"]
            pid = row["pid"]
            position = row["position"]

            if cid not in self.cid_pid_pos:
                self.cid_pid_pos[cid] = {}
            
            self.cid_pid_pos[cid][pid] = COMMITTEE_POSITION_MAP[position]


    def load_csv(self,
            file_name: str,
            states: List[str] = VALID_STATES,
            years: List[str] = OTHER_STATES_VALID_YEARS,
            method: str = "custom"
        ) -> Dict[str, Any] | pd.DataFrame:
        """Load data from CSVs into a Python object."""
        # Validate inputs
        if states is not None and not all(item in VALID_STATES for item in states):
            raise Exception("Invalid State Abbv(s), corpus only contains data on CA, FL, NY, and TX")

        if file_name not in CSV_FILENAMES:
            raise Exception("Invalid filename, must be one of the 9 files provided")

        match method:
            case "custom":
                payload = {}
            case "pandas":
                payload = pd.DataFrame()
            case _:
                raise ValueError("Invalid csv loading method")
            
        header_row = True

        for state in states:
            file_paths = []

            for year in years:
                file_paths.append(f"{self.corpus_path}{state}/{year}/CSV/{file_name}.csv")

            for file_path in file_paths:
                match method:
                    case "custom":
                        with open(file_path, newline='', encoding='utf-8', errors='replace') as csvfile:
                            rows = csv.reader(csvfile, delimiter=',')
                            for row in rows:
                                if header_row:
                                    payload['column_headers'] = row
                                    payload['rows'] = []
                                    header_row = False
                                    continue
                                payload['rows'].append(row)
                    case "pandas":
                        if isinstance(payload, pd.DataFrame):
                            if payload.shape[0] == 0:
                                payload = pd.read_csv(file_path)
                            else:
                                payload = pd.concat([payload, pd.read_csv(file_path)], axis=0)
                        else:
                            raise ValueError("not sure how we got here")
                    case _:
                        raise ValueError("Invalid csv loading method")       

        return payload


    def _update_speaker_position(self, cid: int, speaker: Speaker):
        # default to non-legislator with non-committee membership and non-authorship
        speaker.speaker_position = None
        speaker.can_file_motions = False
        speaker.is_presenter = False

        # if its someone tracked in the dataset
        if speaker.pid in self.all_pids:
            # if it's a legislator
            if speaker.pid in self.pids:
                speaker.speaker_position = SpeakerPositionEnum.LEGISLATOR
                # TODO: check if they're a primary author on the bill

                # if they're a member of the committee
                pos = self.cid_pid_pos[cid].get(speaker.pid)
                if pos:
                    speaker.can_file_motions = True
                    speaker.speaker_position = pos
                    return speaker

                # if they're a legislator that is not part of the committee
                speaker.speaker_position = SpeakerPositionEnum.LEGISLATOR
                return speaker

            # if it's just the committee secretary or staff
            if speaker.first_name == "Committee" and speaker.last_name == "Secretary":
                speaker.can_file_motions = True
                speaker.speaker_position = None
                return speaker

            # if it's not a legislator,
            #   but they are being tracked
            #   then they must be a member of the public
            speaker.speaker_position = SpeakerPositionEnum.NONLEGISLATOR
            return speaker
        
        # if it's someone not tracked in the dataset
        #   i.e. probably a data annotation error
        # check if person's first+last name are in all_pids
        if speaker.first_name and speaker.last_name:
            clean_first = speaker.first_name.split(" ")[0]
            clean_last = speaker.last_name.split(" ")[0]
            mask = (
                (self.people["first"] == clean_first)
                & (self.people["last"] == clean_last)
            )

            # if there's a match in the list of all people
            masked_people = self.people.loc[mask]
            if len(masked_people) > 0:
                pid = masked_people.iloc[0]["pid"]
                speaker.pid = pid
                speaker.first_name = clean_first
                speaker.last_name = clean_last
                return self._update_speaker_position(cid, speaker)
        
        # if no speaker match found, mark as unknown
        speaker.speaker_position = None
        return speaker


    def load_all_committee_hearings(self) -> List[RawHearing]:
        """
        Load all hearings for each committee and enrich speakers with their positions.

        Builds a nested speech index:

            cid -> hid -> bid -> List[speech_row]

        Then reuses that index to construct Hearing objects directly.
        """
        # Index hearing metadata once by hid
        hearing_rows_by_hid = {
            int(row["hid"]): row
            for _, row in self.hearings.iterrows()
        }

        # Build nested speech index: cid -> hid -> bid -> rows
        speeches_by_cid_hid_bid = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )

        for speech_row in self.speeches["rows"]:
            hid_raw = speech_row[SPEECH_HID_IDX]
            bid = speech_row[SPEECH_BID_IDX]

            try:
                hid = int(hid_raw)
            except Exception as e:
                print(f"{e}")
                continue
            hearing_row = hearing_rows_by_hid.get(hid)

            if hearing_row is None:
                continue

            cid = int(hearing_row.cid)
            speeches_by_cid_hid_bid[cid][hid][bid].append(speech_row)


        hearings: List[RawHearing] = []
        for cid in self.cids:
            hearings_by_hid = speeches_by_cid_hid_bid[cid]
            
            for hid, bills_by_bid in hearings_by_hid.items():
                hearing_row = hearing_rows_by_hid[hid]

                for bid, speech_rows in bills_by_bid.items():
                    hearing = self._build_hearing_from_speech_rows(
                        hid=hid,
                        bid=bid,
                        hearing_row=hearing_row,
                        speech_rows=speech_rows,
                    )

                    # enrich speakers with speaker role info
                    if cid in self.cid_pid_pos:
                        for pid in hearing.speakers.keys():
                            hearing.speakers[pid] = self._update_speaker_position(cid, hearing.speakers[pid])

                    hearings.append(hearing)

        return hearings


    def _build_hearing_from_speech_rows(
        self,
        hid: int,
        bid: str,
        hearing_row: Any,
        speech_rows: List[List[Any]],
    ) -> RawHearing:
        """
        Build a Hearing object from pre-indexed speech rows.

        This avoids scanning self.speeches["rows"] again for every hid/bid pair.
        """
        speakers: Dict[int, Speaker] = {}
        utterances: List[OralContribution] = []

        for uid, speech_row in enumerate(speech_rows):
            pid_raw = speech_row[SPEECH_PID_IDX]
            try:
                pid = int(pid_raw)
            except Exception as e:
                print(f"{e}")
                continue

            if pid not in speakers:
                speakers[pid] = Speaker(
                    pid=pid,
                    first_name=(
                        speech_row[SPEECH_FIRST_NAME_IDX]
                        if speech_row[SPEECH_FIRST_NAME_IDX]
                        else None
                    ),
                    last_name=(
                        speech_row[SPEECH_LAST_NAME_IDX]
                        if speech_row[SPEECH_LAST_NAME_IDX]
                        else None
                    ),
                    speaker_position=None,
                    can_file_motions=None,
                    is_presenter=None,
                    first_mention_uid=None,
                    first_uid=1000000,
                    last_uid=-1
                )

            utterances.append(
                OralContribution(
                    uid=uid,
                    pid=pid,
                    text=speech_row[SPEECH_TEXT_IDX],
                )
            )

        return RawHearing(
            hid=hid,
            bid=bid,
            cid=int(hearing_row.cid),
            cname=getattr(hearing_row, "Committee"),
            hearing_date=datetime.strptime(hearing_row.hDate, "%Y-%m-%d"),
            state=hearing_row.state,
            speakers=speakers,
            utterances=utterances,
        )


    def bill_discussion_info(self,
            hid: int,
            bid: str,
        ) -> RawHearing:
        """Get complete bill discussion info."""
        hid_str = str(hid)

        # get transcript data
        lines = []
        speakers = dict()
        uid = 0
        for row in self.speeches['rows']:
            if hid_str == row[SPEECH_HID_IDX] and bid == row[SPEECH_BID_IDX]:
                speaker_pid = int(row[SPEECH_PID_IDX]) if row[SPEECH_PID_IDX] else -1
                speakers[speaker_pid] = Speaker(
                    pid=speaker_pid,
                    first_name=row[SPEECH_FIRST_NAME_IDX] if row[SPEECH_FIRST_NAME_IDX] else None,
                    last_name=row[SPEECH_LAST_NAME_IDX] if row[SPEECH_LAST_NAME_IDX] else None,
                    speaker_position=None,
                    can_file_motions=None,
                    is_presenter=None,
                    first_mention_uid=None,
                    first_uid=1000000,
                    last_uid=-1
                )

                oral_contribution = OralContribution(
                    uid=uid,
                    pid=speaker_pid,
                    text=row[SPEECH_TEXT_IDX],
                )

                lines.append(oral_contribution)
                uid += 1

        row = self.hearings.loc[self.hearings["hid"] == hid].iloc[0, :]
        return RawHearing(
            hid=hid,
            bid=bid,
            cid=int(row["cid"]),
            cname=row["Committee"],
            hearing_date=datetime.strptime(row["hDate"], '%Y-%m-%d'),
            state=row["state"],
            speakers=speakers,
            utterances=lines
        )


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
