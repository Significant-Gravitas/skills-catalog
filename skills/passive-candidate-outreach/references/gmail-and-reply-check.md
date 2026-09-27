# Gmail drafts and reply checks

How this skill touches Gmail, and only this way. Gmail is reached through
platform capabilities; scripts never see a Google token (only GitHub tokens
exist in the sandbox). Tool ids are never hard-coded: resolve them each time.

## A. Put approved drafts in the owner's Gmail (optional)

Only after the owner has approved the text of a specific message, and only
if Gmail is connected. A copyable draft in chat is always the default.

1. `find_capability(query="gmail create draft")`. Read the connected state.
   Not connected: do not call anything (a call would surface a sign-in card);
   say "Gmail isn't connected, so the drafts are here to copy" and stop.
2. Pick a tool whose **name or description says draft**. If the only match
   sends mail, do not use it; fall back to copyable drafts and say why.
3. `describe_capability(id=...)` to read the input schema.
4. `run_capability(id=..., input={to, subject, body}, validate_only=true)`.
5. The real call, one per approved message: `run_capability(id=..., input=...)`.
6. Read each result:
   - success: count it.
   - `approval_required` (the platform gate holds the write): tell the owner
     the draft is waiting on their approval card; keep working on anything
     independent; do not retry.
   - `review_required` (legacy review): wait for the owner, then
     `resume_capability(review_id)`.
   - error: report it; the chat copy is still the draft.
7. Say "N drafts are in your Gmail, none sent" **only** for calls that returned
   success. Never say "sent". The log row stays `drafted` until the owner says
   they sent it.

## B. Check for replies before drafting any follow-up (optional)

A "no" that arrived but was never logged would get a follow-up, which is
the most damaging outreach failure. When Gmail is connected, check first:

1. `find_capability(query="gmail search messages")` (read-only; READ effect,
   so it runs without asking).
2. For each log row with status `sent`: search only by that person's
   published address and the send date, e.g.
   `from:<route> after:<YYYY/MM/DD of touch 1>`. Never search broader; never
   open unrelated threads; never summarise non-hiring mail.
3. For each reply found, show the owner: who, date, a one-line quote of the
   job-relevant part, and a proposed `reply_type` (positive / not-now /
   not-interested / do-not-contact).
4. Log it with `scripts/log_touch.py update ...` (or `dnc`) **only after the
   owner confirms** the classification. Never reply from here.

LinkedIn InMail replies are not visible to this skill; ask the owner to paste
them, and remember LinkedIn counts "Not interested" as a response [96].

## C. Approval behaviour, stated once

- The owner's explicit yes to a specific message is required before anything
  leaves as more than chat text (persona boundary). Creating a Gmail draft is
  a write: on top of the owner's yes, the platform gate may ask again
  (`approval_required`). That is expected; wait for it.
- In a scheduled or unattended run (no owner in the chat), never call a
  write tool at all: drafts stay in chat and in the log as `drafted`.
- Nothing is sent from this skill, ever. There is no send step.

Sources: capabilities ground truth [114] (tool call forms, approval gate,
sandbox credentials); LinkedIn InMail policy [96]
(https://www.linkedin.com/help/recruiter/answer/a413279).
