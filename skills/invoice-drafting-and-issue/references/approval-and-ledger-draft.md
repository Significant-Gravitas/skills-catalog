# Approval, numbering and creating a ledger draft

## Contents
1. One yes per action
2. Recording the approval
3. Creating a Draft in the billing system (optional)
4. After the owner issues or sends
5. What stays with the owner

## 1. One yes per action

Each action needs its own explicit yes that names it and the draft. Only one
of them, creating a Draft in the billing system, is ever performed by Mina:

| Action | Who performs it | Notes |
| --- | --- | --- |
| Assign invoice number | owner or billing system | Mina may suggest the next number from `register_check.py`; the suggestion is not an assignment. Mina never passes a number of her own. Some systems (Xero for sales invoices) assign the next number automatically when a draft is created without one (Xero Accounting API spec, ACCREC InvoiceNumber: "when missing will auto-generate from your Organisation Invoice Settings"; github.com/XeroAPI/Xero-OpenAPI, xero_accounting.yaml, read 2026-09-27); Mina records whatever number the owner or the system assigns |
| Create the invoice as a Draft in the billing system | Mina, only after a recorded yes that names this action | Status must stay Draft (see 3) |
| Approve / authorise / finalise in the billing system | owner | In Xero, approving an invoice posts it to the ledger and afterwards it can only be voided [103] |
| Send to the customer | owner | This skill never sends. Payment reminders for issued invoices are drafted by accounts-receivable-follow-up under its own approval rule |

A yes for one action never implies another. An edit to the draft after a yes
voids that yes (the hash no longer matches).

## 2. Recording the approval

1. Render the draft (`render_invoice.py`) and hash it:
   `cd ~/skills/invoice-drafting-and-issue && python3 scripts/log_approval.py hash /home/user/out/draft-<id>.html`.
2. Ask with `ask_question` (see `templates/approval-questions.md`). The question
   names the draft id, the total and the exact action, and says that the
   billing system may assign the next invoice number to the draft. Run
   section 3 steps 1-2 (find and describe) first, and offer the "create it in
   <system> as a Draft" option only when a tool that can create with status
   Draft is present.
3. Record the answer:
   `cd ~/skills/invoice-drafting-and-issue && python3 scripts/log_approval.py record --artefact ... --shown-sha <hash> --action "create draft <id> in <system> with status Draft" --approver "<name as the user stated>" --option "<label exactly as picked>" --log <state>/approvals.csv`
   (`--reply "<verbatim>"` for a typed answer). Only the "create it in
   <system> as a Draft" option, or a typed reply that itself names creating
   it in the same system ("yes, create it in Xero"), is recorded; a bare
   typed yes is refused for a create action (it could mean "I will issue it
   myself"), and so is every other answer, and nothing is done (see
   `templates/approval-questions.md`).
4. Before acting:
   `cd ~/skills/invoice-drafting-and-issue && python3 scripts/log_approval.py verify --artefact ... --action "..." --log <state>/approvals.csv`
   must print "approved by …".

This owner approval is the business control. The platform may also hold an
external call for its own approval (`approval_required`); that is separate
and does not replace step 3.

## 3. Creating a Draft in the billing system (optional)

Only when `log_approval.py verify` passes for "create draft in <system>":

1. `find_capability(query="<system> create invoice")`.
2. `describe_capability(id=...)`. Find the status field. Proceed only if the
   tool can create with status Draft (Xero `DRAFT`; QuickBooks and Stripe draft
   equivalents as the schema shows). If the status defaults to authorised,
   approved, open or sent, or cannot be set, stop and give the owner the PDF
   and the figures to enter instead.
3. `run_capability(id=..., input={... status Draft ...}, validate_only=true)`.
4. `run_capability(id=..., input={...})`. If it returns `approval_required`,
   wait for the held result; if it returns `review_required` (legacy review),
   resume with `resume_capability(review_id=...)` only after the owner confirms.
5. Record the returned id in `invoice-register.csv` (`status=draft_in_ledger`,
   `ledger_id=<id>`) and, if the response carries an invoice number the system
   assigned, put it in `number` and tell the owner: "Xero gave this draft
   number <n>" (it may differ from the suggestion). If no number came back,
   leave `number` blank.
6. Never call authorise, approve, finalise, void or send endpoints.

A sign-in card means stop and ask the user to connect; the fallback is the PDF
or HTML plus owner entry. Which billing integrations exist in a workspace is not
known in advance.

## 4. After the owner issues or sends

Record what the owner says was issued, when and by whom, in
`invoice-register.csv` (`status=issued_per_owner`, `issued_on`, `issued_by`,
`evidence` = the owner's message or a billing export row). Do not claim the
invoice exists outside the draft until a supplied record proves it. A later
billing export wins over the register.

## 5. What stays with the owner

Pricing and terms; the invoice number; issuing; sending (unless separately
approved); any credit note, void or write-off; tax treatment (with the
accountant).
