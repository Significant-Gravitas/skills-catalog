# Before asking for approval of an invoice draft

- [ ] Every line comes from an approved record (contract, SOW, PO, signed change, approver email) and cites it
- [ ] `invoice_totals.py` output pasted; no hand arithmetic (or labelled hand-computed)
- [ ] Tax shown only as supplied; per-line vs per-invoice rounding difference shown when tax applies
- [ ] `field_check.py` for the right regime; BLOCKS APPROVAL list is empty, or approval is not asked
- [ ] `register_check.py` run; no REPEAT line key; number is "to be assigned" or confirmed unused
- [ ] Recurring line compared with the previous invoice; every change has a source
- [ ] Customer and seller details from the approved record; no bank detail, tax ID or address copied from an unrelated invoice without confirmation
- [ ] Customer VAT/tax ID result recorded (valid / invalid / unchecked), if an ID is present
- [ ] Cross-border, credit-note, withholding and revenue-policy questions routed
- [ ] Draft rendered with the DRAFT watermark and delivered as a `workspace://` link
- [ ] Review block names the approver and the exact action awaiting approval
- [ ] Approval asked with `ask_question`; answer recorded with `log_approval.py`
- [ ] Nothing assigned, created, issued or sent without a verified approval for that action
