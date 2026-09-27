# Hard case: "keep culture fit and top schools", then a change mid-screen

Fictional, for shape only.

## Part 1: the hiring manager pushes back

> Rae (Engineering Manager): "Add 'culture fit' and 'from a top CS school' as
> criteria. That's what actually predicts success here. And make the
> communication one 'articulate, confident speaker'."

What Harper does:

1. Does not add them. The validator would stop all three anyway:
   `disallowed signal 'culture fit' in criterion [fit]`, `disallowed signal 'school' in criterion [prestige]`,
   `disallowed signal 'confident' in criterion [affect]`.
2. Explains in two lines, with sources: "culture fit" works as a class proxy
   and tends to encode the evaluators' own backgrounds [79]; years of
   education predict job performance weakly (about .10 in the older canon)
   while structured interviews are among the strongest predictors [18][77].
   "Articulate, confident speaker" rewards accent and style rather than the
   work.
3. Asks for the behaviour behind each one, as an `ask_question` card:
   - "When someone was a great fit on your team, what did they do in the
     first three months?" Rae: "wrote design docs before coding and asked for
     review early".
   - "What does the top-school requirement stand in for?" Rae: "strong
     fundamentals: data structures, complexity".
   - "What does the communication need to produce?" Rae: "explaining an
     incident to support in plain language".
4. Proposes criteria that test those behaviours, each traced to a requirement:

| Criterion | Anchor 3 (required scope) | Confirm with |
| --- | --- | --- |
| Writes a design doc before building and asks for review | Shares a doc with problem, options and trade-offs, and changes the plan after review | Design-doc exercise |
| Applies data structures and complexity to a real problem | Picks a structure for the sample problem and explains its cost correctly | Work sample |
| Explains an incident to a non-technical team in writing | A written incident note support could act on, with cause, impact and next step | Written exercise |

5. New requirements for the design doc and the incident note go back to
   role-intake-and-job-description as test-in-process rows, so the posting and
   the rubric agree. "Top CS school" is recorded as removed, reason: "stands in
   for fundamentals, now tested directly".

If Rae insists on keeping "culture fit" as written, Harper keeps it out of the
rubric, records the disagreement in the plan's open questions for the final
decision-maker, and does not freeze a rubric containing it. The guardrail does
not bend; the owner can decide not to use Harper's rubric, but Harper does not
write that one.

The same stop applies when a proxy hides in an anchor, a not-assessed rule or
the scorer cell rather than the criterion. A draft with anchor_1 "Worked only
at small firms, not Big 4 or Fortune 500", not_assessed_rule "candidate
graduated before 2010 or is not local to Denver", and a scorer note "prefers
candidates who ... native-born" gets:

```
ERROR 1. line 17 (C1): disallowed signal 'small firms' in anchor_1 [prestige]: Employer brand is not evidence of the work [105]
ERROR 2. line 17 (C1): disallowed signal 'Big 4' in anchor_1 [prestige]: Employer brand is not evidence of the work [105]
ERROR 3. line 17 (C1): disallowed signal 'Fortune 500' in anchor_1 [prestige]: Employer brand is not evidence of the work [105]
ERROR 4. line 17 (C1): disallowed signal 'graduated before 2010' in not_assessed_rule [age]: Age terms and proxies [45][34]
ERROR 5. line 17 (C1): disallowed signal 'not local' in not_assessed_rule [location]: ZIP and commute are named proxies [72]
ERROR 6. line 18 (C2): disallowed signal 'native' in scorer [origin]: National-origin proxy; name the language task the work needs instead [34]
```

`approve_rubric.py` refuses to freeze it until all six are gone.

## Part 2: a change after screening has started

Two weeks later, 30 applicants (A-001 to A-030) have been screened against
`rubric-v1.md`.

> Rae: "Can you quickly add 'has run on-call' to the rubric?"

What Harper does:

1. Does not edit `rubric-v1.md`. It is approved and checksummed; editing it
   would make resume-screening's `find_rubric.py` stop with exit 4 ("changed
   after approval"), and `approve_rubric.py --verify` report "CHANGED AFTER APPROVAL".
2. Runs `python3 ~/skills/hiring-rubric-design/scripts/approve_rubric.py ~/workspace/hiring/platform-eng/rubric-v1.md --new-version`,
   which creates a draft `rubric-v2.md`.
3. Adds the criterion (with a requirement row "has run on-call for a
   production service", must-show or test-in-process as Rae decides), validates,
   and shows it for approval.
4. Tells Rae, before approval: "A-001 to A-030 were screened on v1, which has
   no on-call criterion. Once v2 is approved, do you want them re-screened on
   v2, or should v2 apply only from A-031? Applying two bars to one pool treats
   early and late applicants differently." Rae decides; Harper records the
   decision and who made it in the plan's change log.
5. Freezes v2 only after Rae's explicit approval sentence.
