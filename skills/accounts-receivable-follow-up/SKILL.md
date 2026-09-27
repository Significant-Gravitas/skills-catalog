---
name: "accounts-receivable-follow-up"
description: "Reviews open receivables at a stated cutoff and drafts factual, staged payment follow-ups without inventing status or contacting a customer: builds the aging from invoice and payment exports, checks the bank for payments not yet applied before any chase, keeps disputes, part-payments and promised dates visible, and drafts the next reminder or statement of account for the owner's approval. Use when a user asks who owes money or who hasn't paid, wants an aged debtors or receivables review, needs to chase an overdue invoice, draft a payment reminder or statement of account, or run credit control."
triggers: ["chase an overdue invoice", "draft a payment reminder", "which customers owe us money", "customer hasn't paid their invoice", "review open receivables", "overdue invoice follow-up", "aged debtors report", "credit control", "who hasn't paid us", "send a statement of account"]
version: "2"
---

# Accounts receivable follow-up

Use this to prepare a receivables review and message drafts. The owner approves
all customer contact.

**Use when:** reviewing who owes what, chasing an overdue invoice, preparing a
reminder or statement of account.
**Do not use for:** drafting a new invoice (invoice-drafting-and-issue),
applying cash or writing off a debt in the ledger (the owner; write-offs the
accountant), or disputes, hardship, insolvency and legal threats beyond
acknowledging and routing them (bookkeeping-exception-escalation).

## Inputs and where they come from

| Input | Where it comes from |
| --- | --- |
| Invoice export (invoice, customer, currency, issue date, due date or terms, amount, credits, billing contact) | Billing system or ledger export (`templates/invoice-export.csv` shows the columns), pulled with `read_workspace_file(..., save_to_path="/home/user/in/<name>")` |
| Payment records through a stated cutoff time | Same export or a payments report |
| Newest bank export | Upload; normalised with `scripts/normalize_export.py` |
| Dispute log, contact log | `dispute-log.csv`, `contact-log.csv` in the state folder (templates in `templates/`) |
| Last customer contact, remittances, promises | Mailbox, read-only, if connected (`references/evidence-and-sending.md`); otherwise the account owner |
| Account owner, approver, mailbox | `intake.json` (`ar.account_owner`, `approvers.customer_contact`, `ar.mailbox`); a null or "not supplied" field is asked of the owner. No intake → load `run_capability(id="skill:bookkeeping-getting-started", input={})` |

State, file I/O and memory: `references/books-state.md`.

## Tools and pre-flight

1. State pre-flight (`references/books-state.md`, section 1).
2. `bash_exec` `python3 --version`. With Python, balances, days and buckets come
   from the scripts and are named. Without it, compute by hand and label them
   "hand-computed, not script-verified".
3. State the evidence cutoff (date and time of the payment records) before any figure.

## Procedure

1. **Verify before calling an invoice overdue.** For each open invoice, collect
   the invoice record, customer, currency, issued date, due date, original
   amount, credits, payments, open balance, last contact, dispute status, and
   account owner. Check payment records through the stated cutoff time. If the
   due date or balance cannot be proved, mark the item `status unconfirmed`
   rather than overdue. An invoice with no due date shows in a ledger as due on
   receipt [97]; confirm the agreed terms first.
2. **Look for money already received:**
   `cd ~/skills/accounts-receivable-follow-up && python3 scripts/find_unapplied.py --bank /home/user/work/bank.csv --invoices /home/user/in/invoices.csv --payments /home/user/in/payments.csv --cutoff "<YYYY-MM-DD HH:MM>" --out /home/user/work/unapplied.csv`.
   Also ask about deposits in undeposited funds and unapplied credits [88].
   Any candidate → `status unconfirmed`, no chase; the owner applies the cash.
   That includes the weakest kind, "customer name, amount differs (possible
   part or combined payment)": a credit from the customer for a different
   amount may be a part-payment, so ask before chasing the full balance
   (match kinds: `references/aging-and-terms.md`, section 3).
   `BANK_COVERAGE_GAP` (exit 1: the bank export ends before the cutoff) → no
   draft is offered for sending yet. Ask in one `ask_question` card: "The bank
   export ends <d>; payments after that cannot be seen. How should I proceed?"
   Options: `I will upload a newer bank export` · `Chase anyway: I confirm
   nothing arrived after <d>` · `Not yet`. Record the answer verbatim (who, when)
   in the contact log's `reply_summary` for each affected invoice, and state
   the gap in every approval question until a newer export closes it.
