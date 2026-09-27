---
name: "candidate-offer-draft"
description: "Draft candidate offer materials from approved terms while leaving pay, conditions, approval, and sending to authorised people. Use only after an authorised person has approved the candidate and supplied the offer terms. Records every term with its source and approver, checks dates, currency and email-versus-letter consistency, refuses any figure derived from the candidate's current or past pay, fills the company's own offer template (DOCX or text) without touching its clauses, and flags background-check or medical contingencies that need an FCRA disclosure or post-offer handling."
triggers: ["draft the offer email", "prepare the offer letter draft", "offer draft for the approved candidate", "fill in the offer template", "offer approval checklist", "check the offer terms", "fill our offer template with the approved terms"]
version: "2"
---

# Candidate offer draft

Turns approved offer terms into an offer email draft, a filled offer letter
from the company's template, and an internal approval checklist. This skill
does not choose pay, set conditions, negotiate or make the offer.

**Use when:** an authorised person has approved the candidate and supplied
(or will supply) the offer terms.
**Do not use for:** deciding who is hired (people decide;
candidate-interview-debrief records it), estimating pay or bands,
negotiating or counter-offers (log them for the approver), or writing legal
clauses when no template exists.

## Inputs and where they come from

| Input | Source |
|---|---|
| Hire decision and decision-maker | The decision record (`~/workspace/hiring/<role-slug>/debriefs/<candidate-id>/decision-record.md`) or the owner. Missing: stop. |
| Offer terms: entity, title, level, manager, location, work terms, start date, pay, currency, pay period, bonus and equity wording, benefits source, contingencies, response-by date, signatory | Written approvals from named authorised people, and the hiring plan (`~/workspace/hiring/<role-slug>/hiring-plan.md`; legacy `hiring-plan-<role>.md` via `run_capability(id="tool:list_workspace_files", input={"include_all_sessions": true})`). Each term is recorded in `terms.json` with its value, source, approver and date. |
| The company's approved offer template or required clauses | An upload (`read_workspace_file(file_id=..., save_to_path="/home/user/offer/template.docx")`), or Drive if connected: `find_capability(query="google drive download file")` → `describe_capability` → `run_capability(..., validate_only=true)` → download. A sign-in card means ask for an upload. |
| Hiring jurisdiction (country, and US state if any) | The hiring plan; otherwise the owner. Recorded as `jurisdiction` in `terms.json`. It decides whether the US FCRA flag or the local-rules flag applies; empty is treated as US. |
| Whether an FCRA disclosure and authorisation (or, outside the US, the local notice/consent step) is on record, if there is a background check | The owner or people lead. |

Missing terms stay `[OWNER TO CONFIRM]`. Collect them in one `ask_question`
call, naming the approver for each.

## Tools and pre-flight

1. `bash_exec`: `mkdir -p ~/workspace/hiring/<role-slug>/offers/<candidate-id> && test -w ~/workspace/hiring/<role-slug>/offers && echo STATE_OK`.
   No `STATE_OK`: deliver with `write_workspace_file` only, and say that the files will not persist.
2. `bash_exec`: `python3 --version`. For a DOCX template: `python3 -c "import docx" || pip install --user python-docx`.
   Without Python: fill the template by hand, run the checks in `references/pay-terms-rules.md` and
   `references/contingency-order.md` by hand, and label the drafts "hand-checked, not script-verified".

## Procedure

1. **Confirm authority.** Record the hire decision (decision-maker and date)
   and the authorised approver for offer terms. Without both, stop.
2. **Record the terms** in `~/workspace/hiring/<role-slug>/offers/<candidate-id>/terms.json`
   (`templates/offer-terms.json`), taking only values an authorised person
   approved. Never infer a term from another candidate, market data, an
   earlier draft, or the candidate's current or past pay, even if the
   candidate volunteered it or the manager asks you to match it. Take
   contingencies only from the template, in its order.
3. **Check the terms:**
   `cd ~/skills/candidate-offer-draft && python3 scripts/check_terms.py ~/workspace/hiring/<role-slug>/offers/<candidate-id>/terms.json --today <YYYY-MM-DD>`
   Decisions:
   - `PAY_HISTORY` / `INFERRED` → ask the approver for the figure from the
     approved band. Never argue a number.
   - `RESPONSE_PAST` / `START_BEFORE_RESPONSE` → ask which date moves.
   - `CONTINGENCY_SOURCE` → ask for the template's clause, or route to the people lead.
   - `FCRA_DISCLOSURE` warning (US, or no jurisdiction recorded) → flag to
     the owner that a standalone disclosure and authorisation must come
     before the report is procured [48].
   - `LOCAL_CHECK_RULES` warning (non-US jurisdiction) → do not cite US
     statutes; say "local background-check rules may apply (e.g. UK DBS, UK
     GDPR Art. 10); confirm with the people lead".
   - `MEDICAL` warning → only after the offer, and for every entrant in the
     category [46]. Flag it to the people lead.
   Show errors first. Fix only by getting approvals, never by editing a value yourself.
