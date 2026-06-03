# Inference Rules
If the context is satisfied, then the implicature follows.
Mark

|   `valid_speaker_positions`   |   Speaker `is_legislator` |   Speaker `is_committee_member`   |   Speaker `is_bill_author`    |   Other Context                   |   Implied `SpeakerRoleEnum` |   Implied `SectionEnum`                     |
|   --------------------        |    ---------------------  |   --------------------            |    ---------------------      |   --------------------      |    ---------------------    |   --------------------    |
|   N/A                         |    N/A                    |   False                           |    N/A                        |   N/A                         |    `PRESENTER` or `EXPERT`  |   `PRESENTATION` or `EXPERT_TESTIMONY`      |


# TODO: Parse the following items as table entries above
if a non-member of a committee is speaking at a hearing, they are either an expert or a presenter (entry already added)

non-presiding chairs should be treated the same as SpeakerRoleEnum.MEMBER
```
∀s:Speaker. (has_position(s, CHAIRMAN) ∨ has_position(s, VICE_CHAIRMAN)) ∧ ¬presiding_at(s, h)
→
should_be_classified_as(s, COMMITTEE_MEMBER)
```

if the primary author (as indicated by bills.csv) is present and they're the only non-committee-member legislator, then they will be a presenter
```
∃s:Speaker. (is_author(s, bill(h)) ∧ is_legislator(s) ∧ ¬is_committee_member(s) ∧ ∀s':Speaker. (¬(s' = s) → ¬is_author(s', bill(h)) ∨ is_committee_member(s')) )
→
has_role(s, PRESENTER)
```

if a non-legislator's name is mentioned before their first utterance and they have a longer utterance than average, they are probably an expert
```
∀s:Speaker, u:Utterance. ¬is_legislator(s) ∧ first_utterance(s, u) ∧ mentioned_before(s, u) ∧ len(u) > average_utterance_length
→
has_role(s, EXPERT)
```

first expert utterance to the last expert utterance is the whole expert testimony section (even if it includes legislator discussion in the middle)
```
∀h:Hearing, s1, s2, s3:Speaker, u1,u2,u3:Utterance. speaker(u1) = s1 ∧ speaker(u3) = s3  ∧ role(s1) = EXPERT ∧ role(s3) = EXPERT ∧ u1.uid ≤ u2.uid ≤ u3.uid
→
in_section(u2, EXPERT_TESTIMONY)
```

any committee member may file motions
```
∀s:Speaker, m:Motion. is_committee_member(s)
→
can_file(s, m)
```

experts' names will always be mentioned before their first utterance.
```
∀s:Speaker. has_role(s, PUBLIC) ∨ has_role(s, EXPERT) ∧ 
  ∃mention:NameMention, u:Utterance. is_first_utterance(u, s) ∧
  mentions(mention, s) ∧ precedes(mention, u) → has_role(s, EXPERT)
```

members of the public (and maybe experts? ask prof) will always introduce themselves with their full name or part of their name
```
∀s:Speaker. has_role(s, PUBLIC) ∨ has_role(s, EXPERT) ∧ ∃mention:NameMention, u:Utterance. is_first_utterance(u, s) ∧ mentions(mention, s) ∧ precedes(mention, u)
→
has_role(s, EXPERT)
```

members of the public will never be mentioned before their first utterance and they will mention their name within their first utterance (according to sofija and pallavi)
```
∀s:Speaker. has_role(s, PUBLIC) ∨ has_role(s, EXPERT) ∧ ¬∃mention:NameMention, u:Utterance. is_first_utterance(u, s) ∧ mentions(mention, s) ∧ precedes(mention, u)
→
has_role(s, PUBLIC)
```

# Other Rules (parse and integrate later)

a member of the public will never have more than 3 utterances
```
∀s:Speaker. has_role(s, PUBLIC)
→
|{u:Utterance | uttered_by(u, s)}| ≤ 3
```

speaker name mentions may be misspelled
```
∀mention:NameMention. [speaker name mentions may be misspelled]
```

if a statement by the presiding chair or staff is purely for demarcating a transition, you can leave it untagged/sectioned
```
∀u:Utterance, s:Speaker. (has_role(s, PRESIDING_CHAIR) ∨ [is staff](s)) ∧ [purely demarcates transition](u)
→
[can leave untagged/unsectioned](u)
```

there will always be exactly 1 presiding chair per hearing (chair, co-chair, vice-chair are only ones allowed to preside)
```
∀h:Hearing. ∃!c:Speaker. (presiding_at(c, h) ∧ (has_position(c, CHAIRMAN) ∨ has_position(c, VICE_CHAIRMAN)))
```

utterances by members of the public will never preceed utterances by experts
```
∀u₁,u₂:Utterance. has_role(speaker(u₁), PUBLIC) ∧ has_role(speaker(u₂), EXPERT)
→
¬precedes(u₁, u₂)
```

# To clarify with Khosmood
- will experts ever introduce themselves, or will they always be introduced by committee staff/members?
