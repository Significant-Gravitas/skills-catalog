# Blocking questions: `ask_question` patterns

Put every blocking question into one `ask_question` call (at most 10
questions; options at most 200 characters each). Give each an id (Q1, Q2 …)
in the question text so the answer can be recorded in
`intake.json.open_questions`. More than 10: ask the ten that unblock the most
work and list the rest in the intake.

Rules
- Every option comes from the records or is a neutral choice. Never offer a
  guessed amount, date, account or tax treatment as an option.
- Always include a "Not sure" route. For basis, tax and policy questions it
  is "Not sure: ask the accountant".
- Never pre-select a default for basis or tax.
- Record the answer and who the user said they are ("answered_by_as_stated").
  Never infer identity.

| Gap | Question | Options |
| --- | --- | --- |
| Ambiguous dates | Q1. Are dates in `<file>` day/month/year or month/day/year? (Row 3 reads 03/04/2026.) | Day/Month/Year · Month/Day/Year · Not sure: I will check the bank app |
| Short export | Q2. `<file>` stops on `<date>`. Can you export to `<period end>`? | Yes, uploading now · That is all there is · Not sure |
| Opening balance | Q3. Has `<accountant>` signed off the `<prior month>` closing balances? | Yes: I will upload the signed trial balance · Not yet · Not sure: ask `<accountant>` |
| Basis | Q4. Should management reports be on a cash or an accrual basis? | Cash · Accrual · Not sure: ask the accountant |
| Entity | Q5. Does `<file>` belong to `<entity>`? | Yes · No: different entity · Mixed personal and business |
| Sign convention | Q6. In `<card file>`, are positive amounts charges? | Yes, positives are charges · No, positives are refunds or payments · Not sure |
| Balance break | Q7. `<file>` balance jumps by `<difference>` at line `<n>`. Is a page or row missing? | I will re-export the full period · The bank shows the same · Not sure |
| Fiscal year end | Q8. What is the fiscal year end? | 31 December · 31 March · 5 April · Other: I will type it · Not sure: ask the accountant |
| Approver | Q9. Who approves invoices and customer messages? | `<names the owner has mentioned>` · Me · I will type a name |
| Export copy | Q10. Do you hold your own export of the ledger and documents? | Yes · No: I will export them · Not sure how |

After the answers arrive, update `intake.json`, rerun `intake_check.py`, and
move each unblocked item from Blocked to Ready or Usable with a warning.
