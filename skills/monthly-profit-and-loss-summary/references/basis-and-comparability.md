# Basis and comparability

Written 2026-09-27. Sources at the end; numbers in brackets refer to them.

## Cash and accrual

- **Cash basis:** income when received, expenses when paid. **Accrual basis:**
  income when earned, expenses when incurred, whatever the cash timing [1].
- QuickBooks reports default to the company's method but the method can be
  switched per report, so the same account can show two different months [2].
  Every P&L therefore prints its basis, and `pl_variance.py` refuses to compare
  two periods whose bases differ or are unknown.
- Agents on an accounting benchmark fetched the right documents and then
  substituted the wrong basis; the best model passed 21.5% of tasks at 8 tries [3].
  That is the failure this refusal prevents.
- A fiscal year is not always the calendar year; never assume it [1].

## What a bank export can and cannot give

A P&L built only from bank data is cash-basis. Adjusting entries never involve
cash, so a bank export alone cannot produce an accrual P&L [4]. When the owner
wants accrual figures from bank data, list the candidates for the accountant
instead of estimating them:

| Adjustment type [4] | Candidate to list |
| --- | --- |
| Prepaid expense | an annual subscription or insurance paid in one month |
| Unearned revenue | a customer deposit or advance payment |
| Accrued revenue | work delivered and not yet invoiced |
| Accrued expense | a supplier bill not yet received for work done this month |

## Materiality is not only size

Small items can be material when they turn a loss into a profit or the reverse,
affect a loan covenant or owner pay, or may involve illegality [5]. Related-party
items are added here as practitioner judgement (unsourced; not among SAB 99's
listed factors). Route these to the accountant whatever the amount, and say in
the brief that they are excluded or included.

## Percentages

A percentage change on a zero or near-zero prior value misleads.
`pl_variance.py` prints "n/m" when the prior is zero, when the sign changed, or
when the prior is below a floor of 1% of prior revenue (default — confirm with
the owner). Say why in the brief instead of quoting the percentage.

## Comparisons the owner will ask for

- Prior month: the default comparison.
- Same month last year: owners judge seasonality year on year. Use
  `pl/<YYYY-MM>.csv` from state only when its basis matches and its status is
  known; a comparison against a draft month says so.
- Plan or budget: only from a file the owner supplies (`templates/budget-template.csv`),
  same basis and currency. Never create a plan figure.

## Sources

1. IRS, Publication 538, Accounting Periods and Methods (2025). https://www.irs.gov/publications/p538
2. Intuit QuickBooks, Run reports in QBO (accounting method) (2026). https://quickbooks.intuit.com/learn-support/en-us/help-article/report-management/run-reports-quickbooks-online/L7aILHhbl_US_en_US
3. Benchek et al. (Mercor, Ramp), APEX-Accounting (2026). https://arxiv.org/html/2607.27189v1
4. OpenStax, *Principles of Accounting Vol. 1*, 4.2 Adjusting Entries (2019). https://openstax.org/books/principles-financial-accounting/pages/4-2-discuss-the-adjustment-process-and-illustrate-common-types-of-adjusting-entries
5. SEC, Staff Accounting Bulletin No. 99, Materiality (1999). https://www.sec.gov/interps/account/sab99.htm
