# Next review and standing review (optional)

Both only on the user's yes to the exact wording and time shown. Check the
input shape first with `describe_capability`. Both are platform actions and may
be held for approval; wait for the result.

## One follow-up for the next review date

`schedule_followup` ends the current turn, so call it last, after everything
else in this run is delivered:

```
run_capability(id="tool:schedule_followup", input={
  "message": "AR review for <entity>: check the invoices due for their next stage per contact-log.csv (next_review on or before today). Prepare drafts only; do not send or contact anyone.",
  "delay_seconds": <seconds until the next review date at the time the user chose>,
  "session_id": "<this session>"
})
```

## Weekly standing review

```
run_capability(id="tool:schedule_routine", input={
  "title": "Weekly AR review: <entity>",
  "prompt": "Load skill:accounts-receivable-follow-up for <entity> (state folder ~/workspace/bookkeeping/<entity-slug>/). Say the date of the newest invoice, payment and bank exports first; if they are older than the last run, stop and ask for new exports. Update the aging, run find_unapplied.py, and draft next-stage reminders for approval. Do not send, call, or contact anyone, and do not change any invoice.",
  "crons": ["<cron for the weekday and time the user picked>"],
  "session_mode": "THREAD"
})
```

Scheduled runs are not interactive and the platform approval gate is off in
them, so the prompt itself forbids sending. A stale export would repeat old
findings; the prompt makes the run report export dates first.
