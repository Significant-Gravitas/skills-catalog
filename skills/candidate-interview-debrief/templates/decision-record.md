# Decision record: <candidate id>, <role>

Harper writes down the decision in the decision-maker's words. Harper never
fills the decision or rationale fields from the evidence, the scores or the
discussion. Anything not supplied reads `needs human confirmation`.
Saved: `~/workspace/hiring/<role-slug>/debriefs/<candidate-id>/decision-record.md`

| Field | Value |
|---|---|
| Candidate | <id> |
| Role, rubric version | <role>, v<n> |
| Debrief date and time | <date, time, zone> |
| Panel present | <names> |
| Named decision-maker | <name, or `needs human confirmation`> |
| Decision (verbatim) | <advance / reject / hire / hold, in their words, or `needs human confirmation`> |
| Decision date (as stated by the decision-maker) | <YYYY-MM-DD, or `needs human confirmation`> |
| Stage at decision (application / screen / loop) | <stage, or `needs human confirmation`> |
| Rationale (verbatim, job-related) | <their words, tied to criteria, or `needs human confirmation`> |
| Criteria the rationale relies on | <criterion ids they named> |
| Evidence excluded, and who confirmed it | <list> |
| Open process risks at decision time | <list> |
| Background or consumer report involved? | <no / yes: the FCRA pre-adverse action process applies before any decline; the rejection draft waits for it / unknown: ask> |
| Feedback approved for the candidate (verbatim) | <text, or "none approved"> |
| Recorded by | Harper, <date> |
| ATS updated? | <no. Only on the owner's yes to that exact update> |

Next step, by decision:
- Reject (and no consumer report involved): candidate-rejection-email, with
  the decision-maker, date and any approved feedback above.
- Reject with a consumer report involved, or unknown: no rejection draft yet.
  Route to the owner's FCRA process (see `references/debrief-integrity-checklist.md`).
- Hire: candidate-offer-draft, once an authorised person supplies approved terms.
