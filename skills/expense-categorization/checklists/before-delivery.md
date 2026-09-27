# Before delivering an expense review

- [ ] Totals from `write_review.py` (or labelled "hand-computed, not script-verified"): source rows and amount, Ready, Needs review, unresolved, excluded
- [ ] Ready + Needs review = source total; control total ties or the difference is shown
- [ ] Every source row appears once, amounts unedited, sign and currency kept
- [ ] Every account name is from the approved chart, or `unresolved`
- [ ] No row in Ready to post has missing evidence, a special line, an open question or a medium/low confidence
- [ ] Every receipt ties to a payment line, or is listed as an exception
- [ ] Duplicate pairs listed with both rows kept; none deleted
- [ ] Refunds, transfers, card payments, owner items, loans, tax, payroll and processor lines kept apart from operating expense
- [ ] Foreign-currency lines keep both the source and settled amounts
- [ ] Possible fixed assets and contractor payees flagged for the accountant; no deductibility or capitalisation stated
- [ ] No tax or substantiation threshold quoted from memory
- [ ] Each review need names one fact and one owner
- [ ] Files delivered with `workspace://` links; state copy saved to `expenses/<YYYY-MM>-review.csv`
- [ ] New or changed coding rules recorded with approver and date
