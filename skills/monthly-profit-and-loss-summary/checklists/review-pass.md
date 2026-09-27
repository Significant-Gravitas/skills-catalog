# Review pass before releasing a P&L brief

The first draft of a set of statements nearly always contains errors (Bragg,
AccountingTools, closing procedure). Do this pass every time.

## Numbers

- [ ] Every figure in the brief appears in `pl_variance.json` (or is labelled hand-computed).
- [ ] Detail sums to report totals, or the difference is stated and explained.
- [ ] Both periods are on the same basis, printed beside the table.
- [ ] No percentage on a zero, near-zero or sign-changed base.
- [ ] Net result shown only when nothing is unmapped and totals tie.
- [ ] Plan figures are only those supplied, with their source and date.

## Drivers

- [ ] Each of the 3 to 5 points cites a record (invoice, bill, export row).
- [ ] Each driver quotes its traced and untraced amounts from `trace_movement.py`.
- [ ] A cause the records do not prove is labelled "hypothesis".

## Exceptions

- [ ] Unmapped accounts, sales tax lines, 1099-K revenue and owner items are listed, not fixed.
- [ ] Each material open item says whether the draft includes or excludes it.
- [ ] Qualitative-materiality items (profit/loss flip, covenant, owner pay, possible illegality, related party) are routed whatever their size.

## Words

- [ ] "DRAFT for review, not final accounts" at the top.
- [ ] Cash movement kept apart from profit.
- [ ] No solvency forecast, tax advice, financing or investment advice.
- [ ] Every default is labelled "default — confirm with the owner".
