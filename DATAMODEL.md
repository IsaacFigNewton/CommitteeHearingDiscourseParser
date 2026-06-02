
# Data Model

## Core Dataclasses

### Hearing ([Hearing.py](src/dataclasses/Hearing.py))
Base class representing a committee hearing.

| Field | Type | Description |
|-------|------|-------------|
| `hid` | `int` | Hearing ID |
| `bid` | `str` | Bill ID (e.g., "AB_2017-2018_7") |
| `cid` | `int` | Committee ID |
| `cname` | `str` | Committee name |
| `hearing_date` | `datetime` | Date of the hearing |
| `state` | `str` | State (e.g., "CA") |
| `speakers` | `Dict[int, Speaker]` | Dictionary mapping speaker PIDs to Speaker objects |

### RawHearing ([Hearing.py](src/dataclasses/Hearing.py))
Extends Hearing with raw, unparsed utterances.

| Field | Type | Description |
|-------|------|-------------|
| `utterances` | `List[OralContribution]` | List of all raw OralContributions in the hearing |

### ParsedHearing ([Hearing.py](src/dataclasses/Hearing.py))
Extends Hearing with structured sections. Note: transcripts may contain portions of adjacent hearings which remain uncategorized.

| Field | Type | Description |
|-------|------|-------------|
| `intro` | `Optional[Section]` | Opening remarks, pledge of allegiance, etc. |
| `presentation` | `Section` | Bill description/introduction by presenter (usually the author) |
| `legislator_discussion` | `Optional[Section]` | Discussion among legislators |
| `expert_testimony` | `Optional[Section]` | Expert testimony (always before public discussion) |
| `discussion` | `List[Section]` | Sequence of discussion sections (legislators or public, never experts) |
| `closing_remarks` | `Optional[Section]` | Closing remarks by chair or presenter |
| `vote` | `List[VoteSection]` | Voting sections with motions and roll calls |

