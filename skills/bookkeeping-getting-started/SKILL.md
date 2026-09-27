---
name: "bookkeeping-getting-started"
description: "Sets up a safe bookkeeping intake for a business or a new period: entity, reporting period, currency, accounting basis, chart of accounts, approvers, the accountant, where the books live, and a profile of every supplied export with row counts, date ranges, control totals and open gaps. Use when a user starts bookkeeping, takes on a new client or entity, uploads a batch of bank, card, billing, POS or ledger exports (QuickBooks, Xero), asks to catch up their books, or asks what records are needed before expenses, reconciliation or month-end."
triggers: ["set up my bookkeeping", "start bookkeeping with you", "what finance records do you need", "bookkeeping intake checklist", "get my books organised", "new bookkeeping client", "here are my bank statements", "QuickBooks export", "Xero export", "catch up my books"]
version: "2"
---

# Bookkeeping getting started

Use this before sorting expenses, reconciling a statement, drafting an invoice
or a month-end report. The aim is a complete, traceable input set, not a fast
guess. The output is a saved intake that every other bookkeeping skill reads.

**Use when:** a new business, entity or period starts; a user uploads a batch of
exports; another kit skill finds no `intake.json` for the entity; a user asks
what records are needed.
**Do not use for:** coding transactions (expense-categorization), matching a
statement (statement-reconciliation), or tax, payroll or policy questions (the
accountant, via bookkeeping-exception-escalation).

## Inputs and where they come from

| Input | Where it comes from |
| --- | --- |
| Exports (bank, card, processor, POS, billing, payroll, ledger) | User uploads: find with `run_capability(id="tool:list_workspace_files", input={"include_all_sessions": true})`, pull with `read_workspace_file(file_id=..., save_to_path="/home/user/in/<name>")`. Raw CSV exports are fine; do not assume a QuickBooks or Xero file exists [10]. |
| Entity facts, approvers, accountant, basis | The owner, in chat or by `ask_question`. Never inferred. |
| Chart of accounts, coding rules, account definitions | Owner or accountant file. |
| Previous intake | `~/workspace/bookkeeping/<entity-slug>/intake.json` if it exists. |
| Remembered rules | `memory_search` (optional); a hit is a proposal to confirm. |

State layout, file I/O and memory rules: `references/books-state.md`.

## Tools and pre-flight

1. State: `bash_exec` `mkdir -p ~/workspace/bookkeeping/<entity-slug> && test -w ~/workspace/bookkeeping/<entity-slug> && echo STATE_OK`.
   No `STATE_OK` → say "state will not carry to the next chat" and deliver every
   file with `write_workspace_file`.
2. `bash_exec` `python3 --version`. With Python, every count and total in the
   output comes from a script and names it. Without Python, compute by hand and
   label each figure "hand-computed, not script-verified".
3. Data minimisation [63]: before any rows enter the conversation, run
   `cd ~/skills/bookkeeping-getting-started && python3 scripts/redact.py /home/user/in/<file>.csv --out /home/user/work/<file>.masked.csv`
   (add `--keep-column <name>` for a reference the matching needs). It masks
   identifier columns (sort code, account number, IBAN, card) whole and drops
   bank preamble lines; check its `masked by column:` lines before reading any
   row. Work from the masked copy. Ask only for the data the task needs.
4. For a first intake, mirror `checklists/intake-checklist.md` in `TodoWrite`.

## Procedure

1. **Identify the entity and period.** One intake per entity. If files look like
   more than one entity (different account numbers, a location column, personal
   cards), stop and ask which belongs where; never merge periods or entities
   until the owner confirms (see `examples/catch-up-mixed-entity.md`). For a
   catch-up, work oldest period first, one period at a time.
