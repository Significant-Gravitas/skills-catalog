---
name: "invoice-drafting-and-issue"
description: "Drafts a customer invoice from approved commercial terms (contract, SOW, purchase order or recurring schedule), recalculates its totals exactly, checks the required fields for the seller's jurisdiction and the invoice register for double billing, renders a watermarked DRAFT, and holds numbering, issue and send for the owner's explicit approval. Use when a user wants to bill or invoice a customer, raise a monthly retainer or VAT invoice, turn a contract into an invoice, or check an invoice before it is issued."
triggers: ["draft an invoice for this client", "invoice the customer for this month", "create an invoice from this contract", "check this invoice before it goes out", "issue an invoice", "raise an invoice", "bill the client for", "monthly retainer invoice", "VAT invoice"]
version: "2"
---

# Invoice drafting and issue

Draft from approved commercial records. Never turn a chat request into a sent
invoice without a review step. The owner numbers, issues and sends; Mina
drafts, checks and records.

**Use when:** billing a customer from a contract, SOW, PO, signed change or
recurring schedule; checking an invoice before it goes out.
**Do not use for:** chasing unpaid invoices (accounts-receivable-follow-up),
credit notes, voids, write-offs, tax treatment, cross-border or revenue-policy
questions (the accountant, via bookkeeping-exception-escalation).

## Inputs and where they come from

| Input | Where it comes from |
| --- | --- |
| Contract, SOW, PO, signed change, approver email | Uploads pulled with `read_workspace_file(..., save_to_path="/home/user/in/<name>")` |
| Seller details, jurisdiction, VAT/sales-tax registration, approver | `~/workspace/bookkeeping/<entity-slug>/intake.json` (`entity.address`, `entity.contact`, `entity.vat_number`, `approvers.invoices`). A field that is null or "not supplied" is asked of the owner, never filled in. No intake → load `run_capability(id="skill:bookkeeping-getting-started", input={})` |
| Tax fields (rate, treatment, rounding method) | The owner or accountant only |
| Payment instructions | The approved record, or the owner typing them |
| Invoice register, previous invoices | `invoice-register.csv` in the state folder; a billing export wins over it |

State, file I/O and memory: `references/books-state.md`.

## Tools and pre-flight

1. State pre-flight (`references/books-state.md`, section 1).
2. `bash_exec` `python3 --version`. With Python, totals and checks come from
   the scripts and are named. Without it, compute by hand and label every total
   "hand-computed, not script-verified".
3. Work in `/home/user/work/`; deliverables in `/home/user/out/`.

## Procedure

1. **Gather the terms.** Require the legal seller and customer names, billing
   addresses, purchase order or contract reference, approved line items,
   quantity, rate, currency, service or delivery period, invoice date, due
   terms, payment instructions, and any tax fields supplied by the owner or
   accountant. If a term is missing, leave a marked blank. Do not copy a bank
   detail, tax ID or customer address from an unrelated invoice without
   confirmation. A changed bank detail is an exception for the owner to verify
   through a known contact [61].
2. **Build `draft.json`** from `templates/draft.json`: one line per approved
   charge with a line key `<contract>/<line>/<service period>`, a source per line
   and term, conflicts listed with both sources, blanks listed in `missing`.
3. **Recurring billing:** compare with the previous invoice for the same line and
   the schedule; list every change and its source (`references/recurring-billing.md`) [14].
4. **Run the checks:**
   ```
   cd ~/skills/invoice-drafting-and-issue && python3 scripts/invoice_totals.py /home/user/work/draft.json --write
   cd ~/skills/invoice-drafting-and-issue && python3 scripts/field_check.py /home/user/work/draft.json --regime <uk-vat|uk-general|other>
   cd ~/skills/invoice-drafting-and-issue && python3 scripts/register_check.py /home/user/work/draft.json --register <state>/invoice-register.csv [--billing-export /home/user/in/<export>.csv]
   ```
   Decisions:
   - Tax requested but a rate is blank (exit 2) → leave tax blank; ask the accountant.
   - Per-line and per-invoice tax differ → show both; the owner or accountant picks.
   - `REPEAT` or `REPEAT IN DRAFT` line key → remove the line or ask; never bill a period twice.
   - Register empty or gappy → ask for the billing export; the export wins.
   - BLOCKS APPROVAL items → approval is not asked until each is settled.
   Regime: UK and VAT registered → `uk-vat`; UK not registered → `uk-general`;
   otherwise `other` (`references/invoice-field-checklists.md`) [48][28].
5. **Customer tax ID** (only if one is on the draft): check per
   `references/tax-id-checks.md` and record valid, invalid or unchecked.
6. **Render the draft:**
   `cd ~/skills/invoice-drafting-and-issue && python3 scripts/render_invoice.py /home/user/work/draft.json --out /home/user/out/draft-<id>.html --pdf`
   (HTML if no headless Chrome). The DRAFT watermark cannot be removed.
   Deliver with `write_workspace_file(source_path=...)` as a `workspace://` link.
7. **Review block** (`templates/review-block.md`): totals checked; missing fields;
   term or source conflicts; double-billing and numbering results; named
   approver; the exact action awaiting approval.
