# Worked example: April P&L brief, with a basis trap

Fictional. Bramble Design Ltd, April 2026 vs March 2026, GBP. Input files are
in `examples/april-2026/`. Run `python3 scripts/pl_variance.py --selftest` and
`python3 scripts/trace_movement.py --selftest` to check them.

## 1. Scope

- Pre-flight: `python3 --version` ok; state root writable; `intake.json` says
  basis accrual (set by Dev Patel), fiscal year from 1 January, figures net of VAT.
- Jo uploads `pl-2026-04.csv` (ledger P&L export of 6 May, accrual) and, for
  March, a file that turns out to be a **cash-basis** export
  (`pl-2026-03-cash.csv`).

## 2. The hard case: two bases

```
$ python3 scripts/pl_variance.py --current pl-2026-04.csv --current-period 2026-04 --current-basis accrual \
    --prior pl-2026-03-cash.csv --prior-period 2026-03 --currency GBP --out /home/user/out/pl/2026-04
NOT COMPARABLE: current is accrual basis and prior is cash: not comparable. Get both periods on the same basis
from the ledger; never convert by estimate
```

No change or percentage is computed. Jo is asked with `ask_question`: "March's
export is cash basis and April's is accrual. Which should I do?" Options:
"I'll export March on accrual" / "Show April alone for now". She uploads the
accrual March export (`pl-2026-03.csv`). State already held a stored
`pl/2026-03.csv`, but it was a draft on the same basis and its figures agreed with
the new export, so either would do; the fresh export is used and cited.

## 3. Variance run

The run with `--reported-current reported-2026-04.csv --plan budget.csv` gives
(script-verified):

| Line | Apr | Mar | Change | % |
| --- | --- | --- | --- | --- |
| Revenue | 22,750.00 | 18,200.00 | 4,550.00 | 25.0% |
| Direct costs (freelancers) | 6,900.00 | 5,100.00 | 1,800.00 | 35.3% |
| Gross result | 15,850.00 | 13,100.00 | 2,750.00 | 21.0% |
| Operating expenses | 11,420.00 | 10,980.00 | 440.00 | 4.0% |
| Operating result | 4,430.00 | 2,120.00 | 2,310.00 | 109.0% |
| Net result | not shown: 1,040.20 unmapped | | | |

- The export's own operating-expense total is 12,460.20; mapped detail is
  11,420.00. The difference (1,040.20) equals "Uncategorised Expense", which is
  excluded from subtotals and listed.
- Workshops and Travel had a zero prior: "n/m", not a percentage.
- Plan (FY26 budget v2, supplied by Jo): retainers 500.00 over, projects 650.00
  under, freelancers 900.00 over.

## 4. Tracing the drivers