3. **Age the ledger:**
   `cd ~/skills/accounts-receivable-follow-up && python3 scripts/ar_aging.py --invoices ... --payments ... --cutoff "<YYYY-MM-DD HH:MM>" --disputes <state>/dispute-log.csv --contact-log <state>/contact-log.csv --unapplied /home/user/work/unapplied.csv --out /home/user/work/aging.csv`.
   Buckets Current / 1-30 / 31-60 / 61-90 / 90+ by days past the due date [97][98]
   are the default; confirm with the owner. Payments after the cutoff are ignored
   and listed. `--unapplied` also reads the bank coverage that find_unapplied.py
   wrote beside it (`unapplied.coverage.json`); while the bank export ends before
   the cutoff, each chaseable row's next stage is `hold: bank export ends <d>`
   (planned stage in notes). After the owner's answer, rerun with a newer bank
   export, or with `--coverage-confirmed "<owner's words, verbatim>"`.
   Details: `references/aging-and-terms.md`.
4. **Prioritise the queue.** Groups:
   - due soon;
   - past due with no known dispute;
   - disputed or blocked;
   - promised payment not yet due;
   - status unconfirmed.
   Within each group, sort by age and open balance, oldest bucket first, then
   note any named customer or contract rule that changes the handling. Do not
   invent a credit policy.
5. **Check the evidence** (optional, if mail is connected): search only threads
   matching the invoice number or customer domain; quote dated lines that prove a
   dispute, remittance or promise, and log them.
6. **Draft the next stage only** (`templates/reminder-stages.md`), reading the
   contact log so no stage repeats: first reminder → second reminder → statement
   of account (`cd ~/skills/accounts-receivable-follow-up && python3 scripts/render_statement.py ...`,
   one customer only; it leaves off disputed, unconfirmed and promised items) → owner call.
   Each draft states the invoice number, issue and due dates, open balance,
   currency, and the requested next step. Keep the tone calm. Ask whether payment
   has been made or whether a record is missing. For a dispute, acknowledge the
   stated issue and route it to the owner; do not argue the contract. Record
   disputes in the dispute log (stated issue, date, evidence, owner, status) [14].
7. **UK statutory interest** only if the owner opts in and confirms UK B2B with
   no contract rate: fetch the reference rate, then
   `cd ~/skills/accounts-receivable-follow-up && python3 scripts/uk_late_interest.py ...`
   (`references/uk-late-payment.md`) [30][47]. Otherwise never mention it.
8. **Ask for approval** with one `ask_question` call, one question per draft,
   naming the draft, amount, mailbox and recipient. Hash each draft before asking
   and record answers with
   `cd ~/skills/accounts-receivable-follow-up && python3 scripts/log_approval.py record ... --option "<label exactly as picked>"`
   (`references/evidence-and-sending.md`, section 2). Only `Send exactly as
   shown` is a yes to send; `I will send it myself` means the owner sends it.
9. **Send only what was approved.** After a verified yes for that message and
   recipient, send through the connected mail tool (`references/evidence-and-sending.md`:
   find, describe, validate_only, send; wait on `approval_required`). No mail tool
   or a sign-in card → the owner sends it.
10. **Log and schedule.** Append contact-log rows (draft stage, evidence cutoff,
    owner, approval state, sent by, next review date). Offer a follow-up for the
    next review date and a weekly review (`templates/follow-up-and-routine.md`);
    create neither without a yes. `schedule_followup` ends the turn, so it goes last.

## Output contract

1. Cutoff line: "Payment records to <date time>; bank export to <date>." If
   the bank export ends before the cutoff, say so and show the gap question.
2. Aging table: invoice, customer, due (or "none on record"), open (with
   part-payment), days past due, bucket, group, next stage; open balance by bucket.
3. Unapplied-payment candidates and the question for the owner.
4. Drafts, each ending with the exact action awaiting a yes, for example "send
   this email from accounts@ to the billing contact".
5. Contact-log rows; disputes routed; items for the owner or accountant.

## Guardrails

- Never send a message, call a customer, apply a fee, stop service, change an
  invoice, or threaten collection. Only after an explicit yes for that exact
  message and recipient, recorded against the draft's hash, may a connected mail
  tool send it; otherwise the owner sends it.
