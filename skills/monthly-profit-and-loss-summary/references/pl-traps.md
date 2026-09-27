# P&L traps: lines that do not belong, and figures that mislead

Each trap is an exception to list, not something to fix. `pl_variance.py`
flags the account-name patterns; the rest need a look at the source.

| Trap | Why it is wrong | What to do | Source |
| --- | --- | --- | --- |
| "Sales tax expense" or VAT in expenses | Sales tax or VAT collected from customers is a liability, not revenue or expense. Tax paid on purchases may be an expense where it cannot be recovered | List it; the accountant decides | [1] |
| Revenue taken from a 1099-K or processor total | 1099-K totals mix personal and business receipts; processor totals are gross of refunds | Revenue comes from the invoice register or ledger, not the form | [2] |
| Net processor payouts booked as revenue | Revenue is gross; fees are an expense | Ask whether the payout split was booked (statement-reconciliation, processor clearing) | [3] |
| Owner or personal items in the P&L | They belong in equity as contributions or draws | Owner question; do not recategorise | [4] |
| Loan payments in expenses | Only the interest is an expense; principal reduces the liability | Unresolved without a lender schedule | [5] |
| Suspense, "Ask My Accountant", Uncategorised | Items not yet coded | Unmapped: excluded from subtotals and listed with their total | practitioner judgement (unsourced) |
| Report on the other basis | Cash and accrual months are not comparable | Refuse the comparison; get the other export | [6] |
| Cash movement presented as profit | Cash and profit differ by timing, financing and owner items | Keep any cash bridge separate, from reconciled bank totals only | practitioner judgement (unsourced) |
| Percentage on a tiny base | "+400%" on a 100.00 prior tells the reader nothing | "n/m" with the reason | practitioner judgement (unsourced) |

## Dimension views

When the chart of accounts uses classes, locations, jobs, funds or properties,
a view by that dimension is often what the owner needs: "which jobs made
money" [7]. Produce it only from dimensions present in the export; never
allocate costs to a dimension by estimate.

## Sources

1. Steven Bragg, Accounting for sales taxes, AccountingTools (2026). https://www.accountingtools.com/articles/accounting-for-sales-taxes
2. Intuit TurboTax blog, Mixing business and personal Venmo. https://blog.turbotax.intuit.com/self-employed/confession-ive-been-mixing-my-business-and-personal-venmo-140479/
3. Stripe, Payout reconciliation report (2026). https://docs.stripe.com/reports/report-types/payout-reconciliation
4. GrowthForce, Risks of commingling funds: piercing the corporate veil. https://www.growthforce.com/blog/piercing-the-corporate-veil
5. AccountingCoach, Recording a loan payment with interest and principal. https://www.accountingcoach.com/blog/interest-principal-loan-payments
6. Intuit QuickBooks, Run reports in QBO (accounting method) (2026). https://quickbooks.intuit.com/learn-support/en-us/help-article/report-management/run-reports-quickbooks-online/L7aILHhbl_US_en_US
7. Remote Raven, Full Charge Bookkeeper (CPA) job posting (2026). https://apply.workable.com/remote-raven/j/70CA2FAF85
