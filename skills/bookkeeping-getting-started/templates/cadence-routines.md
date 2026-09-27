# Optional standing cadence

Offer this only at the end of intake, and create a routine only after the user
says yes to the exact wording and times shown. Check the input shape first
with `describe_capability(id="tool:schedule_routine")`, then call
`run_capability(id="tool:schedule_routine", input={...})`. It is a platform
action, so it may be held for approval; wait for the result.

Scheduled runs are not interactive, so the platform approval gate does not
apply in them. The routine prompt itself must forbid every external action.

## Monthly close kick-off

- Title: `Month-end prep: {{entity.legal_name}}`
- When: the business day and time the user picks. The target is a close within
  5 to 10 business days after month-end, as one CPA practice guide describes
  [66]; the exact day is the owner's choice.
- Session mode: `THREAD` (keeps the conversation for context)
- Prompt:

> Load skill:month-end-close-checklist for {{entity.legal_name}}
> (state folder ~/workspace/bookkeeping/{{entity.slug}}/), period = last
> calendar month. Report the export dates you found first. Prepare and report
> only: do not post entries, issue or send invoices, contact anyone, or move
> money. List what is blocked and who owns each item.

## Weekly receivables review

- Title: `Weekly AR review: {{entity.legal_name}}`
- When: the weekday and time the user picks.
- Session mode: `THREAD`
- Prompt:

> Load skill:accounts-receivable-follow-up for {{entity.legal_name}}. Use the
> newest invoice and bank exports and say their dates first. Update the aging,
> check for unapplied payments, and draft next-stage reminders for approval.
> Do not send, call or contact anyone.

Record created routines in `intake.json.cadence.routines_created`.
