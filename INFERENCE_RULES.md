# Inference Rules
If the context is satisfied, then the implicature follows.

| Description | `ValidPositions` | `Speaker.is_legislator` | `Speaker.is_committee_member` | `Speaker.is_presiding` | `Speaker.has_position_UNKNOWN` | `Speaker.is_mentioned_prior` | `Speaker.existing_role` | `Utterance.is_first_by_speaker` | `Utterance.is_self_introduction` | `Utterance.order_relation` | Other Context | Implied `SpeakerRoleEnum` | Implied `SectionEnum` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| If a non-member of a committee is speaking at a hearing, they are either an expert or a presenter. | - | - | False | - | - | - | - | - | - | - | - | `PRESENTER` or `EXPERT` | `PRESENTATION` or `EXPERT_TESTIMONY` |
| Non-presiding chairs should be labelled the same as committee members. | `CHAIRMAN` or `VICE_CHAIRMAN` | - | - | False | - | - | - | - | - | - | - | `COMMITTEE_MEMBER` | - |
| If the primary author is present and is the only non-committee-member legislator, then they are a presenter. | - | True | False | - | - | - | - | - | - | - | Primary author is indicated by `bills.csv`; all other bill authors, if present, are committee members.; `Speaker.is_bill_author`: True; `Hearing.unique_noncommittee_author`: True | `PRESENTER` | - |
| The section from the first expert utterance through the last expert utterance is expert testimony. | - | - | - | - | - | - | - | - | - | `first_expert_utterance.uid <= u.uid <= last_expert_utterance.uid` | - | - | `EXPERT_TESTIMONY` |
| Members of the public, and sometimes experts, introduce themselves. | - | - | - | - | - | - | - | True | True | - | - | `PUBLIC` or `EXPERT` | - |
| Experts' names are always mentioned before their first utterance and they will usually utter more than 3 sentences. | - | - | - | - | - | True | `PUBLIC` or `EXPERT` | True | True | - | `Speaker.total_sentences`: `> 3` | `EXPERT` | - |
| Members of the public are never mentioned before their first utterance and will never utter more than 3 sentences. | - | - | - | - | - | False | `PUBLIC` or `EXPERT` | True | True | - | `Speaker.total_sentences`: `<= 3` | `PUBLIC` | - |
| If an utterance is purely transitional, leave it untagged/unsectioned. | - | - | - | - | - | - | - | - | - | - | `Utterance.is_transition`: True | - | `None` |
| Any committee member may file motions; if an unknown-position speaker files a motion, infer committee membership. | - | - | - | - | True | - | - | - | - | - | Speaker filed a motion; fuzzy match against `committeeRosters.csv` when `people.csv` does not contain the `pid`; another speaker has role `PRESIDING_CHAIR`.; `Utterance.is_motion`: True | `COMMITTEE_MEMBER` | - |
| If every speaker has a known position and there is only one chair or vice chair, that speaker is the presiding chair. | `CHAIRMAN` or `VICE_CHAIRMAN` | - | - | - | False | - | - | - | - | - | `Hearing.has_unknown_speaker`: False; `Hearing.unique_chair_or_vice_chair`: True | `PRESIDING_CHAIR` | - |
| Utterances by members of the public never precede utterances by experts. | - | - | - | - | - | - | Earlier speaker: candidate `PUBLIC`<br>Later speaker: candidate `EXPERT` | - | - | `u1 precedes u2` | Rule is the contrapositive of the natural-language statement. | Not both: earlier `PUBLIC` and later `EXPERT` | - |
# Additional Notes
- Names may be misspelled
- There will always be exactly one presiding chair per hearing.