# Declines after a background check, and identity verification

Orientation only, dated 2026-09. Employment legal questions go to the
owner's attorney with a one-line brief and the facts (persona).
`[n]` numbers follow the recruiting dossier (section 8).

## 1. Before drafting any decline

Ask once: "Did a background check or any consumer report play any part in
this decision?" (`ask_question`, options "No", "Yes", "Not sure").

- **No:** draft the decline as normal (`templates/messages.md`).
- **Yes or Not sure:** draft **nothing**. In the US, an employer that takes
  adverse action based in whole or part on a consumer report must follow the
  FCRA process: a pre-adverse action notice with a copy of the report and
  the summary of rights, a pause for the candidate to respond, then an
  adverse action notice [48][76]. Reply: "This decline goes through your
  background-check (FCRA) process first; who runs it?" Record in the
  candidate row `next_step: FCRA process with <owner of the process>`.
  Outside the US, route to the owner's background-check owner the same way.

## 2. Identity verification for remote roles

Fake and stolen-identity candidates are a real risk: Gartner predicts one in
four candidate profiles could be fake by 2028 [103], and North Korean
remote IT-worker schemes use deepfakes and stolen identities [81].
Mitigations named in [81]: live or in-person identity verification,
verifying employment history directly, and shipping equipment only to the
address on the ID.

How coordination handles it:
- The **owner** sets the verification step (e.g. "live ID check on video
  before the onsite"). It applies to **every** candidate at that stage for
  the role, never selectively.
- It is tracked as a loop row (coverage `verification`) and in the
  candidate's `verification_step` column: `pending`, `done <date>`, or
  `mismatch reported by <owner>`.
- A mismatch is recorded only as a FACT the owner reported ("ID name does not
  match the interview identity, per Maya"). The owner decides what happens next.
- Never infer fraud, or suggest verification, from a name, accent,
  nationality, location, photo or time zone. That is discrimination, not
  verification.

## 3. The response-window promise

61% of job seekers report being ghosted after an interview [80]. Default
promise: candidates hear back within 24 hours at every stage, 48 at most,
unless the owner has set their own. `stall_sweep.py` flags a candidate past
the window with no update (`response_window`); draft a truthful holding note.

## Sources

| # | Source | URL |
| --- | --- | --- |
| 48 | 15 U.S.C. 1681b (FCRA) | https://www.law.cornell.edu/uscode/text/15/1681b |
| 76 | FTC, Using Consumer Reports: What Employers Need to Know | https://www.ftc.gov/business-guidance/resources/using-consumer-reports-what-employers-need-know |
| 80 | Greenhouse, 2024 State of Job Hunting | https://www.greenhouse.com/blog/greenhouse-2024-state-of-job-hunting-report |
| 81 | Skadden, North Korean remote IT worker fraud | https://www.skadden.com/insights/publications/2026/06/north-korean-remote-it |
| 103 | HR Dive, Gartner: 1 in 4 candidate profiles fake by 2028 | https://www.hrdive.com/news/fake-job-candidates-ai/757126/ |
