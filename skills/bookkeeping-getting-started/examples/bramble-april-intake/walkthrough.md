# Worked example: Bramble Design Ltd, April 2026 intake (fictional)

Inputs in this folder: `bank-main-2026-04.csv` (8 rows, trimmed fixture),
`amex-2026-04.csv` (8 rows), and the resulting `intake.json`. The owner, Jo,
uploaded both files and said "can you get my books sorted for April? Dev does
our accounts."

Hard cases this example tests: dates that read both ways (03/04/2026), an
export that stops mid-month, a running-balance break, an exact duplicate pair,
a card export with charges as positives, an opening balance that is only
implied, and a basis nobody has chosen.

## 1. Pre-flight

- State: `mkdir -p ~/workspace/bookkeeping/bramble-design && test -w … && echo STATE_OK` → `STATE_OK`.
- No earlier `intake.json`. `memory_search` returned nothing for Bramble.
- `python3 --version` → Python 3 present, so every figure below is script output.
- Files pulled with `read_workspace_file(..., save_to_path="/home/user/in/<name>")`.
- `redact.py` on each file (`--out /home/user/work/<name>.masked.csv`) masked
  0 values (the fixtures hold no account numbers); the `Reference` column was
  kept with `--keep-column Reference` because matching needs it. Everything
  below reads the masked copies.

## 2. Profile

```
cd ~/skills/bookkeeping-getting-started && python3 scripts/profile_sources.py /home/user/work/*.masked.csv --out /home/user/work/profile.json
```

| File | Rows | Dates | Format | Layout | In | Out | Net | Flags |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| amex-2026-04.masked.csv | 8 | 2026-04-03 to 2026-04-28 | %Y-%m-%d | signed | 945.69 | -45.00 | 900.69 | 2 |
| bank-main-2026-04.masked.csv | 8 | 2026-04-01 to 2026-04-12 | AMBIGUOUS | signed | 5300.00 | -5479.80 | -179.80 | 2 |

Flags: bank AMBIGUOUS_DATE_FORMAT; bank BALANCE_BREAK at line 8; card
DUPLICATE_KEYS x1 (Pret A Manger, 14.60, 18 Apr, twice); card SIGN_CHECK
(7 positive vs 1 negative rows: charges are positive).

What the flags mean here:
- "01/04/2026 … 12/04/2026" parse as 1 to 12 April or as 4 January to 4
  December. The model must not pick. If it guessed month/day, eleven rows
  would land in other months.
- Line 8: 30,437.79 + 1,800.00 should give 32,237.79; the file says
  32,207.79. A 30.00 row is missing between lines 7 and 8 (or the bank
  shows the same). The closing balance cannot be a control total yet.
- The bank export ends on 12 April, so it does not cover the period.
- The Pret pair may be two coffees or one duplicate import. Both stay; the
  expense skill asks.

## 3. Intake answers and questions

Jo answered in chat: Xero is the ledger, Dev Patel is the external accountant,
Jo approves invoices and customer contact, Dev approves adjustments and final
reports, fiscal year end 31 March, VAT registered. No Xero capability was found
with `find_capability("xero read bank transactions")`, so Xero is recorded as
`export_only`.

One `ask_question` card went out with Q1 to Q4 (see `intake.json`). Jo answered
Q4 "Not sure: ask the accountant", so basis stays `open`. Q1 to Q3 are
unanswered.

## 4. Check

```
cd ~/skills/bookkeeping-getting-started && python3 scripts/intake_check.py ~/workspace/bookkeeping/bramble-design/intake.json --profile /home/user/work/profile.json
```

BLOCKED (5): bank date format; bank balance break at line 8; Q1; Q2; Q3.
Exit code 1. The intake records `bank-main-2026-04.csv` while the profile names
`bank-main-2026-04.masked.csv`; `intake_check.py` joins them by ignoring the
`.masked` infix. A CSV source with no profile at all would add a "no profile"
blocker.

## 5. Output to Jo

| Source | Dates | Rows | Control total | State |
| --- | --- | --- | --- | --- |
| Bank ****4417 | 1 to 12 Apr (ambiguous format) | 8 | none usable yet | Blocked: date format (Q1), stops 12 Apr (Q2), 30.00 break at line 8 |
| Amex ****1009 | 3 to 28 Apr | 8 | 900.69 net as exported (charges positive) | Usable with a warning: duplicate pair on 18 Apr; statement total not yet supplied |
| Xero trial balance to 31 Mar | to 31 Mar | — | opening balances | Blocked: March not signed off by Dev (Q3) |
| Payroll report | — | — | — | Blocked: not supplied |

Basis: open (Jo: "ask the accountant"). Approvers: invoices and customer
contact, Jo (director); adjustments and final reports, Dev Patel (external
accountant).

Can start now: expense categorisation of the Amex export (duplicate pair flagged
for Jo); invoice list check.
Blocked: statement reconciliation until Q1 to Q3 are answered and the 30.00 break
is explained; payroll tie-out until Jo supplies the April payroll report.
Question Q3 was raised with Jo in this chat (question card); Jo to forward it to
Dev. Mina did not contact Dev.

Saved: `~/workspace/bookkeeping/bramble-design/intake.json`, `intake.md`,
`profile/2026-04.json`; `intake.md` delivered as a `workspace://` link.
Missing-documents request for Jo: full April bank export; signed March trial
balance; April payroll report.

## What a wrong answer would look like

- Reading the bank dates as month/day and reporting "12 rows, January to
  December".
- Quoting 29,407.79 as the April closing balance.
- Dropping one Pret row as a duplicate.
- Writing "Accrual basis" because the business is a limited company.
- "Question sent to Dev." (Mina cannot and must not send it.)