The sources in their real shapes: `april-2026/invoice-register.csv` (the
register `invoice-drafting-and-issue` keeps: no account column, one `line_key`
per contract line per period such as `C-3/retainer/2026-04`, statuses
`issued_per_owner`, `voided_per_owner`, `approved_to_issue`),
`april-2026/line-accounts.csv` (Jo's confirmed map from the stable part of the
key, `C-3/retainer`, to a P&L account) and `april-2026/gl-detail.csv` (the
ledger's transaction detail by account export). The register traces accrual
revenue only; on a cash basis the GL detail export or the payments are used.
Each is reshaped first:

```
python3 scripts/trace_movement.py --reshape --in examples/april-2026/invoice-register.csv \
    --date-col issued_on --amount-col amount --ref-col number \
    --key-col line_key --key-strip-period --account-map examples/april-2026/line-accounts.csv \
    --include-status issued_per_owner --out /home/user/in/trace-invoices.csv
wrote 10 rows to /home/user/in/trace-invoices.csv; skipped 2 by status (listed in ....skipped.csv; they are not traced)
UNMAPPED: 1 rows (250.00) have a key not in the account map; ... They stay untraced.

python3 scripts/trace_movement.py --reshape --in examples/april-2026/gl-detail.csv \
    --date-col Date --account-col Account --amount-col Amount --ref-col Num \
    --out /home/user/in/trace-gl.csv
```

The voided INV-1046 and INV-1052 (approved to issue in May, no issue date yet)
are skipped and listed, never counted and never given a date. INV-1051 (a 250.00
deposit, key `C-7/deposit`) has no mapping, so it is listed and Jo is asked which account it belongs to; it is
not guessed. (`april-2026/sources.csv` is the combined reshaped result.) Then
`trace_movement.py --sources /home/user/in/trace-*.csv` for each line:

- Sales - Retainers +3,500.00: fully traced to INV-1049 (Oriel Health retainer).
- Workshops +900.00: traced to INV-1050.
- Sales - Projects +150.00: **untraced**. INV-1047 (5,200.00) explains April's
  project revenue except 150.00.
- Freelancers +1,800.00: traced to bills #551 and #553 against March's #540,
  #541 and #544.

## 5. Review pass

A clean-context sub-session checks each point against `pl_variance.json` and
the trace (`run_sub_session`, because this is the first month with Bramble and
the operating result moved over 100%). It flags one sentence, "freelancer costs
rose because of the Oriel work", as not proven by any record. It becomes a hypothesis.

## 6. The brief (as delivered)

**DRAFT for review, not final accounts.** Bramble Design Ltd, April 2026 vs
March 2026, accrual basis (from the export header), GBP, net of VAT. Source:
ledger P&L export of 6 May (both months).

- Revenue up 4,550.00 (25.0%): 4,400.00 traced: the new Oriel Health retainer
  (3,500.00, INV-1049) and a workshop day (900.00, INV-1050). 150.00 of project
  revenue is not yet traced to a record.
- Freelancer costs up 1,800.00: bills #551 and #553. Hypothesis, not proven:
  the rise relates to the Oriel work; the bills do not name the client.
- Operating result 4,430.00, up 2,310.00. Net result not shown until the
  uncategorised 1,040.20 is coded.
- Against budget: retainers 500.00 over, projects 650.00 under.
- Open and excluded: 1,040.20 uncategorised (5 card items), Amex not yet
  reconciled, no payroll accrual reviewed. The operating result will move once
  Dev settles these.

Decisions needed: Jo to code the 5 card items; Dev to confirm whether a payroll
accrual is needed. Saved to `pl/2026-04.csv` (status draft) and
`pl/2026-04-brief.md`; bridge chart attached.

## The original example (kept from version 1)

Fictional draft, Bramble Design Ltd, April 2026 vs March 2026, GBP, from the
ledger P&L export of 6 May. Basis: not supplied (open). Figures net of VAT.
**Draft for review, not final accounts.**

| Line | Apr | Mar | Change | % |
| --- | --- | --- | --- | --- |
| Revenue | £22,750 | £18,200 | +£4,550 | +25% |
| Direct costs (freelancers) | £6,900 | £5,100 | +£1,800 | +35% |
| Gross result | £15,850 | £13,100 | +£2,750 | +21% |
| Operating expenses | £11,420 | £10,980 | +£440 | +4% |
| Operating result | £4,430 | £2,120 | +£2,310 | +109% |

- Revenue up £4,550: £4,400 of it is the new Oriel Health retainer (£3,500,
  INV-1049) and a workshop day (£900, INV-1050). The other £150 is not yet
  traced to a record.
- Freelancer costs up £1,800: two Oriel-related bills (#551, #553). That the
  cost rose because of Oriel is a hypothesis; the bills do not name the client.
- Open and excluded: 5 unresolved card items (£1,040.20), Amex not yet
  reconciled, no payroll accrual reviewed. Operating result will move once Dev
  settles these.

Note for version 2: with the basis "not supplied (open)", version 2 still
summarises April on its own, headed "basis: unknown (open)", but does not
compute the change columns until both months' basis is confirmed.
