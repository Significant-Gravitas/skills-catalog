# Recurring billing: checks and an optional routine

Postings list billing on a recurring schedule as part of the job [14].
Retainers and subscriptions are billed from the contract and a schedule, and
the classic errors are a missed month, a double-billed month, or a stale rate.

## Checks for a recurring draft

- Line key = `<contract>/<line>/<service period>` (for example
  `SOW-014/retainer/2026-04`). `register_check.py` flags any key already
  billed (REPEAT).
- Compare with the previous invoice for the same line: rate, quantity,
  description, tax fields, PO number. List every change and its source (a
  signed change order, an email from the approver). No source → conflict.
- Check the contract term: start and end dates, notice given, rate review
  dates. A period outside the term is a conflict.
- A PO can expire or run out of value: if the PO value is supplied, show the
  remaining value after this invoice.

## Optional routine

Offer only after the user confirms the schedule. Show the exact wording and
time, and create it only on a yes:

```
describe_capability(id="tool:schedule_routine")
run_capability(id="tool:schedule_routine", input={
  "title": "Prepare <customer> <contract> invoice draft",
  "prompt": "Load skill:invoice-drafting-and-issue for <entity>. Prepare the <customer> <contract> invoice draft for the period just ended. Run register_check.py and stop if the line was already billed. Post the draft and review block here. Do not assign a number, create anything in the billing system, issue, send or contact anyone.",
  "crons": ["<cron at the day and time the user chose>"],
  "session_mode": "THREAD"
})
```

Scheduled runs are not interactive and the platform approval gate is off in
them, so the prompt itself forbids every external action. It is a platform
action and may be held for approval; wait for the result.
