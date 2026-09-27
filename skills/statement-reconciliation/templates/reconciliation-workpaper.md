# Reconciliation workpaper: <entity>, <account label>, <period> (<currency>)

Status: **<RECONCILED | NOT RECONCILED | STOPPED>**. Prepared by <preparer>.
Figures: <from rec_match.py (script-verified) | hand-computed, not script-verified>.
Matching window: <n> days (<as supplied | default — confirm with the owner>).
Sources: statement <file, pages or rows, export time>; ledger <file, export time>.

## Prior-period tie

Prior approved closing: <amount> (<recs file>, approval <approvals.csv timestamp>) | none on file: open item.
Statement opening: <amount>. <Agrees | DIFFERS by X: stopped, reported to owner>.

## Layout

```
Balance per statement at <date>:              X
Add: deposits in transit (<n>)                X
Less: outstanding payments (<n>)             (X)
Add/less: statement errors, proved (<n>)      X
Adjusted statement balance:                   X

Balance per ledger at <date>:                 X
Add/less: items not in the ledger (<n>)       X
Add/less: ledger errors, proved (<n>)         X
Adjusted ledger balance:                      X

Unexplained difference:                       X
```

Matched: <n> groups, value <X>. Statement lines: <n>; ledger rows: <n>.
Ledger-side items are proposals for the accountant, not entries.

## Reconciling items and aging

Buckets: 0-30 current, 31-60 aging, 61-90 overdue, over 90 stale (default — confirm with the owner).

| Side | Id | Date | Description | Amount | Class | Age | Bucket | Owner | Next step |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Controls and diagnostics

- Feed vs statement: <agrees | differs by X: feed incomplete>
- Duplicates: <none | list>
- Out-of-period rows refused: <none | list>
- Arithmetic hints: <divide-by-nine, sign error, transposition candidates>

## Escalations raised

| Exception id | Item | Class | Owner |
| --- | --- | --- | --- |

## Sign-off

<Ready for owner sign-off | Not reconciled: may be recorded as reviewed, never as reconciled.>
Reviewer: <as stated>  Date: <date>  Approval: approvals.csv row with this file's SHA-256.
