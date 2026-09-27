# Routing matrix: class → owner → urgency → safe interim state

Owners are roles; the names come from `intake.json` or the user. Urgency is
"at once" (raise in this turn), "before <deadline>" (a sourced date), or "next
review" (batch into the missing-documents request or accountant hand-off).
Sources at the end.

| Class (register value) | Route to | Urgency | Safe interim state |
| --- | --- | --- | --- |
| missing-source | The person who holds the record (usually the owner) | Next review; before close if it blocks a control | Item stays unresolved; batched into a missing-documents request |
| duplicate-or-conflict | Owner; accountant if already posted | Before the next payment run if a payment is involved | Leave both records; recommend Exclude (not delete) for a feed duplicate |
| unknown-party-or-purpose | Owner | Next review | Unresolved; never guess a category |
| mismatch (amount, date, currency, entity) | Owner; accountant if a correction is needed | Next review | Unresolved; source left unchanged |
| bank-detail-change | Approved finance owner | **At once**, and before any payment to the payee [1] | Payment to the payee held in the draft run; verification only through a contact on file before the change |
| unusual-payment | Approved finance owner | **At once** | Unresolved; no contact with the payee from here |
| payroll-tax-shortfall | Owner and accountant | **At once** [2] | Never suggest paying other creditors first |
| tax-payroll-equity-loan-asset-policy | Qualified accountant or tax adviser | Next hand-off; at once if a filing deadline is sourced | Draft only; no treatment chosen |
| worker-classification | Accountant [3] | Next hand-off | Record how each contractor was paid; no 1099/W-9 decision |
| payee-missing-w9-tin | Accountant [4] | Before year-end reporting | List the gap; never compute backup withholding |
| receipt-without-payment-line | Owner | Next review; at once if a pattern suggests fabricated receipts [5] | Receipt is not support until tied to a card or bank line |
| closed-period-change | Accountant | At once | Nothing re-opened or undone; propose a current-period correction [6] |
| suspected-error-fraud | Finance owner; if the concern involves them, the next named owner | **At once** | No accusation; no contact with the suspected party; original records untouched |
| privacy-access | Security or privacy owner | At once | Recommend the owner restricts access; this assistant cannot change access to any system |
| Legal claim or dispute (any class) | Counsel, via the owner | As the owner decides | No statement to the other party |

## Qualitative triggers (escalate whatever the amount)

An item that turns a loss into a profit or the reverse, affects a loan covenant
or owner pay, or may involve illegality is material regardless of size [7].
Related-party items are added as practitioner judgement (unsourced; not among
SAB 99's listed factors). Never claim materiality from size unless the owner
supplied a threshold.

## Owner-delegate path

If the concern involves the person who would normally decide (for example the
finance owner is the payee, approved the payment, or changed the vendor record),
route to the next named owner in `intake.json` and say why in one factual line.
Owner or executive frauds cost more than nine times employee frauds and more
than half of cases involve missing or overridden controls [8]. If there is no
second named owner, ask the user who else should receive it; never pick one.

## Sources

1. FBI IC3, Business Email Compromise: The $55 Billion Scam (2024). https://www.ic3.gov/PSA/2024/PSA240911
2. IRS, Employment taxes and the Trust Fund Recovery Penalty. https://www.irs.gov/businesses/small-businesses-self-employed/employment-taxes-and-the-trust-fund-recovery-penalty-tfrp
3. IRS, Independent contractor (self-employed) or employee? (2025). https://www.irs.gov/businesses/small-businesses-self-employed/independent-contractor-self-employed-or-employee
4. IRS, Backup withholding (2025). https://www.irs.gov/businesses/small-businesses-self-employed/backup-withholding
5. PYMNTS (AppZen data), AI-generated fake receipts now 71% of expense fraud (2026). https://www.pymnts.com/news/artificial-intelligence/2026/ai-generated-fake-receipts-now-make-up-71percent-of-expense-fraud/
6. Intuit QuickBooks, Undo or remove transactions from reconciliations (2026). https://quickbooks.intuit.com/learn-support/en-us/help-article/accounting-bookkeeping/undo-remove-transactions-reconciliations-online/L6ERlEXxn_US_en_US
7. SEC, Staff Accounting Bulletin No. 99, Materiality (1999). https://www.sec.gov/interps/account/sab99.htm
8. ACFE, Key Findings: Occupational Fraud 2026. https://www.acfe.com/acfe-insights-blog/blog-detail?s=key-findings-report-to-the-nations-2026
