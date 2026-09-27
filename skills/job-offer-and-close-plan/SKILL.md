---
name: "job-offer-and-close-plan"
description: "Use when a finalist emerges and the offer needs shaping, approving, negotiating, or closing to a signed yes — composition, letter, approvals, and the dated close plan. Covers counters, competing offers, sales offers with OTE and commission, contingencies, and offers nearing their answer-by date."
triggers: ["shape the offer for our finalist", "the candidate countered", "offer approval brief", "close plan for the finalist", "draft the offer letter", "candidate has a competing offer", "shape an offer within the approved band", "sales offer with OTE and commission", "check this offer's answer-by status"]
version: "2"
---

# Job offer and close plan

Run this when a finalist emerges and the owner needs the offer shaped,
approved, negotiated or closed: composition, letter, approvals, and the
dated plan to a signed yes. Package files are at `~/skills/job-offer-and-close-plan/`.

**Not for:** deciding who to hire (hiring-debrief-and-decision), declines
and the stall sweep (interview-coordination), offer-acceptance numbers
(hiring-pipeline-analytics), or any legal question (attorney, with
templates/attorney-brief.md).

## Inputs and where they come from

| Input | Source | If missing |
|---|---|---|
| Interview record and decision | ~/workspace/hiring/debriefs/, the tracker, or the owner | Ask; do not compose before a recorded decision |
| Approved band + approver + date | Owner or finance, in writing | Stop and ask (`ask_question`). Never estimate |
| Level, bonus, equity, commission plan, benefits | Company grids and plan documents | `[OWNER TO CONFIRM]` |
| What the candidate values, other processes, notice period | Their words in screen or call notes | Ask the owner to ask them |
| Company offer template | Upload: `read_workspace_file(..., save_to_path="/home/user/offer/<cand>/template.docx")`; Drive: `find_capability("google drive download")` -> `run_capability` | Letter clauses stay `[COMPANY TEMPLATE REQUIRED]` |
| Approval chain, answer-by window | Owner; `memory_search("offer approvals answer-by")` first | Default answer-by 24-48 h after the letter - default, confirm with the owner |

Never ask for, record or use current or past pay, even when volunteered
(references/pay-history-and-transparency.md).

## Procedure

Mirror these steps in `TodoWrite`. Pre-flight once: `python3 --version`
(scripts are standard library only).

1. **Band first.** Asked "what should we pay?", ask for the approved band and
   who approved it. No figure, estimate or band inferred from stage, size or
   funding. `scripts/offer_math.py` exits 3 without a band and approver.
2. **Pre-close before you compose.** Confirm what they value (comp, growth,
   team, mission, flexibility), other processes and why they are moving,
   expectations (never history), notice period in their words. Set the
   answer-by expectation before the offer lands and line up the hiring
   manager's follow-up for right after the verbal
   (references/negotiation-and-close.md).
3. **Compose from evidence.** Base, bonus, equity, signing, benefits, start
   date, level rationale; sales roles add on-target variable, OTE and the
   commission plan as approved text. Every number comes from
   `cd ~/skills/job-offer-and-close-plan && python3 scripts/offer_math.py --band-min … --band-max … --currency … --band-approver "…" --base … [--variable-target …]`;
   paste its table. Comp evidence is only the band, company grids, or
   posted pay with a link.
4. **Write the offer brief** (templates/offer-brief.md): record in three
   lines, composition with one evidence line per element, anticipated
   negotiation with the paired give inside the band, escalation flags
   (above-band ask, competing offer, timeline pressure, contingency issue).
   Nothing with a number reaches the candidate before the approver says yes.
5. **Check the terms.** Write terms.json (templates/offer-terms.json) from
   approved sources only, then
   `cd ~/skills/job-offer-and-close-plan && python3 scripts/check_terms.py <terms.json>`.
   Errors go to the owner first. Above band needs `above_band_approval`
   with approver, date and an amount at least the base.
   Decision: a background-check contingency with no standalone disclosure on
   record, or a medical exam not marked post-offer for all entrants, is
   flagged and fixed in the close plan (references/contingency-order.md).
6. **Draft the letter from the approved brief.** Verbal yes first, then
   written.
   `cd ~/skills/job-offer-and-close-plan && python3 scripts/fill_offer_template.py <template> <terms.json> <out>`
   fills placeholders only, keeps binding clauses and contingency order as
   the template has them, and names the file DRAFT. Exit 4 (no placeholders):
   ask for the placeholder version; never retype binding wording. Re-run
   `cd ~/skills/job-offer-and-close-plan && python3 scripts/check_terms.py <terms.json> --text <letter-DRAFT.docx|.md> --text <email> --template <template>`
   so every money figure (currency-marked or "k") and date matches, in the
   offer currency. A derived or extra figure (monthly gross, allowance) is
   cleared by adding it as its own term with source and approver; a figure
   fixed in the company template prints as INFO. Never wave an ERROR
   through: fix the draft or the terms, or ask the owner. Pay-history
   detection catches common phrasings; the rule is yours to apply. Defer
   anything legal to the attorney.
