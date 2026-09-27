# Required invoice fields by jurisdiction

Checked 2026-09-27. Before relying on a list for a real invoice, re-read the
cited page (`web_fetch`) and say the date you read it. `field_check.py`
encodes these lists; if the page has changed, follow the page and tell the
owner the script is out of date.

## Contents
1. UK: any business (GOV.UK) [48]
2. UK: VAT invoices (HMRC VAT Notice 700/21) [28]
3. Other jurisdictions
4. Tax on an invoice is a liability
5. Which regime applies

## 1. UK: any business [48]

An invoice must include:
- a unique identification number;
- the business's name, address and contact information (a limited company
  uses its full registered company name);
- the customer's company name and address;
- a clear description of what is being charged for;
- the date the goods or service were provided (supply date);
- the date of the invoice;
- the amount(s) being charged;
- VAT amount, if applicable;
- the total amount owed.

## 2. UK: VAT invoices [28]

A full VAT invoice adds, among other things: the seller's VAT registration
number; the time of supply (tax point) if different from the invoice date;
for each line the description, quantity, unit price, rate of VAT and amount
excluding VAT; the total VAT charged, shown in sterling; and any discount.
VAT records must be kept for at least 6 years [28]. Simplified and modified
invoices have their own rules: route those to the accountant.

## 3. Other jurisdictions

Required fields are set by contract, local law and the customer's accounts
payable process (practitioner judgement, unsourced). `field_check.py
--regime other` checks a minimum: parties and addresses, invoice date,
currency, description per line, due date or terms, payment instructions.
Anything beyond that comes from the accountant or the customer's PO terms.

## 4. Tax on an invoice is a liability

Sales tax or VAT charged to a customer is owed to the tax authority; it is a
liability, not revenue [77]. Show it on its own line, only as supplied by the
owner or accountant (rate per line, and the rounding method if they differ).
Never pick a rate, an exemption, reverse charge or zero-rating.

## 5. Which regime applies

| intake.json says | Regime |
| --- | --- |
| jurisdiction UK and VAT registered | `uk-vat` |
| jurisdiction UK, not VAT registered | `uk-general` |
| anything else, or unknown | `other`, and ask the accountant what the invoice must show |

Cross-border supplies, credit notes, withholding, retentions and progress
billing always go to the accountant before approval.
