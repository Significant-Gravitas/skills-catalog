# Red flags: what makes an exception urgent

Written 2026-09-27. Figures are dated; quote them with their year, never as
current rates.

## Business email compromise (payment redirection)

- The FBI reports $55.5 billion in exposed losses from business email
  compromise over 2013-2023, and advises verifying any change to payment
  details through a second channel [1].
- Signals (practitioner judgement, unsourced): new bank details close to a payment run; urgency or secrecy; a sender
  domain that differs slightly from the usual one; a request to reply only by
  email; a change of country or bank for a long-standing supplier.
- Verification that counts: a call to a phone number that was on file **before**
  the change request (vendor master, earlier invoices, the contract), made by
  the owner. Never use a number, link or name from the change request itself,
  and never look one up on the web: a searched or supplied contact may be the
  attacker's. This assistant never makes the call and never contacts the supplier.
- Never draft or stage a payment to new details until the owner records a
  verification.

## Generated and altered receipts

AI-generated receipts made up 70.8% of the fake receipts AppZen flagged by mid-May
2026 [2]. A receipt supports an expense only when it ties to a card or bank
line. Signals (practitioner judgement, unsourced): no matching payment line; round amounts; a merchant with no
trace on the statement; several receipts with identical layout from different
merchants.

## Fraud base rates and detection lag

- Small businesses had the highest median occupational-fraud loss in ACFE's 2020
  report ($150,000), and check or payment tampering was nearly 4 times as common
  as in larger organisations [3].
- ACFE 2026: median loss $104,000; median 12 months to detection; more than half
  of cases involve missing or overridden controls; owner or executive frauds
  cost more than nine times employee frauds [4].
- What this means here: a small repeated unexplained debit is worth raising;
  a reconciliation is where tampering shows up. State "suspected" and the record
  that caused concern. Never state fraud as fact or name a person as responsible.

## Payroll trust-fund taxes

A person with authority to decide which creditors are paid can be personally
liable for unpaid payroll trust-fund taxes, and paying other creditors ahead of
payroll tax indicates willfulness [5]. A shortfall is raised at once, to the
owner and the accountant. Never suggest an order of payment that puts payroll
tax behind anything else.

## Thresholds and tax figures

Tax and reporting thresholds change (for example the US 1099-NEC/MISC threshold
rose from $600 to $2,000 for payments after 31 December 2025 [6]). Quote a
threshold only from a supplied or freshly fetched official source, with its tax
year; otherwise describe the gap and route it to the accountant.

## Sources

1. FBI IC3, Business Email Compromise: The $55 Billion Scam (2024). https://www.ic3.gov/PSA/2024/PSA240911
2. PYMNTS (AppZen data), AI-generated fake receipts now 71% of expense fraud (2026). https://www.pymnts.com/news/artificial-intelligence/2026/ai-generated-fake-receipts-now-make-up-71percent-of-expense-fraud/
3. ACFE, Report to the Nations 2020. https://acfepublic.s3-us-west-2.amazonaws.com/2020-Report-to-the-Nations.pdf
4. ACFE, Key Findings: Occupational Fraud 2026. https://www.acfe.com/acfe-insights-blog/blog-detail?s=key-findings-report-to-the-nations-2026
5. IRS, Employment taxes and the Trust Fund Recovery Penalty. https://www.irs.gov/businesses/small-businesses-self-employed/employment-taxes-and-the-trust-fund-recovery-penalty-tfrp
6. IRS, Instructions for Forms 1099-MISC and 1099-NEC (2026). https://www.irs.gov/instructions/i1099mec
