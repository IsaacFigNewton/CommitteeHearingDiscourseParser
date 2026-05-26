# Speaker roles and associated actions
## Committee chair
 - Introduces name of bill under discussion and references bill presenter
  - "She'll be presenting AB 10, file item number one."
 - Thanks experts and opens floor to public comments
  - "Others in support, please come forward, state your name, affiliation, and position on the bill"
 - Closes public comments section and yields floor to other assemblymembers for bill discussion
  - "All right, thank you. Any others in support? Seeing no others in support, any opposition to the bill? Seeing no opposition, any comments from the Committee Members?"

## Bill presenter
 - Usually primary bill author?
  - Introduces bill with "Thank you. Good afternoon Chair and members. I'm here presenting AB 10"

## Section notes
 - LegislatorDiscussion section usually has back-and-forth dialogue with bill author


# EDA notes
## Phrase and keyword extraction
 1. Tag and replace named entities with references to their associated types (ex: AB 10 -> [BILL])
 2. get bigram, trigram, n-gram frequencies
 3. filter down to most promising/relevant ngrams
  - correlation between ngram appearance and speaker role, relative position of utterance in transcript

## Utterance classification
 1. Vectorize each utterance using:
  - MOHE'd ngram presence
  - OHE'd speaker role
  - relative position of utterance within bill discussion (normalize between 0.0 to 1.0)
 2. Train a binary classifier to tag each utterance with following:
  - BIO tags:           Beginning, Inside, Outside tag
   - Can have 2 consecutive Beginning-tagged utterances but no 2 consecutive Inside or Outside utterances (to support single-utterance sections)
  - Discussion section: Intro, Presentation, LegislatorDiscussion, ExpertTestimony, PublicComments, ClosingRemarks, Vote, Outro