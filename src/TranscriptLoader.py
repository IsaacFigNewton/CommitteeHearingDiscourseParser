"""
TranscriptLoader - A class for loading and querying Digital Democracy Corpus data
"""

import sys
import csv
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup

from .config import *
from .dataclasses.Hearing import Hearing


class TranscriptLoader:
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


    def _setup_csv_field_limit(self):
        """Set up CSV field size limit (Windows compatible)."""
        try:
            csv.field_size_limit(sys.maxsize)
        except OverflowError:
            # Windows workaround
            maxInt = int(2**31 - 1)
            csv.field_size_limit(maxInt)


    def load_content(self, file_name: str, states: Optional[List[str]] = None,
                     years: Optional[List[int]] = None) -> Dict[str, Any]:
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

        payload = {}
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
                with open(file_path, newline='', encoding='utf-8', errors='replace') as csvfile:
                    rows = csv.reader(csvfile, delimiter=',')
                    for row in rows:
                        if header_row:
                            payload['column_headers'] = row
                            payload['rows'] = []
                            header_row = False
                            continue
                        payload['rows'].append(row)

        return payload


    def find_bill_from_bid(self, bid: str, partial_match: bool = False,
                          speeches: Optional[Dict] = None) -> List[List[str]]:
        """Find hearings where a bill is discussed."""
        if speeches is None:
            speeches = self.load_content("speeches")
        hids, matches = [], []
        for row in speeches['rows']:
            if not partial_match and row[SPEECH_BID_IDX] == bid and row[SPEECH_HID_IDX] not in hids:
                matches.append([bid, row[SPEECH_HID_IDX], row[SPEECH_SESSION_IDX], row[SPEECH_DATE_IDX]])
                hids.append(row[SPEECH_HID_IDX])
            if partial_match and bid in row[SPEECH_BID_IDX] and row[SPEECH_HID_IDX] not in hids:
                matches.append([row[SPEECH_BID_IDX], row[SPEECH_HID_IDX], row[SPEECH_SESSION_IDX], row[SPEECH_DATE_IDX]])
                hids.append(row[SPEECH_HID_IDX])
        return matches


    @staticmethod
    def add_seconds(start_time: str, seconds_to_add: int) -> str:
        """Add seconds to a time string."""
        time_obj = datetime.strptime(start_time, TIME_FORMAT)
        new_time = time_obj + timedelta(seconds=seconds_to_add)
        return new_time.strftime(TIME_FORMAT)


    def get_metadata_hearing(self,
            hid: int,
            bid: int,
            hearings: Optional[Dict] = None
        ) -> Optional[Hearing]:
        """Get hearing metadata."""
        if hearings is None:
            hearings = self.load_content("hearings")
        hid = str(hid)
        for row in hearings['rows']:
            if hid == row[HEARING_HID_IDX]:
                return Hearing(
                    hid=int(hid),
                    bid=bid,
                    cid=int(row[HEARING_CID_IDX]),
                    cname=row[HEARING_CNAME_IDX],
                    hearing_date=datetime.strptime(row[HEARING_HDATE_IDX], '%Y-%m-%d'),
                    state=row[HEARING_STATE_IDX]
                )
        return None


    def get_hearing_transcript(self,
            hid: int,
            bid: str,
            speeches: Optional[Dict] = None
        ) -> List[Dict[str, Any]]:
        """Get transcript for a bill discussion."""
        if speeches is None:
            speeches = self.load_content("speeches")
        hid = str(hid)
        lines = []
        for row in speeches['rows']:
            if hid == row[SPEECH_HID_IDX] and bid == row[SPEECH_BID_IDX]:
                offset_time = self.add_seconds("00:00:00", int(row[SPEECH_STARTING_TIME_IDX]))
                lines.append({
                    'bid': row[SPEECH_BID_IDX],
                    'first name': row[SPEECH_FIRST_NAME_IDX],
                    'last name': row[SPEECH_LAST_NAME_IDX],
                    'pid': row[SPEECH_PID_IDX],
                    'text': row[SPEECH_TEXT_IDX]
                })
        return lines


    def bill_discussion_info(self,
            hid: int,
            bid: str,
            hearings: Optional[Dict] = None,
            speeches: Optional[Dict] = None
        ) -> Dict[str, Any]:
        """Get complete bill discussion info."""
        return {
            "metadata": self.get_metadata_hearing(hid, bid, hearings),
            "transcript": self.get_hearing_transcript(hid, bid, speeches)
        }


    @staticmethod
    def pprint_discussion(
            metadata: Hearing,
            transcript_info: List[Dict[str, Any]]
        ):
        """Print formatted transcript."""
        print()
        print(f"] Discussion of {metadata.state} {metadata.cname} held on {metadata.hearing_date.strftime('%Y-%m-%d')}")
        print("] printing transcript: ")
        prev_video = -1
        for line in transcript_info:
            print(f"{line['first name']} {line['last name']}: ")
            print(f"\t{line['text']}")
        print()
