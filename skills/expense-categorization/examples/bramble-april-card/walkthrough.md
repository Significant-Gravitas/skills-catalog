# Worked example: Bramble Design Ltd, Amex, April 2026 (fictional)

Inputs in this folder: `amex-2026-04.csv` (raw export, charges positive),
`receipts.csv` (four receipts, typed or from `receipt_text.py`),
`receipt-trainline.txt`, `chart.csv` (chart v2 with short definitions),
`coding-rules.csv` (owner rules; R7 never approved), `history/2026-03-review.csv`
(last month's approved rows). The correct result is `expected-review.csv`.

Hard cases: a subscription charged twice and later refunded; an exact duplicate
pair with one receipt; a receipt with no card line; a rule conflict; an
unapproved rule; a USD charge settled in GBP.

## 1. Pre-flight and inputs

- `intake.json` for bramble-design exists: period April 2026, GBP, card
  sign convention confirmed (positives are charges), chart v2.
- `python3 --version` present. State pre-flight printed `STATE_OK`.
- Files pulled with `read_workspace_file(..., save_to_path="/home/user/in/...")`.

## 2. Normalise, check, propose

```
cd ~/skills/expense-categorization && python3 scripts/normalize_export.py /home/user/in/amex-2026-04.csv --date-format %Y-%m-%d --flip-sign --out /home/user/work/amex.csv
cd ~/skills/expense-categorization && python3 scripts/expense_checks.py --tx /home/user/work/amex.csv --receipts /home/user/in/receipts.csv --control-total -900.69 --out /home/user/work/checks.json
cd ~/skills/expense-categorization && python3 scripts/propose_from_history.py --tx /home/user/work/amex.csv --rules ~/workspace/bookkeeping/bramble-design/coding-rules.csv --history ~/workspace/bookkeeping/bramble-design/expenses/ --checks /home/user/work/checks.json --chart /home/user/in/chart.csv --out /home/user/work/proposals.csv
```

`expense_checks.py` output (abridged): 8 rows; out -945.69; in 45.00; net
-900.69; control total ties. Exact duplicates amex:6 and amex:7 (Pret, 18 Apr).
Likely duplicates amex:2 and amex:5 (Figma, 12 days apart). Special lines:
amex:8 refund; amex:9 processor and foreign currency. Receipts: 3 of 4 tied;
EXCEPTION R4 (Screwfix 89.00, 20 Apr) has no payment line.

`propose_from_history.py`:

| Row | Proposal | Basis | Cap |
| --- | --- | --- | --- |
| 2 | Software subscriptions | rule R1 | high |
| 3 | — | conflict: R4a=Travel vs R4b=Staff training | medium |
| 4 | Office supplies | unapproved rule R7 | medium |
| 5 | Software subscriptions | rule R1; likely duplicate | medium |
| 6, 7 | Meals and subsistence | history: 2 approved rows; exact duplicate | low |
| 8 | — | special line: refund | low |
| 9 | — | none | — |

## 3. Reason over what the scripts could not settle

- Row 3: the Trainline receipt says "client visit, Leeds", which fits R4a
  (Travel), but only Jo can confirm; proposed Travel, medium.
- Row 4: no receipt. R7 was Mina's March suggestion, never approved, and £612.99
  could be equipment. Left `unresolved`, low; ask for an itemised receipt and
  flag "possible fixed asset, accountant to decide".
- Row 8: a Figma refund of 45.00 on 22 April probably reverses row 5; the pairing
  is a question, not a fact.
- Row 9: "STRIPE USD 120.00" settled as GBP 95.10. Both amounts kept; what was
  bought is unknown.
- R4 Screwfix receipt: no card line. It is an exception (perhaps paid by
  another card or personally), not support for anything.

## 4. Build and validate the table

The completed table is `expected-review.csv`. Then:

```
cd ~/skills/expense-categorization && python3 scripts/write_review.py --review /home/user/work/review.csv --tx /home/user/work/amex.csv --chart /home/user/in/chart.csv --checks /home/user/work/checks.json --proposals /home/user/work/proposals.csv --control-total -900.69 --outdir /home/user/out/expenses-2026-04
```

| Measure | Rows | Amount |
| --- | --- | --- |
| Source export | 8 | -900.69 |
| Ready to post | 1 | -45.00 |
| Needs review | 7 | -855.69 |
| of which unresolved | 4 | |
| Excluded (listed with reason) | 0 | |

Ready + needs review = source: yes. Control total -900.69: ties.

## 5. Output to Jo

"One expense is ready to post and seven need review. The seven are listed with
the receipt, my proposed category and the one fact that would settle each. I
left tax treatment blank for Dev." Then the Needs review rows, the totals
table, the exception (R4 has no card line), and a link to the full file
(`workspace://…`). One `ask_question` card with rows 4, 3, 5+8, 6+7 and 9
(`templates/review-queue-questions.md`).

Saved: `~/workspace/bookkeeping/bramble-design/expenses/2026-04-review.csv`.
When Jo answers "Trainline to Leeds is always client travel", a rule is added
to `coding-rules.csv` with Jo as approver and the date.

## What a wrong answer would look like

- Coding row 7 as a second Pret lunch without asking, or deleting it.
- Treating R4 as evidence for row 4 because both are "supplies".
- Converting USD 120.00 at a remembered rate.
- Marking row 4 "Office supplies, high" because R7 exists.
- Saying the Pret lunch is "50% deductible".