### Speaker ([Speaker.py](src/speakers/Speaker.py))
Represents a person speaking at the hearing (based on UK Parliament's agent ontology). Extends RoleProperties.

| Field | Type | Description |
|-------|------|-------------|
| `pid` | `int` | Person ID |
| `first_name` | `Optional[str]` | First name (not always available) |
| `last_name` | `Optional[str]` | Last name (not always available) |
| `speaker_type` | `Optional[SpeakerTypeEnum]` | Type of speaker (e.g., CHAIRMAN, LEGISLATOR) |
| `speaker_role` | `Optional[SpeakerRoleRequirementsEnum]` | Role within committee with requirements |
| `is_committee_member` | `Optional[bool]` | Whether the speaker is a committee member |
| `is_bill_author` | `Optional[bool]` | Whether the speaker is an author of the bill |

### OralContribution ([OralContribution.py](src/dataclasses/OralContribution.py))
Represents a single utterance (based on UK Parliament's oral contribution ontology).

| Field | Type | Description |
|-------|------|-------------|
| `uid` | `int` | Utterance ID within the hearing |
| `pid` | `int` | Speaker's person ID |
| `text` | `str` | The utterance text |

### Section ([Section.py](src/dataclasses/Section.py))
Represents a segment of the hearing.

| Field | Type | Description |
|-------|------|-------------|
| `span` | `Tuple[int, int]` | Utterance indices [start_uid, end_uid) |
| `valid_speakers` | `SectionSpeakerEnum` | Expected speaker roles for this section |
| `utterances` | `List[OralContribution]` | Utterances in this section |

### VoteSection ([Section.py](src/dataclasses/Section.py))
Specialized Section for votes (extends Section).

| Field | Type | Description |
|-------|------|-------------|
| `motion_type` | `MotionEnum` | Type of motion being voted on |
| `motion` | `OralContribution` | The motion statement |
| `second` | `OralContribution` | The second to the motion |
| `roll_call` | `OralContribution` | Roll call results |
| `results` | `List[OralContribution]` | Vote outcome announcements |
| `discussion` | `Optional[List[OralContribution]]` | Discussion during the vote |

## Supporting Classes

### RoleProperties ([RoleProperties.py](src/speakers/roles/RoleProperties.py))
Base dataclass for role-based properties.

| Field | Type | Description |
|-------|------|-------------|
| `is_committee_member` | `Optional[bool]` | Whether the speaker is a committee member |
| `is_bill_author` | `Optional[bool]` | Whether the speaker is a primary bill author |

### RoleRequirements ([RoleRequirements.py](src/speakers/validation/RoleRequirements.py))
Extends RoleProperties to configure SpeakerRoleRequirementsEnum items.

| Field | Type | Description |
|-------|------|-------------|
| `valid_speaker_types` | `FrozenSet[SpeakerTypeEnum]` | Set of valid speaker types for this role |

## Enums

### SpeakerTypeEnum ([SpeakerTypeEnum.py](src/speakers/types/SpeakerTypeEnum.py))
Types of speakers in committee hearings.

| Enum Value | String Value | Description |
|------------|--------------|-------------|
| `CHAIRMAN` | `"CHAIRMAN"` | Committee chair |
| `VICE_CHAIRMAN` | `"VICE_CHAIRMAN"` | Committee vice chair |
| `SECRETARY` | `"SECRETARY"` | Committee secretary |
| `LEGISLATOR` | `"LEGISLATOR"` | Legislator (may or may not be a committee member) |
| `NONLEGISLATOR` | `"NONLEGISLATOR"` | Non-legislator (expert or public) |
| `UNKNOWN` | `"UNKNOWN"` | Unknown/other role |

**COMMITTEE_POSITION_MAP**: Dictionary for mapping committee position titles to SpeakerTypeEnum values.

| Position Title | Maps To |
|----------------|---------|
| `"Chair"` | `SpeakerTypeEnum.CHAIRMAN` |
| `"Co-Chair"` | `SpeakerTypeEnum.CHAIRMAN` |
| `"Vice-Chair"` | `SpeakerTypeEnum.VICE_CHAIRMAN` |
| `"Member"` | `SpeakerTypeEnum.LEGISLATOR` |

### SpeakerRoleEnum ([SpeakerRoleEnum.py](src/speakers/roles/SpeakerRoleEnum.py))
Basic roles that speakers can have in committee hearings.

| Enum Value | String Value | Description |
|------------|--------------|-------------|
| `PRESIDING_CHAIR` | `"PRESIDING_CHAIR"` | Committee chair or vice chair presiding |
| `SECRETARY` | `"SECRETARY"` | Committee secretary |
| `PRESENTER` | `"PRESENTER"` | Bill presenter (usually bill author) |
| `COMMITTEE_MEMBER` | `"COMMITTEE_MEMBER"` | Committee member |
| `EXPERT` | `"EXPERT"` | Expert witness |
| `PUBLIC` | `"PUBLIC"` | Member of the public |
| `UNKNOWN` | `"UNKNOWN"` | Unknown/other role |

### SpeakerRoleRequirementsEnum ([SpeakerRoleRequirementsEnum.py](src/speakers/validation/SpeakerRoleRequirementsEnum.py))
Role definitions with requirements and valid speaker types.

| Role | Valid Speaker Types | Committee Member | Bill Author |
|------|-------------------|------------------|-------------|
| `PRESIDING_CHAIR` | `CHAIRMAN`, `VICE_CHAIRMAN` | `True` | `None` |
| `SECRETARY` | `SECRETARY` | `False` | `False` |
| `PRESENTER` | `LEGISLATOR` | `None` | `None` |
| `COMMITTEE_MEMBER` | `CHAIRMAN`, `VICE_CHAIRMAN`, `LEGISLATOR` | `True` | `None` |
| `EXPERT` | `LEGISLATOR`, `NONLEGISLATOR` | `False` | `False` |
| `PUBLIC` | `NONLEGISLATOR` | `False` | `False` |
| `UNKNOWN` | `UNKNOWN` | `False` | `False` |

### SectionSpeakerEnum ([SectionSpeakerEnum.py](src/speakers/validation/SectionSpeakerEnum.py))
Defines valid speaker roles for each section type.

**Note**: `PRESIDING_CHAIR` and `SECRETARY` are always implicitly allowed in all sections.

| Section Type | Allowed Speaker Roles | Description |
|--------------|----------------------|-------------|
| `INTRO` | `[PRESIDING_CHAIR]` | Opening remarks, pledge of allegiance, etc. |
| `PRESENTATION` | `[PRESENTER]` | Bill description/introduction |
| `LEGISLATOR_DISCUSSION` | `[PRESIDING_CHAIR, SECRETARY, COMMITTEE_MEMBER]` | Discussion among legislators |
| `EXPERT_TESTIMONY` | `[PRESIDING_CHAIR, SECRETARY, COMMITTEE_MEMBER, EXPERT]` | Expert testimony with legislator questions |
| `PUBLIC_COMMENTS` | `[PRESIDING_CHAIR, SECRETARY, PUBLIC]` | Public comment period |
| `CLOSING_REMARKS` | `[PRESIDING_CHAIR, PRESENTER]` | Closing remarks by chair or presenter |
| `VOTE` | `[PRESIDING_CHAIR, SECRETARY]` | Voting section |

### MotionEnum ([MotionEnum.py](src/enums/MotionEnum.py))
Types of motions that can be made.

| Enum Value | String Value | Description |
|------------|--------------|-------------|
| `DUE_PASS` | `"due pass"` | Motion for due pass |
| `RECONSIDERATION` | `"reconsideration"` | Motion for reconsideration |
| `AMENDMENT` | `"amendment"` | Motion for amendment |

## Project Structure

```
src/
├── dataclasses/
│   ├── Hearing.py              # Hearing, RawHearing, ParsedHearing
│   ├── OralContribution.py     # OralContribution
│   └── Section.py              # Section, VoteSection
├── speakers/
│   ├── Speaker.py              # Speaker
│   ├── roles/
│   │   ├── RoleProperties.py   # RoleProperties
│   │   └── SpeakerRoleEnum.py  # SpeakerRoleEnum
│   ├── types/
│   │   └── SpeakerTypeEnum.py  # SpeakerTypeEnum
│   └── validation/
│       ├── RoleRequirements.py              # RoleRequirements
│       ├── SectionSpeakerEnum.py            # SectionSpeakerEnum
│       └── SpeakerRoleRequirementsEnum.py   # SpeakerRoleRequirementsEnum
├── enums/
│   ├── MotionEnum.py           # MotionEnum
│   └── SpeechActEnum.py        # (Currently empty placeholder)
├── HearingParser.py
├── HearingLoader.py
└── config.py
```
