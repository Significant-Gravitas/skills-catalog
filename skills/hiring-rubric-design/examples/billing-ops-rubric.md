# Worked example: rubric for a Billing Operations Lead

Fictional, for shape only. Files are in `examples/billing-ops/`:
`requirements.csv` (from role-intake-and-job-description, with R6 added in
this run), `rubric-v1-first-draft.md` (what a hurried first pass looks like)
and `rubric-v1.md` (the version shown for approval). All script output below
is real output from those files.

## Inputs

- Intake brief outcomes: failed-payment queue owned by day 30; month-end
  close with finance by day 60; billing runbook in use by day 90.
- Requirements: R1 must-show (recurring process end to end), R2
  test-in-process (SQL), R3 learn-after-hire, R4 and R5 removed.
- Plan: rubric approver Maya Chen; interviewers Maya, Tom, Priya.

## Step 4, first pass: the validator stops a bad draft

The first draft reused the hiring manager's words from the kickoff call.

```
$ python3 ~/skills/hiring-rubric-design/scripts/validate_rubric.py ~/workspace/hiring/billing-ops-lead/rubric-v1.md --requirements ~/workspace/hiring/billing-ops-lead/requirements.csv
ERROR 1. line 17 (C1): anchor_1 means 'method completed, no qualifying evidence'; 'not assessed' is separate, never a 1
ERROR 2. line 17 (C1): disallowed signal 'top-tier' in anchor_4 [prestige]: School or employer prestige predicts little and carries class and pedigree bias [18][105][79]
ERROR 3. line 18 (C2): anchor_4 compares candidates ('Better than'); anchors describe behaviour against a fixed standard [78]
ERROR 4. line 19 (C3): 'scorer' is empty
ERROR 5. line 19 (C3): disallowed signal 'culture fit' in criterion [fit]: 'Culture fit' works as a class proxy and encodes evaluator demographics [79]
ERROR 6. line 19 (C3): a communication criterion must name the work product and the level the role needs
ERROR 7. C3: cites removed requirement R4 ('degree in finance'); the posting no longer asks for it, so it must not be scored [111]
WARN  3 criteria; the default is 4 to 7 (fewer is fine for a narrow role; confirm with the owner)
WARN  line 17 (C1): anchor_4 uses a rating word ('Excellent'); describe what the person did [78]
...
WARN  5 loop methods; the default is 4 or fewer [29]; add loop_reason or cut one
WARN  test-in-process requirement R6 ('writes procedures a team follows') has no criterion
Criteria: 3; status: draft; version: 1
7 error(s); fix them before asking for approval
```

(In this run the requirements file shipped with R6 already present; in the
live session R6 did not exist yet. The runbook outcome had no requirement
behind it, so Harper asked Maya, and role-intake-and-job-description added R6
"writes procedures a team follows" as test-in-process, with the JD's "Useful"
line updated to match.)

## Fixes

| Error | Fix |
| --- | --- |
| C1 anchor 1 "not assessed" | "Describes no recurring finance or billing process they ran themselves"; "not assessed" moved to `not_assessed_rule` |
| C1 "top-tier finance team" | Removed; level 4 now "owned a recurring process across teams and changed it, with a stated result" |
| C2 "better than the other candidates" | "Correct query plus a reusable mismatch check, explained in writing, that removes a manual step" |
| C3 "strong communicator and culture fit", scored at a panel lunch, citing R4 | Replaced by "Writes procedures a team follows" (R6), tested by the refund-policy writing exercise; scorer Priya |
| C2 scorer OPEN | Tom Reid, named by Maya |
| Five loop methods (panel lunch) | Panel lunch dropped; four methods |

## Step 4, second pass

```
$ python3 ~/skills/hiring-rubric-design/scripts/validate_rubric.py ~/workspace/hiring/billing-ops-lead/rubric-v1.md --requirements ~/workspace/hiring/billing-ops-lead/requirements.csv
WARN  3 criteria; the default is 4 to 7 (fewer is fine for a narrow role; confirm with the owner)
Criteria: 3; status: draft; version: 1
OK
```

## Step 5: shown to Maya

The table from `rubric-v1.md`, equal weighting, the evidence rules, the
disallowed signals, and one open warning: "three criteria, below the default
of four; fine for a narrow role if you agree". Structure checklist: components
8 and 9 yes; 11-13 go to interview-plan-and-scorecard; 14 (interviewer
training) has no skill yet.

> Maya: "Approved, three criteria is right for this role."

## Step 6: freeze

```
$ python3 ~/skills/hiring-rubric-design/scripts/approve_rubric.py ~/workspace/hiring/billing-ops-lead/rubric-v1.md --approver "Maya Chen" --quote "Approved, three criteria is right for this role." --requirements ~/workspace/hiring/billing-ops-lead/requirements.csv
approved: rubric-v1.md v1 by Maya Chen on 2026-09-27
checksum: <sha256> -> rubric-v1.md.sha256
$ python3 ~/skills/hiring-rubric-design/scripts/validate_rubric.py ~/workspace/hiring/billing-ops-lead/rubric-v1.md --requirements ~/workspace/hiring/billing-ops-lead/requirements.csv --write-back
WARN  3 criteria; the default is 4 to 7 (fewer is fine for a narrow role; confirm with the owner)
Criteria: 3; status: approved; version: 1
Wrote rubric_criterion_id back to /home/user/workspace/hiring/billing-ops-lead/requirements.csv
OK
```

`requirements.csv` now maps R1 to C1, R2 to C2 and R6 to C3, so the JD
approval item "every must-show requirement maps to a rubric criterion" can be
ticked. resume-screening's `find_rubric.py` checks the checksum before it
screens anyone.

## Output to Maya (shape)

> Rubric v1 approved and frozen: [rubric-v1.md]. Three criteria, equal weight,
> anchors at all four levels. R1 → C1, R2 → C2, R6 → C3; the removed degree
> requirement is not scored anywhere. Next: the interview plan, which puts
> each criterion with one interviewer.
