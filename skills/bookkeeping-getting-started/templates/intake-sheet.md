# Bookkeeping intake: {{entity.legal_name}}, {{period.start}} to {{period.end}}

DRAFT for owner review. Prepared {{prepared_on}}. Figures come from
`profile_sources.py` unless marked "hand-computed, not script-verified".

## Entity and period

| Item | Value | Source or status |
| --- | --- | --- |
| Legal name | {{entity.legal_name}} | |
| Address and invoice contact | {{entity.address}}; {{entity.contact}} | as supplied by the owner; used on invoices |
| Jurisdiction | {{entity.jurisdiction}} | |
| Fiscal year end | {{entity.fiscal_year_end}} | |
| Period | {{period.start}} to {{period.end}} | |
| Reporting currency | {{reporting_currency}} | other currencies: {{other_currencies}} |
| Accounting basis | {{basis}} | `open` = not supplied; not chosen by Mina |
| Chart of accounts | {{chart.source}} ({{chart.version}}) | changes owned by {{chart.owner}} |
| Coding rules / account definitions | {{coding_rules.source}} | |
| Dimensions in use | {{dimensions}} | class, location, job, fund or property; only if supplied |
| VAT / sales tax registration | {{entity.vat_or_sales_tax_registered}}; number {{entity.vat_number}} | recorded as supplied, not decided or looked up |
| MTD for Income Tax (UK sole traders) | {{entity.mtd_income_tax_status}} | |
| System of record | {{system_of_record.name}}, {{system_of_record.connection}} | owner holds export copy: {{system_of_record.owner_holds_export_copy}} |

## Sources

| Source | System / account | Dates | Export time | Rows | Currency | Control total | State |
| --- | --- | --- | --- | --- | --- | --- | --- |
| {{file}} | {{system}} {{account}} | {{from}} to {{to}} | {{export_time}} | {{rows}} | {{currency}} | {{control_total}} | Ready / Usable with a warning: … / Blocked: … |

Masked before reading: {{masked_fields}}.

## Opening balances

| Account | Value | Evidence | Approved by |
| --- | --- | --- | --- |

## Approvers

| Decision | Approver (as stated by the owner) |
| --- | --- |
| Invoices | {{approvers.invoices}} |
| Customer contact | {{approvers.customer_contact}} |
| Adjustments | {{approvers.adjustments}} |
| Final reports | {{approvers.final_reports}} |
| If the approver is the subject of a concern | {{approvers.next_owner_if_approver_conflicted}} |
| Tax, policy, material exceptions | {{accountant}} |

## Receivables (only if the owner uses AR follow-up)

| Item | Value (as supplied by the owner) |
| --- | --- |
| AR account owner | {{ar.account_owner}} |
| Mailbox reminders are sent from | {{ar.mailbox}} |
| Aging buckets confirmed | {{ar.aging_buckets_confirmed}} |

## Readiness

**Ready:** …
**Usable with a warning:** …
**Blocked:** … (question asked: Q#)

## Next

- Can start now: …
- Blocked work and who unblocks it: …
- Open questions: Q# … (owner)
