import sys
import csv
from datetime import datetime
from typing import Optional, List, Dict, Any
import pandas as pd

from .config import *
from .dataclasses.Hearing import Hearing
from .dataclasses.Speaker import Speaker
from .dataclasses.OralContribution import OralContribution

from .enums.SpeakerRoleEnum import SpeakerRoleEnum, COMMITTEE_POSITION_MAP

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
        self._setup_csv_field_limit()

        self.hearings: pd.DataFrame =           self.load_csv("hearings", method="pandas")
        self.speeches: Dict[str, Any] =         self.load_csv("speeches", method="custom")
        self.committeeRosters: pd.DataFrame =   self.load_csv("committeeRosters", method="pandas")[["pid", "cid", "position"]]
        
        # get a set of all the cids
        self.cids = set(self.committeeRosters["cid"].unique().tolist())
        # get a set of all the legislators' pids
        #   if a pid is not in this set, then the person is not a legislator
        self.pids = set(self.committeeRosters["pid"].unique().tolist())

        self.cid_pid_pos = self.get_cid_pid_pos()

    def _setup_csv_field_limit(self):
        """Set up CSV field size limit (Windows compatible)."""
        try:
            csv.field_size_limit(sys.maxsize)
        except OverflowError:
            # Windows workaround
            maxInt = int(2**31 - 1)
            csv.field_size_limit(maxInt)


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


    def get_cid_pid_pos(self) -> Dict[int, Dict[int, SpeakerRoleEnum]]:
        """
        Create a dictionary mapping committee IDs to participant positions.

        Returns:
            Dictionary of the form {cid: {pid: position}} where position is the
            role (e.g., "Chair", "Member") for each participant in each committee.
        """
        result = {}
        for _, row in self.committeeRosters.iterrows():
            cid = row["cid"]
            pid = row["pid"]
            position = row["position"]

            if cid not in result:
                result[cid] = {}
            
            result[cid][pid] = COMMITTEE_POSITION_MAP[position]
        
        return result


    def get_position(self, cid: int, pid: int):
        # if it's a legislator
        if pid in self.pids:
            # if they're a member of the committee
            pos = self.cid_pid_pos[cid].get(pid)
            if pos:
                return pos

            # if they're a legislator that is not part of the committee
            #   (check with Khosmood to see if nonmembers are only ever authors)
            else:
                return SpeakerRoleEnum.NONMEMBER

        # if it's not a legislator,
        #   not enough info for disambiguation yet, so mark as unknown
        return SpeakerRoleEnum.OTHER


    def bill_discussion_info(self,
            hid: int,
            bid: str,
        ) -> Hearing:
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
                    speaker_role=None,
                )

                oral_contribution = OralContribution(
                    uid=uid,
                    pid=speaker_pid,
                    text=row[SPEECH_TEXT_IDX]
                )

                lines.append(oral_contribution)
                uid += 1

        row = self.hearings.loc[self.hearings["hid"] == hid].iloc[0, :]
        return Hearing(
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
