# Writing anchors and criteria

Read this before writing anchors. Source numbers refer to `sources.md`.

## Contents
1. What the evidence says
2. Criteria: how many, and separable
3. Anchor formula
4. Five worked anchor ladders
5. Pitfalls the validator catches
6. Weights and the loop

## 1. What the evidence says

- Structured interviews are the strongest common predictor of job
  performance: r = .42 in the 2022 re-estimate, ahead of job-knowledge tests
  (.40), work samples (.33) and cognitive ability (.31) [77]. The older canon
  puts structured at .51 against .38 for unstructured [18].
- Anchored rating scales are one of the named components of structure [19].
  Anchors are behavioural examples for each proficiency level, fixed in
  advance, so candidates are rated against the standard and not against each
  other [78]. Four levels (poor, borderline, solid, outstanding) with
  illustrative answers is a common layout [28].
- Rate each trait on its own before forming an overall view; "do not skip
  around" [20]. In the meeting, review each assessment separately and keep
  intuition for last [21].

## 2. Criteria: how many, and separable

- Derive criteria from the approved outcomes in the intake brief, not from an
  ideal person. Default four to seven (confirm with the owner); fewer is fine
  for a narrow role. Kahneman recommends about six traits [20]; a scorecard carries 3-8
  outcomes [22].
- **Separable:** if two criteria would be scored from the same answer, merge
  them. Each criterion needs its own evidence method.
- **Traceable:** each criterion cites the requirement(s) it tests from
  `requirements.csv`. A criterion with no requirement means the rubric scores
  something the posting does not ask for; add the requirement (usually
  test-in-process) or drop the criterion [111].
- A communication criterion names the work product and the level: "writes a
  procedure a team follows", not "strong communicator".

## 3. Anchor formula

**verb + object + scope + result**, in terms an interviewer could hear or see.

| Level | Meaning (default 1-4 scale) | Shape |
| --- | --- | --- |
| 1 | Method completed; no qualifying evidence | "Describes no <object> they <verb> themselves" |
| 2 | Partial or indirect evidence | "Took part in <object>; own <scope> not stated" |
| 3 | Clear evidence at the required scope | "<Verb> <object> at <scope the role needs>, and <how they handled a problem>" |
| 4 | Greater scope, with a stated result | "<Verb> <object> across <wider scope>, with a stated result such as <kind of result>" |

"Not assessed" is not a level. It means the method has not run, or could not
run (for example an adjustment is still being arranged).

## 4. Five worked anchor ladders

**Process ownership** (recurring operations roles)
1. Describes no recurring process they ran themselves.
2. Took part in a recurring run; own steps or deadlines not stated.
3. Names a process they owned, its steps, and how they handled a missed deadline.
4. Owned a process across teams and changed it, with a stated result such as the cycle finishing earlier.

**Reporting queries / data work**
1. Sample submitted; no query returns the required totals.
2. Returns totals but misses duplicates or date boundaries.
3. Correct result with one check for duplicates.
4. Correct result plus a reusable check, explained in writing, that removes a manual step.

**Writing for others to follow**
1. Exercise completed; nothing another person could follow.
2. Written, but missing steps, owners or exceptions.
3. A procedure a team used, with how it was kept current.
4. Adopted by more than one team and kept current through a change, with a stated result.

**Stakeholder handling**
1. Describes no disagreement they worked through.
2. Describes a disagreement someone else resolved.
3. Names the stakeholders, the trade-off, what they proposed and the outcome.
4. Resolved a cross-team conflict and changed a process so it did not recur, with a stated result.

**Incident response**
1. Describes no incident they handled.
2. Was present for an incident; own actions not stated.
3. Names the incident, their actions in order, and what they changed after.
4. Led the response, wrote the follow-up, and the fix measurably reduced repeats.

## 5. Pitfalls the validator catches

| Pitfall | Why | Fix |
| --- | --- | --- |
| Rating words ("excellent", "strong", "good") | Not observable; each interviewer reads them differently [78] | Say what the person did |
| Comparatives ("better than others", "top 10%") | Anchors fix a standard in advance; comparing candidates is not a standard [78] | Describe the behaviour at that level |
| "Not assessed" as level 1 | Treats an untested criterion as a failure | Put it in `not_assessed_rule` |
| Prestige, gaps, fit, energy, polish, native, age, postcode | Proxies for protected traits or class [79][63][64][72][45] | Remove; score the work |
| Communication with no work product | Rewards style, accent or polish | Name the document, call or artefact |

If a disallowed word is part of the job itself (for example "patient health
outcomes" for a clinical role), list it in the `allowed_terms` header line with
the reason: `allowed_terms: health (clinical role: patient health outcomes)`.
Allowed terms match the exact word or phrase only ("health" does not allow
"healthy"), and can be scoped to one criterion:
`allowed_terms: C2:billing health (the job's own metric)`.
The validator then prints a warning the approver sees, instead of an error.
The word must describe the work, never the candidate.

## 6. Weights and the loop

- Equal weight is the default. Custom weights are the owner's choice; they
  must add up to 100.
- The rubric should be testable by four or fewer evidence methods (default,
  confirm with the owner): four interviews predicted the hiring decision with
  86% confidence in Google's analysis [29]. More than four needs a
  `loop_reason`.
- Every interviewer scores independently, before any discussion [19][21].
