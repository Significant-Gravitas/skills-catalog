# Special lines: what is not an operating expense

These lines distort the P&L when coded as ordinary spend. `expense_checks.py`
flags them by description pattern (table in section 2); the flag is a prompt
for a question, not a coding decision. Checked 2026-09-27.

## Contents
1. Handling by kind
2. Default detection patterns
3. Contractor and fixed-asset flags

## 1. Handling by kind

| Kind | Why it is special | What Mina does | Question to ask | Decides |
| --- | --- | --- | --- | --- |
| Refund / reversal | Reduces an earlier cost; is not new spend | Pair with the original charge by vendor and amount; propose the same account as the original with the pairing stated | "Which charge does this refund reverse?" | owner |
| Transfer between own accounts | Moves money; no income or cost | Mark `unresolved` until both sides are identified | "Is `<account>` one of the business's own accounts?" | owner |
| Card payment (from bank) | Pays the card balance; the spend is coded on the card lines | Exclude from expense coding with reason "card payment, coded on card export" | none if the card export is in scope | owner |
| Owner / personal items | Commingled personal items belong in owner equity (contribution or draw), not the P&L [81][18] | Flag; never code to an expense account | "Business or personal?" | owner; accountant for treatment |
| Loan repayment | Splits into interest (expense) and principal (liability) [78] | `unresolved` until the lender schedule is supplied; never split by guess | "Can you share the lender's statement or schedule for `<month>`?" | accountant |
| Tax payments (VAT, sales tax, payroll tax, corporation tax) | Sales tax or VAT collected is a liability, not revenue or expense [77] | Keep out of operating expense; `unresolved` with the tax named | "Which return or period does this payment relate to?" | accountant |
| Payroll | Wages, withholdings and employer taxes need the payroll register | Never code from the bank line alone; route | "Can you share the payroll register for `<period>`?" | accountant / payroll provider |
| Processor lines (Stripe, PayPal, Square) | Payouts are net of fees, refunds and disputes [94][96]; charges through a processor hide the real vendor | For fees: propose the fee account only with a payout report; for a purchase through a processor ask what was bought | "What was bought, and from whom?" | owner |
| Foreign currency | Settled amount differs from the source amount | Keep both amounts and currencies; never convert with a remembered rate | "Is there an invoice in the original currency?" | owner; FX policy to accountant |
| Money in (on a bank export) | Income or a transfer, not an expense | Out of scope for this skill; hand to invoice/AR or reconciliation | none | — |
| Auto-added bank-rule items | Bank rules can add items without review [100] | Include them in the review like any other line | "Was this rule meant to auto-add?" | owner |

## 2. Default detection patterns (case-insensitive regular expressions)

Override with `--patterns <csv with kind,regex>` when a client's bank uses other wording.

| Kind | Pattern |
| --- | --- |
| refund | `\b(REFUND|REVERSAL|REVERSED|RETURN|CHARGEBACK|CREDIT VOUCHER)\b` |
| card_payment | `\b(AMEX PAYMENT|CARD PAYMENT|PAYMENT RECEIVED|PAYMENT THANK YOU|CC PAYMENT)\b` |
| transfer | `\b(TFR|TRANSFER|XFER|TRF|INTERNAL TRANSFER|TO SAVINGS)\b` |
| owner | `\b(DRAWINGS?|OWNER|DIRECTOR'?S? LOAN|DLA|PERSONAL)\b` |
| loan | `\b(LOAN|FUNDING CIRCLE|IWOCA|MORTGAGE|LENDING|FINANCE DD|SBA)\b` |
| tax | `\b(HMRC|IRS|EFTPS|VAT|SALES TAX|FRANCHISE TAX|CORP TAX|COMPANIES HOUSE)\b` |
| payroll | `\b(PAYROLL|GUSTO|ADP|SALARY|SALARIES|WAGES|PAYE|NEST|PENSION)\b` |
| processor | `\b(STRIPE|PAYPAL|SQUARE|SUMUP|ZETTLE|SHOPIFY PAYMENTS)\b` |
| foreign_currency | `\b(USD|EUR|GBP|CAD|AUD|NZD|CHF|JPY)\s?\d` or `\b(FX|NON-STERLING|FOREIGN|INTL)\b` |
| money_in | any positive amount not already flagged refund or card_payment |

A pattern miss is possible (a transfer described only by a name, for example
"J SMITH"). Patterns reduce misses; they do not replace reading each line.

## 3. Contractor and fixed-asset flags

- **Possible fixed asset.** Equipment, computers, furniture, vehicles: mark
  "possible fixed asset, accountant to decide" and ask for an itemised
  invoice. US de minimis capitalisation rules need an election and apply per
  item or invoice, so itemisation matters [22][83]. Never decide to expense
  or capitalise.
- **Contractor payments.** Record the payee and the payment method (bank
  transfer, card, PayPal and so on). Card and third-party network payments
  reported on Form 1099-K are excluded from 1099-NEC reporting [24]; the
  accountant decides reporting. A regular fixed payment to someone labelled a
  contractor is a classification flag for the accountant: the IRS test turns
  on behavioural control, financial control and the relationship, not the
  contract label [27].
- **Thresholds.** Do not quote any 1099, capitalisation or substantiation
  threshold from memory. Use only a figure the owner or accountant supplied,
  or one fetched from the current official page with its tax year [65][76].
