# CommitteeHearingDiscourseParser

A parser for California legislative committee hearing transcripts, modeling the discourse structure of bill discussions.

## Data Model Overview

The project models committee hearings using several core dataclasses:

- **[Hearing](src/dataclasses/Hearing.py)**: Base class for committee hearings with metadata and speakers
- **[RawHearing](src/dataclasses/Hearing.py)**: Extends Hearing with raw, unparsed utterances
- **[TaggedHearing](src/dataclasses/Hearing.py)**: Extends Hearing with tagged utterances containing extracted features
- **[Speaker](src/speakers/Speaker.py)**: Represents a person speaking at the hearing with their position and role (based on UK Parliament's agent ontology)
- **[OralContribution](src/dataclasses/OralContribution.py)**: Represents a single utterance by a speaker (based on UK Parliament's oral contribution ontology)
- **[TaggedOralContribution](src/dataclasses/OralContribution.py)**: Extends OralContribution with extracted features and metadata
- **[FlatTaggedOralContribution](src/dataclasses/OralContribution.py)**: Flattened version combining TaggedOralContribution with speaker properties for classification
- **[Section](src/dataclasses/Section.py)**: Represents a segment of the hearing with a span of utterances

Supporting classes and enums:
- **[SpeakerPositionEnum](src/speakers/enums/SpeakerPositionEnum.py)**: Speaker positions with hierarchical authority levels (Secretary, Presiding Chair, Chairman, Vice Chairman, Committee Member, Bill Author, Legislator, Expert, Nonlegislator, Public)
- **[RoleProperties](src/speakers/interfaces/SpeakerProperties.py)**: Base properties for speaker roles (can_file_motions, is_presenter)
- **[PositionRoleProperties](src/speakers/interfaces/SpeakerProperties.py)**: Extends RoleProperties with speaker_position
- **[SpeakerPositionRoleProperties](src/speakers/interfaces/SpeakerProperties.py)**: Extends PositionRoleProperties with utterance tracking (first_mention_uid, first_uid, last_uid)
- **[SectionEnum](src/enums/SectionEnum.py)**: Section types (INTRO, PRESENTATION, LEGISLATOR_DISCUSSION, EXPERT_TESTIMONY, PUBLIC_COMMENTS, CLOSING_REMARKS, VOTE, OTHER)
- **[VoteSectionEnum](src/enums/SectionEnum.py)**: Vote subsection types (MOTION, SECOND, ROLL_CALL, RESULTS, DISCUSSION)
- **[MotionEnum](src/enums/MotionEnum.py)**: Types of motions (Due Pass, Reconsideration, Amendment)
- **[SpeechActEnum](src/enums/SpeechActEnum.py)**: Types of speech acts (Statement, Argument)
- **[TOP](src/Grammar.py)**: High-level hearing segment types for grammar (START, MIDDLE, LOWER_MIDDLE, END)

For detailed field-level documentation, see [DATAMODEL.md](DATAMODEL.md).

### Valid Speaker Positions/Roles by Section
![Valid Speaker Positions/Roles by Section](figures\valid_SpeakerPositionEnum_by_SectionEnum.png)

## Class Hierarchy

```mermaid
graph TD
    %% Hearing hierarchy
    Hearing[Hearing]
    Hearing -->|fields| hearing_fields["hid, bid, cid, cname, hearing_date, state, speakers: Dict[int, Speaker]"]
    RawHearing[RawHearing]
    RawHearing -->|adds| raw_fields["utterances: List[OralContribution]"]
    RawHearing -->|extends| Hearing
    TaggedHearing[TaggedHearing]
    TaggedHearing -->|extends| Hearing
    TaggedHearing -->|adds| tagged_fields["utterances: List[TaggedOralContribution]"]

    %% OralContribution hierarchy
    OralContribution[OralContribution]
    TaggedOralContribution[TaggedOralContribution]
    FlatTaggedOralContribution[FlatTaggedOralContribution]
    FlatTaggedOralContribution -->|extends| TaggedOralContribution
    FlatTaggedOralContribution -->|combines with| PositionRoleProperties

    %% Speaker property hierarchy
    RoleProperties[RoleProperties]
    PositionRoleProperties[PositionRoleProperties]
    SpeakerPositionRoleProperties[SpeakerPositionRoleProperties]
    Speaker[Speaker]

    %% Other classes
    ParseNode[ParseNode]

    %% OralContribution hierarchy relationships
    TaggedOralContribution -->|extends| OralContribution

    %% Speaker property hierarchy relationships
    PositionRoleProperties -->|extends| RoleProperties
    PositionRoleProperties -->|adds| position_fields["speaker_position"]
    SpeakerPositionRoleProperties -->|extends| PositionRoleProperties
    SpeakerPositionRoleProperties -->|adds| tracking_fields["first_mention_uid, first_uid, last_uid"]
    Speaker -->|extends| SpeakerPositionRoleProperties

    OralContribution -->|fields| oral_fields["uid, pid, text"]
    TaggedOralContribution -->|adds| tagged_oral_fields["pids_mentioned, bids_mentioned, relative_position, sent_count, speech_act_cues, section_cues, section"]

    RoleProperties -->|fields| role_fields["can_file_motions, is_presenter"]
    Speaker -->|adds| speaker_fields["pid, first_name, last_name"]

    ParseNode -->|fields| parse_fields["symbol, span: Tuple[int, int], children"]

    %% Styling
    classDef dataclass fill:#e1f5ff,stroke:#333,stroke-width:2px,color:#000
    classDef fieldNode fill:#f0f0f0,stroke:#666,stroke-width:1px,color:#000,stroke-dasharray: 5 5

    class Hearing,RawHearing,TaggedHearing,OralContribution,TaggedOralContribution,FlatTaggedOralContribution,RoleProperties,PositionRoleProperties,SpeakerPositionRoleProperties,Speaker,ParseNode dataclass
    class hearing_fields,raw_fields,tagged_fields,oral_fields,tagged_oral_fields,role_fields,position_fields,tracking_fields,speaker_fields,section_fields,parse_fields fieldNode
```

## Architecture Diagram

```mermaid
graph LR
    %% Data flow
    CSV[CSV Files<br/>Digital Democracy Corpus] -->|load| HearingLoader

    HearingLoader -->|creates| RawHearing[RawHearing<br/>raw utterances]

    RawHearing -->|tag features| HearingTagger
    HearingTagger -->|uses| UtteranceTagger
    HearingTagger -->|creates| TaggedHearing[TaggedHearing<br/>tagged utterances]

    TaggedHearing -->|parse & predict| HearingParser
    HearingParser -->|uses| Tokenizer[Tokenizer<br/>CYK parsing]
    HearingParser -->|uses| MaskedSoftmaxClassifier

    Tokenizer -->|applies| Grammar[Grammar<br/>CNF production rules]
    Tokenizer -->|creates| ParseNode[ParseNode<br/>parse tree]

    MaskedSoftmaxClassifier -->|uses| MaskedSoftmaxHelper
    MaskedSoftmaxHelper -->|constraints from| ParseNode
    MaskedSoftmaxHelper -->|constraints from| Grammar

    HearingParser -->|outputs| PredictedSections[Predicted Section Labels<br/>per utterance]

    %% Component grouping
    subgraph "Data Loading"
        HearingLoader
        CSV
    end

    subgraph "Feature Extraction"
        HearingTagger
        UtteranceTagger
    end

    subgraph "Section Classification"
        HearingParser
        Tokenizer
        Grammar
        ParseNode
        MaskedSoftmaxClassifier
        MaskedSoftmaxHelper
    end

    %% Styling
    classDef input fill:#fff4e1,stroke:#333,stroke-width:2px,color:#000
    classDef data fill:#e1f5ff,stroke:#333,stroke-width:2px,color:#000
    classDef processing fill:#d4edda,stroke:#333,stroke-width:2px,color:#000
    classDef output fill:#ffe1e1,stroke:#333,stroke-width:2px,color:#000

    class CSV input
    class RawHearing,TaggedHearing,ParseNode data
    class HearingLoader,HearingTagger,UtteranceTagger,HearingParser,Tokenizer,Grammar,MaskedSoftmaxClassifier,MaskedSoftmaxHelper processing
    class PredictedSections output
```