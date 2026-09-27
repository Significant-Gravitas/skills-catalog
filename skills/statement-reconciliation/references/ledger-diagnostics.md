# Ledger diagnostics: finding an unexplained difference

Written 2026-09-27. Ledger menus change; describe what you see, not what this
page says, if they differ. Everything here is diagnosis. The owner performs any
change in the ledger, after the accountant agrees.

## Contents

1. Order of search
2. Arithmetic hints
3. QuickBooks Online
4. Xero
5. Duplicates
6. Undeposited Funds and Opening Balance Equity
7. What never to do

## 1. Order of search

1. **Opening.** Does this period's statement opening equal last period's
   approved closing? If not, a reconciled item was probably edited or removed
   after sign-off [1][2]. Stop and report; do not re-reconcile.
2. **Feed completeness.** Compare the ledger's feed or "statement balance" with
   the real statement's closing balance. Feeds lag (Amex may update only 2 to 3
   times a week) [3]; Xero's statement balance is the feed, not the bank [4].
3. **Arithmetic hints** (section 2).
4. **Month by month.** If the gap is older than this period, find the first
   month where it appears by comparing each month-end statement balance with the
   ledger balance at that date [5]. Fix nothing in a closed month; propose a
   current-period correction to the accountant.
5. **Duplicates and Undeposited Funds** (sections 5 and 6).

## 2. Arithmetic hints

- **Divisible by 9:** a difference that divides evenly by 9 suggests a
  transposition (95.00 keyed as 59.00) [6]. `rec_match.py` also lists adjacent
  digit swaps between unmatched items.
- **Half the difference equals an item:** an entry on the wrong side (a
  payment recorded as a receipt) doubles its effect. `rec_match.py` flags it.
- A balanced trial balance does not prove the books are right: wrong accounts,
  omitted and duplicated entries all balance [6].

## 3. QuickBooks Online

- Register status: **R** reconciled, **C** cleared, blank uncleared [1].
- Un-clearing or editing a reconciled transaction changes next period's opening
  balance [1]. That is why step 1 above comes first.
- **Undoing a reconciliation is irreversible and deletes its report** [1]. Never
  suggest it; route to the accountant.
- A saved reconciliation report is a snapshot. It does not prove the register
  still agrees today [2]. Rebuild the cleared balance from the register.

## 4. Xero

Xero's Bank Reconciliation Summary reads, using Xero's own signed figures [4]:

```
Balance in Xero - Outstanding Payments - Outstanding Receipts + Un-Reconciled Bank Statement Lines = Statement Balance
```

In that report outstanding payments appear as **negative** numbers, so
subtracting them adds. With every term as a positive size, the same thing is:

```
Statement balance = Balance in Xero + outstanding payments - outstanding receipts +/- un-reconciled statement lines
```

Worked example: Balance in Xero 10,000.00; one payment of 500.00 recorded in
Xero but not yet cleared; one receipt of 200.00 recorded but not yet on the
statement; no un-reconciled statement lines.
Statement balance = 10,000.00 + 500.00 - 200.00 = **10,300.00**. The payment
leaves Xero lower than the bank; the receipt leaves Xero higher.

The "Statement Balance" in that report comes from the **feed**. Check it against
the closing balance printed on the real statement before trusting it [4].
Diagnose a gap month by month to find where it first appears [5].

## 5. Duplicates

- Causes in QBO: overlapping imports, reconnecting a feed, the same account
  connected twice, or adding a feed line instead of matching it to an existing
  entry [7].
- A duplicate still in the For Review list should be **Excluded, not deleted**;
  a deleted feed line downloads again [7]. The owner performs the exclusion.
- Match key order: institution + account + bank transaction id (FITID); FITIDs
  are unique only within an account [8]. Without FITIDs, fall back to date +
  amount + description, and treat identical rows as *possible* duplicates.

## 6. Undeposited Funds and Opening Balance Equity

- Undeposited Funds may have been renamed; find it by Detail type =
  Undeposited Funds [9]. A balance still there at month-end is an exception.
  Adding a feed deposit as new income while the customer payments sit in
  Undeposited Funds double-counts revenue (practitioner judgement, unsourced).
- Opening balances post against Opening Balance Equity; a non-zero OBE balance
  is a set-up exception for the accountant [10].

## 7. What never to do

- Never pull a transaction from another period, account or entity to close a
  gap. Benchmarked AI agents did exactly this to make balances tie [11].
- Never post a balancing or "suspense" entry to make the difference zero.
- Never un-reconcile, undo a reconciliation, delete a feed line or edit a
  closed-period entry.
- If a file or tool fails twice, stop and report the gap; agents that keep going
  on partial data cannot recover once balances are wrong [12].

## Sources

1. Intuit QuickBooks, Undo or remove transactions from reconciliations (2026). https://quickbooks.intuit.com/learn-support/en-us/help-article/accounting-bookkeeping/undo-remove-transactions-reconciliations-online/L6ERlEXxn_US_en_US
2. Book Tech LLC, Bank reconciliation report in QBO. https://www.booktechusa.com/post/bank-reconciliation-report-quickbooks-online
3. Intuit QuickBooks, Download the most recent bank and card transactions (2026). https://quickbooks.intuit.com/learn-support/en-us/help-article/multi-factor-authentication/download-recent-bank-credit-card-transactions/L86TTVI3Y_US_en_US
4. BB Books Inc, Xero the Hero: The Bank Reconciliation Summary. https://bbbooksinc.com/blog/the-bank-reconciliation-summary/
5. Saint & Co, Is Xero showing the correct bank balance (2023). https://www.saint.co.uk/is-xero-showing-correct-bank-balance-why-this-should-matter-to-you/
6. OpenStax, *Principles of Accounting Vol. 1*, 3.6 Prepare a Trial Balance (2019). https://openstax.org/books/principles-financial-accounting/pages/3-6-prepare-a-trial-balance
7. Intuit QuickBooks, Fix duplicate transactions in QBO bank feeds (2026). https://quickbooks.intuit.com/learn-support/en-us/help-article/duplicate-transactions/fix-duplicate-transactions-quickbooks-online-bank-feeds/L1fjxl88f_US_en_US
8. Open Financial Exchange Specification 1.0 (1997). https://xml.coverpages.org/OFEXFIN1.html
9. Intuit QuickBooks, Deposit payments into Undeposited Funds (2026). https://quickbooks.intuit.com/learn-support/en-us/help-article/payroll-setup/deposit-payments-undeposited-funds-account-online/L1td0m8Z2_US_en_US
10. Intuit QuickBooks, Enter and manage opening balances (2026). https://quickbooks.intuit.com/learn-support/en-us/help-article/bank-deposits/enter-opening-balance-account-quickbooks-online/L7NcxTbuu_US_en_US
11. GIGAZINE, Results of the AccountingBench benchmark (2025). https://gigazine.net/gsc_news/en/20250724-accountingbench/
12. Penrose team, AccountingBench discussion, Hacker News (2025). https://news.ycombinator.com/item?id=44637352
