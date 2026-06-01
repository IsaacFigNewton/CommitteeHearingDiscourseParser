"""
TranscriptLoader - A class for loading and querying Digital Democracy Corpus data
"""

import sys
import csv
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup


class TranscriptLoader:
    """
    A class to load and query committee hearing transcripts from the Digital Democracy Corpus.

    This class provides methods to:
    - Load CSV data from the corpus
    - Search for people by name or ID
    - Find bills and hearings
    - Retrieve and format hearing transcripts
    """

    # Class constants
    VALID_STATES = ["CA", "FL", "NY", "TX"]
    CSV_FILENAMES = ['bills', 'committeeHearings', 'committeeRosters',
                     'committees', 'hearings', 'legislature',
                     'people', 'speeches', 'videos']


    def __init__(self, corpus_path: str = 'DH2024_Corpus_Release/'):
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
        if states is not None and not all(item in self.VALID_STATES for item in states):
            raise Exception("Invalid State Abbv(s), corpus only contains data on CA, FL, NY, and TX")

        if file_name not in self.CSV_FILENAMES:
            raise Exception("Invalid filename, must be one of the 9 files provided")

        if years is not None:
            if not all(item > 2015 for item in years) and (states is None or "CA" not in states):
                raise Exception("Data for requested year not included in corpus.")
            if not all(item <= 2018 for item in years):
                raise Exception("Valid session_years are 2017 and 2018 for all states. 2015 and 2016 are valid for CA.")

        payload = {}
        header_row = True

        if states is None:
            states = self.VALID_STATES

        if years is None:
            if "CA" in states:
                years = [2015, 2016, 2017, 2018]
            else:
                years = [2017, 2018]

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
        HID_IDX, BID_IDX, SESSION_IDX, DATE_IDX = 3, 4, 7, 6
        if speeches is None:
            speeches = self.load_content("speeches")
        hids, matches = [], []
        for row in speeches['rows']:
            if not partial_match and row[BID_IDX] == bid and row[HID_IDX] not in hids:
                matches.append([bid, row[HID_IDX], row[SESSION_IDX], row[DATE_IDX]])
                hids.append(row[HID_IDX])
            if partial_match and bid in row[BID_IDX] and row[HID_IDX] not in hids:
                matches.append([row[BID_IDX], row[HID_IDX], row[SESSION_IDX], row[DATE_IDX]])
                hids.append(row[HID_IDX])
        return matches


    @staticmethod
    def add_seconds(start_time: str, seconds_to_add: int) -> str:
        """Add seconds to a time string."""
        time_obj = datetime.strptime(start_time, '%H:%M:%S')
        new_time = time_obj + timedelta(seconds=seconds_to_add)
        return new_time.strftime('%H:%M:%S')


    def get_metadata_hearing(self, hid: int, hearings: Optional[Dict] = None,
                            videos: Optional[Dict] = None) -> Dict[str, Any]:
        """Get hearing metadata."""
        HID_IDX, CID_IDX, CNAME_IDX, HDATE_IDX, STATE_IDX = 0, 4, 8, 1, 3
        if hearings is None:
            hearings = self.load_content("hearings")
        hid = str(hid)
        for row in hearings['rows']:
            if hid == row[HID_IDX]:
                return {
                    'hid': row[HID_IDX], 'cid': row[CID_IDX], 'cname': row[CNAME_IDX],
                    'hearing_date': row[HDATE_IDX], 'state': row[STATE_IDX]
                }
        return {}


    def get_hearing_transcript(self, hid: int, bid: str, speeches: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """Get transcript for a bill discussion."""
        PID_IDX, BID_IDX, HID_IDX = 1, 4, 3
        VID_START_IDX, VID_END_IDX = 9, 10
        LAST_NAME_IDX, FIRST_NAME_IDX, TEXT_IDX = 14, 15, 16
        STARTING_TIME_IDX = 11
        if speeches is None:
            speeches = self.load_content("speeches")
        hid = str(hid)
        lines = []
        for row in speeches['rows']:
            if hid == row[HID_IDX] and bid == row[BID_IDX]:
                offset_time = self.add_seconds("00:00:00", int(row[STARTING_TIME_IDX]))
                lines.append({
                    'video start': row[VID_START_IDX], 'video end': row[VID_END_IDX],
                    'offset': offset_time, 'bid': row[BID_IDX],
                    'first name': row[FIRST_NAME_IDX], 'last name': row[LAST_NAME_IDX],
                    'pid': row[PID_IDX], 'text': row[TEXT_IDX]
                })
        return lines


    def bill_discussion_info(self, hid: int, bid: str, hearings: Optional[Dict] = None,
                            speeches: Optional[Dict] = None, videos: Optional[Dict] = None) -> Dict[str, Any]:
        """Get complete bill discussion info."""
        return {
            "metadata": self.get_metadata_hearing(hid, hearings, videos),
            "transcript": self.get_hearing_transcript(hid, bid, speeches)
        }


    @staticmethod
    def pprint_discussion(metadata: Dict[str, Any], transcript_info: List[Dict[str, Any]]):
        """Print formatted transcript."""
        print()
        print(f"] Discussion of {metadata['state']} {metadata['cname']} held on {metadata['hearing_date']}")
        print("] printing transcript: ")
        prev_video = -1
        for line in transcript_info:
            video = line['video start']
            if video != prev_video:
                print()
                print(f"] Discussing {line['bid']}")
                print()
                prev_video = video
            print(f"[{line['offset']}] {line['first name']} {line['last name']}: ")
            print(f"\t{line['text']}")
        print()
