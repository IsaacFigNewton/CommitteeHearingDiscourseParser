# CommitteeHearingDiscourseParser

A parser for California legislative committee hearing transcripts, modeling the discourse structure of bill discussions.

## Data Model Overview

The project models committee hearings using several core dataclasses:

- **[Hearing](src/dataclasses/Hearing.py)**: Base class for committee hearings with metadata, speakers, and utterances
- **[TaggedHearing](src/dataclasses/Hearing.py)**: Extends Hearing with tagged utterances containing extracted features
- **[Speaker](src/speakers/Speaker.py)**: Represents a person speaking at the hearing with their position and role (based on UK Parliament's agent ontology)
- **[OralContribution](src/dataclasses/OralContribution.py)**: Represents a single utterance by a speaker (based on UK Parliament's oral contribution ontology)
- **[TaggedOralContribution](src/dataclasses/OralContribution.py)**: Extends OralContribution with extracted features and metadata
- **[FlatTaggedOralContribution](src/dataclasses/OralContribution.py)**: Flattened version combining TaggedOralContribution with speaker properties for classification

Supporting classes and enums:
- **[SpeakerPositionEnum](src/speakers/enums/SpeakerPositionEnum.py)**: Speaker positions with hierarchical authority levels (Secretary, Presiding Chair, Chairman, Vice Chairman, Committee Member, Bill Author, Legislator, Expert, Nonlegislator, Public)
- **[RoleProperties](src/speakers/interfaces/SpeakerProperties.py)**: Base properties for speaker roles (can_file_motions, is_presenter, speaker_position)
- **[SpeakerProperties](src/speakers/interfaces/SpeakerProperties.py)**: Extends PositionRoleProperties with utterance tracking (first_mention_uid, first_uid, last_uid)
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
    Hearing -->|fields| hearing_fields["hid, bid, cid, cname, hearing_date, state,<br/>speakers: Dict[int, Speaker],<br/>utterances: List[OralContribution]"]
    TaggedHearing[TaggedHearing]
    TaggedHearing -->|extends| Hearing
    TaggedHearing -->|overrides| tagged_fields["utterances: List[TaggedOralContribution]"]

    %% OralContribution hierarchy
    OralContribution[OralContribution]
    OralContribution -->|fields| oral_fields["uid, pid, text"]
    TaggedOralContribution[TaggedOralContribution]
    TaggedOralContribution -->|extends| OralContribution
    TaggedOralContribution -->|adds| tagged_oral_fields["pids_mentioned, bids_mentioned, relative_position,<br/>sent_count, speech_act_cues, section_cues, section"]
    FlatTaggedOralContribution[FlatTaggedOralContribution]
    FlatTaggedOralContribution -->|extends| TaggedOralContribution
    FlatTaggedOralContribution -->|extends| RoleProperties

    %% Speaker property hierarchy
    RoleProperties[RoleProperties]
    RoleProperties -->|fields| role_fields["can_file_motions, is_presenter, speaker_position"]
    SpeakerProperties[SpeakerProperties]
    SpeakerProperties -->|extends| RoleProperties
    SpeakerProperties -->|adds| tracking_fields["first_mention_uid, first_uid, last_uid"]
    Speaker[Speaker]
    Speaker -->|extends| SpeakerProperties
    Speaker -->|adds| speaker_fields["pid, first_name, last_name"]

    %% Other classes
    ParseNode[ParseNode]
    ParseNode -->|fields| parse_fields["symbol: TOP | SectionEnum | SpeakerPositionEnum,<br/>children: Optional[List[ParseNode]],<br/>utterance_indices: Optional[List[int]]"]

    %% Styling
    classDef dataclass fill:#e1f5ff,stroke:#333,stroke-width:2px,color:#000
    classDef fieldNode fill:#f0f0f0,stroke:#666,stroke-width:1px,color:#000,stroke-dasharray: 5 5

    class Hearing,TaggedHearing,OralContribution,TaggedOralContribution,FlatTaggedOralContribution,RoleProperties,PositionRoleProperties,SpeakerProperties,Speaker,ParseNode dataclass
    class hearing_fields,tagged_fields,oral_fields,tagged_oral_fields,role_fields,position_fields,tracking_fields,speaker_fields,parse_fields fieldNode
```

## Architecture Diagram

```mermaid
graph TD
    %% Data flow
    CSV[CSV Files<br/>Digital Democracy Corpus] -->|load| HearingLoader

    HearingLoader -->|creates| Hearing[Hearing<br/>with OralContributions]

    Hearing -->|tag features| HearingTagger
    subgraph HearingTagger[HearingTagger]
        OralContributions -->|input to| UtteranceTagger
    end

    HearingTagger -->|creates| TaggedHearing
    subgraph TaggedHearing[TaggedHearing]
        TaggedOralContributions
    end
    TaggedHearing -->|input to| HearingParser

    subgraph HearingParser[HearingParser]
        Features[Feature DataFrame] -->|input to| Pipeline

        subgraph Pipeline["sklearn Pipeline"]
            direction TB

            CT[ColumnTransformer] -->|text column| TfidfVec[TfidfVectorizer]
            CT -->|categorical columns| OHE[OneHotEncoder]
            CT -->|numeric columns| Scaler[StandardScaler]

            TfidfVec -->|sparse matrix| FeatureMatrix[Combined Feature Matrix]
            OHE -->|sparse matrix| FeatureMatrix
            Scaler -->|dense array| FeatureMatrix

            FeatureMatrix -->|input to| MC

            subgraph MC[MaskedClassifier]
                direction TB

                BE[BaseEstimator]
                BE -->|outputs| RawProbs[Raw SectionEnum class probabilities]

                subgraph MSH[MaskedSoftmaxHelper]
                    direction TB

                    Tokenizer[Tokenizer<br/>CYK parsing]
                    Tokenizer -->|uses| Grammar[Grammar<br/>CNF production rules]
                    Tokenizer -->|generates| ParseNode[ParseNode<br/>parse tree]
                end

                MSH -->|masks| RawProbs
            end
        end
        MC --> NoisyPredictions[Noisy SectionEnum Predictions]
        NoisyPredictions -->|smooth outliers| SmoothedSectionLabels[Smoothed SectionEnum Predictions]
    end
    SmoothedSectionLabels -->|returns| PredictedSections[Final Section Labels<br/>per utterance]

    %% Styling
    classDef input fill:#fff4e1,stroke:#333,stroke-width:2px,color:#000
    classDef data fill:#e1f5ff,stroke:#333,stroke-width:2px,color:#000
    classDef processing fill:#d4edda,stroke:#333,stroke-width:2px,color:#000
    classDef output fill:#ffe1e1,stroke:#333,stroke-width:2px,color:#000

    class CSV input
    class Hearing,TaggedHearing,OralContributions,TaggedOralContributions,Features,FeatureMatrix,ParseNode,RawProbs,NoisyPredictions,SmoothedSectionLabels,PredictedSections data
    class HearingLoader,HearingTagger,UtteranceTagger,HearingParser,CT,TfidfVec,OHE,Scaler,MC,BE,MSH,Tokenizer,Grammar processing

    %% Softer HSV-inspired subgraph fills
    style HearingParser fill:#ffd6d6,stroke:#333,stroke-width:2px,color:#000
    style Pipeline fill:#e5ffd6,stroke:#333,stroke-width:2px,color:#000
    style MC fill:#d6fffd,stroke:#333,stroke-width:2px,color:#000
    style MSH fill:#ead6ff,stroke:#333,stroke-width:2px,color:#000
```