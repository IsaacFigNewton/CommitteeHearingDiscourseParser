# TODO
## Data cleaning and tokenization
0. Update README.md and DATAMODEL.md
1. map Robert's Rules of Order (RROO) to these SpeechActEnum enumerables
2. use regexes and/or a SpaCy Matcher to match RROO keyphrases in the utterances
3. replace RROO keyphrase mentions with the associated SpeechActEnum

## Feature extraction
1. . get correlation of utterances' TF-IDF embeddings with possible SectionEnums based on other SectionEnum requirements, speaker inference rules
 - terms are tokens
 - docs are loose requirement-based section spans
  - get initial bounds for section spans by taking earliest possible start, latest possible end
  - ex: if legislator_discussion has largest possible span of (4, 7) and expert_testimony has largest possible span of (3, 9), treat each as a separate instance of their own doc type and get 2 TF-IDF embeddings for tokens in (3, 4)
2. filter down to top correlated ngrams
3. add the top-correlated ngrams to KeyPhraseEnum and its associated map