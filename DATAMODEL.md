
# Data Model

## Core Dataclasses

### Hearing ([src/dataclasses/Hearing.py](src/dataclasses/Hearing.py))
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
| `utterances` | `List[OralContribution]` | List of all OralContributions in the hearing |

### TaggedHearing ([src/dataclasses/Hearing.py](src/dataclasses/Hearing.py))
Extends Hearing with tagged utterances that include extracted features and metadata.

| Field | Type | Description |
|-------|------|-------------|
| `utterances` | `List[TaggedOralContribution]` | List of all tagged OralContributions with extracted features |

### Speaker ([src/speakers/Speaker.py](src/speakers/Speaker.py))
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

### OralContribution ([src/dataclasses/OralContribution.py](src/dataclasses/OralContribution.py))
Represents a single utterance (based on UK Parliament's oral contribution ontology).

| Field | Type | Description |
|-------|------|-------------|
| `uid` | `int` | Utterance ID within the hearing |
| `pid` | `int` | Speaker's person ID |
| `text` | `str` | The utterance text |

### TaggedOralContribution ([src/dataclasses/OralContribution.py](src/dataclasses/OralContribution.py))
Extends OralContribution with extracted features and tags for classification.

| Field | Type | Description |
|-------|------|-------------|
| `pids_mentioned` | `Optional[Set[int]]` | PIDs of speakers mentioned in this utterance |
| `bill_mentioned` | `Optional[bool]` | If a bill was mentioned in this utterance |
| `relative_position` | `Optional[float]` | Relative position of utterance within hearing (0.0 to 1.0) |
| `tok_count` | `Optional[int]` | Number of tokens in the utterance |
| `sent_count` | `Optional[int]` | Number of sentences in the utterance |
| `speech_act_cues` | `Optional[Set[SpeechActEnum]]` | Detected speech act cues (e.g., STATEMENT, ARGUMENT) |
| `section_cues` | `Optional[Set[SectionEnum]]` | Detected section transition cues |
| `section` | `Optional[SectionEnum]` | Predicted or labeled section type |

### FlatTaggedOralContribution ([src/dataclasses/OralContribution.py](src/dataclasses/OralContribution.py))
Extends TaggedOralContribution with flattened speaker properties. Combines `PositionRoleProperties` and `TaggedOralContribution` for feature extraction in classification.

## Supporting Classes

### RoleProperties ([src/speakers/interfaces/SpeakerProperties.py](src/speakers/interfaces/SpeakerProperties.py))
Base dataclass for role-based properties.

| Field | Type | Description |
|-------|------|-------------|
| `can_file_motions` | `Optional[bool]` | Whether the speaker can file motions (e.g., committee members, secretary) |
| `is_presenter` | `Optional[bool]` | Whether the speaker is presenting the current bill |

### PositionRoleProperties ([src/speakers/interfaces/SpeakerProperties.py](src/speakers/interfaces/SpeakerProperties.py))
Extends RoleProperties with speaker position information.

| Field | Type | Description |
|-------|------|-------------|
| `speaker_position` | `Optional[SpeakerPositionEnum]` | Speaker's level of legislative authority |
| (inherited fields) | | All fields from RoleProperties |

### SpeakerPositionRoleProperties ([src/speakers/interfaces/SpeakerProperties.py](src/speakers/interfaces/SpeakerProperties.py))
Extends PositionRoleProperties with utterance tracking information.

| Field | Type | Description |
|-------|------|-------------|
| `first_mention_uid` | `Optional[int]` | First UID where speaker is mentioned |
| `first_uid` | `int` | UID of speaker's first utterance |
| `last_uid` | `int` | UID of speaker's last utterance |
| (inherited fields) | | All fields from PositionRoleProperties |

### ParseNode ([src/grammar/ParseNode.py](src/grammar/ParseNode.py))
Represents a node in the parse tree produced by CYK parsing.

| Field | Type | Description |
|-------|------|-------------|
| `symbol` | `Any` | Can be TOP, SectionEnum, or Terminal (SpeakerPositionEnum) |
| `children` | `Optional[List[ParseNode]]` | Child nodes in the parse tree |
| `utterance_indices` | `Optional[List[int]]` | Utterance indices covered by this node |

**Key Methods:**
- `to_nltk_tree()`: Convert ParseNode to NLTK Tree format for visualization
- `_format_symbol_label(symbol)`: Format a symbol for use as an NLTK Tree label

## Enums

### SpeakerPositionEnum ([src/speakers/enums/SpeakerPositionEnum.py](src/speakers/enums/SpeakerPositionEnum.py))
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

### SectionEnum ([src/enums/SectionEnum.py](src/enums/SectionEnum.py))
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

### VoteSectionEnum ([src/enums/SectionEnum.py](src/enums/SectionEnum.py))
Subsection types within voting sections.

| Enum Value | String Value | Description |
|------------|--------------|-------------|
| `MOTION` | `"MOTION"` | Motion statement |
| `SECOND` | `"SECOND"` | Second to the motion |
| `ROLL_CALL` | `"ROLL_CALL"` | Roll call voting |
| `RESULTS` | `"RESULTS"` | Vote results announcement |
| `DISCUSSION` | `"DISCUSSION"` | Discussion during vote |

### MotionEnum ([src/enums/MotionEnum.py](src/enums/MotionEnum.py))
Types of motions that can be made.

| Enum Value | String Value | Description |
|------------|--------------|-------------|
| `DUE_PASS` | `"due pass"` | Motion for due pass |
| `RECONSIDERATION` | `"reconsideration"` | Motion for reconsideration |
| `AMENDMENT` | `"amendment"` | Motion for amendment |

### SpeechActEnum ([src/enums/SpeechActEnum.py](src/enums/SpeechActEnum.py))
Types of speech acts/utterances.

| Enum Value | String Value | Description |
|------------|--------------|-------------|
| `STATEMENT` | `"STATEMENT"` | Statement speech act |
| `ARGUMENT` | `"ARGUMENT"` | Argument speech act |

**SPEECH_ACT_CUES**: Dictionary mapping speech acts to their identifying phrases.

### RelativePositionEnum ([src/speakers/enums/UtilEnums.py](src/speakers/enums/UtilEnums.py))
Relative position of an utterance within the hearing.

| Enum Value | Integer Value | Description |
|------------|---------------|-------------|
| `BEFORE` | `-1` | Before the main content |
| `DURING` | `0` | During the main content |
| `AFTER` | `1` | After the main content |

### TOP ([src/grammar/Grammar.py](src/grammar/Grammar.py))
High-level hearing segment types used in the grammar production rules.

| Enum Value | String Value | Description |
|------------|--------------|-------------|
| `ROOT` | `"ROOT"` | Root symbol for complete hearings |
| `START` | `"START"` | Opening section(s) of hearing (INTRO and/or PRESENTATION) |
| `MIDDLE` | `"MIDDLE"` | Middle section(s) with discussion and testimony |
| `LOWER_MIDDLE` | `"LOWER_MIDDLE"` | Later middle section(s) (EXPERT_TESTIMONY and/or PUBLIC_COMMENTS) |
| `END` | `"END"` | Closing section(s) (CLOSING_REMARKS and/or VOTE) |

## Processing Classes

### HearingLoader ([src/HearingLoader.py](src/HearingLoader.py))
Loads and queries committee hearing transcripts from the Digital Democracy Corpus.

**Key Methods:**
- `load_csv()`: Load data from CSVs into Python objects
- `load_all_committee_hearings()`: Load all hearings for committees with enriched speaker data
- `bill_discussion_info()`: Get complete bill discussion info for a specific hearing
- `pprint_hearing()`: Print formatted transcript

### HearingTagger ([src/HearingTagger.py](src/HearingTagger.py))
Tags utterances with features and metadata. Extends `ITagger`.

**Key Methods:**
- `__call__(raw_hearing)`: Process a RawHearing and return TaggedHearing
- `_assign_presiding_chair()`: Identify and assign the presiding chair role

### UtteranceTagger ([src/UtteranceTagger.py](src/UtteranceTagger.py))
Tags individual utterances with extracted features. Extends `ITagger`.

**Key Methods:**
- `__call__(utterance, ...)`: Tag an individual utterance
- `substitute_named_entities()`: Replace speaker names with position tags using spaCy NER
- `substitute_keyphrases()`: Replace keyphrases with standardized tokens
- `_get_speech_act_cues()`: Extract speech act indicators
- `_get_section_cues()`: Extract section transition indicators

### HearingParser ([src/HearingParser.py](src/HearingParser.py))
Predicts section labels for hearing utterances using a masked classifier with parse tree constraints.

**Feature Columns:**
- `TEXT_COL`: 'text' - utterance text
- `CAT_COLS`: ['speaker.position', 'section_cues', 'speech_act_cues'] - categorical features
- `NUM_COLS`: ['relative_position', 'sent_count', 'mentions_speaker', 'mentions_bill'] - numeric features

**Key Methods:**
- `_make_model(base_estimator)`: Initialize the section prediction model pipeline (class method)
- `_fill_missing(df, label_col)`: Fill missing feature values before training or prediction (class method)
- `train_model(train_df, label_col)`: Train the section prediction model on labeled data
- `predict_hearing_sections(hearing, utterances_df, smooth)`: Predict section labels for a single hearing using parse tree constraints
- `predict_hearings_batch(hearings, smooth)`: Predict section labels for multiple hearings in batch mode
- `smooth_label_list(labels)`: Smooth predictions by fixing single outlier labels (static method)
- `_build_utterance_rows(hearings)`: Build feature DataFrame from list of TaggedHearings

### Tokenizer ([src/grammar/Tokenizer.py](src/grammar/Tokenizer.py))
Tokenizes utterances into speaker position sequences and constructs parse trees using CYK parsing.

**Key Methods:**
- `parse()`: Construct parse tree from hearing using CYK algorithm
- `tokenize_utterances()`: Extract SpeakerPositionEnum tokens from hearing
- `parse_to_nltk_tree()`: Convert parse tree to NLTK Tree format for visualization
- `get_all_parses()`: Get all possible parse trees for a hearing (up to max_parses)
- `get_all_parses_as_nltk_trees()`: Get all possible parse trees as NLTK Trees

### Grammar ([src/grammar/Grammar.py](src/grammar/Grammar.py))
Defines the context-free grammar for valid hearing structures in Chomsky Normal Form (CNF).

**Key Components:**
- `GRAMMAR`: List of (lhs, rhs) production rules defining valid hearing structures
- `TOP`: Enum for high-level hearing segments (ROOT, START, MIDDLE, LOWER_MIDDLE, END)
- Terminal symbols: `SpeakerPositionEnum` values
- Production rules mapping:
  - Hearing structure (ROOT → START + MIDDLE + END, with variations)
  - Section sequences (e.g., INTRO → PRESENTATION → EXPERT_TESTIMONY → VOTE)
  - Valid speaker positions for each section type (e.g., PRESENTATION can only have BILL_AUTHOR or PRESIDING_CHAIR)

### MaskedClassifier ([src/classifier/MaskedClassifier.py](src/classifier/MaskedClassifier.py))
Classifier wrapper that applies grammar/parser-constrained masking during prediction. Integrates with sklearn pipelines by accepting masking parameters via `set_params()`.

**Constructor Parameters:**
- `base_estimator`: Underlying classifier (e.g., LogisticRegression)
- `hearing`: TaggedHearing object for context
- `tokenizer`: Tokenizer for parsing
- `grammar`: Grammar for fallback masking
- `speaker_positions`: Array of speaker position values per row
- `can_file_motions`: Array of can_file_motions flags per row
- `is_presenters`: Array of is_presenter flags per row
- `max_parses`: Maximum number of parses to consider (default: 2)

**Key Methods:**
- `fit(X, y)`: Fit the base classifier (typically LogisticRegression)
- `predict(X)`: Predict class labels after applying grammar-constrained masking
- `predict_proba(X)`: Return class probabilities after masking and renormalizing
- `allowed_sections_for_hearing()`: Build allowed sections for each utterance in a hearing (class method)
- `_apply_masking()`: Apply masking and renormalization to probabilities
- `_section_key()`: Return a stable section key for backward compatibility (class method)

### MaskedSoftmaxHelper ([src/classifier/MaskedSoftmaxHelper.py](src/classifier/MaskedSoftmaxHelper.py))
Utilities for building and applying grammar/parser-constrained masks. Implements parse tree-based and grammar-based masking.

**Key Methods:**
- `allowed_sections_for_hearing()`: Build allowed SectionEnums for each utterance in a hearing
- `_sections_by_utterance_from_tree()`: Extract SectionEnums for utterance leaves from an NLTK Tree
- `_allowed_sections_from_grammar_fallback()`: Fallback masks using terminal grammar rules and speaker type
- `_terminal_to_reachable_sections()`: Map each terminal token in GRAMMAR to SectionEnums reachable from it
- `_section_key()`: Return a stable section key for backward compatibility

### ITagger ([src/interfaces/ITagger.py](src/interfaces/ITagger.py))
Abstract base class for tagger implementations.

**Key Methods:**
- `match_regex_pattern()`: Match regex pattern in text
- `matches_any_regex_pattern()`: Check if text matches any of multiple patterns
- `normalize_text()`: Normalize text (lowercase, remove punctuation, preserve ALL_CAPS)
- `simple_match()`: Simple normalized substring matching
- `fuzzy_substring_match()`: Fuzzy substring matching with threshold
- `contains_any_phrase()`: Check if text contains any phrase from a set

## Visualization Classes

### SectionSpeakerRulePlotter ([src/visualizations/SectionSpeakerRulePlotter.py](src/visualizations/SectionSpeakerRulePlotter.py))
Visualizes valid speaker positions for each section type based on grammar rules.

**Key Methods:**
- `plot()`: Generate a bar chart showing which SpeakerPositionEnums are valid for each SectionEnum

## Constants

### Bill Reference Normalization ([src/constants/bill_ref_normalization.py](src/constants/bill_ref_normalization.py))
Constants for identifying and normalizing bill references in text.

**Regex Patterns:**
- `BILL_ID_TERMS`: Regex terms matching bill identifiers (AB, SB, SJR, Assembly Bill, Senate Bill, this bill, the measure, item number)
- `BILL_ID_REGEX`: Composite regex matching any bill identifier with optional number
- `BILL_ID_PATTERN`: Compiled regex for bill IDs
- `NORMALIZED_BILL_REGEX`: Matches the normalized token "BILL"

### General Constants ([src/constants/constants.py](src/constants/constants.py))
Constants for bill action patterns and keyphrase extraction.

**Keyphrase Dictionaries:**
- `BILL_KEYPHRASES`: Dictionary of bill-related keyphrases by category:
  - `0`: "take up" phrases
  - `1`: Modal phrases ("would", "would also")
  - `2`: Action verbs (require, authorize, prohibit, allow, establish, create, extend, impose)
- `DISPOSITION_SUFFIXES`: Vote result phrases ("'s out", "is out", "passes")

**Regex Patterns:**
- `BILL_MODAL_REGEX`: Regex matching bill modal phrases
- `BILL_ACTION_VERB_REGEX`: Regex matching bill action verbs
- `BILL_TAKE_UP_REGEX`: Regex matching "take up" phrases
- `DISPOSITION_SUFFIX_REGEX`: Regex matching disposition suffixes
- `BILL_ACTION_PATTERN`: Compiled regex for bill action statements (e.g., "BILL would authorize...")
- `BILL_TAKE_UP_PATTERN`: Compiled regex for "take up BILL" statements
- `BILL_DISPOSITION_PATTERN`: Compiled regex for bill disposition statements (e.g., "BILL passes")

## Configuration ([src/config.py](src/config.py))

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
│   ├── Hearing.py              # Hearing, TaggedHearing
│   └── OralContribution.py     # OralContribution, TaggedOralContribution, FlatTaggedOralContribution
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
├── grammar/
│   ├── Grammar.py              # GRAMMAR rules, TOP enum, production rules
│   ├── ParseNode.py            # ParseNode dataclass
│   └── Tokenizer.py            # Tokenizer (CYK parsing)
├── classifier/
│   ├── MaskedClassifier.py     # MaskedClassifier (pipeline-compatible)
│   └── MaskedSoftmaxHelper.py  # MaskedSoftmaxHelper (masking utilities)
├── visualizations/
│   └── SectionSpeakerRulePlotter.py    # SectionSpeakerRulePlotter
├── interfaces/
│   └── ITagger.py              # ITagger base class
├── constants/
│   ├── bill_ref_normalization.py       # Bill reference regex patterns
│   └── constants.py                    # Bill action patterns and keyphrases
├── HearingLoader.py            # HearingLoader
├── HearingTagger.py            # HearingTagger
├── UtteranceTagger.py          # UtteranceTagger
├── HearingParser.py            # HearingParser
├── config.py                   # Configuration constants
└── __init__.py                 # Package initialization
```

## Data Flow

1. **Loading**: `HearingLoader` loads raw transcripts from CSV files → `Hearing`
   - Reads committee hearing data from Digital Democracy Corpus
   - Creates `Speaker` objects with metadata from committee rosters
   - Constructs `OralContribution` objects from speech transcripts

2. **Tagging**: `HearingTagger` processes hearings → `TaggedHearing`
   - Uses `UtteranceTagger` to extract features from each utterance
   - Identifies speaker positions and roles using named entity recognition
   - Extracts speaker/bill mentions, speech act cues, section cues
   - Computes metadata (relative position, sentence count)

3. **Parsing**: `Tokenizer` generates discourse parse trees
   - Tokenizes utterances into `SpeakerPositionEnum` sequences
   - Applies CYK parsing algorithm with `GRAMMAR` (CNF format)
   - Produces `ParseNode` trees representing valid hearing structures
   - Can convert to NLTK Tree format for visualization

4. **Classification**: `HearingParser` predicts section labels
   - Builds sklearn Pipeline with two stages:
     1. Feature extraction: ColumnTransformer with TF-IDF (text), OneHotEncoder (categorical), StandardScaler (numeric)
     2. MaskedClassifier: LogisticRegression with grammar/parser-constrained masking
   - Builds feature DataFrame from `TaggedHearing` objects via `_build_utterance_rows()`
   - For each hearing, sets masking parameters on `MaskedClassifier` via `set_params()`:
     - hearing, tokenizer, grammar
     - speaker_positions, can_file_motions, is_presenters arrays
   - During prediction, `MaskedClassifier.predict_proba()`:
     - Gets base probabilities from LogisticRegression
     - Calls `MaskedSoftmaxHelper.allowed_sections_for_hearing()` to build allowed sections per utterance
     - `MaskedSoftmaxHelper` generates parse tree using `Tokenizer` (CYK algorithm)
     - Extracts allowed sections from parse tree leaves
     - Falls back to grammar-based masking when parse tree is unavailable
     - Applies masking and renormalizes probabilities
   - `MaskedClassifier.predict()` selects argmax of masked probabilities
   - Optionally smooths predictions to remove single-utterance outliers
   - Returns predicted `SectionEnum` labels for each utterance
