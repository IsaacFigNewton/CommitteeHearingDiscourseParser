# TODO
## Data cleaning and tokenization
0. map Robert's Rules of Order (RROO) to these SpeechActEnum enumerables
1. use regexes and/or a SpaCy Matcher to match RROO keyphrases in the utterances
2. replace RROO keyphrase mentions with the associated SpeechActEnum
3. add section keyphrases and associate them with SpeechActEnums
 - "others in support" indicates a possible transition to public comments

## Feature extraction
1. add the top-correlated ngrams to KeyPhraseEnum and its associated map

## Grammar expansion
1. add VoteSectionEnum grammar rules
2. add VoteSectionEnum sub-parsing/sub-classification
3. update labelled samples accordingly
4. evaluate subsection classification