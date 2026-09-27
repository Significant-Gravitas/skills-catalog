# Before drafting any payment follow-up

- [ ] Evidence cutoff stated (date and time of the payment records used)
- [ ] Aging from `ar_aging.py` (or labelled "hand-computed, not script-verified")
- [ ] `find_unapplied.py` run on the newest bank export with `--cutoff`; every candidate invoice moved to `status unconfirmed`
- [ ] Bank export reaches the cutoff date; if `BANK_COVERAGE_GAP`, the owner was asked for a newer export (or confirmed, verbatim, that nothing arrived after the bank end date) before any draft is offered for sending
- [ ] Undeposited funds and unapplied credits asked about if the ledger may hold them
- [ ] Due date or agreed terms on record for every invoice called overdue
- [ ] Part-payments, credits, disputes and promised dates visible in the table
- [ ] Dispute log and contact log read; the draft is the next stage, not a repeat
- [ ] Mailbox checked for remittances, disputes or promises (if connected), matching threads only
- [ ] No late fee, interest, service stop, collection or legal wording unless the owner opted in under an approved policy
- [ ] Each draft names one customer and only that customer's invoices
- [ ] Each draft ends with the exact action awaiting approval, naming mailbox and recipient
- [ ] Contact log rows prepared with stage, evidence cutoff, owner, approval state, next review
- [ ] Disputes, hardship, insolvency, legal threats and sanctions routed, not drafted around
