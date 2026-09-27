# US substantiation notes (for flags only)

Checked 2026-09-27. Rules change: confirm current rules with the accountant
before relying on any figure here. This file is the only place in the package
that states a dollar threshold. Mina flags; the accountant decides
deductibility.

## Contents
1. Records that support an expense
2. Travel, meals and gifts
3. Receipts must tie to a payment
4. How to use this in the review

## 1. Records that support an expense

- Supporting documents include receipts, invoices, account statements,
  cancelled checks and petty-cash slips; they should show the amount paid and
  that the amount was for a business expense [18].
- Proof of payment alone (a bank or card line) does not establish what was
  bought or the business purpose [18].

## 2. Travel, meals and gifts

- 26 CFR 1.274-5(c)(2)(iii) requires documentary evidence (such as a receipt)
  for any lodging expense and for any other expenditure of **$75 or more** [20].
- Record the amount, the time and place, and the business purpose, at or near
  the time of the expense [20][21].
- Meals are generally 50% deductible [21], so keep them in their own account;
  the percentage and any exception are the accountant's call.

## 3. Receipts must tie to a payment

AI-generated receipts made up 70.8% of the fake receipts AppZen flagged by
mid-May 2026 [60]. A receipt is support only when its amount and date tie to a
card or bank line (`expense_checks.py --receipts`). A receipt with no payment
line is an exception to report, not evidence.

## 4. How to use this in the review

- Only when the owner or accountant confirms the threshold for the tax year
  in question, run `expense_checks.py --threshold <value> --threshold-source "<who, date>"`.
- For flagged travel, meal or gift lines without a receipt, and for any
  lodging without a receipt, ask for the receipt, the business purpose and (for
  meals) who attended. Do not state whether the item is deductible.
- For non-US entities, do not apply this file; ask the accountant what
  evidence they need.
