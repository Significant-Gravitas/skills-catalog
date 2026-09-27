---
name: "expense-categorization"
description: "Turns receipts and bank or card transaction exports into a sourced expense review table without guessing at unclear items or tax treatment: each line gets its source row, evidence, a proposed account from the owner's own chart, a reason, a confidence level and the one fact still needed, split into ready-to-post and needs-review with totals that tie to the export. Use when a user shares a bank or card export, bank-feed lines awaiting review (QuickBooks For Review, Xero uncategorised), or receipts and wants each item coded to their chart of accounts, or asks what a charge is."
triggers: ["categorize these expenses", "code my card transactions", "sort these receipts into accounts", "which account does this expense go in", "expense review table", "uncategorized transactions", "code my bank feed", "code this charge on my statement", "match receipts to transactions", "For Review transactions"]
version: "2"
---

# Expense categorization

Use this to prepare expenses for review. A proposed category is not a posted
entry and not tax advice.

**Use when:** coding card or bank lines, matching receipts to payments,
answering "which account does this go in". If the user does not recognise a
charge at all (possible fraud, an unknown payee), load
`run_capability(id="skill:bookkeeping-exception-escalation", input={})` instead
of coding it.
**Do not use for:** matching a statement to the ledger (statement-reconciliation),
customer receipts and invoices (invoice-drafting-and-issue,
accounts-receivable-follow-up), or deciding deductibility, capitalisation or
worker classification (the accountant).

## Inputs and where they come from

| Input | Where it comes from |
| --- | --- |
| Transaction export (card, bank) | Upload, pulled with `read_workspace_file(file_id=..., save_to_path="/home/user/in/<name>")`; or, if the ledger is `live` in `intake.json`, a read-only capability (`references/confidence-and-coding.md`, section 4) |
| Receipts and invoices | Uploads saved to `/home/user/in/receipts/`; `scripts/receipt_text.py` extracts candidates; otherwise the user types date, total and merchant. Confirm each extracted row with the user (date as YYYY-MM-DD, total, currency) before passing the receipts CSV to `expense_checks.py --receipts` |
| Approved chart of accounts (exact names, short definitions) | Owner or accountant; `intake.json.chart` |
| Entity, period, currency, sign convention, dimensions | `~/workspace/bookkeeping/<entity-slug>/intake.json`. None → load `run_capability(id="skill:bookkeeping-getting-started", input={})` first |
| Coding rules and history | `coding-rules.csv` and `expenses/*-review.csv` in the state folder; `memory_search` hits are proposals only |

Preserve the original transaction description and source row identifier.
State, file I/O and memory: `references/books-state.md`.

## Tools and pre-flight

1. State pre-flight (`references/books-state.md`, section 1).
2. `bash_exec` `python3 --version`. With Python, every total comes from the
   scripts and names them. Without it, work by hand and label each total
   "hand-computed, not script-verified".
3. Money is exact decimal; never round an intermediate value.

## Procedure

1. **Normalise** each export (once the owner has confirmed date format and sign):
   `cd ~/skills/expense-categorization && python3 scripts/normalize_export.py /home/user/in/<file>.csv --date-format <fmt> [--flip-sign] [--currency <CCY>] --out /home/user/work/<file>.csv`
2. **Run the checks** (add a second `--tx` to check card and bank together, which
   also finds a cost paid on both):
   `cd ~/skills/expense-categorization && python3 scripts/expense_checks.py --tx /home/user/work/<file>.csv [--receipts /home/user/work/receipts.csv] [--control-total <statement total>] --out /home/user/work/checks.json`
   Decisions:
   - Control total does not tie (exit 1) → stop coding; report the difference and
     ask for the full export. Do not code a partial file.
   - Duplicate pairs → keep both rows; one question per pair.
   - Receipt with no payment line → exception, never support [60].
   - Special lines (refund, transfer, card payment, owner, loan, tax, payroll,
     processor, foreign currency, money in) → handle per `references/special-lines.md`.
   - Substantiation flags (US) only when the owner or accountant supplied the
     threshold: `--threshold <value> --threshold-source "<who, date>"`
     (`references/substantiation-us.md`).
