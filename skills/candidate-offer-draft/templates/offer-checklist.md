# Internal offer approval checklist: <candidate id>, <role>

Internal only; never sent to the candidate. Generated from `terms.json`
after `check_terms.py` passes. Status: DRAFT.
Saved: `~/workspace/hiring/<role-slug>/offers/<candidate-id>/offer-checklist.md`

| Term | Value | Source | Approver | Approved on |
|---|---|---|---|---|
| Legal entity | <value> | <source> | <name> | <date> |
| Title / level | | | | |
| Manager | | | | |
| Location and work terms | | | | |
| Start date | | | | |
| Base pay, currency, period | | | | |
| Bonus wording | `[OWNER TO CONFIRM]` | - | - | - |
| Equity wording | | | | |
| Benefits source | | | | |
| Contingencies (template order) | | offer template section <n> | | |
| Response-by date | | | | |
| Signatory | | | | |

## Checks

- `check_terms.py`: <0 errors / list>. Warnings: <list>.
- Pay basis: approved band and approver only. No current or past pay was
  asked for, recorded or used, even though <"the candidate volunteered it" / n/a> [56][75].
- Contingencies copied from the template, in the template's order.
- Background check: standalone disclosure and authorisation on record before
  the report is procured? <yes, date / NOT ON RECORD: owner to confirm> [48].
  (US hires. Hiring jurisdiction: <jurisdiction>. Outside the US: the local
  notice/consent step, confirmed by the people lead; no US FCRA wording.)
- Medical exam or inquiry: <none / post-offer only, and for every entrant in the job category> [46].
- Template clauses unchanged; only `{{placeholders}}` filled (`fill_offer_template.py` report attached).
- Email figures and dates match the letter (`check_terms.py --email --letter`).

## Open items (block sending)

- <term>: `[OWNER TO CONFIRM]`, owner <name>

## Reviews required before anything is sent

- [ ] Authorised people lead: <name>
- [ ] Counsel, if the company requires it: <name / not required per owner>
- [ ] Signatory: <name>

Nothing has been sent, signed, negotiated or recorded as accepted.
