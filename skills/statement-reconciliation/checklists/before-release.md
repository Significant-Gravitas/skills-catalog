# Before releasing a reconciliation

Tick every line or say why it does not apply. Any "no" in section A blocks the
word "reconciled".

## A. Controls

- [ ] Statement opening equals the prior approved closing, or the gap is reported and nothing else was done.
- [ ] Statement closing comes from the real statement, not a ledger feed balance.
- [ ] Both files prove: opening + in-period lines = closing (rec_match did not stop).
- [ ] PDF statements were extracted with `extract_statement.py` and printed PROVEN.
- [ ] Unexplained difference is exactly 0.00, or the status says NOT RECONCILED.
- [ ] No out-of-period, other-account or other-entity row was used to close a gap.
- [ ] No balancing, suspense or plug line appears anywhere.

## B. Items

- [ ] Every match has one row id on each side (or a batch sharing one reference).
- [ ] Every unmatched item has a class, an owner and a next step (no UNASSIGNED left in the report).
- [ ] Timing items carry the date they cleared, or "unconfirmed". No timing item is older than the matching window unless the next statement shows it cleared or the owner explained it.
- [ ] Possible duplicates are flagged, with Exclude (not delete) recommended for the owner.
- [ ] Carried items from last period appear with their original dates and ages.
- [ ] Processor deposits are split into gross, fees, refunds and disputes.

## C. Escalation

- [ ] Unknown withdrawals, changed bank details, duplicate payments, large or repeated differences and suspected fraud were raised through bookkeeping-exception-escalation, each with an exception id.

## D. Output

- [ ] Header states entity, account label (last 4 digits only), period, currency and sources.
- [ ] Every total says "script-verified" (from rec_match.py) or "hand-computed, not script-verified".
- [ ] Every default used (window, aging buckets) is labelled "default — confirm with the owner".
- [ ] Ledger-side items are presented as drafts for the accountant.
- [ ] State written: `recs/<account>-<YYYY-MM>.json` with `approval_ref` empty until the owner signs off.
