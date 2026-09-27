---
name: "hiring-rubric-design"
description: "Build a job-related hiring rubric (the role scorecard) with observable score anchors before any candidate is screened or interviewed. Use after the role outcomes and requirements are approved. Checks every anchor, every proxy term and every must-have before approval, then freezes the approved version so screening and interviews all score against the same bar."
triggers: ["build a hiring rubric", "scoring criteria for this role", "evidence-based rubric before screening", "what should we score candidates on", "define selection criteria for the role", "approve the rubric", "change the rubric after screening started"]
version: "2"
---

# Hiring rubric design

Build the rubric before reading a resume. It tests evidence for the role; it
does not describe an ideal person.

**Use when:** outcomes and requirements are approved and nobody has been
screened yet; the owner wants to approve or change the rubric.
**Do not use for:** the JD or requirement sort (role-intake-and-job-description;
if they are not approved, get that first), interview questions and scorecards
(interview-plan-and-scorecard), or screening (resume-screening).

## Inputs and where they come from

| Input | Where it comes from |
| --- | --- |
| Approved outcomes | `~/workspace/hiring/<role-slug>/intake-brief.md` |
| Approved requirements | `~/workspace/hiring/<role-slug>/requirements.csv` (must-show and test-in-process rows) |
| Owners, scorers, rubric approver | `~/workspace/hiring/<role-slug>/hiring-plan.md` |
| Company scale or weights | The owner; otherwise the defaults below |
| Earlier versions | `rubric-v<N>.md` in the role folder |

If `requirements.csv` is missing (older plans kept everything in the plan
file), rebuild it with role-intake-and-job-description first. Layout:
`references/hiring-state.md`.

## Tools and pre-flight

1. `bash_exec`: `python3 --version || echo "python3 missing"`. Without Python,
   run the checks in step 4 by hand from `references/anchor-writing-guide.md`,
   label them "hand-checked", and do not claim a frozen version (step 6).
2. Mirror `checklists/pre-approval-checklist.md` in `TodoWrite`.

## Procedure

1. **Read** the intake brief, `requirements.csv`, the plan, and
   `references/anchor-writing-guide.md`.
2. **Choose criteria** from the approved outcomes (default: four to seven;
   fewer is fine if the role is narrow). Each criterion is separable (scored
   from its own evidence; merge two that would be scored from the same answer)
   and cites the requirement(s) it tests. For each, write:
   - the job outcome it supports;
   - acceptable evidence sources;
   - an anchor for every level, in observable terms, fixed before any resume is read;
   - when it is "not assessed";
   - one interview question or work sample that can confirm it;
   - the owner who scores it.
3. **Scale.** Default, unless the company uses its own: one to four.
   - 1: the evidence method was completed and found no qualifying evidence.
   - 2: partial or indirect evidence.
   - 3: clear evidence at the required scope.
   - 4: clear evidence at greater scope, with a stated result.
   When the source or method is unavailable, or the criterion was not yet
   tested, mark it "not assessed", not one or zero. A resume that simply omits
   a criterion is "not assessed" until the interview or work sample tests it.
   Each criterion is scored before any overall view is formed [20][21].
4. **Write and validate.** Save `~/workspace/hiring/<role-slug>/rubric-v<N>.md`
   from `templates/rubric.md` (keep the header lines and the column row exactly),
   then run:
   `python3 ~/skills/hiring-rubric-design/scripts/validate_rubric.py ~/workspace/hiring/<role-slug>/rubric-v<N>.md --requirements ~/workspace/hiring/<role-slug>/requirements.csv`
   Decisions:
   - `ERROR`: fix it and re-run. Never show an erroring rubric for approval.
   - A must-show requirement with no criterion: add a criterion, or go back to
     the JD owner to move the requirement.
   - A criterion citing no requirement: add the requirement to
     `requirements.csv` (via role-intake-and-job-description) or drop the criterion.
   - A disallowed word that is part of the job itself: list it in
     `allowed_terms` with the reason; never for a word about the candidate.
   - More than four evidence methods (default): add `loop_reason` or cut one [29].
   - `WARN`: fix, or show it to the owner with the rubric.
5. **Show for approval.** Present the rubric table, weighting (equal by
   default; the owner decides), evidence rules, disallowed signals, the
   validator's remaining warnings, the structure checklist
   (`references/structure-components-checklist.md`, components 8 and 9 at
   least), and an approval line. Ask the owner to approve in words.
