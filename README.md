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
    Hearing -->|fields| hearing_fields["hearing, speaker, and utterance metadata"]
    TaggedHearing[TaggedHearing]
    TaggedHearing -->|extends| Hearing
    TaggedHearing -->|includes| tagged_fields["additional utterance metadata"]

    %% OralContribution hierarchy
    OralContribution[OralContribution]
    OralContribution -->|fields| oral_fields["uid, pid, text"]
    TaggedOralContribution[TaggedOralContribution]
    TaggedOralContribution -->|extends| OralContribution
    TaggedOralContribution -->|adds| tagged_oral_fields["additional utterance metadata"]
    FlatTaggedOralContribution[FlatTaggedOralContribution]
    FlatTaggedOralContribution -->|extends| TaggedOralContribution
    FlatTaggedOralContribution -->|extends| RoleProperties

    %% Speaker property hierarchy
    RoleProperties[RoleProperties]
    RoleProperties -->|fields| role_fields["speaker metadata"]
    SpeakerProperties[SpeakerProperties]
    SpeakerProperties -->|extends| RoleProperties
    SpeakerProperties -->|adds| tracking_fields["utterance-based speaker metadata"]
    Speaker[Speaker]
    Speaker -->|extends| SpeakerProperties
    Speaker -->|adds| speaker_fields["speaker identification metadata"]

    %% Other classes
    ParseNode[ParseNode]
    ParseNode -->|fields| parse_fields["grammar symbol, utterance span, and any child nodes"]

    %% Styling
    classDef dataclass fill:#e1f5ff,stroke:#333,stroke-width:2px,color:#000
    classDef fieldNode fill:#f0f0f0,stroke:#666,stroke-width:1px,color:#000,stroke-dasharray: 5 5

    class Hearing,TaggedHearing,OralContribution,TaggedOralContribution,FlatTaggedOralContribution,RoleProperties,PositionRoleProperties,SpeakerProperties,Speaker,ParseNode dataclass
    class hearing_fields,tagged_fields,oral_fields,tagged_oral_fields,role_fields,position_fields,tracking_fields,speaker_fields,parse_fields fieldNode
```

## Data Flow Diagram

```mermaid
flowchart TD
    %% External entity / source
    CSV[/"CSV Files<br/>Digital Democracy Corpus"/]

    %% Main processes
    P1(("Load<br/>Hearings"))
    P6(("Smooth<br/>Predictions"))

    %% Data stores
    D1[(Hearing + OralContributions)]
    D5[(CNF Grammar Productions)]
    MASKED[(Masked Probability Store)]

    %% Outputs
    OUT[/"Final Section Labels<br/>per utterance"/]

    CSV -->|raw hearing rows| P1
    P1 -->|hearing objects| D1
    subgraph PIPELINE [Pipeline]
        direction TD

        HL -. implements .- P1

        %% Tagging subgraph: TD inside
        subgraph TAGGING [Tagging]
            direction TD
            
            HT["HearingTagger"]
            UT["UtteranceTagger"]
            HT -. coordinates .- P2
            UT -. tags .- P2
            HP -. runs .- P3

            P2(("Tag<br/>Utterance Features"))
            D2[(TaggedHearing + TaggedOralContributions)]
            P2 -->|tagged oral contributions| D2
        end

        %% Feature processing + classification + masking grouped TD
        subgraph SECTION_MODEL [Feature Processing, Classification, and Masking]
            direction TD

            %% Feature processing subgraph: TD inside
            subgraph FEATURES [Feature Processing]
                direction TD
                P3(("Build<br/>Feature Matrix"))
                D3[(Feature DataFrame)]
                T1["TfidfVectorizer"]
                T2["OneHotEncoder"]
                T3["StandardScaler"]
                D4[(Transformed Feature Matrix)]

                P3 -->|feature dataframe| D3
                D3 -->|text column| T1
                D3 -->|categorical columns| T2
                D3 -->|numeric columns| T3
                T1 -->|text features<br/>sparse matrix| D4
                T2 -->|categorical features<br/>sparse matrix| D4
                T3 -->|numeric features<br/>dense array| D4
            end

            HP["HearingParser"]
            HP -. runs .- P4
            HP -. runs .- P6

            %% Classification subgraph: TD inside
            subgraph CLASSIFICATION [Classification]
                direction TD
                P4(("Predict<br/>Section Labels"))
                RAW[(Raw Probability Store)]
                MC["MaskedClassifier"]
                MC -. wraps .- P4
                BE["BaseEstimator"]
                BE -. estimates .- P4

                P4 -->|raw SectionEnum class probabilities| RAW
            end

            %% Masking subgraph: TD inside
            subgraph MASKING [Grammar Masking]
                direction TD
                
                MSH["MaskedSoftmaxHelper"]
                MSH -. implements .- P5

                TOK(("Tokenize / CYK Parse"))
                PN[(Parse Tree<br/>ParseNode)]
                P5(("Apply<br/>Grammar Mask"))

                TOK -->|parse tree| PN
                PN -->|valid masks| P5
            end

            D4 -->|combined features| P4
            RAW -->|unmasked probabilities| P5
        end

        %% Main data flow: LR outside

        D1 -->|oral contributions| P2
        D2 -->|tagged hearing data| P3

        D5 -->|production rules| TOK
        D5 -->|valid section transitions| P5

        P5 -->|grammar-constrained probabilities| MASKED
        MASKED -->|noisy SectionEnum predictions| P6
        
    end
    P6 -->|smoothed SectionEnum predictions| OUT

    %% Implementation annotations
    HL["HearingLoader"]

    %% Styling
    classDef external fill:#fff4e1,stroke:#333,stroke-width:2px,color:#000
    classDef process fill:#d4edda,stroke:#333,stroke-width:2px,color:#000
    classDef datastore fill:#e1f5ff,stroke:#333,stroke-width:2px,color:#000
    classDef output fill:#ffe1e1,stroke:#333,stroke-width:2px,color:#000
    classDef impl fill:#f4f4f4,stroke:#777,stroke-width:1px,color:#000,stroke-dasharray:4 4

    class CSV external
    class P1,P2,P3,P4,P5,P6,T1,T2,T3,TOK process
    class D1,D2,D3,D4,D5,RAW,MASKED,PN datastore
    class OUT output
    class HL,HT,UT,HP,BE,MC,MSH impl
```