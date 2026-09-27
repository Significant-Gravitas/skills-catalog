# Offer brief and letter fields

Read when composing the brief or checking a template. Each field says where
its value may come from. Anything without a source is `[OWNER TO CONFIRM]`.

| Field | Source allowed | Notes |
|---|---|---|
| Interview record (3 lines) | Debrief record, filed scorecards | Quote; never paraphrase a strength. Decision in the decision-maker's words. |
| Band min/max, currency, approver, date | Owner or finance, in writing | No band, no composition. |
| Level and level rationale | Company level grid; debrief evidence | The level is the approver's call. |
| Position type | Owner | Full-time, part-time, fixed-term, contractor. Contractor classification questions go to the attorney. |
| Base | Inside the band; `offer_math.py` output | One evidence line: what the candidate said they value, and where it sits in band. |
| Bonus | Company bonus plan text | Percent or amount exactly as the plan says. |
| Equity | Company equity grid, approved text | Text only; never a value estimate (strike, valuation and vesting are the approver's words). |
| Signing | Approver | Often the paired give; log it in the counter log. |
| Sales: variable at target, OTE, pay mix | Approved comp plan | OTE = base + on-target variable (`offer_math.py --variable-target`). Sales postings name OTE and commission explicitly [13][14]. |
| Sales: commission plan, ramp, draw, quota | Approved plan document | Carried as the approver's text; never summarised, never modelled as "likely earnings". Accelerators, clawbacks and quota relief questions go to the plan owner. |
| Benefits | Benefits source document | Name the document; do not describe tax or benefit rules. |
| Start date | Candidate's stated notice, in their words; owner | `check_terms.py` warns if the notice period makes it unrealistic (`notice_days`). |
| Probation | Company template | |
| Contingencies | Company template, in template order | See references/contingency-order.md. |
| Answer-by | Owner (set before the offer lands) | Default 24-48 hours after the written offer - default, confirm with the owner. |
| Contact for questions | Owner | A named person, not "the team". |
| Signatory | Owner | |

## Brief sections (templates/offer-brief.md)

1. Interview record in three lines.
2. Approved band and approver.
3. What the candidate values, in their words (expectations, never history).
4. Recommended composition, one evidence line per element.
5. Anticipated negotiation with the paired give inside the band, and the walk-away line.
6. Escalation flags: above-band ask, competing offer, timeline pressure, contingency issue, legal question.
7. Close plan pointer.
8. Approval table.

## Evidence labels

FACT = from the tracker, a document or the person's own words with the
source named. INFERENCE = your read, with the reasoning shown. UNKNOWN =
missing; never filled with a guess.
