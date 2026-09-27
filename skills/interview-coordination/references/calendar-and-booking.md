# Calendar reads, holds and invites

Google Calendar has no "draft invite". Creating an event with the candidate
or panel as attendees sends real invitations. So this skill reads freely,
and writes only after the owner's yes to that exact booking.

## 1. Read availability (no approval needed; READ effect)

1. `find_capability(query="google calendar free busy")` (or "google calendar
   list events"). Read the connected state from the result. Not connected:
   use pasted availability and say the options rest on it.
2. `describe_capability(id=...)` for the input shape.
3. `run_capability(id=..., input={...})` for each panelist's calendar over the
   candidate's window. Convert each busy span to the `busy` list in
   `templates/availability-example.json` (ISO with offset, or with `tz`).
4. Never read event titles or attendees beyond busy/free; never open
   unrelated events.

## 2. Build options

`cd ~/skills/interview-coordination && python3 scripts/tz_slots.py /home/user/coord/availability.json`.
Present its options verbatim, strongest first, each with its one compromise.

## 3. After the owner picks an option

Ask exactly what they want written (one `ask_question`):
- "Put attendee-less holds on my calendar" (titled `HOLD: <candidate> · <slot>`;
  no one is notified);
- "Create the events and invite the panel";
- "Create the events and invite the panel and the candidate";
- "Just give me the table".

Then, only for the chosen action:
1. `find_capability(query="google calendar create event")` → `describe_capability`.
2. `run_capability(id=..., input={...}, validate_only=true)`.
3. Describe the effect in one line before the call ("this sends 3
   invitations"), then call it once per event.
4. `approval_required`: the gate is holding it; tell the owner, continue with
   independent work (drafting the candidate email), do not retry.
5. Report what exists only after success. Update `loops.csv` rows to
   `status=booked` (holds: `status=hold`) and write the tracker back.

Some calendar tools notify attendees on update too: treat any change to an
event with attendees (moving, cancelling) as sending, with its own yes.

## 4. Moves and drop-outs

If an interviewer drops out or the loop moves, the competency still needs
covering: name a substitute who can take it (the kit's slot, not a random
free person), or tell the owner the slot has no owner yet. Rebuild options
with `tz_slots.py` (add `alternates` for the dropped slot). Cancelling or
moving an event is its own yes.

## 5. Unattended runs

In a routine (no owner in the chat), never call a calendar write. Read only.

Sources: capabilities ground truth [114] (capability call forms, gate
effects); practitioner judgement (unsourced) for the hold convention.
