# Requirement tests: the four-way sort and the must-have tests

Source numbers refer to `sources.md`.

## Contents
1. Why cut requirements
2. The four-way sort
3. The three-part must-have test
4. Common requirements and what to do with them
5. From requirement to rubric

## 1. Why cut requirements

- Employers "piled on job requirements" until almost no applicant met them
  all, and only about 40% of employers test skills [36].
- Skills-based hiring mostly fails in practice: fewer than 1 in 700 hires
  benefited from a dropped degree requirement, and about 45% of firms changed
  in name only [111]. The failure mode is a requirement removed from the
  posting but still used in screening. The rule that follows: every must-show
  requirement in the posting maps to a rubric criterion that the screen and the
  interview actually score, and nothing else is screened on.
- A scorecard states the mission and 3-8 measurable outcomes before any search
  [22]; performance objectives replace skills lists [26].

## 2. The four-way sort

For each requirement, ask the hiring manager: **what work would fail without it?**

| Group | Test | Where it goes |
| --- | --- | --- |
| must-show | The work fails in the first months without it, and it can be shown before hire | JD "What we need to see"; a rubric criterion; screened |
| test-in-process | Needed, but a resume cannot show it; a work sample or interview can | JD "Useful" with how it is tested; a rubric criterion; not screened on the resume |
| learn-after-hire | Needed later; training or support exists | JD "Useful, and we will help you build it", or left out; never screened |
| removed | No clear link to the work, or a personality label | Out of the JD and the rubric; listed with the reason for the owner |

A requirement moves to "removed" unless the hiring manager gives a
job-related reason. Record the reason in `what_fails_without_it`.

## 3. The three-part must-have test

A must-show requirement must be all three [49]:

- **Objective:** two reviewers with the same resume would agree whether it is met.
- **Non-comparative:** it is met or not on its own, never "the strongest",
  "top 10%", or "better than".
- **Job-relevant:** tied to an outcome in the intake brief.

The regulation this pattern comes from is being rescinded for federal
contractors on 2026-10-26 [50]; the three tests remain sound practice
(practitioner judgement, unsourced).

## 4. Common requirements and what to do with them

| Requirement as given | Usual result | Why |
| --- | --- | --- |
| "Degree in X" | removed, or "or equivalent experience" with a work reason | Degree screens predict little and dropping them changes nothing unless the screen changes too [111][18] |
| "5+ years of experience" | Replace with the outcome behind it ("has run a monthly close end to end") | Years are a proxy; requirement inflation [36]; an experience ceiling can be an age proxy [34][45] |
| "Knows <our tool>" | learn-after-hire, or "a tool like it" | Tool training usually exists; long tool lists narrow the pool (practitioner judgement, unsourced) |
| "Culture fit", "rockstar", "self-starter" | removed; ask for the behaviour meant | "Culture fit" works as a class proxy [79]; labels are not evidence |
| "Native English speaker" | "writes <named documents> in English" | National-origin proxy (practitioner judgement, unsourced) |
| "Lives within 20 miles" / postcode | Write work terms: onsite days, hours | ZIP code is named as a proxy in Illinois law [72] |
| "Must be able to lift 50 lb" | Keep only if essential; add "with or without reasonable accommodation" | ADA pre-offer rules [35][46] |
| "Recent graduate", "young", "digital native" | removed; name the level or the skill | ADEA help-wanted rule [45]; age proxy [34] |

The "20 miles" and "50 lb" figures are examples of what owners write, not recommendations.

## 5. From requirement to rubric

`requirements.csv` is the hand-off. hiring-rubric-design's validator reads it,
checks that every must-show row has a criterion, and writes the criterion id
back into `rubric_criterion_id`. Until that column is filled, the approval
checklist line "every must-show requirement maps to a rubric criterion" stays open.