3. **Propose from rules and history:**
   `cd ~/skills/expense-categorization && python3 scripts/propose_from_history.py --tx ... --rules <state>/coding-rules.csv --history <state>/expenses/ --checks /home/user/work/checks.json --chart <chart.csv> --out /home/user/work/proposals.csv`
   A cap is a ceiling. Reason only over rows with basis `none`, a conflict, or a
   special line. In a first period with a client, expect lower confidence and
   cite the account definition in each reason [59][44].
4. **Work each item** into `templates/expense-review-template.csv` (column rules in
   `templates/review-table-guide.md`):

   | Field | Rule |
   | --- | --- |
   | Source | File or system plus row identifier |
   | Date | Use the source date; keep transaction and posting dates separate |
   | Vendor | Use the receipt or source text; do not infer a legal name |
   | Amount | Keep sign and currency |
   | Evidence | Receipt, invoice, contract, or `missing`; says whether it ties |
   | Payment line | The card or bank row that pays for the evidence, or `none` |
   | Proposed category | Exact approved account name, or `unresolved` |
   | Class / location / job / fund | Only from supplied lists |
   | Reason | One sentence tied to the evidence |
   | Confidence | High, medium, or low |
   | Review need | The one fact or owner needed next |

   Use high confidence only when the evidence ties to the payment line and
   written rules point to one approved account. Use medium when the purpose is
   clear but more than one account could fit, or the basis is history only. Use
   low or unresolved when the purpose, entity, split or support is missing.
   Include items that bank rules auto-added without review [100].
5. **Validate and split:**
   `cd ~/skills/expense-categorization && python3 scripts/write_review.py --review /home/user/work/review.csv --tx /home/user/work/<file>.csv --chart <chart.csv> --checks /home/user/work/checks.json --proposals /home/user/work/proposals.csv [--control-total <x>] --outdir /home/user/out/expenses-<YYYY-MM>`
   Exit 2 means the table dropped, repeated or edited a source row, has a
   shifted column (quote any field containing a comma), or used an account not
   in the chart: fix the table, never the export. `--checks` and `--proposals`
   keep exact duplicates, special lines, rows above their proposal cap and
   rows sharing one receipt out of Ready to post. An owner's split is entered
   as numbered parts in `split_part` that add up exactly to the source amount.
6. **Settle the review queue** with one `ask_question` call: up to 10 items,
   largest first, options from the approved chart plus "Personal / owner item",
   "Split: I will give the amounts" and "Not sure: send to the accountant"
   (`templates/review-queue-questions.md`). Never offer a tax option.
7. **Record answers.** Update the table; when the owner says "always", add an
   approved rule to `coding-rules.csv` (approver as stated, date) and, if memory
   is on, store it as a rule for this entity. Items for the accountant: load
   `run_capability(id="skill:bookkeeping-exception-escalation", input={})`.
8. **Deliver.** In chat show only the Needs review rows and the totals; deliver
   `ready-to-post.csv`, `needs-review.csv`, `totals.md` (and `review.xlsx` if
   written) with `write_workspace_file(source_path=...)` as `workspace://` links;
   save the table to `<state>/expenses/<YYYY-MM>-review.csv`. A Google Sheet only
   if asked, append-only, after a yes naming the sheet (`references/confidence-and-coding.md`, section 5).

## Output contract

1. One line: "N ready to post, M need review", with the source file and period.
2. Needs review rows: source, date, vendor, amount, evidence, proposed category,
   reason, confidence, review need.
3. Totals (from `write_review.py`): source rows and amount, ready, needs review,
   unresolved, excluded with reasons, tie to the control total.
4. Exceptions: receipts with no payment line, duplicate pairs, special lines.
5. Links to the files; the question card; rules added.

