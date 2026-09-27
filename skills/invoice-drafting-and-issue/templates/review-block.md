# Review block: {{draft_id}}

**DRAFT, not issued.** Customer {{customer}} · {{currency}} {{total}} {{("before tax" if no tax)}} · approver {{approver}}

| Check | Result | Script / source |
| --- | --- | --- |
| Totals recalculated | subtotal …, discount …, tax …, total …; rounding: … | invoice_totals.py |
| Required fields ({{regime}}) | BLOCKS APPROVAL: … / BLOCKS ISSUE: … | field_check.py, references/invoice-field-checklists.md |
| Every line and term sourced | yes / gaps: … | field_check.py |
| Double billing | no repeat / REPEAT <line key> as <number> | register_check.py |
| Numbering | next number suggestion … (not assigned); gaps …; export wins | register_check.py |
| Recurring change vs previous invoice | none / … | previous invoice <number> |
| Customer VAT/tax ID | valid / invalid / unchecked (source, date) | references/tax-id-checks.md |
| Contract comparison | differences: … | contract clause refs |

**Missing fields:** … (each with who supplies it)
**Term or source conflicts:** … (each with both sources)
**Routed to the accountant:** tax treatment, credit note, cross-border, withholding, revenue policy (if any)
**Draft document:** workspace://… (HTML or PDF, watermarked DRAFT)

**Awaiting approval (exact action):** one of
- "Approve draft <draft_id> for the owner to number, issue and send"
- "Create draft <draft_id> in <system> with status Draft" (the only action Mina performs, after a recorded yes)
or: "None of assign, create, issue or send can happen until <blockers> are settled."
