import sys
import csv
from datetime import datetime
from typing import Optional, List, Dict, Any
import pandas as pd

from .config import *
from .dataclasses.Hearing import Hearing
from .dataclasses.Speaker import Speaker
from .dataclasses.OralContribution import OralContribution


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

        self.cid_roster_cache = None

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
            states: Optional[List[str]] = None,
            years: Optional[List[int]] = None,
            method: str = "custom"
        ) -> Dict[str, Any] | pd.DataFrame:
        """Load data from CSVs into a Python object."""
        # Validate inputs
        if states is not None and not all(item in VALID_STATES for item in states):
            raise Exception("Invalid State Abbv(s), corpus only contains data on CA, FL, NY, and TX")

        if file_name not in CSV_FILENAMES:
            raise Exception("Invalid filename, must be one of the 9 files provided")

        if years is not None:
            if not all(item > 2015 for item in years) and (states is None or "CA" not in states):
                raise Exception("Data for requested year not included in corpus.")
            if not all(item <= 2018 for item in years):
                raise Exception("Valid session_years are 2017 and 2018 for all states. 2015 and 2016 are valid for CA.")

        match method:
            case "custom":
                payload = {}
            case "pandas":
                payload = pd.DataFrame()
            case _:
                raise ValueError("Invalid csv loading method")
            
        header_row = True

        if states is None:
            states = VALID_STATES

        if years is None:
            if "CA" in states:
                years = CA_VALID_YEARS
            else:
                years = OTHER_STATES_VALID_YEARS

        for state in states:
            file_paths = []

            if 2017 in years or 2018 in years:
                file_paths.append(f"{self.corpus_path}{state}/2017-2018/CSV/{file_name}.csv")

            if state == "CA" and (2015 in years or 2016 in years):
                file_paths.append(f"{self.corpus_path}{state}/2015-2016/CSV/{file_name}.csv")

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


    def bill_discussion_info(self,
            hid: int,
            bid: str,
        ) -> Hearing:
        """Get complete bill discussion info."""
        hid_str = str(hid)

        # get transcript data
        lines = []
        uid = 0
        for row in self.speeches['rows']:
            if hid_str == row[SPEECH_HID_IDX] and bid == row[SPEECH_BID_IDX]:
                speaker = Speaker(
                    pid=int(row[SPEECH_PID_IDX]) if row[SPEECH_PID_IDX] else None,
                    first_name=row[SPEECH_FIRST_NAME_IDX] if row[SPEECH_FIRST_NAME_IDX] else None,
                    last_name=row[SPEECH_LAST_NAME_IDX] if row[SPEECH_LAST_NAME_IDX] else None,
                    speaker_role=None,
                )

                oral_contribution = OralContribution(
                    uid=uid,
                    speaker=speaker,
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
            first_name = contribution.speaker.first_name or "UNKNOWN"
            last_name = contribution.speaker.last_name or "UNKNOWN"
            name = f"{first_name} {last_name}:"
            print(f"{name:<20} {contribution.text}")
        print()
