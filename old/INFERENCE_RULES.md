# Inference Rules
If the context is satisfied, then the implicature follows.

| Description | `ValidPositions` | `ValidRoles` | `Speaker.is_legislator` | `Speaker.is_committee_member` | `Speaker.is_presiding` | `Speaker.is_bill_author` | `Speaker.is_mentioned_prior` | `Utterance.is_first_by_speaker` | `Utterance.is_self_introduction` | `Utterance.order_relation` | Other Context | Implied `SpeakerRoleEnum` | Implied `SectionEnum` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| If a non-member of a committee is speaking at a hearing, they are either an expert or a presenter. | `LEGISLATOR` | - | - | False | - | - | - | - | - | - | - | `PRESENTER` or `EXPERT` | `PRESENTATION` or `EXPERT_TESTIMONY` |
| Non-presiding chairs should be labelled the same as committee members. | `CHAIRMAN` or `VICE_CHAIRMAN` | - | - | - | False | - | - | - | - | - | - | `COMMITTEE_MEMBER` | - |
| If a primary author is present and is the only non-committee-member legislator, then they are a presenter. | `LEGISLATOR` | - | True | False | - | True | - | True | - | - | `Hearing.unique_noncommittee_author`: True | `PRESENTER` | `PRESENTATION` |
| The section from the first expert utterance through the last expert utterance is expert testimony. | - | `PRESIDING_CHAIR` or `COMMITTEE_MEMBER` or `SECRETARY` or `EXPERT`| - | - | - | - | - | - | - | `first_expert_utterance.uid <= u.uid <= last_expert_utterance.uid` | - | - | `EXPERT_TESTIMONY` |
| Members of the public, and sometimes experts, introduce themselves. | `NONLEGISLATOR` or `LEGISLATOR`  | - | - | - | - | - | - | True | True | - | - | `PUBLIC` or `EXPERT` | - |
| Experts' names are USUALLY mentioned before their first utterance and they will usually utter more than 3 sentences. | `NONLEGISLATOR` or `LEGISLATOR` | - | - | False | False | False | True | True | True | - | `Speaker.total_sentences`: `> 3` | `EXPERT` | - |
| Members of the public are never mentioned before their first utterance and will never utter more than 3 sentences. | `NONLEGISLATOR` | - | False | False | False | False | False | True | True | - | `Speaker.total_sentences`: `<= 3` | `PUBLIC` | - |
| If an utterance is purely transitional, leave it untagged/unsectioned. | - | `PRESIDING_CHAIR` or `COMMITTEE_MEMBER` or `SECRETARY` | - | - | - | - | - | - | - | - | `Utterance.is_transition`: True | - | `None` |
| Any committee member may file motions, so if an unknown-position speaker files a motion, infer committee membership. | `UNKNOWN` | - | - | - | - | - | - | - | - | - | `Utterance.is_motion`: True | `COMMITTEE_MEMBER` | - |
| If every speaker has a known position and there is only one chair or vice chair, that speaker is the presiding chair. | `CHAIRMAN` or `VICE_CHAIRMAN` | - | True | True | - | - | - | - | - | - | `Hearing.has_unknown_speaker`: False; `Hearing.unique_chair_or_vice_chair`: True | `PRESIDING_CHAIR` | - |
| Utterances by members of the public never precede utterances by experts. | - | `EXPERT` or `PUBLIC` | - | False | False | False | - | - | - | `u1 precedes u2` | Rule is the contrapositive of the natural-language statement. | `u1 != PUBLIC` and `u2 != EXPERT` | - |

# Additional Notes
- Names may be misspelled
- There will always be exactly one presiding chair per hearing.