## Checks

- Total source rows, total amount, categorized rows, and unresolved rows.
- Find exact and likely duplicates without deleting either one.
- Keep refunds, reversals, transfers, owner transactions, loan payments, tax
  payments and card payments apart from operating expenses [81][78][77].
- Flag foreign-currency items and preserve both source and settled amounts when supplied.
- Show any row excluded from the total and why.
- Full pre-delivery list: `checklists/before-delivery.md`.

## Guardrails

- Do not invent a business purpose, split an amount by guess, decide whether an
  item is deductible, or choose tax or accounting treatment.
- A receipt counts as support only when it ties to a card or bank line [60].
- Do not quote a tax, 1099, capitalisation or substantiation threshold from
  memory; use only a supplied figure or one fetched from the current official
  source with its tax year [65][76].
- Do not post entries, push categories into a ledger, or edit the source.
  Ledger access here is read-only.
- Options offered to the owner come only from the approved chart.
- If a file or tool fails twice, stop and report the gap [71].
- Route payroll, owner distributions, fixed assets, loans, taxes, gifts,
  contractor classification, legal settlements, and suspected fraud to the
  finance owner or a qualified accountant.

## Quality self-check

- [ ] Every figure names its script or is labelled hand-computed.
- [ ] Ready + Needs review equals the source total; the control total ties or the gap is stated.
- [ ] No row in Ready has missing evidence, a special line or an open question.
- [ ] No duplicate was deleted; no amount was split or converted by guess.
- [ ] No tax treatment appears anywhere in the output.

## Related skills

bookkeeping-getting-started (no intake yet), statement-reconciliation (bank
side of the same lines), month-end-close-checklist (control 3 uses this table),
bookkeeping-exception-escalation (accountant items). Load with
`run_capability(id="skill:<slug>", input={})` when the step is reached.

## Package files

- `scripts/normalize_export.py`, `expense_checks.py`, `propose_from_history.py`,
  `write_review.py`, `receipt_text.py` (shared helpers `bkio.py`; each has `--selftest`)
- `references/special-lines.md`, `substantiation-us.md`,
  `confidence-and-coding.md`, `books-state.md`, `sources.md`
- `templates/expense-review-template.csv`, `review-table-guide.md`,
  `review-queue-questions.md`, `coding-rules.csv`
- `checklists/before-delivery.md`
- `examples/bramble-april-card/` (end-to-end with fixtures and `expected-review.csv`),
  `examples/hard-lines/` (bank lines that are not expenses)

## Example (short form; full run in `examples/bramble-april-card/walkthrough.md`)

Fictional rows from `amex-2026-04.csv`, chart of accounts v2 (Bramble Design Ltd).

| Source | Date | Vendor | Amount | Evidence | Proposed category | Reason | Conf. | Review need |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| amex:2 | 03 Apr | FIGMA | -£45.00 | R1 receipt (ties) | Software subscriptions | Monthly seat invoice names Figma Professional; rule R1 | High | — |
| amex:3 | 07 Apr | TRAINLINE | -£118.40 | R2 receipt (ties) | Travel | Return ticket; receipt notes "client visit, Leeds" | Medium | Confirm client travel vs staff training (coding rule 4 splits them) |
| amex:4 | 09 Apr | AMZN MKTP UK | -£612.99 | missing | unresolved | No receipt; could be equipment or supplies | Low | Receipt, and whether it is a fixed asset (accountant) |
| amex:5 | 15 Apr | FIGMA | -£45.00 | missing | unresolved | Likely duplicate of amex:2 (same amount and vendor, 12 days apart) | Low | Jo: second seat or duplicate charge? (refund on amex:8) |

Totals (write_review.py): 8 rows, -£900.69, ties to the export; 1 ready to
post, 7 need review, 4 unresolved, 0 excluded. Exception: receipt R4
(Screwfix £89.00) has no card line.