6. **Freeze on an explicit yes.** Only after the owner's approval sentence in
   this chat:
   `python3 ~/skills/hiring-rubric-design/scripts/approve_rubric.py ~/workspace/hiring/<role-slug>/rubric-v<N>.md --approver "<name>" --quote "<their sentence>" --requirements ~/workspace/hiring/<role-slug>/requirements.csv`
   then
   `python3 ~/skills/hiring-rubric-design/scripts/validate_rubric.py ~/workspace/hiring/<role-slug>/rubric-v<N>.md --requirements ~/workspace/hiring/<role-slug>/requirements.csv --write-back`
   to record each requirement's criterion. Update the plan's Stages and
   "Rubric approver" lines; deliver the rubric with
   `write_workspace_file(source_path=...)` and link it.
7. **Changing an approved rubric.** Never edit an approved file.
   `python3 ~/skills/hiring-rubric-design/scripts/approve_rubric.py <rubric-vN.md> --new-version` creates a
   draft `rubric-v<N+1>.md`; edit, validate and approve it as above. Tell the
   owner which candidates (by id) were already screened or scored on vN, so
   they decide whether to re-screen; applying two bars to one pool is uneven
   treatment.

## Output contract

1. Rubric table (all anchors), weighting and who chose it.
2. Evidence rules and disallowed signals.
3. Validator result (script output, or "hand-checked") and open warnings.
4. Requirement coverage: each must-show requirement and its criterion.
5. Approval line: pending, or approver, date and quote with the frozen file's checksum.
6. Link to `rubric-v<N>.md`.

The rubric supports a human decision; it never produces an automatic advance
or rejection.

## Guardrails

- Do not score protected traits or proxies. Do not score polish, likability,
  shared interests, school prestige, employer prestige, career gaps, names,
  addresses or postcodes, commute, photos, accents, AI-writing style, or
  "culture fit" [79][63][64][72].
- A communication criterion must name the work product and the level the role needs.
- Anchors never compare candidates with each other [78].
- No demeanour, confidence, enthusiasm or affect criterion; never inferred
  from video, voice or photos [73][106].
- Only an owner's explicit approval freezes a rubric. Harper never approves.
- Never rank candidates, and never turn a score into an advance or reject decision.

## Quality self-check

- [ ] Every criterion traces to an approved outcome and a requirement.
- [ ] All four anchors written in observable terms; "not assessed" defined.
- [ ] `validate_rubric.py` shows no ERROR (or the hand check is labelled).
- [ ] Every must-show requirement is covered; no removed requirement is scored.
- [ ] Weighting is the owner's choice, stated.
- [ ] Approval stamped only after an explicit yes, with the quote.

## Related skills

role-intake-and-job-description (before), interview-plan-and-scorecard (next:
questions and scorecards from this rubric), resume-screening (reads only an
approved, unchanged rubric), candidate-interview-debrief. Load with
`run_capability(id="skill:<slug>", input={})`.

## Package files

- `scripts/validate_rubric.py`, `scripts/approve_rubric.py`, `scripts/rubric_io.py` (shared parser)
- `references/anchor-writing-guide.md`, `structure-components-checklist.md`,
  `disallowed-signals.csv` (validator data), `hiring-state.md`, `sources.md`
- `templates/rubric.md`
- `checklists/pre-approval-checklist.md`
- `examples/billing-ops-rubric.md` (end to end, with files in `examples/billing-ops/`),
  `examples/hard-case-fit-prestige-and-change.md` (hard case)

## Example

Fictional rubric excerpt, for shape only. Role: Billing Operations Lead. Equal
weight (Maya's choice). Full run: `examples/billing-ops-rubric.md`.

> | Criterion | Outcome supported | 1 | 2 | 3 | 4 | Confirm with | Scorer |
> |---|---|---|---|---|---|---|---|
> | C1 Runs a recurring finance process end to end | month-end close on time | Describes no recurring process they ran themselves | Took part; own steps not stated | Names a process they owned, its steps, and how they handled a missed deadline | Owned it across teams and changed it, with a stated result | "Walk me through the last close you ran." | Maya |
> | C2 Writes reporting queries for reconciliation | reconciliation from month 2 | No query returns the totals | Totals, but misses duplicates | Correct query with one duplicate check | Plus a reusable mismatch check that removes a manual step | 45-minute SQL work sample | Tom |
> | C3 Writes procedures a team follows | billing runbook in use | Nothing another person could follow | Missing steps or owners | A procedure a team used, kept current | Adopted by more than one team, with a stated result | Refund-policy exercise | Priya |
>
> Disallowed signals: school, employer brand, gaps, "energy", "fit".
> Approval: Maya Chen, 2026-09-27, "Approved, three criteria is right for this role."