4. **Fill the letter** from the company's template:
   `cd ~/skills/candidate-offer-draft && python3 scripts/fill_offer_template.py /home/user/offer/template.docx ~/workspace/hiring/<role-slug>/offers/<candidate-id>/terms.json ~/workspace/hiring/<role-slug>/offers/<candidate-id>/letter.docx`
   The output is named `DRAFT-...`. Report open, refused and unknown
   placeholders, and approved terms the template never uses. Never add
   wording to cover a gap. If the template has no `{{placeholders}}`, ask the
   owner to add them or to name the fields. **No template:** produce
   `templates/term-summary.md` instead of a letter, and say that the people
   lead or counsel supplies the letter.
5. **Draft the email** (`templates/offer-email.md`). It says the written terms
   control, and repeats at most the title, pay and start date.
6. **Cross-check:**
   `cd ~/skills/candidate-offer-draft && python3 scripts/check_terms.py <terms.json> --email <email.txt> --letter <DRAFT-letter.docx|.md> --today <YYYY-MM-DD>`
   Every amount and date in the email and letter must be an approved term,
   in the approved currency and pay period (`CURRENCY_MISMATCH`,
   `PAY_PERIOD_MISMATCH`, and bare amounts such as "65,000" are checked
   too), and dates are written out ("6 January 2027"; `fill_offer_template.py`
   writes them that way, and `ISO_DATE_IN_TEXT` flags any left as YYYY-MM-DD).
7. **Build the checklist** (`templates/offer-checklist.md`), with each term,
   its value, source, approver and date, the pay-basis line, the contingency
   checks, the open items, and the reviews required.
8. **Save and deliver** under `~/workspace/hiring/<role-slug>/offers/<candidate-id>/`,
   with `write_workspace_file(filename=..., source_path=...)`, linked as
   `workspace://<file_id>#<mime>`. Every file name carries DRAFT.

## Output contract

1. A short offer email draft that says the written terms control.
2. The offer document, filled from the supplied template (or a term summary
   when there is no template), with `[OWNER TO CONFIRM]` visible.
3. An internal approval checklist: each term, source, approver and date; the
   `check_terms.py` result; contingency flags; and the reviews required.
4. "Status: DRAFT, not sent", with the count of open terms.

## Guardrails

- Return drafts only. An authorised people lead, and any counsel the company
  requires, reviews them before anything goes out.
- Never negotiate, promise, send, sign or record acceptance. Never change
  compensation or conditions without fresh written approval.
- Never ask about, record, include or derive any term from the candidate's
  current or past pay, even if volunteered [56][75].
- Never estimate pay or a band, and never take a figure from market data,
  another candidate or an earlier draft.
- Contingency lines come only from the template. Background checks need a
  standalone disclosure before the report is procured [48]. Medical exams
  come only after the offer, and for all entrants in the category [46].
- Do not add legal wording, or describe tax, equity, benefits, immigration or
  employment rights beyond the approved source text.
- Never share the letter with the candidate or put it in a mailbox. The
  sender does that after review.

## Quality self-check

- [ ] Every filled term has a source, an approver and a date. None comes from pay history or an estimate.
- [ ] `check_terms.py` shows 0 errors on the terms, email and letter, or the files are labelled hand-checked.
- [ ] The letter differs from the template only inside the placeholders.
- [ ] Every `[OWNER TO CONFIRM]` is listed with its owner.
- [ ] The contingencies match the template's order and words. The FCRA and medical flags are raised where they apply.
- [ ] Every file name says DRAFT, and nothing was sent.

## Files

- `scripts/check_terms.py`, `scripts/fill_offer_template.py`
- `templates/offer-terms.json`, `templates/offer-email.md`, `templates/offer-checklist.md`, `templates/term-summary.md`
- `references/pay-terms-rules.md`, `references/contingency-order.md`, `references/sources.md`
- `examples/billing-ops-lead-offer/walkthrough.md`: end to end, including "match her current salary plus 10%", date conflicts, a background-check contingency and a mismatched email

## Related skills

- candidate-interview-debrief: the hire decision record.
- candidate-rejection-email: for other finalists, and the FCRA route if an offer is withdrawn over a background report.
- recruiting-getting-started: the hiring plan that names the offer approvers and signatory.
