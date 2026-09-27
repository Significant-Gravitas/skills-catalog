# Source documents by category

What to ask for at intake, and what each document proves. US rules come from
IRS Publication 583 [18] and 26 CFR 1.274-5 [20]; UK notes from GOV.UK and HMRC
[28][29]. Checked 2026-09-27. Rules change: confirm current requirements with
the accountant before relying on them.

## Contents
1. Proof of payment vs proof of cost
2. Checklist by category
3. Raw exports are acceptable inputs
4. Retention stance

## 1. Proof of payment vs proof of cost

- A bank or card line proves that money moved. It does not prove what was
  bought or that the cost was a business expense [18].
- Pub 583 lists bank-statement fields that can stand in for a cancelled check
  as proof of payment: amount, payee, and the date the item was posted [18].
- A receipt or invoice proves what was bought. It supports an expense only
  when it ties to a card or bank line: AI-generated receipts were 70.8% of the
  fake receipts AppZen flagged by mid-May 2026 [60].
- So the intake asks for both kinds, and later skills tie one to the other.

## 2. Checklist by category

| Category | Documents to ask for [18] | Proves | Kit skill that uses it |
| --- | --- | --- | --- |
| Gross receipts (income) | cash register tapes or POS exports, deposit records, invoices issued, credit card charge slips, processor payout reports, 1099-K/1099-NEC received (US) | amount and source of income | invoice-drafting-and-issue, accounts-receivable-follow-up, statement-reconciliation |
| Purchases (stock for resale) | supplier invoices, cancelled checks or bank lines, card statements | cost of items bought for resale | expense-categorization |
| Expenses | receipts, invoices, account statements, cancelled checks, petty cash slips | amount, payee, business purpose | expense-categorization |
| Travel, meals, gifts (US) | receipts for lodging and for any other item at or above the documentary-evidence threshold, with amount, time, place and business purpose recorded at or near the time [20][21]; the threshold is in the expense-categorization package's `references/substantiation-us.md` | substantiation | expense-categorization |
| Assets (equipment, vehicles, property) | purchase invoices (itemised), closing statements, cancelled checks, records of improvements and disposals [18] | cost basis, date in service | expense-categorization (flag only) |
| Payroll | provider payroll register, tax deposit confirmations | wages, withholdings, employer taxes | out of scope for preparation; route to the owner or accountant |
| Loans | lender statements and the amortisation schedule [78] | interest vs principal split | expense-categorization (flag), statement-reconciliation |
| Bank, card, processor, loan accounts | statements (PDF or export) with opening and closing balance; processor payout reports [94][96] | control totals | statement-reconciliation |
| Opening position | prior year-end or month-end trial balance signed off by the accountant; prior approved reconciliations | opening balances | every downstream skill |

UK: VAT-registered businesses keep VAT records and VAT invoices; HMRC's VAT
record-keeping notice sets the detail [28]. Limited companies keep accounting
records described by GOV.UK [29].

## 3. Raw exports are acceptable inputs

Some bookkeeping services work straight from POS and bank exports without a
QuickBooks or Xero file [10]. Accept raw CSV exports from banks, cards, POS,
Stripe, PayPal and billing tools. Do not assume a ledger file exists.

## 4. Retention stance

Never advise discarding or deleting a source record. Retention periods vary by
record type and jurisdiction (see `jurisdiction-flags.md`) [17][29]; questions
about what can be thrown away go to the accountant [84].
