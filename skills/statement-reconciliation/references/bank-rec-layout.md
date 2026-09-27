Adapted from anthropics/knowledge-work-plugins `finance/skills/reconciliation` (Apache-2.0); see ATTRIBUTION.md and LICENSE in this package.

# Bank reconciliation layout

Use this layout for a bank or card account when the ledger and the statement
share a period-end date. Fill every line from a named record; leave a line at
zero rather than removing it, so the reviewer can see it was checked.

Start with the prior-period tie. If the two figures differ, stop: a reconciled
item was probably changed after sign-off. Report it; never undo or re-reconcile.

```
Prior approved closing at <prior date>:       X   (recs/<account>-<prior YYYY-MM>.json, approved in approvals.csv)
Statement opening at <date>:                  X   (must equal the line above)

Balance per statement at <date>:              X
Add: deposits in transit                      X   (in ledger, not yet on statement)
Less: outstanding payments                   (X)  (in ledger, not yet cleared)
Add/less: statement errors, if proved         X
Adjusted statement balance:                   X

Balance per ledger at <date>:                 X
Add: interest or credits not in the ledger    X
Less: fees or charges not in the ledger      (X)
Add/less: ledger errors, if proved            X
Adjusted ledger balance:                      X

Unexplained difference:                       X   (must be 0.00 to call it reconciled)
```

The unexplained difference is never closed with a plug. A match needs a
one-to-one source link on both sides; never pull a transaction from another
period, account or entity to close a gap, and never post a balancing or
suspense entry. An open difference stays open, with an owner and next step.

Items on the ledger side (fees, interest, errors) are proposals for the
accountant, not entries. Each one needs a source line and stays open until the
owner approves a correction.

## Classify each reconciling item

- **Timing:** deposits in transit, outstanding payments, items pending in one
  system. Expected to clear without an entry. Record the date each should clear.
- **Needs a correction:** unrecorded fees or interest, wrong amount, wrong
  account, duplicate, missing entry. Draft for accountant review.
- **Needs investigation:** no obvious cause, disputed, or recurring every
  period. Owner and next step required.

## Aging of open items

Illustrative defaults; confirm the buckets and actions with the owner:

| Age | Label | Default action |
| --- | --- | --- |
| 0 to 30 days | current | monitor |
| 31 to 60 days | aging | ask the owner why it has not cleared |
| 61 to 90 days | overdue | escalate to the finance owner |
| over 90 days | stale | escalate; accountant decides on any correction |

| Item | Description | Amount | Originated | Age (days) | Class | Owner | Next step |
| --- | --- | --- | --- | --- | --- | --- | --- |

Flag an item that appears again next period, and a growing count or total of
open items, even when each item is small.

`scripts/write_workpaper.py` fills this layout and the aging table from the
`rec_match.py` output; use this page by hand only when Python is unavailable,
and label every total "hand-computed, not script-verified".
