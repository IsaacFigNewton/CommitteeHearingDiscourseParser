# TODO
## Data cleaning and tokenization
0. associate authorship info (in bills.csv) with initial speaker parsing
1. enumerate the different kinds of speech acts in [[SpeechActEnum.py]]
2. map Robert's Rules of Order (RROO) to these SpeechActEnum enumerables (use a dictionary?)
3. use regexes and/or a SpaCy Matcher to match RROO keyphrases in the utterances
4. replace RROO keyphrase mentions with the associated SpeechActEnum
5. use regexes and/or a SpaCy Matcher to match speaker name and bill name mentions in the utterances
6. replace speaker name mentions with the associated PIDs or SpeakerTypeEnum values
7. replace bill name (or sometimes section number) mentions with the associated BID or a "BILL" token
8. identify other common keyphrases (or stophrases like "Thank you") and associate them with some KeyPhraseEnum
9. map common keyphrases and stop-phrases to these KeyPhraseEnum enumerables (use a dictionary?)
10. use regexes and/or a SpaCy Matcher to match KeyPhraseEnum mentions in the utterances
11. replace KeyPhraseEnum mentions with the associated KeyPhraseEnum values
12. remove stop-phrases

## Feature extraction
1. tokenize the cleaned utterances
2. perform ngram TF-IDF with ngrams of length > 1 (maybe also add-one smoothing?)
3. get correlation of utterances' TF-IDF embeddings with:
 - Speaker: speaker type
 - Relative position in transcript: OralContribution.uid / len(Hearing.utterances)
4. filter correlated ngrams
5. add the top-correlated ngrams to KeyPhraseEnum and its associated map

## Classification model
evaluate based on coverage and performance against manually-annotated ground-truth sample of 5 transcripts?
1. re-tokenize utterances using the new RROO, speaker name, bill name, and ngram maps
2. use manual rules for speaker role induction
3. vectorize utterances using:
 - TF-IDF token embeddings
 - speaker type
 - speaker role
 - relative position of utterance within transcript
 - relative length of utterance within transcript (if it's one of the longest utterances, it's probably a bill presentation)
4. perform section BIO tagging on OralContributions