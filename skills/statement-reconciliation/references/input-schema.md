# Input schema for the reconciliation scripts

All files are UTF-8 CSV with a header row (column names are case-insensitive)
or JSON. Money is a plain decimal (`-12.50`); `1,250.00` and `(12.50)` are also
read. Dates are `YYYY-MM-DD`. Templates for each file are in `templates/`.

## statement.csv and ledger.csv

| Column | Required | Meaning |
| --- | --- | --- |
| id | yes | Unique row id: the statement line number, or the ledger transaction id. |
| date | yes | Posting date on the statement; transaction date in the ledger. |
| amount | yes | Signed. **Positive raises the balance as the statement shows it.** |
| description | no | Payee or narrative, as exported. |
| reference | no | Invoice, bill, cheque or transfer reference. Used for passes 2, 4 and batches. |
| fitid | no | Bank transaction id from the feed (OFX FITID). Unique only within one account. |

Sign convention by account type (see `account-types.md`):

- **Bank and petty cash:** deposits positive, payments negative, on both files.
- **Card and loan (liabilities):** the statement shows the amount owed, so
  charges or drawdowns are positive and payments negative. Many ledgers export a
  liability register the other way round; flip the ledger column before running.
- The script proves both files (opening + in-period lines = closing). If a file
  proves only with the signs reversed, it stops and says "flip the amount column".

Rows dated outside `period_start`..`period_end` are never matched. They are
listed in `out_of_period.csv`.

## balances.json

```json
{
  "account": "main-4411",
  "currency": "GBP",
  "period_start": "2026-04-01",
  "period_end": "2026-04-30",
  "statement_opening": "20000.00",
  "statement_closing": "23392.50",
  "ledger_opening": "20000.00",
  "ledger_closing": "23055.00",
  "prior_approved_closing": "20000.00",
  "window_days": 3
}
```

- `account`: a label with at most the last 4 digits. The script refuses 5 or more digits.
- `statement_*`: from the **real statement** (PDF or bank export), never from a
  ledger's feed balance.
- `ledger_*`: the ledger account balance at the day before `period_start` and at `period_end`.
- `prior_approved_closing`: last month's approved statement closing, from
  `recs/<account>-<prior YYYY-MM>.json` with an approval in `approvals.csv`.
  Omit it only for a first period; the omission becomes an open item.
- `window_days`: optional. Default 3 (default — confirm with the owner).
- `stale_days`: optional. Age at period end after which an uncleared ledger-only
  row defaults to investigate, and the clearing lag beyond which a row confirmed
  on `--next-statement` is flagged "late clearing" for escalation (step 7) when
  it is a deposit; a late payment is noted as routine, not escalated.
  Without it the matching window is used (default — confirm with the owner).

Descriptions and references are masked in every output file (6 or more digits
keep only the last 4; IBANs and sort codes are starred; dates and amounts
stay). The unmasked text stays only in the sandbox input.

## carried.csv (optional)

Last period's open items that have not cleared. Produced as
`carried-next.csv` by `write_workpaper.py`.

Drafted ledger corrections are carried too. A confirmed `ledger-error` pair
becomes a statement-side `correction` row with id `<statement_id>/<ledger_id>`
and amount statement minus ledger. A ledger row classed `correction` (for
example a duplicate) becomes a statement-side `correction` row with id
`ledger-<id>` for the reversing amount. While the correction is unposted it
adjusts the ledger side. Once the accountant posts it, it matches the
correcting entry and clears.

Carried ids are namespaced: a carried row `L3` from March is shown and written
as `carried:2026-03:L3`, so it can never replace this period's own `L3` (line
numbers repeat every month). An id that already starts with `carried:` is kept
as it is. In `classify.csv` and `owners.csv` use the id as the output files show
it; `classify.csv` also accepts the original id when no current row uses it.

`side` (statement or ledger), `id`, `date`, `amount`, `description`,
`reference`, `originated` (YYYY-MM), `class`, `owner`, `next_step`.

Carried ledger items (outstanding payments, deposits in transit) may match this
period's statement lines. Carried statement items (fees awaiting an entry) may
match this period's ledger rows. They are not in this period's sums.

## classify.csv (optional; the owner's or bookkeeper's decisions)

`side`, `id`, `class`, `pair_id`, `note`.

| Side | Class | Effect |
| --- | --- | --- |
| statement | investigate (default) | Stays in the unexplained difference. |
| statement | correction | Bank shows it, ledger lacks it (fee, interest, unrecorded receipt). Adjusts the ledger side. Draft for the accountant. |
| statement | bank-error | Proved bank error. Adjusts the statement side. |
| statement | ledger-error + pair_id | Same transaction, wrong amount in the ledger. Removes both and adjusts the ledger by the difference. |
| statement | match + pair_id | A person confirmed the pair. Amounts must be equal. Logged as a manual match with the note. |
| ledger | timing (default only when fresh) | Deposit in transit or outstanding payment. Adjusts the statement side. "Unconfirmed" until it clears. The script defaults to timing only for a row dated within `stale_days` (default `window_days`) of period end, or one `--next-statement` shows cleared; a deposit that cleared more than `stale_days` after its ledger date is flagged "late clearing" for escalation (a late payment is only noted). |
| ledger | investigate (default when stale) | A ledger-only row older than `stale_days` (default `window_days`) at period end and not confirmed cleared, or a carried timing item that did not clear this period ("stale timing item"). Classify as timing only on the owner's explanation. |
| ledger | correction | Ledger entry that should not exist (for example a duplicate). Adjusts the ledger side. |
| ledger | investigate | Stays in the unexplained difference. Default for a possible duplicate. |

A classification is a proposal that the report shows with its note. It never
changes the ledger.

## Stripe payout reconciliation CSV (payout_breakdown.py stripe)

Needs `gross`, `fee`, `net`, `automatic_payout_id` and one date column
(`automatic_payout_effective_at`, `effective_at`, `available_on` or `created`).
`reporting_category` is used to split charges, refunds and disputes. Rows with
an empty `automatic_payout_id` are reported, never dropped.

## PayPal activity download CSV (payout_breakdown.py paypal)

Needs `Date`, `Currency`, `Gross`, `Fee`, `Net`, `Balance Impact`; uses `Type` and
`Transaction ID` when present. Non-ISO dates need `--date-format`. With more
than one currency, `--currency` is required; other currencies are listed, never summed in.
