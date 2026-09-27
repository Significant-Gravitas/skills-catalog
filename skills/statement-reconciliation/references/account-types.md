# Account types: what "statement" means and which equation to use

Pick the row for the account, then use the layout in `bank-rec-layout.md`.
Sources are listed at the end; numbers in brackets refer to them.

| Account | The external record ("statement") | Ledger side | Equation | Typical reconciling items |
| --- | --- | --- | --- | --- |
| Bank current or savings | Bank statement (PDF or export) for the full period | Cash account register | Adjusted statement = adjusted ledger [1] | Deposits in transit, outstanding payments, unrecorded fees and interest, errors |
| Credit card | Card issuer statement; the closing balance is the amount owed | Card liability account | Same, with charges positive and payments negative on both sides | Charges posted after the statement date, payments in transit, unrecorded fees or interest, disputed charges |
| Loan or line of credit | Lender statement or amortisation schedule | Loan liability account | Lender principal balance = ledger liability | Payment split between interest (expense) and principal (liability) missing; without a lender schedule the line is unresolved [2] |
| Processor (Stripe, PayPal, Square) | Processor balance report and payout report | A clearing account for the processor | Gross sales - fees - refunds - disputes = net payout; the net payout ties to a bank deposit [3][4] | Payouts in transit at cutoff, fee rows, refunds, disputes, report time-zone cutoffs; see `processor-clearing.md` |
| Petty cash (imprest) | A count of cash on hand plus the receipts in the box | Petty cash account at its fixed fund amount | Cash counted + receipts = fund amount [5] | Differences go to cash over/short; a recurring shortage is a control flag for the owner [5] |
| Other balance-sheet accounts (deposits held, payroll liabilities, sales tax payable) | The third-party statement, schedule or return | The liability or asset account | Third-party balance = ledger balance | Timing of filings and payments. Route any tax or payroll question to the accountant. |

## Rules that apply to every type

- Only book-side items need entries. Bank-side (timing) items clear without an
  entry [1]. Every book-side item is a draft for the accountant, never posted here.
- The statement is the authority. A ledger's "statement balance" may be the
  feed, not the bank [6]; see `ledger-diagnostics.md`.
- Opening balances post against Opening Balance Equity. A non-zero OBE balance is
  a set-up exception for the accountant [7].

## Sources

1. OpenStax, *Principles of Accounting Vol. 1*, 8.6 Bank Reconciliation (2019). https://openstax.org/books/principles-financial-accounting/pages/8-6-define-the-purpose-of-a-bank-reconciliation-and-prepare-a-bank-reconciliation-and-its-associated-journal-entries
2. AccountingCoach, Recording a loan payment with interest and principal. https://www.accountingcoach.com/blog/interest-principal-loan-payments
3. Stripe, Payout reconciliation report (2026). https://docs.stripe.com/reports/report-types/payout-reconciliation
4. Catch Creation, Bookkeeper (Ecommerce) job posting (2026), clearing-account duties. https://job-boards.greenhouse.io/catchcreationllc/jobs/4078182009
5. OpenStax, *Principles of Accounting Vol. 1*, 8.4 Petty Cash (2019). https://openstax.org/books/principles-financial-accounting/pages/8-4-define-the-purpose-and-use-of-a-petty-cash-fund-and-prepare-petty-cash-journal-entries
6. BB Books Inc, Xero the Hero: The Bank Reconciliation Summary. https://bbbooksinc.com/blog/the-bank-reconciliation-summary/
7. Intuit QuickBooks, Enter and manage opening balances (2026). https://quickbooks.intuit.com/learn-support/en-us/help-article/bank-deposits/enter-opening-balance-account-quickbooks-online/L7NcxTbuu_US_en_US