7. **Handle counters with the comparison first.**
   `cd ~/skills/job-offer-and-close-plan && python3 scripts/offer_math.py --band-* --offer-* --ask-* --proposal-*`
   gives offer vs ask vs proposal; then the paired give and the walk-away
   line. Exit 1 means the base or proposal is above band max (or the
   proposal is above the walk-away line): that figure does not go in the
   brief without the approver's written yes. Above-band ask: escalate to the band approver, never counter above
   band. Append every concession to counter-log.csv with who approved it.
8. **Run the close plan.** Dated, single-owner tracks with timezones:
   approvals, verbal, letter, questions, answer-by, signature, first-week
   hand-off, plus contingency tracks in legal order. Every owner is an
   internal person, never you and never the candidate. Check it with
   `cd ~/skills/job-offer-and-close-plan && python3 scripts/close_plan.py <close-plan.csv> --candidate "<name>" --assistant "<your name>" --terms <terms.json>`
   (it also flags a background check dated before the disclosure track, a
   medical exam or drug test before acceptance, and a terms contingency
   with no track). Use its "Next check date" (never in the past) for the
   follow-up and chase the "Overdue since" lines first. Draft follow-ups with the open
   question, the deadline and who to talk to (templates/close-messages.md).
   With Gmail connected they may sit as unsent Gmail drafts:
   `find_capability("gmail create draft")` -> `describe_capability` ->
   `run_capability(..., validate_only=true)` -> run; never a send tool. A
   sign-in card means stop and ask the owner to connect.
   Before the brief or plan is marked ready, when a teammate is hired, ask
   for one bounded check of the money and dates:
   `run_capability(id="tool:consult_teammate", input={"expert_id": "<teammate>", "work": "<brief + terms, no candidate contact details>", "authority": "review only", "question": "Do the figures and dates match the approvals?"})`.
   A block goes to the owner first. No teammate hired: skip it.
9. **Schedule the answer-by check** on the owner's yes. With memory on,
   first keep the agreed answer-by and approver for later sessions:
   `run_capability(id="tool:memory_store", input={...})` with a fact such as
   "Offer <role>/<cand>: answer-by <date time tz>, band approver <name>"
   (no figures). Then, as the last action of the turn (it ends the turn):
   `run_capability(id="tool:schedule_followup", input={"message": "Check offer status for <cand> (<role>): answer-by <date time tz>", "delay_seconds": <n>})`.
10. **After the signature,** hand the hire to the first-week owner with the
    start date and team; onboarding is theirs. With Linear connected and the
    owner's yes: `find_capability("linear create issue")` -> `describe_capability`
    -> `run_capability(..., validate_only=true)` -> run, role-level details
    only. A sign-in card means stop and ask the owner to connect.

## Output contract

- Offer brief, letter DRAFT, counter-log.csv and close-plan.csv in
  `~/workspace/hiring/offers/<role-slug>-<candidate-slug>/`, delivered with
  `write_workspace_file(source_path=...)` and a `workspace://` link.
- The reply leads with blockers and open `[OWNER TO CONFIRM]` terms, then
  the brief. Every load-bearing line is FACT, INFERENCE (reasoning shown) or
  UNKNOWN.
- On the owner's confirmation, set the candidate's stage in
  `~/workspace/hiring/tracker/candidates.csv` (offer-out / accepted /
  declined) using interview-coordination's column names.

## Guardrails

- Drafts only. Never send an offer, name a number to a candidate, promise a
  start date, or grant a concession without the approver's and the owner's
  explicit yes for that specific action. Integration writes may also raise
  `approval_required`; wait for it and carry on with independent work.
- Never estimate a band or infer one from stage; never counter above band.
- Never ask about, record or use current or past pay; volunteered history
  is dropped with a one-line note, including from the counter log.
- Competing offers are the candidate's words, labelled unverified; never ask
  for the document.
- Contingency wording and order come only from the template. An adverse
  background-check result stops the skill: route to the owner's FCRA
  adverse-action process and the attorney; draft no plain decline.
- No protected characteristic or health information in any file. Offer
  files hold compensation: never post them to a channel; delete on request
  in the same turn.

## Fallbacks

No band: say so and ask; do not compose around the gap. No template:
outline only (templates/offer-letter-outline.md), clauses
`[COMPANY TEMPLATE REQUIRED]`, route to the attorney. Unverifiable competing
offer: note it as the candidate's words and shape the plan on what you can
verify. Python unavailable: do the arithmetic by hand, show every step, and
label the lines INFERENCE until the owner checks them.

## Quality self-check

Before replying, run checklists/before-anything-reaches-the-candidate.md.
At minimum: every figure traces to `offer_math.py` or an approver; 0 errors
from `check_terms.py`; each close-plan track has one named owner and a
zoned date; no pay history anywhere.

## Examples and references

- examples/priya-nair-backend/walkthrough.md - end to end, with a counter.
- examples/marco-silva-sales-hard-case/walkthrough.md - OTE, volunteered
  pay history, above-band ask, missing FCRA disclosure.
- references/: offer-brief-fields.md, negotiation-and-close.md,
  contingency-order.md, pay-history-and-transparency.md, sources.md.

Siblings in this kit: hiring-debrief-and-decision (the decision this starts
from), interview-coordination (tracker, stall sweep, declines),
hiring-pipeline-analytics (offer acceptance and offers past answer-by).
