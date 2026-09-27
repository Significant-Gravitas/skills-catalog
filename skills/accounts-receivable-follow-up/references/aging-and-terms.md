# Aging, terms and what "overdue" means

Checked 2026-09-27.

## Contents
1. Buckets
2. Due dates and terms
3. Payments that are not yet applied
4. Groups and stages
5. Decisions that are not Mina's

## 1. Buckets

The common aging report shows Current, 1-30, 31-60, 61-90 and over 90 days,
counted from the due date; "Current" means not yet due [97][98]. The same
aging detail report is the working list for collections [98]. `ar_aging.py`
uses these edges by default (`--buckets 30,60,90`); they are a default, so
confirm with the owner whether they use others. The oldest bucket is escalated
first: it is the least collectable, and the allowance method used in
accounting estimates more loss the older a balance is [38].

`days_past_due` is negative when the invoice is not yet due (for example -2 =
due in 2 days).

## 2. Due dates and terms

- Use the due date printed on the invoice, or the issue date plus the agreed
  terms (`terms_days`) when the terms are on record.
- With neither, the invoice is `status unconfirmed`. In QuickBooks an invoice
  with no due date is treated as due on receipt and ages from its date [97];
  that is a system default, not the agreed terms, so confirm the terms with
  the account owner before calling it overdue.
- UK: with no agreed terms, B2B payment is late 30 days after the customer
  receives the invoice or the goods or service are delivered, whichever is
  later [30]. Record this as the owner's position only if they confirm it.

## 3. Payments that are not yet applied

Before any chase, look for money that already arrived:
- bank credits on or after the invoice date (`find_unapplied.py`), strongest
  first: the invoice number or its digits as a whole word ('REF 1047') in the
  description; the open balance and a customer word; the open balance only;
  a customer word with a different amount ("customer name, amount differs
  (possible part or combined payment)"). The last is the weakest, but it
  still stops the chase: a part or combined payment must be applied or ruled
  out by the owner first. A name-only credit is listed against every open
  invoice of that customer. A credit that ties for two invoices (the same
  amount, no name) is listed on both, marked 'ambiguous: also ...'; neither is
  chased until the owner says which it paid. Names are matched with accents
  folded ('Cafe Nord' meets 'CAFE NORD'). A recorded payment accounts for one
  bank credit only, so another customer's equal payment is still checked;
- deposits sitting in an undeposited-funds account: in QuickBooks it can be
  renamed, so find it by Detail type = Undeposited Funds [88];
- unapplied credits or credit notes on the customer's account.
A candidate moves the invoice to `status unconfirmed`, and the owner applies
the cash in the ledger. Chasing a customer who has paid is the costliest
mistake in receivables.

## 4. Groups and stages

| Group | Meaning | Action |
| --- | --- | --- |
| due soon | due within 7 days of the cutoff (default, confirm with the owner) | no chase; optional courtesy note only if the owner asks |
| past due, no known dispute | past the due date, open, no dispute, no promise | next stage draft |
| disputed or blocked | open dispute in the dispute log, or another blocker | acknowledge and route to the account owner; no payment request |
| promised payment not yet due | customer promised a date that has not passed | no chase; review the day after the promised date |
| status unconfirmed | no due date or terms, or a possible unapplied payment | ask the account owner; no chase |
| paid / credit balance | nothing open, or the customer is owed money | no chase; a credit goes to the owner |

Stages in order: first reminder → second reminder → statement of account →
owner call (the owner phones) → escalate to the owner for a decision.
`ar_aging.py` suggests the next stage from the contact log's last approved or
sent stage. Spacing between stages is the owner's choice; if none is set, use
at least 7 days between stages as a default and say it is a default to confirm.

## 5. Decisions that are not Mina's

Late fees, statutory interest, service stops, payment plans, collection
agencies, legal action and bad-debt write-offs. Write-offs and the allowance
method belong to the accountant [38]. Hardship, insolvency, legal threats and
sanctions go to the finance owner or counsel.
