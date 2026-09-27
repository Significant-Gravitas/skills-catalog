# Worked example: Billing Operations Lead loop (fictional)

Everything here is fictional: Acme Ltd, Maya Chen (hiring manager and final
decision-maker), Tom Reyes, Priya Nair, Luis Ortega, Jo Patel (people team).
The files beside this walkthrough are the real inputs; run the commands to
see the same output.

## Request

> Maya: "Rubric v1 is approved. Plan the loop for Billing Ops Lead. I've put
> my draft loop and questions in the folder. Luis wants to join too, and I
> added a 'team fit' round at the end. 2 hours total."

## Step 1. Load the approved rubric and plan

`~/workspace/hiring/billing-ops-lead/hiring-plan.md` records rubric v1
approved by Maya Chen on 2026-09-24, the accommodation contact (Jo Patel,
people@acme.example), and no AI-use policy yet. The rubric has 3 criteria;
it is saved as `rubric.csv` with the anchors copied verbatim.

## Step 2. Check Maya's draft loop (hard case)

```
python3 scripts/check_loop.py rubric.csv loop-draft.csv --loop-minutes 120
```

```
ERROR   slot 5: criterion 'C4' is not in the rubric. The loop may not add criteria.
ERROR   criterion C1 (...): scored in 2 slots ['1 (Maya Chen)', '3 (Priya Nair)']. ...
ERROR   criterion C3 (...): scored in 2 slots ['3 (Priya Nair)', '4 (Luis Ortega)']. ...
ERROR   slot minutes add up to 180, stated loop length is 120.
ERROR   5 slots is over the default of 4 (Bock [29]); fill `reason` for slots ['5'] or cut them.
```

Decisions Harper makes and explains, rather than silently fixing:

- **"Team fit" round (C4):** not in the approved rubric. Harper does not add
  it. Harper tells Maya that "fit" is not scoreable evidence and tends to
  track the interviewers' own backgrounds [79]. If there is a real
  behaviour behind it (for example "hands off work across time zones"), that
  goes back to hiring-rubric-design as a rubric change for Maya to approve.
- **Double coverage:** C1 stays with Maya (primary). Tom may probe C1 during
  the work sample as a secondary, without scoring it. C3 stays with Priya.
- **Luis:** no criterion left for him. Harper lists him as an optional
  interviewer if Maya wants a different primary for C3, and does not create a
  slot for him.
- **Length:** three slots, 30 + 45 + 45 = 120 minutes.

Result: `loop.csv`, and `check_loop.py` reports OK.

## Step 3. Lint the question bank (hard case)

```
python3 scripts/question_lint.py questions-draft.md
```

```
line 3 [ORIGIN -> ... R2] 'Where are you originally from': national origin, race or ethnicity
line 4 [FAMILY -> ... R4] 'childcare': marital status, children, pregnancy or caring duties
line 4 [HEALTH -> ... R5] 'health': health or disability before an offer
line 5 [AFFECT -> ... R13] 'gel with': affect, demeanour or unsupported fit
```

Changes shown to Maya:

| Was | Now | Why |
|---|---|---|
| Q3 "Where are you originally from? Just to break the ice." | Removed. The ice-breaker is small talk that is not scored | National origin [34] |
| Q4 "Any health issues or childcare we should plan around?" | AR1 in the unscored "Ability requirements" section: "Month-end close runs to 19:00 on the last two working days of each month. Can you meet that schedule, with or without reasonable accommodation?" (asked of everyone, mapped to no criterion) | ADA pre-offer rule [35][46]; childcare questions [74] |
| Q5 "Would you gel with a small, fast team?" | Removed with the C4 slot | Not a rubric criterion [79] |

The 19:00 schedule is Maya's stated requirement, recorded in the plan with
her name. It is an ability requirement, not evidence for any criterion, so
it is not mapped to C3 or any other criterion and does not appear on a scored
card: Priya's slot lists only Q2 (`loop.csv`), and Maya reads AR1 to every
candidate at the start of slot 1. `question_lint.py questions.md` then
reports no hits.

The filled bank in template format is `question-bank.md`: Q1, the WS1 work
sample for Tom's C2 slot (task, follow-ups and pass evidence), Q2, and AR1 in
the unscored "Ability requirements" section. `question_lint.py
question-bank.md` also reports no hits (its "Do not score" lines are guidance
and are skipped).

## Step 4. Scorecards

```
python3 scripts/make_scorecards.py rubric.csv loop.csv \
  ~/workspace/hiring/billing-ops-lead/scorecards/B-003/blank --candidate B-003 --role "Billing Operations Lead"
```

This writes three cards (Maya: C1; Tom: C2; Priya: C3), each with its anchors,
a `not assessed` option, the file-before-peers instruction, and a CSV twin.
There is no overall field. Harper delivers each card with
`write_workspace_file(source_path=...)` for Maya to hand out, and does not
send them.

## Step 5. Candidate information note (excerpt)

> **Using AI tools** [OWNER TO CONFIRM: Maya has not set a policy. Suggested
> pattern for her to decide on: written materials "draft yourself, then
> refine with AI"; SQL work sample "no AI tools unless we tell you"; live
> interviews "no AI assistance" [104].]
> **Adjustments:** contact Jo Patel at people@acme.example. You don't need to
> tell us why or share medical details.
> **When you'll hear:** [OWNER TO CONFIRM]

## Step 6. Output returned

1. Loop table (3 slots, 120 min), with `check_loop.py` OK.
2. Criterion coverage.
3. Question bank with the change table above, and the lint clean.
4. Three scorecard links.
5. Candidate note, DRAFT.
6. Missing owners: interview coordinator. Open items: AI-use policy and
   decision timing.
7. Approval line: `Approved by: Maya Chen, pending`. Nothing sent,
   scheduled or changed in a calendar or ATS.