2. **Read the previous intake** if there is one. Changes are confirmed in step 8.
3. **Profile every export:**
   `cd ~/skills/bookkeeping-getting-started && python3 scripts/profile_sources.py /home/user/work/*.masked.csv --out /home/user/work/profile.json`.
   Decisions:
   - `AMBIGUOUS_DATE_FORMAT` → Blocked; ask day/month or month/day. Never pick.
   - `SIGN_CHECK` → ask whether positives are charges; record the answer.
   - `BALANCE_BREAK` or `UNREADABLE_*` → Blocked; that file cannot supply a control total.
   - `NO_ROWS` → Blocked until the owner confirms there were no transactions
     in the period and gives the statement balance for it.
   - `RAGGED_ROWS` or `BOTH_DEBIT_AND_CREDIT` → Blocked; a row has more cells
     than the header or the other rows (usually an unquoted comma), so its
     amount cannot be trusted. Ask for a properly quoted export; never pick
     the amount cell yourself.
   - "no amount column found" on a file with a bank preamble → rerun with
     `--header-line <N>` (the line holding the column names).
   - `DUPLICATE_KEYS` → warning; list them, never drop a row.
   - Dates not covering the period → Usable with a warning or Blocked, per task.
   - XLSX or PDF → ask for a CSV export; for a PDF statement also ask for the
     opening balance, closing balance and period as printed.
   Once the owner confirms format and sign, `scripts/normalize_export.py` writes
   the canonical CSV that later skills read.
4. **Build the intake sheet** (`templates/intake.json`, shown as `templates/intake-sheet.md`). Record:
   1. Entity legal name and reporting period.
   2. Reporting currency and any foreign currencies in the records.
   3. Accounting basis if the owner or accountant has supplied it. Otherwise
      mark it `open`; do not choose one.
   4. Approved chart of accounts and the person who owns changes to it.
   5. Source systems and exports supplied: bank, card, processor, billing,
      payroll, expenses, and ledger.
   6. Opening balances and the record that supports each one.
   7. Who approves invoices, adjustments, customer contact, and final reports,
      and the next owner if the usual approver is the subject of a concern [73].
   8. The accountant or finance owner who receives tax, policy, and material exceptions.
   9. System of record: where the ledger and documents live, `live` or
      `export_only`, and whether the owner holds exported copies [62][85]
      (`references/system-of-record-and-connections.md` has the read-only probe).
   10. Dimensions in use (class, location, job, fund, property), only as supplied [6][12].
   11. Jurisdiction flags: country, VAT or sales tax registration, MTD status for
       UK sole traders, fiscal year end (`references/jurisdiction-flags.md`) [31].
   12. Coding rules and short account definitions, if any [44].

   For each source state its filename or record name, covered dates, export
   time, row count, currency, control total and which fields were masked.
   Documents to request by category: `references/source-document-checklist.md`.
5. **Check readiness:**
   `cd ~/skills/bookkeeping-getting-started && python3 scripts/intake_check.py ~/workspace/bookkeeping/<entity-slug>/intake.json --profile /home/user/work/profile.json`
   The profile of `<name>.masked.csv` is matched to the intake source
   `<name>.csv`; a CSV source with no profile is reported as Blocked, and so is
   a profile `AMBIGUOUS_DATE_FORMAT` without `date_format_confirmed`, and an
   empty `opening_balances` or one with no `evidence` (unless
   `period.first_period` is true because the owner said this is the first ever
   period).
   Sort every source into:
   - **Ready:** present, readable, in period, tied to a control total.
   - **Usable with a warning:** a named gap that does not block the task.
   - **Blocked:** missing dates, unclear entity, broken file, ambiguous date
     format, no opening balance, or totals that do not agree.
6. **Ask the blocking questions** in one `ask_question` call, one question per
   blocking gap, with options (`templates/blocking-questions.md`). Always include
   a "Not sure" route; for basis or tax it is "Not sure: ask the accountant".
   Prefer a source record over a recollection. Record answers in
   `intake.json.open_questions` with the approver as the user stated it.
7. **Prepare the missing-documents request** per document holder
   (`templates/missing-documents-request.md`) and add each item to `open-items.csv`
   in the state folder (columns in `templates/open-items.csv`).
8. **Save and diff.** Write `intake.json` and `intake.md` to the state folder and
   `profile.json` to `profile/<YYYY-MM>.json`. If there was a previous intake,
   run `intake_check.py --previous <old>` and ask the owner to confirm each change.
   Deliver `intake.md` with `write_workspace_file(source_path=...)` as a `workspace://` link.
