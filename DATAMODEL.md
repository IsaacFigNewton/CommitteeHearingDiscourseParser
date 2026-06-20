
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

### TaggedHearing ([Hearing.py](src/dataclasses/Hearing.py))
Extends Hearing with tagged utterances that include extracted features and metadata.

| Field | Type | Description |
|-------|------|-------------|
| `utterances` | `List[TaggedOralContribution]` | List of all tagged OralContributions with extracted features |

### Speaker ([Speaker.py](src/speakers/Speaker.py))
Represents a person speaking at the hearing (based on UK Parliament's agent ontology). Extends `SpeakerPositionRoleProperties`.

| Field | Type | Description |
|-------|------|-------------|
| `pid` | `int` | Person ID |
| `first_name` | `Optional[str]` | First name (not always available) |
| `last_name` | `Optional[str]` | Last name (not always available) |
| `speaker_position` | `Optional[SpeakerPositionEnum]` | Position of speaker (e.g., PRESIDING_CHAIR, BILL_AUTHOR, COMMITTEE_MEMBER) |
| `can_file_motions` | `Optional[bool]` | Whether the speaker can file motions (inherited from RoleProperties) |
| `is_presenter` | `Optional[bool]` | Whether the speaker is presenting the current bill (inherited from RoleProperties) |
| `first_mention_uid` | `Optional[int]` | First utterance where speaker is mentioned (inherited from SpeakerPositionRoleProperties) |
| `first_uid` | `int` | UID of speaker's first utterance (inherited from SpeakerPositionRoleProperties) |
| `last_uid` | `int` | UID of speaker's last utterance (inherited from SpeakerPositionRoleProperties) |

### OralContribution ([OralContribution.py](src/dataclasses/OralContribution.py))
Represents a single utterance (based on UK Parliament's oral contribution ontology).

| Field | Type | Description |
|-------|------|-------------|
| `uid` | `int` | Utterance ID within the hearing |
| `pid` | `int` | Speaker's person ID |
| `text` | `str` | The utterance text |

### TaggedOralContribution ([OralContribution.py](src/dataclasses/OralContribution.py))
Extends OralContribution with extracted features and tags for classification.

| Field | Type | Description |
|-------|------|-------------|
| `pids_mentioned` | `Optional[Set[int]]` | PIDs of speakers mentioned in this utterance |
| `bids_mentioned` | `Optional[Set[str]]` | Bill IDs mentioned in this utterance |
| `relative_position` | `Optional[float]` | Relative position of utterance within hearing (0.0 to 1.0) |
| `sent_count` | `Optional[int]` | Number of sentences in the utterance |
| `speech_act_cues` | `Optional[Set[SpeechActEnum]]` | Detected speech act cues (e.g., STATEMENT, ARGUMENT) |
| `section_cues` | `Optional[Set[SectionEnum]]` | Detected section transition cues |
| `section` | `Optional[SectionEnum]` | Predicted or labeled section type |

### FlatTaggedOralContribution ([OralContribution.py](src/dataclasses/OralContribution.py))
Extends TaggedOralContribution with flattened speaker properties. Combines `PositionRoleProperties` and `TaggedOralContribution` for feature extraction in classification.

### Section ([Section.py](src/dataclasses/Section.py))
Represents a segment of the hearing.

| Field | Type | Description |
|-------|------|-------------|
| `span` | `Tuple[int, int]` | Utterance indices [start_uid, end_uid) (exclusive end) |
| `valid_speakers` | `SectionSpeakerRequirementsEnum` | Expected speaker roles for this section (Note: enum currently referenced but not implemented) |
| `utterances` | `List[OralContribution]` | Utterances in this section |

## Supporting Classes

### RoleProperties ([SpeakerProperties.py](src/speakers/interfaces/SpeakerProperties.py))
Base dataclass for role-based properties.

| Field | Type | Description |
|-------|------|-------------|
| `can_file_motions` | `Optional[bool]` | Whether the speaker can file motions (e.g., committee members, secretary) |
| `is_presenter` | `Optional[bool]` | Whether the speaker is presenting the current bill |

### PositionRoleProperties ([SpeakerProperties.py](src/speakers/interfaces/SpeakerProperties.py))
Extends RoleProperties with speaker position information.

| Field | Type | Description |
|-------|------|-------------|
| `speaker_position` | `Optional[SpeakerPositionEnum]` | Speaker's level of legislative authority |
| (inherited fields) | | All fields from RoleProperties |

### SpeakerPositionRoleProperties ([SpeakerProperties.py](src/speakers/interfaces/SpeakerProperties.py))
Extends PositionRoleProperties with utterance tracking information.

| Field | Type | Description |
|-------|------|-------------|
| `first_mention_uid` | `Optional[int]` | First UID where speaker is mentioned |
| `first_uid` | `int` | UID of speaker's first utterance |
| `last_uid` | `int` | UID of speaker's last utterance |
| (inherited fields) | | All fields from PositionRoleProperties |

## Enums

### SpeakerPositionEnum ([SpeakerPositionEnum.py](src/speakers/enums/SpeakerPositionEnum.py))
Positions of speakers in committee hearings. Values represent hierarchical authority levels.

| Enum Value | Integer Value | Description |
|------------|---------------|-------------|
| `SECRETARY` | `9` | Committee secretary |
| `PRESIDING_CHAIR` | `8` | Committee chair or vice chair presiding over the hearing |
| `CHAIRMAN` | `7` | Committee chair |
| `VICE_CHAIRMAN` | `6` | Committee vice chair |
| `COMMITTEE_MEMBER` | `5` | Committee member |
| `BILL_AUTHOR` | `4` | Bill author (subdivided by can_file_motions, determines is_presenter) |
| `LEGISLATOR` | `3` | Legislator (may or may not be a committee member) |
| `EXPERT` | `2` | Expert witness |
| `NONLEGISLATOR` | `1` | Non-legislator (expert or public, not yet classified) |
| `PUBLIC` | `0` | Member of the public |

**COMMITTEE_POSITION_MAP**: Dictionary for mapping committee position titles to SpeakerPositionEnum values.

| Position Title | Maps To |
|----------------|---------|
| `"Chair"` | `SpeakerPositionEnum.CHAIRMAN` |
| `"Co-Chair"` | `SpeakerPositionEnum.CHAIRMAN` |
| `"Vice-Chair"` | `SpeakerPositionEnum.VICE_CHAIRMAN` |
| `"Member"` | `SpeakerPositionEnum.COMMITTEE_MEMBER` |

**SPEAKER_POSITION_CUES**: Dictionary mapping speaker positions to identifying phrases.

| Position | Cue Phrases |
|----------|-------------|
| `PUBLIC` | `"on behalf of"`, `"NONLEGISLATOR representing ORG"`, `"NONLEGISLATOR with ORG"` |

### SectionEnum ([SectionEnum.py](src/enums/SectionEnum.py))
Section types in committee hearings. Note: hearing transcripts may contain portions of previous/following hearings which remain uncategorized.

| Enum Value | String Value | Description |
|------------|--------------|-------------|
| `INTRO` | `"INTRO"` | Introducing senators, pledge of allegiance, etc. |
| `PRESENTATION` | `"PRESENTATION"` | Bill description/introduction (generally presenter == author if present) |
| `LEGISLATOR_DISCUSSION` | `"LEGISLATOR_DISCUSSION"` | Discussion among legislators |
| `EXPERT_TESTIMONY` | `"EXPERT_TESTIMONY"` | Expert testimony (always before public discussion) |
| `PUBLIC_COMMENTS` | `"PUBLIC_COMMENTS"` | Public comment period (only legislators or public, never experts) |
| `CLOSING_REMARKS` | `"CLOSING_REMARKS"` | Closing remarks by committee chair or bill author |
| `VOTE` | `"VOTE"` | Voting section (includes all vote subsections) |
| `OTHER` | `"OTHER"` | Fallback for ambiguous sections or discussions of other bills |

**SECTION_CUE_PHRASES**: Dictionary mapping section types to their identifying phrases.

### VoteSectionEnum ([SectionEnum.py](src/enums/SectionEnum.py))
Subsection types within voting sections.

| Enum Value | String Value | Description |
|------------|--------------|-------------|
| `MOTION` | `"MOTION"` | Motion statement |
| `SECOND` | `"SECOND"` | Second to the motion |
| `ROLL_CALL` | `"ROLL_CALL"` | Roll call voting |
| `RESULTS` | `"RESULTS"` | Vote results announcement |
| `DISCUSSION` | `"DISCUSSION"` | Discussion during vote |

### MotionEnum ([MotionEnum.py](src/enums/MotionEnum.py))
Types of motions that can be made.

| Enum Value | String Value | Description |
|------------|--------------|-------------|
| `DUE_PASS` | `"due pass"` | Motion for due pass |
| `RECONSIDERATION` | `"reconsideration"` | Motion for reconsideration |
| `AMENDMENT` | `"amendment"` | Motion for amendment |

### SpeechActEnum ([SpeechActEnum.py](src/enums/SpeechActEnum.py))
Types of speech acts/utterances.

| Enum Value | String Value | Description |
|------------|--------------|-------------|
| `STATEMENT` | `"STATEMENT"` | Statement speech act |
| `ARGUMENT` | `"ARGUMENT"` | Argument speech act |

**SPEECH_ACT_CUES**: Dictionary mapping speech acts to their identifying phrases.

### RelativePositionEnum ([UtilEnums.py](src/speakers/enums/UtilEnums.py))
Relative position of an utterance within the hearing.

| Enum Value | Integer Value | Description |
|------------|---------------|-------------|
| `BEFORE` | `-1` | Before the main content |
| `DURING` | `0` | During the main content |
| `AFTER` | `1` | After the main content |

### TOP ([Grammar.py](src/Grammar.py))
High-level hearing segment types used in the grammar production rules.

| Enum Value | String Value | Description |
|------------|--------------|-------------|
| `START` | `"START"` | Opening section(s) of hearing (INTRO and/or PRESENTATION) |
| `MIDDLE` | `"MIDDLE"` | Middle section(s) with discussion and testimony |
| `LOWER_MIDDLE` | `"LOWER_MIDDLE"` | Later middle section(s) (EXPERT_TESTIMONY and/or PUBLIC_COMMENTS) |
| `END` | `"END"` | Closing section(s) (CLOSING_REMARKS and/or VOTE) |

## Processing Classes

### HearingLoader ([HearingLoader.py](src/HearingLoader.py))
Loads and queries committee hearing transcripts from the Digital Democracy Corpus.

**Key Methods:**
- `load_csv()`: Load data from CSVs into Python objects
- `load_all_committee_hearings()`: Load all hearings for committees with enriched speaker data
- `bill_discussion_info()`: Get complete bill discussion info for a specific hearing
- `pprint_hearing()`: Print formatted transcript

### HearingTagger ([HearingTagger.py](src/HearingTagger.py))
Tags utterances with features and metadata. Extends `ITagger`.

**Key Methods:**
- `__call__(raw_hearing)`: Process a RawHearing and return TaggedHearing
- `_assign_presiding_chair()`: Identify and assign the presiding chair role

### UtteranceTagger ([UtteranceTagger.py](src/UtteranceTagger.py))
Tags individual utterances with extracted features. Extends `ITagger`.

**Key Methods:**
- `__call__(utterance, ...)`: Tag an individual utterance
- `substitute_named_entities()`: Replace speaker names with position tags using spaCy NER
- `substitute_keyphrases()`: Replace keyphrases with standardized tokens
- `_get_speech_act_cues()`: Extract speech act indicators
- `_get_section_cues()`: Extract section transition indicators

### HearingParser ([HearingParser.py](src/HearingParser.py))
Predicts section labels for hearing utterances using a masked softmax classifier with parse tree constraints.

**Key Methods:**
- `train_model()`: Train the section prediction model on labeled data
- `predict_hearing_sections()`: Predict section labels for a single hearing using parse tree constraints
- `predict_hearings_batch()`: Predict section labels for multiple hearings in batch mode
- `smooth_label_list()`: Smooth predictions by fixing single outlier labels (legacy method)

### Tokenizer ([Tokenizer.py](src/Tokenizer.py))
Tokenizes utterances into speaker position sequences and constructs parse trees using CYK parsing.

**Key Classes/Methods:**
- `ParseNode`: Represents a node in the parse tree with `symbol`, `span`, and `children` attributes
- `parse()`: Construct parse tree from hearing using CYK algorithm
- `tokenize_utterances()`: Extract SpeakerPositionEnum tokens from hearing
- `parse_to_nltk_tree()`: Convert parse tree to NLTK Tree format for visualization

### Grammar ([Grammar.py](src/Grammar.py))
Defines the context-free grammar for valid hearing structures in Chomsky Normal Form (CNF).

**Key Components:**
- `Hearing_Grammar`: List of (lhs, rhs) production rules defining valid hearing structures
- `ROOT`: Root symbol for complete hearings
- `TOP`: Enum for high-level hearing segments (START, MIDDLE, LOWER_MIDDLE, END)
- Terminal symbols: `SpeakerPositionEnum` values
- Production rules mapping:
  - Hearing structure (ROOT → START + MIDDLE + END, with variations)
  - Section sequences (e.g., INTRO → PRESENTATION → EXPERT_TESTIMONY → VOTE)
  - Valid speaker positions for each section type (e.g., PRESENTATION can only have BILL_AUTHOR or PRESIDING_CHAIR)

### MaskedSoftmaxClassifier ([MaskedSoftmaxClassifier.py](src/classifier/MaskedSoftmaxClassifier.py))
Classifier that applies masked softmax based on speaker and grammar constraints.

**Key Methods:**
- `fit()`: Fit the underlying logistic regression model
- `predict()`: Predict class labels with masking
- `predict_proba()`: Predict class probabilities with masking

### MaskedSoftmaxHelper ([MaskedSoftmaxHelper.py](src/classifier/MaskedSoftmaxHelper.py))
Helper for section masks, masked logits, and sequence smoothing. Implements parse tree-based and grammar-based masking.

**Key Methods:**
- `build_utterance_mask()`: Generate boolean mask for valid sections per utterance based on parse tree or grammar
- `extract_valid_sections_from_parse_tree()`: Extract valid sections from parse tree nodes
- `apply_mask_to_logits()`: Set invalid section logits to -inf before softmax
- `masked_softmax()`: Compute numerically stable softmax on masked logits
- `predict_proba_from_logits()`: Apply masking and smoothing to raw logits, returning final probabilities
- `smooth_predictions()`: Smooth prediction sequences to remove single-utterance outliers

### ITagger ([ITagger.py](src/interfaces/ITagger.py))
Abstract base class for tagger implementations.

**Key Methods:**
- `match_regex_pattern()`: Match regex pattern in text
- `matches_any_regex_pattern()`: Check if text matches any of multiple patterns
- `normalize_text()`: Normalize text (lowercase, remove punctuation, preserve ALL_CAPS)
- `simple_match()`: Simple normalized substring matching
- `fuzzy_substring_match()`: Fuzzy substring matching with threshold
- `contains_any_phrase()`: Check if text contains any phrase from a set

## Constants ([constants.py](src/constants.py))

### Regex Patterns
- `AB_BILL_REGEX`, `SB_BILL_REGEX`, `SJR_BILL_REGEX`: Match bill IDs (e.g., "AB 123", "SB 456")
- `ASSEMBLY_BILL_REGEX`, `SENATE_BILL_REGEX`: Match full bill names (e.g., "Assembly Bill 123")
- `NAME_BIGRAM_REGEX`: Match capitalized name bigrams for speaker name extraction
- `BILL_ID_PATTERN`: Compiled regex for bill IDs
- `BILL_ACTION_PATTERN`: Compiled regex for bill action statements (e.g., "AB 123 would authorize...")

### Keyphrase Dictionaries
- `BILL_KEYPHRASES`: Dictionaries containing:
  - `BILL_PREFIXES`: Bill type prefixes (AB, SB, SJR)
  - `BILL_ACTION_VERBS`: Common bill action verbs (require, authorize, prohibit, etc.)
- `DISPOSITION_SUFFIXES`: Vote result phrases ("'s out", "is out", "passes")
- `TOKEN_PHRASE_MAP`: Maps standardized tokens to their phrase variants (e.g., "BILL" → {"this bill", "the measure"})
- `PHRASE_TOKEN_MAP`: Reverse mapping from phrases to standardized tokens

## Configuration ([config.py](src/config.py))

### Corpus Settings
- `VALID_STATES`: List of valid state abbreviations in the corpus (`["CA", "FL", "NY", "TX"]`)
- `CSV_FILENAMES`: Available CSV filenames in the Digital Democracy Corpus
- `DEFAULT_CORPUS_PATH`: Default path to corpus data (`'DH2024_Corpus_Release/'`)
- `CA_VALID_YEARS`: Valid year ranges for California (`["2015-2016", "2017-2018"]`)
- `OTHER_STATES_VALID_YEARS`: Valid year ranges for other states (`["2017-2018"]`)

### CSV Column Indices
**Speeches CSV:**
- `SPEECH_HID_IDX`, `SPEECH_BID_IDX`, `SPEECH_PID_IDX`: Hearing, bill, and person IDs
- `SPEECH_SESSION_IDX`, `SPEECH_DATE_IDX`: Session and date information
- `SPEECH_VID_START_IDX`, `SPEECH_VID_END_IDX`: Video timestamp indices
- `SPEECH_FIRST_NAME_IDX`, `SPEECH_LAST_NAME_IDX`: Speaker name indices
- `SPEECH_TEXT_IDX`: Utterance text index
- `SPEECH_STARTING_TIME_IDX`: Starting time within video

**Hearings CSV:**
- `HEARING_HID_IDX`: Hearing ID index
- `HEARING_CID_IDX`, `HEARING_CNAME_IDX`: Committee ID and name indices
- `HEARING_HDATE_IDX`: Hearing date index
- `HEARING_STATE_IDX`: State index

**Other:**
- `TIME_FORMAT`: Time format string (`'%H:%M:%S'`)

## Project Structure

```
src/
├── dataclasses/
│   ├── Hearing.py              # Hearing, RawHearing, TaggedHearing
│   ├── OralContribution.py     # OralContribution, TaggedOralContribution, FlatTaggedOralContribution
│   └── Section.py              # Section
├── speakers/
│   ├── Speaker.py              # Speaker
│   ├── enums/
│   │   ├── SpeakerPositionEnum.py      # SpeakerPositionEnum, COMMITTEE_POSITION_MAP, SPEAKER_POSITION_CUES
│   │   └── UtilEnums.py                # RelativePositionEnum
│   └── interfaces/
│       └── SpeakerProperties.py        # RoleProperties, PositionRoleProperties, SpeakerPositionRoleProperties
├── enums/
│   ├── MotionEnum.py           # MotionEnum
│   ├── SectionEnum.py          # SectionEnum, VoteSectionEnum, SECTION_CUE_PHRASES
│   └── SpeechActEnum.py        # SpeechActEnum, SPEECH_ACT_CUES
├── classifier/
│   ├── MaskedSoftmaxClassifier.py      # MaskedSoftmaxClassifier
│   └── MaskedSoftmaxHelper.py          # MaskedSoftmaxHelper
├── interfaces/
│   └── ITagger.py              # ITagger base class
├── HearingLoader.py            # HearingLoader
├── HearingTagger.py            # HearingTagger
├── UtteranceTagger.py          # UtteranceTagger
├── HearingParser.py            # HearingParser
├── Tokenizer.py                # Tokenizer, ParseNode
├── Grammar.py                  # Hearing_Grammar, TOP enum, production rules
├── constants.py                # Regex patterns, keyphrase dictionaries
├── config.py                   # Configuration constants
└── __init__.py                 # Package initialization
```

## Data Flow

1. **Loading**: `HearingLoader` loads raw transcripts from CSV files → `RawHearing`
   - Reads committee hearing data from Digital Democracy Corpus
   - Creates `Speaker` objects with metadata from committee rosters
   - Constructs `OralContribution` objects from speech transcripts

2. **Tagging**: `HearingTagger` processes raw hearings → `TaggedHearing`
   - Uses `UtteranceTagger` to extract features from each utterance
   - Identifies speaker positions and roles using named entity recognition
   - Extracts speaker/bill mentions, speech act cues, section cues
   - Computes metadata (relative position, sentence count)

3. **Parsing**: `Tokenizer` generates discourse parse trees
   - Tokenizes utterances into `SpeakerPositionEnum` sequences
   - Applies CYK parsing algorithm with `Hearing_Grammar` (CNF format)
   - Produces `ParseNode` trees representing valid hearing structures
   - Can convert to NLTK Tree format for visualization

4. **Classification**: `HearingParser` predicts section labels
   - Extracts features from `TaggedHearing` into feature matrix
   - Generates parse tree using `Tokenizer` for structural constraints
   - Uses `MaskedSoftmaxClassifier` with parse tree-based masking
   - `MaskedSoftmaxHelper` applies parse tree constraints to mask invalid sections
   - Falls back to grammar-based masking when parse tree is unavailable
   - Smooths predictions to remove single-utterance outliers
   - Returns predicted section labels for each utterance
