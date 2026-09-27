# Rubric: <Role title>
role_slug: <role-slug>
version: 1
status: draft
approved_by:
approved_on:
approval_quote:
scale: 1-4
weighting: equal
loop_methods: <e.g. resume screen; SQL work sample; interview 1; interview 2>
loop_reason:

<!-- The header lines above and the column row below are the contract that
     validate_rubric.py, approve_rubric.py and resume-screening read. Keep them
     exactly. One row per criterion. Anchors describe what the person did,
     at each level, in observable terms. Fixed before any resume is read. -->

## Criteria

| criterion_id | criterion | outcome_supported | requirement_ids | evidence_sources | anchor_1 | anchor_2 | anchor_3 | anchor_4 | not_assessed_rule | confirm_method | scorer | weight |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | <what is tested> | <outcome from the intake brief> | <R1;R2 from requirements.csv> | <resume; work sample; interview> | <method completed, no qualifying evidence> | <partial or indirect evidence> | <clear evidence at the required scope> | <clear evidence at greater scope, with a stated result> | <when to mark not assessed> | <question or work sample> | <named person> | equal |

## Evidence rules

- Scale (default, unless the company uses its own): one to four.
  - 1: the evidence method was completed and found no qualifying evidence.
  - 2: partial or indirect evidence.
  - 3: clear evidence at the required scope.
  - 4: clear evidence at greater scope, with a stated result.
- "Not assessed": the source or method was unavailable, or the criterion was
  not yet tested. Never 1 or 0. A resume that simply omits a criterion is "not
  assessed" until the interview or work sample tests it.
- Each criterion is scored on its own, from its own evidence, before any
  overall view is formed.
- Scores support a human decision; they never advance or reject anyone automatically.

## Disallowed signals

Protected traits and proxies: names, photos, addresses or postcodes, commute,
graduation years, employment gaps, accents, school prestige, employer
prestige, family status, health, writing polish or AI-writing style, shared
interests, likability, "energy", "culture fit".

## Approval

Weighting: <equal | custom>, chosen by <owner>.
Approved by: <name>, <date>, "<the owner's approval sentence>".
