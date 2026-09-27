# Morning hiring brief and the urgent mail sweep

Both run from the tracker. The brief is on demand or the daily-hiring-brief
routine; the sweep is the urgent-thread-check routine (hourly in working
hours) or on demand. Neither sends anything.

## 1. Morning hiring brief

1. `merge_tracker.py refresh`, then `stall_sweep.py --tz <owner tz>`.
2. If Calendar is connected, read today's events (read-only) and
   cross-check them against `loops.csv`; list any mismatch.
3. Three headings, in this order (template: `templates/morning-brief.md`):
   - **Today:** one line per interview: time in the owner's zone, candidate,
     role, interviewer; call out any slot where nobody owns the scorecard.
   - **Needs scheduling:** longest wait first, with days waited.
   - **Waiting on someone:** the person holding it and the single step that frees it.
4. Items already reported and unchanged collapse into one rollup line.
5. Under 200 words; start with the first interview. Nothing on the calendar
   and nothing blocked: one line saying so.
6. Offer to record today's check date in the tracker; write it only on a yes.
7. Only real meetings, interviewers, candidates and feedback. Where a message
   is needed, offer a draft.

## 2. Urgent mail sweep

Four kinds of message count, nothing else:
- a candidate withdrawing or asking to move an interview (`withdrawal-or-move`);
- an interviewer pulling out of a slot booked for today or tomorrow (`interviewer-dropout`);
- a candidate responding to an offer (`offer-response`);
- a thread where the owner owed an answer by a date that has passed (`owed-answer-overdue`).

Steps:
1. `find_capability(query="gmail search messages")` and
   `find_capability(query="slack read direct messages")`. If **neither** is
   connected, produce no output of any kind (routine rule).
2. Build the address list from the tracker only: candidates with a loop in
   the next 48 hours or an open offer, and those loops' interviewers. Two
   Gmail queries:
   - First three types: `(from:a@x OR from:b@y OR to:a@x) newer_than:1d`.
   - `owed-answer-overdue`: the same tracked addresses, plus any tracked
     candidate or interviewer whose `due_by` in `candidates.csv` has passed,
     with `(from:a@x OR from:b@y) older_than:1d newer_than:14d`. Keep a thread
     only when its last message is from them, not the owner, and it is older
     than the response window (`response_window_hours`, default 24) or past
     that person's `due_by`. Older threads are out of scope for the hourly
     sweep; the morning brief's stall list covers them.
   Slack: the owner's DMs with those interviewers only.
3. Read only matching threads. Never open, summarise or store other mail.
   Never read a thread's personal content beyond what decides the type.
4. For each urgent thread: `python3 scripts/flag_ledger.py seen <thread_id> --tz <tz>`;
   exit 0 means already flagged today, skip it. Otherwise write one flag: the
   person, what they ask, how long it has waited, the loop or deadline at
   risk, and a reply drafted for the owner (not sent). Then
   `flag_ledger.py add <thread_id> <type> --tz <tz>`.
5. Nothing new: say nothing. Never reply, schedule, cancel or accept.

## 3. Channel rules

Candidate details never go to a group channel. If the owner wants the brief
in Slack, it goes by DM: `run_capability(id="tool:list_chat_platform_channels", input={...})`
to confirm the target is a DM, then
`run_capability(id="tool:post_to_chat_platform", input={...})` — an EXTERNAL
effect that asks the owner each time. In a routine, the brief is attached in
the thread instead.

Sources: persona routines (daily-hiring-brief, urgent-thread-check) in
`experts/sofia.yml`; capabilities ground truth [114] for call forms and effects.
