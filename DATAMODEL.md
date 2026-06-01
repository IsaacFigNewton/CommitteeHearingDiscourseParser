
# Data Model

## Core Dataclasses

### Hearing ([Hearing.py](src/dataclasses/Hearing.py))
Represents a complete committee hearing.

| Field | Type | Description |
|-------|------|-------------|
| `hid` | `int` | Hearing ID |
| `bid` | `str` | Bill ID (e.g., "AB_2017-2018_7") |
| `cid` | `int` | Committee ID |
| `cname` | `str` | Committee name |
| `hearing_date` | `datetime` | Date of the hearing |
| `state` | `str` | State (e.g., "CA") |
| `speakers` | `Dict[int, Speaker]` | Dictionary mapping speaker PIDs to Speaker objects |
| `utterances` | `List[OralContribution]` | List of all OralContributions in the hearing |

### Speaker ([Speaker.py](src/dataclasses/Speaker.py))
Represents a person speaking at the hearing (based on UK Parliament's agent ontology).

| Field | Type | Description |
|-------|------|-------------|
| `pid` | `int` | Person ID |
| `first_name` | `Optional[str]` | First name (not always available) |
| `last_name` | `Optional[str]` | Last name (not always available) |
| `speaker_role` | `Optional[SpeakerRoleEnum]` | Role within committee |

### OralContribution ([OralContribution.py](src/dataclasses/OralContribution.py))
Represents a single utterance (based on UK Parliament's oral contribution ontology).

| Field | Type | Description |
|-------|------|-------------|
| `uid` | `int` | Utterance ID within the hearing |
| `pid` | `int` | Speaker's person ID |
| `text` | `str` | The utterance text |

### BillDiscussion ([BillDiscussion.py](src/dataclasses/BillDiscussion.py))
Represents the structured discourse of a bill discussion.

| Field | Type | Description |
|-------|------|-------------|
| `intro` | `Optional[Section]` | Opening remarks, pledge of allegiance, etc. |
| `presentation` | `Section` | Bill description/introduction by presenter (usually the author) |
| `discussion` | `List[Section]` | Sequence of discussion sections (legislator discussion, expert testimony, public comments) |
| `closing_remarks` | `Optional[Section]` | Closing remarks by chair or presenter |
| `vote` | `List[VoteSection]` | Voting sections with motions and roll calls |

### Section ([BillDiscussion.py](src/dataclasses/BillDiscussion.py))
Represents a segment of the hearing.

| Field | Type | Description |
|-------|------|-------------|
| `span` | `Tuple[int, int]` | Utterance indices [start_uid, end_uid) |
| `valid_speakers` | `SectionSpeakerEnum` | Expected speaker roles for this section |
| `utterances` | `List[OralContribution]` | Utterances in this section |

### VoteSection ([BillDiscussion.py](src/dataclasses/BillDiscussion.py))
Specialized Section for votes (extends Section).

| Field | Type | Description |
|-------|------|-------------|
| `motion_type` | `MotionEnum` | Type of motion being voted on |
| `motion` | `OralContribution` | The motion statement |
| `second` | `OralContribution` | The second to the motion |
| `roll_call` | `OralContribution` | Roll call results |
| `results` | `List[OralContribution]` | Vote outcome announcements |
| `discussion` | `Optional[List[OralContribution]]` | Discussion during the vote |

## Enums

### SpeakerTypeEnum ([SpeakerTypeEnum.py](src/enums/SpeakerTypeEnum.py))
Types of speakers in committee hearings.

| Enum Value | String Value | Description |
|------------|--------------|-------------|
| `CHAIRMAN` | `"CHAIRMAN"` | Committee chair |
| `VICE_CHAIRMAN` | `"VICE_CHAIRMAN"` | Committee vice chair |
| `SECRETARY` | `"SECRETARY"` | Committee secretary |
| `PRESENTER` | `"PRESENTER"` | Bill presenter (usually bill author) |
| `MEMBER` | `"MEMBER"` | Legislator who is a member of the committee |
| `NONMEMBER` | `"NONMEMBER"` | Legislator who is NOT a member of the committee |
| `EXPERT` | `"EXPERT"` | Expert witness |
| `PUBLIC` | `"PUBLIC"` | Member of the public |
| `UNKNOWN` | `"UNKNOWN"` | Unknown/other role |

### SpeakerRoleEnum ([SpeakerRoleEnum.py](src/enums/SpeakerRoleEnum.py))
Roles that speakers can have in committee hearings.

| Enum Value | String Value | Description |
|------------|--------------|-------------|
| `CHAIRMAN` | `"CHAIRMAN"` | Committee chair |
| `VICE_CHAIRMAN` | `"VICE_CHAIRMAN"` | Committee vice chair |
| `STAFF` | `"STAFF"` | Committee Staff |
| `PRESENTER` | `"PRESENTER"` | Bill presenter (usually bill author) |
| `LEGISLATOR` | `"LEGISLATOR"` | Legislator who may or may not be a committee member |
| `EXPERT` | `"EXPERT"` | Expert witness |
| `PUBLIC` | `"PUBLIC"` | Member of the public |
| `UNKNOWN` | `"UNKNOWN"` | Unknown/other role |

**COMMITTEE_POSITION_MAP**: Dictionary for mapping committee position titles to SpeakerRoleEnum values.

| Position Title | Maps To |
|----------------|---------|
| `"Chair"` | `SpeakerRoleEnum.CHAIRMAN` |
| `"Co-Chair"` | `SpeakerRoleEnum.CHAIRMAN` |
| `"Vice-Chair"` | `SpeakerRoleEnum.VICE_CHAIRMAN` |
| `"Member"` | `SpeakerRoleEnum.MEMBER` |

### SectionSpeakerEnum ([SectionSpeakerEnum.py](src/enums/SectionSpeakerEnum.py))
Defines valid speaker roles for each section type. Note: CHAIRMAN and STAFF are always implicitly allowed.

| Section Type | Allowed Speaker Roles | Description |
|--------------|----------------------|-------------|
| `ANY_SECTION` | `[CHAIRMAN, STAFF, OTHER]` | Any section in the hearing |
| `INTRO` | `[CHAIRMAN]` | Opening remarks, pledge of allegiance, etc. |
| `PRESENTATION` | `[PRESENTER]` | Bill description/introduction |
| `LEGISLATOR_DISCUSSION` | `[LEGISLATOR]` | Discussion among legislators |
| `EXPERT_TESTIMONY` | `[LEGISLATOR, EXPERT]` | Expert testimony with legislator questions |
| `PUBLIC_COMMENTS` | `[PUBLIC]` | Public comment period |
| `CLOSING_REMARKS` | `[CHAIRMAN, PRESENTER]` | Closing remarks by chair or presenter |
| `VOTE` | `[STAFF]` | Voting section |

### MotionEnum ([MotionEnum.py](src/enums/MotionEnum.py))
Types of motions that can be made.

| Enum Value | String Value | Description |
|------------|--------------|-------------|
| `DUE_PASS` | `"due pass"` | Motion for due pass |
| `RECONSIDERATION` | `"reconsideration"` | Motion for reconsideration |
| `AMENDMENT` | `"amendment"` | Motion for amendment |
