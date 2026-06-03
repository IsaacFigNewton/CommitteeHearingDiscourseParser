# Inference Rules
If the context is satisfied, then the implicature follows.
Mark

|   `valid_speaker_positions`   |   Speaker `is_legislator` |   Speaker `is_committee_member`   |   Speaker `is_bill_author`    |   Other Context                   |   Implied `SpeakerRoleEnum` |   Implied `SectionEnum`                     |
|   --------------------        |    ---------------------  |   --------------------            |    ---------------------      |   --------------------      |    ---------------------    |   --------------------    |
|   N/A                         |    N/A                    |   False                           |    N/A                        |   N/A                         |    `PRESENTER` or `EXPERT`  |   `PRESENTATION` or `EXPERT_TESTIMONY`      |


# TODO: Parse the following items as table entries above
if a non-member of a committee is speaking at a hearing, they are either an expert or a presenter (entry already added)
there will always be exactly 1 presiding chair per hearing (chair, co-chair, vice-chair are only ones allowed to preside)
non-presiding chairs should be treated the same as SpeakerRoleEnum.MEMBER
vote roll call can be done by any committee staff member
if the primary author (as indicated by bills.csv) is present and they're the only non-committee-member legislator, then they will be a presenter
if a non-legislator's name is mentioned before their first utterance, they are probably an expert
if a possible expert has a long utterance, they're probably an expert
a member of the public will never have more than 3 utterances
he recommends we treat the first expert utterance to the last expert utterance as the whole expert testimony section (even if it includes legislator discussion in the middle)
utterances by members of the public will never preceed utterances by experts
if a statement by the presiding chair or staff is purely for demarcating a transition, you can leave it untagged/sectioned
non-chair committee members can file motions, but non-committee members cannot
presenters, if they are committee members, may file motions
members of the public will always introduce themselves with their full name or part of theirname
speaker name mentions may be misspelled 
Only individuals that are non-legislators and non-staff may introduce themselves
experts' names will always be mentioned before their first utterance.
members of the public will never be mentioned before their first utterance and they will mention their name within their first utterance