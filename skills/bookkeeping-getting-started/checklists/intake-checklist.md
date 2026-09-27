# Intake checklist

Mirror these in `TodoWrite` for a first intake. Tick only on evidence.

## Before reading any rows
- [ ] State pre-flight run; `STATE_OK` or the "will not persist" line given
- [ ] Existing `intake.json` for this entity read (if any); memory hits treated as proposals
- [ ] `python3 --version` run; if absent, every figure below is labelled "hand-computed, not script-verified"
- [ ] Each file pulled into `/home/user/in/` with `read_workspace_file(save_to_path=...)`
- [ ] `redact.py` run on each file with account or card data; working from the masked copy

## Profile
- [ ] `profile_sources.py` run on every CSV; output saved to `profile/<YYYY-MM>.json`
- [ ] Every AMBIGUOUS_DATE_FORMAT, SIGN_CHECK, BALANCE_BREAK, UNREADABLE, NO_ROWS, RAGGED_ROWS and DUPLICATE flag turned into a question or a warning
- [ ] Each source: file, system, masked account, dates, export time, rows, currency, control total, entity confirmed
- [ ] Sources for different entities or periods kept apart; nothing merged without the owner's yes

## Intake items
- [ ] 1 Entity legal name and period; address, invoice contact and VAT number if the owner supplies them (for invoices)
- [ ] 2 Reporting currency and any other currencies
- [ ] 3 Basis as supplied, else `open`
- [ ] 4 Chart of accounts and its change owner
- [ ] 5 Sources supplied (bank, card, processor, billing, payroll, expenses, ledger)
- [ ] 6 Opening balances with evidence
- [ ] 7 Approvers: invoices, customer contact, adjustments, final reports, and the next owner if the approver is conflicted
- [ ] 8 Accountant or finance owner
- [ ] 9 System of record, connection state, owner's own export copy
- [ ] 10 Dimensions in use (class, location, job, fund, property)
- [ ] 11 Jurisdiction flags (registration, VAT or sales tax, MTD, fiscal year end)
- [ ] 12 Coding rules and short account definitions, if any
- [ ] 13 If receivables follow-up is wanted: AR account owner, the mailbox reminders go from, aging buckets (as the owner states them)

## Finish
- [ ] Blocking gaps asked in one `ask_question` call
- [ ] `intake_check.py` exit code read; BLOCKED list matches the Blocked readiness list
- [ ] Diff against the previous intake confirmed with the owner (if one exists)
- [ ] `intake.json` and `intake.md` saved to state and delivered with a `workspace://` link
- [ ] Missing-documents request prepared per document holder
- [ ] Can start now / blocked work / owner of every open item stated
- [ ] Cadence offered (optional); no routine created without a yes
