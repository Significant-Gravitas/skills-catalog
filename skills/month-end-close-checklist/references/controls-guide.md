# Controls guide: what evidence closes each control

One section per control id in `templates/close-controls.csv`. "Ready for
review" means the evidence below exists and is linked; it never means approved.

## Contents

- Sources S1-S6
- Controls 1-15
- Qualitative materiality
- Owner sign-off as the alternative control
- Payroll tax first
- Sources

## Sources S1-S6

Each source is received when a file covering **every day of the period** is in
the workspace, with its row count and control total recorded. Compare the file
list (`list_workspace_files`) with the sources in `intake.json`. A feed is not a
statement; feeds lag (Amex may update only 2 to 3 times a week) [1].

## Controls

1. **Bank and card reconciled.** One workpaper per account from
   `statement-reconciliation`, status RECONCILED, or NOT RECONCILED with every
   item owned. Opening ties to last month's approved closing.
2. **Sales complete through cutoff.** Invoice register total ties to the billing
   export; credits and refunds listed. Sales tax collected is a liability, not
   revenue [2].
3. **Bills, receipts, claims complete.** Expense review table split into ready
   to post and needs review. A receipt with no matching card or bank line is an
   exception, not support [3].
4. **Receivables and payables aged.** Aging at cutoff; an invoice with no due
   date is due on receipt in the ledger, so confirm terms before calling it
   overdue [4]. Bad-debt write-off is the accountant's decision.
5. **Payroll tied.** Net pay and tax deposits on the bank tie to the approved
   payroll register. Recording only; payroll runs and filings are out of scope.
6. **Loans, transfers, owner and intercompany.** Lender principal equals the
   ledger liability; each transfer appears on both sides; owner items sit in
   equity, not the P&L.
7. **Accountant items packaged.** Fixed-asset, accrual, prepayment, tax and
   revenue-policy candidates, each with its source, sent as a hand-off list via
   `bookkeeping-exception-escalation`. The four adjustment types are prepaid,
   unearned, accrued revenue and accrued expense; adjusting entries never involve
   cash, and a cash-basis bank export cannot produce an accrual P&L alone [5].
8. **P&L and balance movements reviewed.** Draft P&L brief from
   `monthly-profit-and-loss-summary`, basis printed, marked DRAFT, open items
   listed. Compared with prior period and with the plan only if supplied.
9. **Adjustments documented.** Every proposed adjustment has a source, reason,
   preparer and approver (an `approvals.csv` reference). None is posted here.
10. **Processor clearing.** Every payout tied to a bank deposit or shown in
    transit; gross, fees, refunds and disputes shown [6].
11. **Undeposited Funds and suspense.** Balance at cutoff is zero or every item
    is explained. Undeposited Funds may be renamed; find it by Detail type [7].
    A lingering balance is an exception.
12. **Opening Balance Equity.** Zero, or raised to the accountant as a set-up
    exception [8].
13. **Bills not yet received.** Recurring suppliers and expected bills with no
    bill for the period are listed as accrual candidates for control 7 [9].
14. **Owner sign-off on each bank reconciliation.** One `approvals.csv` row per
    workpaper, with its SHA-256. It is recorded as `approved` (checked against
    approvals.csv), `blocked` or `not_applicable`, never `ready_for_review`.
15. **Lock date recorded.** Only the ledger's admin can lock the period; edits
    after the lock need a warning or password [10]. Record the date the owner
    states. Never lock, bypass a lock, or ask anyone to bypass it. Errors found
    in a locked period are corrected in the current period by the accountant
    (practitioner judgement, unsourced).

## Qualitative materiality

Size is not the only test. Route to the accountant, whatever the amount, any
item that turns a loss into a profit or the reverse, touches a loan covenant or
owner pay, or may involve illegality [11]; also related-party items
(practitioner judgement, unsourced; not among SAB 99's listed factors).

## Owner sign-off as the alternative control

Where duties cannot be segregated, management selects and develops alternative
control activities [12]; management review of accounts is one of the controls
linked to at least 50% lower fraud losses and duration [13]. That the owner
signs off each bank reconciliation, because the same assistant both codes and
reconciles, is practitioner judgement (unsourced).

## Payroll tax first

Never suggest paying other creditors ahead of payroll tax deposits. A person who
decides which creditors are paid can be personally liable for unpaid trust-fund
taxes, and paying others first indicates willfulness [14]. Raise any shortfall
at once through `bookkeeping-exception-escalation`.

## Sources

1. Intuit QuickBooks, Download the most recent bank and card transactions (2026). https://quickbooks.intuit.com/learn-support/en-us/help-article/multi-factor-authentication/download-recent-bank-credit-card-transactions/L86TTVI3Y_US_en_US
2. Steven Bragg, Accounting for sales taxes, AccountingTools (2026). https://www.accountingtools.com/articles/accounting-for-sales-taxes
3. PYMNTS (AppZen data), AI-generated fake receipts now 71% of expense fraud (2026). https://www.pymnts.com/news/artificial-intelligence/2026/ai-generated-fake-receipts-now-make-up-71percent-of-expense-fraud/
4. Intuit QuickBooks, Why aging reports have both Current and 1-30 (2026). https://quickbooks.intuit.com/learn-support/en-us/help-article/accounts-payable-reports/aging-reports-current-1-30/L43pItdAj_US_en_US
5. OpenStax, *Principles of Accounting Vol. 1*, 4.2 Adjusting Entries (2019). https://openstax.org/books/principles-financial-accounting/pages/4-2-discuss-the-adjustment-process-and-illustrate-common-types-of-adjusting-entries
6. Stripe, Payout reconciliation report (2026). https://docs.stripe.com/reports/report-types/payout-reconciliation
7. Intuit QuickBooks, Deposit payments into Undeposited Funds (2026). https://quickbooks.intuit.com/learn-support/en-us/help-article/payroll-setup/deposit-payments-undeposited-funds-account-online/L1td0m8Z2_US_en_US
8. Intuit QuickBooks, Enter and manage opening balances (2026). https://quickbooks.intuit.com/learn-support/en-us/help-article/bank-deposits/enter-opening-balance-account-quickbooks-online/L7NcxTbuu_US_en_US
9. Steven M. Bragg, Closing entries / closing procedure, AccountingTools (2026). https://www.accountingtools.com/articles/closing-entries-closing-procedure
10. Intuit QuickBooks, Lock your books in QBO (2026). https://quickbooks.intuit.com/learn-support/en-us/help-article/close-books/close-books-quickbooks-online/L59LelyPM_US_en_US
11. SEC, Staff Accounting Bulletin No. 99, Materiality (1999). https://www.sec.gov/interps/account/sab99.htm
12. COSO, Internal Control - Integrated Framework, Executive Summary (2013; mirror copy). https://www.como.gov/archive/2021/12/COSO-2013.pdf
13. ACFE, Top 4 Internal Controls That Reduce Fraud Losses (2020). https://www.acfe.com/acfe-insights-blog/blog-detail?s=top-internal-controls-that-reduce-fraud-losses-2020
14. IRS, Employment taxes and the Trust Fund Recovery Penalty. https://www.irs.gov/businesses/small-businesses-self-employed/employment-taxes-and-the-trust-fund-recovery-penalty-tfrp