- Drafts must not claim a late fee, interest, service stop, collection action, or
  legal consequence unless an approved policy and owner instruction support it.
- Never chase an invoice with a possible unapplied payment, no confirmed due
  date, an open dispute, or a promised date still to come.
- Never expose another customer's data: one customer per draft and statement;
  read only matching mail threads.
- No base rate, interest rate or fixed sum from memory [30][47].
- If a file or tool fails twice, stop and report the gap [71].
- Route disputes, hardship, insolvency, legal threats, sanctions, write-offs and
  material customer risk to the finance owner, the accountant or counsel
  (bookkeeping-exception-escalation) [38].

## Quality self-check

- [ ] The cutoff is stated and no payment after it was counted.
- [ ] `find_unapplied.py` ran before any draft, or its absence is stated.
- [ ] Every "overdue" invoice has a due date or agreed terms on record.
- [ ] Each draft is the next stage from the contact log, names one customer, and has no threat.
- [ ] Every figure names its script or is labelled hand-computed.
- [ ] Nothing was sent without a verified approval for that message.

## Related skills

invoice-drafting-and-issue (the invoices being chased), statement-reconciliation
(applying the bank side), month-end-close-checklist (control 4 uses this review),
bookkeeping-exception-escalation (disputes and material risk). Load with
`run_capability(id="skill:<slug>", input={})` when the step is reached.

## Package files

- `scripts/ar_aging.py`, `find_unapplied.py`, `render_statement.py`,
  `uk_late_interest.py`, `log_approval.py`, `normalize_export.py` (shared helpers
  `bkio.py`; each has `--selftest`)
- `references/aging-and-terms.md`, `evidence-and-sending.md`,
  `uk-late-payment.md`, `books-state.md`, `sources.md`
- `templates/reminder-stages.md`, `statement-of-account.html`,
  `follow-up-and-routine.md`, `contact-log.csv`, `dispute-log.csv`, `invoice-export.csv`
- `checklists/before-drafting.md`
- `examples/bramble-april-ar/` (end-to-end with fixtures, including a paid-but-unapplied invoice)

## Example (short form; full run in `examples/bramble-april-ar/walkthrough.md`)

Fictional records, cutoff 30 Apr 2026 17:00, billing export of the same time;
bank export to 12 Apr. `find_unapplied.py` reports `BANK_COVERAGE_GAP: bank
ends 2026-04-12, cutoff 2026-04-30`, so before any draft is offered for sending
Sam is asked for a newer bank export or to confirm nothing arrived after 12 Apr.

| Invoice | Customer | Due | Open | Days past due | Group |
| --- | --- | --- | --- | --- | --- |
| INV-1039 | Kestrel Joinery Ltd | 28 Feb | £2,150.00 | 61 | past due, no known dispute: second reminder, on hold (bank export ends 12 Apr) |
| INV-1047 | Tallow & Wick | 15 Apr | £640.00 of £1,280.00 (part-paid 9 Apr) | 15 | past due, no known dispute: first reminder, on hold (bank export ends 12 Apr) |
| INV-1051 | Greyline Studio | 20 Apr | £2,400.00 | 10 | disputed: email of 22 Apr says phase 2 not delivered; routed to Sam (account owner) |
| INV-1042 | Harbour Florists Ltd | 31 Mar | £1,800.00 | 30 | status unconfirmed: bank shows £1,800.00 on 10 Apr naming INV-1042; ask Sam to apply it |
| INV-1055 | Pell Cafe | none on record | £350.00 | — | status unconfirmed: ask Sam for the agreed terms |

Draft for INV-1047 (awaiting Sam's approval to send):

> Subject: Invoice INV-1047, £640.00 remaining, due 15 April
>
> Hi, thank you for the £640.00 received on 9 April. Our records show £640.00
> of invoice INV-1047 (issued 16 March, due 15 April) is still open. If the
> balance has already been paid, could you send the remittance so we can match
> it? If not, please let us know when to expect payment. Thanks, Sam

Awaiting approval (and Sam's answer on the 13-30 Apr bank gap): "send this
email from accounts@bramble.example to hello@tallow.example". Contact log:
INV-1047 | first reminder | evidence cutoff 30 Apr 17:00; bank to 12 Apr | owner
Sam | approval pending | next review 7 May.
