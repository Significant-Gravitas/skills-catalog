Adapted from anthropics/knowledge-work-plugins `finance/skills/close-management` (Apache-2.0); see ATTRIBUTION.md and LICENSE in this package.

# Close dependency map

What must be ready before what. A task cannot move to `ready for review` while
anything it depends on is `not started` or `blocked`. Every step here is
preparation or review; posting, adjusting, and locking the period stay with the
owner and the accountant.

The ids in brackets are the control ids in `templates/close-controls.csv`;
`scripts/close_status.py` enforces this map, so a status change that skips a
dependency is refused.

```
LEVEL 1 (no dependencies; can start at cutoff)
├── Bank and card statements for the full period received [S1]
├── Sales invoice, credit, and refund list through cutoff [S2]
├── Bills, receipts, and expense claims through cutoff [S3]
├── Payroll report received [S4]
├── Loan, transfer, and owner-account statements received [S5]
└── Processor payout or activity reports (Stripe, PayPal, Square) [S6]

LEVEL 2 (needs Level 1)
├── Bank and card reconciliations (needs statements + recorded receipts and payments) [1]
├── Sales complete through cutoff [2]; bills, receipts and claims complete [3]
├── Receivables aging (needs invoices + customer receipts) [4]
├── Payables aging (needs bills + supplier payments) [4]
├── Payroll tie-out (needs payroll report + bank lines) [5]
├── Processor clearing (needs processor reports + bank lines) [10]
├── Opening Balance Equity checked (zero or routed) [12]
└── Bills not yet received checked (needs bills list + known recurring suppliers) [13]

LEVEL 3 (needs Level 2)
├── Accrual, prepayment, fixed-asset, FX, and revenue-policy items packaged for the accountant [7]
├── Loan, interest, owner, and intercompany balances reconciled (needs both sides recorded) [6]
├── Undeposited Funds and suspense reviewed (needs bank and processor reconciliations) [11]
├── Owner sign-off recorded on each bank reconciliation [14]
└── Proposed adjustments listed, each with source, reason, and preparer [9]

LEVEL 4 (needs Level 3 approved, or each open item listed)
├── Draft profit-and-loss and balance movements [8]
└── Variance review against prior period and plan [8]

LEVEL 5 (needs Level 4): the period is "prepared for review" here
├── Owner and accountant review
└── Approval record captured (approvals.csv, by SHA-256)

AFTER APPROVAL (does not gate "prepared for review")
├── Lock date recorded as the owner states it [15]
└── Owner closes the period in their own system (not done here)
```

Critical path, in most small-business closes: statements received → bank
reconciliation → accountant items → draft P&L → review. A late bank statement
delays everything after it; say so in the close report rather than working
around it.

Parallel work: Level 2 reconciliations do not depend on each other, so start
each as soon as its own Level 1 inputs arrive.
