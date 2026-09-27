# Processor clearing: Stripe and PayPal payouts

Written 2026-09-27 from the vendors' current documentation. Report columns and
limits change; if an export does not match what is described here, trust the
export's own header and say so in the report.

## Why deposits never match invoices

A processor pays out **net batches**: many charges, less fees, refunds and
disputes, in one bank deposit. Treat the processor balance as a clearing
account. The equation, per payout:

```
gross sales - fees - refunds - disputes = net payout = bank deposit
```

Revenue is the gross; fees are an expense; the bank line is only the net [1][4].

## Stripe

- Use the **Payout reconciliation report**, keyed on `automatic_payout_id`.
  That id is set **only for accounts on an automatic payout schedule**. For
  manual payouts, run the by-payout report with the payout ID instead [1].
  `payout_breakdown.py` reports rows with an empty key; it never drops them.
- The **Balance summary** report does not link payouts to the payments inside
  them, so it cannot tie a deposit to invoices [2].
- Report time zone causes cutoff differences, and `available_on` differs from
  `created`. State the time zone and the date field used [2].
- A payout that is `in_transit` at period end is timing, not missing [2].
- Fees can be exported as a positive cost (gross - fee = net) or a negative
  amount (gross + fee = net). The script detects which and refuses a row that
  fits neither.

## PayPal

- The **Activity download** report has Gross, Fee, Net and a **Balance Impact**
  column of Debit, Credit or Memo [3].
- Memo rows (for example authorisations) do not move the balance. That is an
  inference from the Balance Impact field, not a sentence in PayPal's
  documentation; the script excludes and lists them.
- Reports over 50,000 rows arrive split across several files in a ZIP, and the
  maximum range is 12 months per report [3]. A balance that does not prove
  (opening + activity - transfers = closing) usually means a split file is missing.
- Withdrawals to the bank are the "payouts" to tie to bank deposits.
- Every row has a Currency, and PayPal keeps a separate balance per currency [3].
  The script never adds currencies together: with more than one it stops
  unless `--currency` names the one paid out to this bank account, lists the
  others as "not included", and shows "General Currency Conversion" rows as FX
  for the accountant, never as sales.
- Debit payment rows (money paid out of PayPal for purchases) are reported as
  `payments_sent`, separately from gross sales, so purchases never reduce
  revenue.

## Procedure

1. Get the processor report for the same period and time zone as the bank statement.
2. Run `payout_breakdown.py` (see SKILL.md step 5) with `--bank` set to the
   canonical bank statement CSV and `--cutoff` at period end.
3. Each payout is either **tied to bank** (one deposit, same net, within the
   window), **after cutoff: in transit** (timing), or **not tied** (investigate).
4. Report gross, fees, refunds and disputes per payout so the accountant can see
   that revenue was booked gross. Never post the split; propose it.
5. An `AMBIGUOUS` tie (two deposits of the same amount in the window) is left
   for a person, never chosen by the script.

## Sources

1. Stripe, Payout reconciliation report (2026). https://docs.stripe.com/reports/report-types/payout-reconciliation
2. Stripe, Balance summary report (2026). https://docs.stripe.com/reports/balance
3. PayPal Developer, Activity Download report (2026). https://developer.paypal.com/docs/reports/online-reports/activity-download/
4. Catch Creation, Bookkeeper (Ecommerce) job posting (2026). https://job-boards.greenhouse.io/catchcreationllc/jobs/4078182009
