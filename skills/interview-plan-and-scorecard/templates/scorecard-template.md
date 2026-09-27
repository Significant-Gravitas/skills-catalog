# Scorecard template

`scripts/make_scorecards.py` renders this layout, one file per interviewer,
with only the criteria that interviewer scores. Fill it by hand only if
Python is unavailable, and then keep the same headings and CSV columns so
candidate-interview-debrief can read it.

```markdown
# Scorecard: <role> | candidate <candidate id> | interviewer <name>

**Submit this before you read anyone else's scorecard or discuss the candidate.**
Rate each criterion on its own, using the anchors below, before writing anything overall.
Write what the candidate said or did (a quote or a specific action), not an impression.
Do not rate or note demeanour, confidence, nerves, enthusiasm, honesty, accent, appearance,
age, family, origin, health or "fit". Use `not assessed` if you did not test the criterion.

## <criterion id>: <criterion>
Slot: <n> | method: <question / work-sample / portfolio / reference> | questions: <Q ids>

| Score | Anchor (what this level looks like) |
|---|---|
| 1 | <anchor copied verbatim from the approved rubric> |
| 2 | <anchor> |
| 3 | <anchor> |
| 4 | <anchor> |
| not assessed | The criterion was not tested in this slot, or time ran out. |

- Score (1 / 2 / 3 / 4 / not assessed):
- Evidence (quote or observed action):
- Source (question / work sample / portfolio / reference):
- Confidence in this evidence (high / medium / low):

## Filing

- Submitted at (date, time and timezone):
- I filed this before seeing other interviewers' scores (yes / no):
```

## Machine-readable twin (CSV)

```
candidate_id,interviewer,slot,criterion_id,criterion,score,evidence_quote,source,confidence,submitted_at
```

- `score`: an integer on the rubric scale, or `not assessed`.
- `submitted_at`: ISO 8601 with a zone, for example `2026-10-02T16:40+01:00`.
- One row per criterion the interviewer scores. No total, average or overall
  column. If the company's process requires an overall recommendation, it is
  recorded in the ATS by the interviewer after every criterion row is complete;
  this scorecard never asks for "gut feel" [20][21].

## What a scorecard never contains

Demeanour, confidence, nerves, enthusiasm, honesty, "energy", "polish",
accent, appearance, age, family, origin, health, or "culture fit". These are
affect or protected-trait proxies, not job evidence [73][79].
