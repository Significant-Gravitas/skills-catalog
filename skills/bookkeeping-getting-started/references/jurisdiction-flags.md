# Jurisdiction flags to capture at intake

Checked 2026-09-27 against the sources cited. Dates and thresholds change:
re-check the cited page (with `web_fetch`) before quoting any figure to the
owner, and quote it with the page and the date you read it. The skill records
these flags; it never decides a tax position.

## Contents
1. Questions for every entity
2. United States
3. United Kingdom
4. Other jurisdictions

## 1. Questions for every entity

- Country of registration and legal form (company, sole trader, partnership).
- Fiscal year end. Never assume a calendar year [19].
- Accounting basis if the accountant has set one (cash or accrual) [19]; else `open`.
- Sales tax / VAT / GST registration: yes, no, or not known.
- Who files returns (the accountant, the owner, a payroll provider).

## 2. United States

| Flag | What to record | Source |
| --- | --- | --- |
| Basis | cash or accrual as supplied; QuickBooks reports can be switched per report, so record the basis the owner wants on reports | [19][99] |
| Record retention | 3 years is the general period; 4 years for employment tax records; 6 years if income is under-reported by more than 25%; 7 years for a bad-debt or worthless-securities claim; indefinitely if no return was filed or for fraud | [17] |
| Sales tax | states where sales are made; economic nexus can arise without physical presence (post-Wayfair); record per-state sales totals, never say no tax is owed | [86] |
| 1099 payees | whether the business pays contractors; record payee names and payment method only; thresholds belong to the accountant and change by tax year | [24][23] |

## 3. United Kingdom

| Flag | What to record | Source |
| --- | --- | --- |
| Company records | limited companies keep records for 6 years from the end of the last company financial year they relate to | [29] |
| Sole trader records | at least 5 years after the 31 January submission deadline of the relevant tax year | [29] |
| VAT | registered or not; VAT number (from the owner, never copied from another document); VAT records kept at least 6 years | [28] |
| Making Tax Digital for Income Tax (sole traders and landlords) | mandatory from 6 April 2026 for qualifying income above £50,000; from April 2027 above £30,000; from April 2028 above £20,000; digital records and quarterly updates | [31][67] |
| Invoices | required fields, see invoice-drafting-and-issue | [48] |

Ask a UK sole trader whether they are signed up for MTD and which software
they use; do not work out whether they must be.

## 4. Other jurisdictions

Record the country and the accountant. Do not apply US or UK rules. Every
tax, retention or invoicing question goes to the accountant.