8. **Settle and approve** with one `ask_question` call (`templates/approval-questions.md`):
   one question per conflict (each source an option), one per missing field
   (never a guessed value), then, only when nothing blocks approval, the action
   question. Before writing that question, run `find_capability` and
   `describe_capability` for "<system> create invoice"
   (`references/approval-and-ledger-draft.md` section 3, steps 1-2); offer the
   "create it in <system> as a Draft" option only when a tool that can create
   with status Draft is present. Otherwise the options are "I will number and
   issue it myself", "Approve with the changes I type" and "Not yet".
   Hash the rendered draft before asking and record the answer:
   `cd ~/skills/invoice-drafting-and-issue && python3 scripts/log_approval.py record --artefact ... --shown-sha ... --action "create draft <id> in <system> with status Draft" --approver "<as stated>" --option "<label exactly as picked>" --log <state>/approvals.csv`
   (a typed answer goes in `--reply "<verbatim>"`). Only the "create it in
   <system> as a Draft" option, or a typed reply that itself names creating
   it in that system, records an approval for Mina to act; a bare "yes" does
   not (it could mean "I will issue it myself"), so ask again. "I will
   number and issue it myself" is recorded in `invoice-register.csv`
   (`status=approved_to_issue`, evidence = the verbatim answer), not as an
   action for Mina. "Approve with the changes I type" means edit, re-render,
   re-hash and ask again. Any edit after a yes needs a new yes.
9. **Optional ledger draft.** Only if the recorded approval names "create draft
   <id> in <system>" and
   `cd ~/skills/invoice-drafting-and-issue && python3 scripts/log_approval.py verify --artefact ... --action "..." --log <state>/approvals.csv`
   prints "approved by …": follow
   `references/approval-and-ledger-draft.md` section 3 (find, describe, confirm
   the status field is Draft, validate_only, then create). If the platform holds
   the call (`approval_required`), wait. Never authorise, approve, finalise,
   void or send. No capability or no Draft status → give the owner the PDF and
   figures instead.
10. **Record what happened.** Append the register row as `draft`,
    `draft_in_ledger` (with the ledger id) or, when the owner reports it,
    `issued_per_owner` with who, when and the evidence. Offer a recurring
    preparation routine if billing is scheduled (`references/recurring-billing.md`).

## Output contract

1. The draft (as a table in chat plus the `workspace://` document), showing:
   draft number or `to be assigned`; seller and bill-to details; contract or PO
   reference; one line per approved charge with description, period, quantity,
   rate, line total and source; subtotal, supplied discount, supplied tax and
   grand total; currency, due date, payment instructions and remittance reference.
2. Script outputs: totals with rounding stated, field check, register check.
3. Differences from the contract or approved order, each listed.
4. The review block ending with the exact action awaiting approval, or the
   blockers that prevent any action.

## Guardrails

- Never invent a charge, tax rate, payment detail, due date, or contract term.
- Never change agreed pricing, choose or assign an invoice number yourself,
  issue or send an invoice, contact the customer, or move money. The owner does
  these. The only write Mina may make is creating the invoice with Draft status
  in the billing system, after a recorded yes naming that action. If the billing
  system assigns a number when the draft is created, record that number and
  tell the owner; never pass a number of your own choosing.
- Do not claim the invoice exists outside the draft until a supplied record
  proves it.
- Tax on an invoice is a liability, not revenue; show it separately and only as
  supplied [77].
- Never bill a contract line for a period already in the register or billing export.
- If a file or tool fails twice, stop and report the gap [71].
- Route tax, withholding, cross-border, credit-note, and revenue-policy
  questions to the accountant or finance owner.

## Quality self-check

- [ ] Every line and term cites a source; blanks are marked, not filled.
- [ ] Totals come from `invoice_totals.py` (or are labelled hand-computed).
- [ ] `field_check.py` and `register_check.py` results are in the review block.
- [ ] The rendered draft carries the DRAFT watermark.
- [ ] No approval was asked while something blocked approval; every yes is logged against the hash.
- [ ] Nothing says "sent" or "issued" without the owner's word or a record.

## Related skills

accounts-receivable-follow-up (after issue), bookkeeping-getting-started (no
intake), bookkeeping-exception-escalation (tax, credit notes, bank-detail
changes), month-end-close-checklist (invoicing complete before close). Load with
`run_capability(id="skill:<slug>", input={})` when the step is reached.

## Package files

- `scripts/invoice_totals.py`, `field_check.py`, `register_check.py`,
  `render_invoice.py`, `log_approval.py` (shared helpers `bkio.py`; each has `--selftest`)
- `references/invoice-field-checklists.md`, `approval-and-ledger-draft.md`,
  `tax-id-checks.md`, `recurring-billing.md`, `books-state.md`, `sources.md`
- `templates/draft.json`, `invoice-draft.html`, `review-block.md`,
  `approval-questions.md`, `invoice-register.csv`
- `checklists/before-approval.md`
- `examples/oriel-april/` (end-to-end: double-billed retainer, rate conflict, missing VAT)

## Example (short form; full run in `examples/oriel-april/walkthrough.md`)

Fictional draft from SOW-014 (signed 2 Jan 2026) and PO 7781.

> **DRAFT invoice, number to be assigned.** Invoice date 30 Apr 2026. Due 30
> May 2026 (net 30, SOW-014 clause 6).
> Seller: Bramble Design Ltd. Bill to: Oriel Health Ltd, 4 Quay St, Bristol.
> Ref: PO 7781 / SOW-014.
>
> | Line | Period | Qty | Rate | Total | Source |
> | --- | --- | --- | --- | --- | --- |
> | Extra workshop day | 14 Apr | 1 | £900.00 | £900.00 | Email approval, M. Ode, 10 Apr |
>
> Subtotal £900.00. VAT: blank, rate not supplied (ask accountant). Total
> before VAT £900.00. Payment details: blank, not in the approved record.

Review block: totals rechecked by invoice_totals.py, no rounding. Removed: the
April retainer (£3,500.00, SOW-014 cl. 4) is already on INV-1045, approved 2
April (register_check.py REPEAT). Missing: VAT treatment, seller VAT number,
bank details, invoice number. Conflict: SOW rate for extra days is £850; the
email says £900. Approver: Jo. Awaiting approval: none of assign, create, issue
or send can happen until the three blanks and the rate conflict are settled.
