# Hard case: bank lines that are not operating expenses (fictional)

Input: `bank-main-2026-04.csv` (Bramble Design Ltd main account; the owner has
confirmed day/month/year). Checked together with the April Amex export:

```
cd ~/skills/expense-categorization && python3 scripts/normalize_export.py /home/user/in/bank-main-2026-04.csv --date-format %d/%m/%Y --currency GBP --out /home/user/work/bank.csv
cd ~/skills/expense-categorization && python3 scripts/expense_checks.py --tx /home/user/work/amex.csv --tx /home/user/work/bank.csv --out /home/user/work/checks.json
```

Script result for the bank rows: `bank:2` and `bank:8` money in; `bank:4` tax;
`bank:5` transfer; `bank:7` loan; `bank:9` card payment. Cross-file pairs:
`amex:3 <-> bank:6` (Trainline, same day, same amount: exact) and
`amex:2`/`amex:5 <-> bank:3` (Figma, likely).

## Expected handling

| Row | Line | Expected outcome | Question / owner |
| --- | --- | --- | --- |
| bank:2 | ORIEL HEALTH LTD INV-1038 +3,500.00 | Excluded from expense coding: money in, for invoice/AR matching | — |
| bank:3 | FIGMA -45.00, 2 Apr | Needs review: Figma also charged on the Amex on 3 and 15 Apr | Jo: which account pays Figma? Is one charge a duplicate? |
| bank:4 | HMRC VAT -1,204.40 | Needs review, `unresolved`: VAT payment is a liability movement (VAT control), not an expense [77] | Dev: which VAT return period? |
| bank:5 | TFR TO J SMITH -500.00 | Needs review, `unresolved`: transfer to a person. Never coded to an expense | Jo: director drawing, loan to director, reimbursement or wages? (treatment: Dev) |
| bank:6 | TRAINLINE -118.40, 7 Apr | Needs review: the same ticket appears on the Amex the same day | Jo: paid twice, or one is a reimbursement? |
| bank:7 | FUNDING CIRCLE DD -812.00 | Needs review, `unresolved` until the lender schedule splits interest and principal [78] | Jo: lender statement for April |
| bank:8 | HARBOUR FLORISTS INV-1042 +1,800.00 | Excluded: money in | — |
| bank:9 | AMEX PAYMENT -2,800.00 | Excluded: card payment; the spend is coded on the card export | — |

Nothing on the bank export is Ready to post. The summary says so plainly:
"None of the eight bank lines is an operating expense I can code without an
answer: two are receipts from customers, one pays the Amex, and five need a
fact from Jo or Dev."

## Traps this tests

- Coding `HMRC VAT` to "Taxes" in the P&L.
- Splitting `FUNDING CIRCLE` 80/20 by guess.
- Coding `TFR TO J SMITH` as "Contractor" or "Wages".
- Coding both the bank and the card Trainline lines, doubling the cost.
- Adding `AMEX PAYMENT` as an expense on top of the card lines.
