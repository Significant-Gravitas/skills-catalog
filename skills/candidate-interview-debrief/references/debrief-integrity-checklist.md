# Debrief integrity: how to keep panel evidence independent and job-related

Citations `[n]` are in `references/sources.md` (the recruiting dossier's
section 8 numbering).

Contents
1. Why independence matters
2. Running order (Mediating Assessments Protocol)
3. Scorecard visibility and late or edited filings
4. "No Decision" and recorded overall recommendations
5. Remarks to exclude, and remarks to ask about
6. Meeting notes and transcripts
7. Reference checks
8. Background checks and the FCRA
9. Requests to decide, rank or total

---

## 1. Why independence matters

Structured interviews predict performance better than unstructured ones
(r = .42 in the 2022 re-estimate [77]). Part of that structure is
evaluation: every answer rated, anchored scales, multiple interviewers, and
no discussion between interviews [19]. A scorecard written after hearing the
hiring manager is not independent evidence; it echoes the manager.

## 2. Running order (Mediating Assessments Protocol) [21][20]

1. Scorecards are filed before any discussion.
2. The meeting takes one criterion at a time, in rubric order. It does not
   start with "so, yes or no?".
3. For each criterion: read the cited evidence, then **estimate-talk-estimate**:
   each person states or writes their rating silently, the group discusses the
   evidence, and each re-rates silently. Re-rating is optional; the owner
   chooses whether to use it.
4. An overall view is formed only after every criterion has been reviewed, by
   the named decision-maker ("intuition last") [20][21].
5. Splits go first so the panel spends its time where evidence conflicts.

The split threshold is the company's own rule. Without one, the default is a
gap of 2 or more on a 4-point scale (default, confirm with the owner).

## 3. Scorecard visibility and late or edited filings

- Some ATSs let interviewers see peers' scorecards before submitting, and
  let admins allow edits after submitting. Greenhouse, for example, has a
  visibility setting and an edit-after-submit permission [90]. Ask the owner
  whether peer scores were visible before filing, and record the answer.
- `scripts/snapshot_scorecards.py` records a hash and first-seen time per
  file and keeps each version. Run it when scorecards arrive and again before
  the debrief. Report CHANGED or LATE files as process risks, quoting the
  timestamps. Never drop a late scorecard yourself; the panel decides how much
  weight it carries.
- A timestamp without a zone cannot be compared. Say so; do not assume UTC.

## 4. "No Decision" and recorded overall recommendations

- Harper's scorecards have no overall field. If the ATS records one (for
  example Greenhouse's Definitely Not / No / Yes / Strong Yes), list each
  verbatim and never combine them.
- A scorecard submitted without a recommendation shows as "No Decision" in
  Greenhouse [90]. Count it separately. It is not a neutral vote and not a
  "no"; ask the interviewer whether it was deliberate.

## 5. Remarks to exclude, and remarks to ask about

`scripts/flag_remarks.py` proposes; a person confirms each exclusion.

| Kind | Examples | Action |
|---|---|---|
| Fit or label without behaviour | "gel", "vibe", "not a fit", "strong instincts", "red flag", "energy", "polished" | Ask: "Which approved criterion, and what did you see or hear?" Exclude if there is no answer. "Fit" tends to track evaluator similarity [79] |
| Affect or demeanour | "nervous", "confident", "enthusiastic", "eye contact", "seemed honest" | Exclude. Affect is not a rubric criterion, so it is out-of-rubric evidence; an AI system inferring emotions in hiring is prohibited in the EU [73], so Harper never infers it either. AI video scoring tracked nothing job-related [106] |
| Protected trait or proxy | age ("overqualified", "young"), family, origin or accent, religion, health, appearance | Exclude from the decision record [34][35][45][74] |
| Gaps or prestige | "gap in her CV", "big-name school" | Ask for the missing criterion evidence instead [64][108] |
| Out of rubric | a new criterion raised in the room | Exclude from this decision. If it matters, it goes to hiring-rubric-design for future candidates |
| Automated or AI scores | "the AI screen gave 62%" | Exclude. Only interviewer evidence counts |

Take care with context: "confident SQL" may describe the query, not the
person. Keep the job evidence and drop only the affect word.

## 6. Meeting notes and transcripts

AI meeting notes are evidence only of what was said. Never infer tone,
confidence, honesty or engagement from a transcript [73]. Unfiled notes are
marked "unfiled". They never replace a scorecard, and are quoted with their
source and time.

## 7. Reference checks

Only where company policy allows, only on the approved criteria, and recorded
like any other evidence source [24]. A reference is never a new criterion.

## 8. Background checks and the FCRA

If a background or other consumer report is part of the decision, in whole
or in part, the US Fair Credit Reporting Act requires the employer to give
the candidate a pre-adverse action notice first. That notice includes a copy
of the report and a summary of rights. Only after that can the adverse action
be taken, with its own notice [48][76]. For Harper:

- The decision record says: "Background or consumer report involved: the
  FCRA pre-adverse action process applies before any decline."
- No rejection draft is prepared until the owner confirms the FCRA steps are
  done. Harper routes; Harper does not advise.
- Outside the US, local rules differ. Say "may apply; confirm with the
  people lead or counsel".

## 9. Requests to decide, rank or total

If asked "who should we hire?", "give her an overall score" or "rank the
finalists": Harper does not. Offer instead the evidence table, the splits,
and the missing evidence. Named people decide [54]. An average hides exactly
the disagreement the panel needs to discuss [21].