9. **Offer a cadence (optional).** Ask whether to set up a monthly close kick-off
   or a weekly receivables review. Only on a yes to the exact wording and time,
   create it with `run_capability(id="tool:schedule_routine", input={...})`
   using `templates/cadence-routines.md`; the routine prompt forbids posting,
   sending and contacting anyone.

## Output contract

1. Intake table (entity, period, currency, basis, chart, approvers, accountant,
   system of record, dimensions, jurisdiction flags).
2. Source table: source, dates, rows, control total, state, with the script
   name (or "hand-computed, not script-verified").
3. Ready / Usable with a warning / Blocked lists; one question per blocking gap.
4. Can start now; blocked work; the owner of every open item.
5. Links to `intake.md` (and the missing-documents request if any); the state
   paths written.

## Guardrails

- Never create a missing amount, date, vendor, customer, account, or currency.
- Never choose tax treatment, accounting policy, basis, or a filing position.
- Never post an entry, change a source record, move money, or contact a third
  party. Questions for other people are raised with the user in this chat; the
  user forwards them.
- Keep personal and bank data to the least detail needed; mask before reading;
  store masked account numbers only.
- Never advise discarding or deleting source records; retention questions go
  to the accountant [17][29].
- Connection probes are read-only; never call a write tool during intake.
- If a file or tool fails twice, stop that step and report the gap [71].
- Route payroll, tax, equity, fraud, and material policy questions to a
  qualified accountant or named finance owner (bookkeeping-exception-escalation).

## Quality self-check

- [ ] Every figure names its script or is labelled hand-computed.
- [ ] No date format, sign convention, basis or entity membership was guessed.
- [ ] Every Blocked item has one question and an owner.
- [ ] Nothing from two entities or two periods was merged.
- [ ] The example-style claim "question sent to …" does not appear; nothing was sent.
- [ ] `intake.json` saved (or the no-state warning given) and `intake.md` delivered.

## Related skills

Load with `run_capability(id="skill:<slug>", input={})` when the step is reached:
expense-categorization (card and bank coding), statement-reconciliation
(opening balances, control totals), invoice-drafting-and-issue,
accounts-receivable-follow-up, month-end-close-checklist,
bookkeeping-exception-escalation (tax, payroll, fraud, material items).

## Package files

- `scripts/profile_sources.py`, `normalize_export.py`, `redact.py`,
  `intake_check.py` (shared helpers in `bkio.py`; each has `--selftest`)
- `references/books-state.md`, `source-document-checklist.md`,
  `jurisdiction-flags.md`, `system-of-record-and-connections.md`, `sources.md`
- `templates/intake.json`, `intake-sheet.md`, `blocking-questions.md`,
  `missing-documents-request.md`, `cadence-routines.md`, `open-items.csv`
- `checklists/intake-checklist.md`
- `examples/bramble-april-intake/` (end-to-end with fixtures),
  `examples/catch-up-mixed-entity.md` (hard case)

## Example (short form; full run in `examples/bramble-april-intake/walkthrough.md`)

Fictional intake, Bramble Design Ltd, April 2026, GBP.

| Source | Dates | Rows | Control total | State |
| --- | --- | --- | --- | --- |
| Bank export, ****4417 | 1 to 12 Apr (format ambiguous) | 8 | none usable | Blocked: day/month unconfirmed (Q1); stops 12 Apr (Q2); 30.00 balance break at line 8 |
| Card export, Amex ****1009 | 3 to 28 Apr | 8 | 900.69 as exported (profile_sources.py) | Usable with a warning: duplicate pair 18 Apr; charges positive (confirmed) |
| Ledger trial balance | to 31 Mar | — | opening balances | Blocked: March not yet signed off by the accountant (Q3) |
| Payroll report | — | — | — | Blocked: not supplied |

Accounting basis: open (Jo: "ask the accountant"). Approvers: invoices and
customer contact, Jo (director); adjustments and final reports, Dev Patel
(external accountant).

Can start now: expense categorisation for the card export; invoice list check.
Blocked: statement reconciliation until Q1 to Q3 are answered (question card
raised with Jo in this chat; Jo to forward Q3 to Dev); payroll tie-out until
Jo supplies the April payroll report.
