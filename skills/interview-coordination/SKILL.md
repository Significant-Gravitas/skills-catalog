---
name: "interview-coordination"
description: "Books, rebuilds and moves interview loops with complete options in both timezones, drafts candidate and interviewer messages, keeps the hiring tracker (roles, candidates, loops) as the record, and sweeps it for stalls grouped by who holds each item. Use when an interview loop has to be booked, rebuilt, or moved, when a candidate or interviewer needs a message, or when the hiring tracker needs updating or checking for stalls. Also runs the morning hiring brief, the daytime sweep of candidate and interviewer mail for anything threatening a booked loop, and removes a candidate from the hiring records on request."
triggers: ["schedule this interview loop", "reschedule the interview", "who is stuck in the hiring pipeline", "update the candidate tracker", "draft a note to the interviewer", "candidate availability windows", "what is stalled in hiring", "an interviewer dropped a slot", "morning hiring brief", "remove this candidate from our records"]
version: "2"
---

# Interview coordination

Run this when a loop must be booked, rebuilt or moved; when a candidate or
interviewer needs a message; when the owner asks what is stuck or wants the
morning brief; when they hand over roles and candidates to keep track of; or
when they ask to remove a candidate.

**Do not use for:** designing the loop's questions and scorecards
(interview-kit-design), running the debrief (hiring-debrief-and-decision),
offers (job-offer-and-close-plan), first outreach to sourced people
(passive-candidate-outreach), funnel metrics (hiring-pipeline-analytics).

## Inputs and where they come from

| Input | Source |
| --- | --- |
| Tracker (roles, candidates, loops) | `~/workspace/hiring/tracker/*.csv` (`references/tracker-schema.md`); or Google Sheets read via capabilities; or any one source to start or rebuild it: a pasted list, an ATS export, a spreadsheet or CSV file, a shared-sheet link, forwarded candidate emails |
| Role, stage, panel, competency per interviewer | Tracker and `~/workspace/hiring/roles/<role-slug>/kit.md` |
| Candidate availability and timezone | The candidate (via the owner); never guessed from a city |
| Interviewer constraints, calendars | Connected Google Calendar (read-only free/busy) or pasted availability |
| Owner timezone, stalled bar, response window, holidays | `~/workspace/hiring/preferences.md` (`timezone`, `stalled_bar`, `stall.<item>`, `response_window_hours`); else `memory_search("hiring preferences")`; else one `ask_question` |

## Pre-flight

Every `python3 scripts/...` command in this skill runs as `cd ~/skills/interview-coordination && python3 scripts/...`: `bash_exec` starts in `/home/user`, not the package folder.

1. `bash_exec`: `cd ~/skills/interview-coordination && python3 --version && python3 -c "import zoneinfo; zoneinfo.ZoneInfo('Europe/Lisbon')" || python3 -m pip install --user tzdata`.
2. `python3 scripts/merge_tracker.py init` (creates `~/workspace/hiring/` and
   header-only tracker files if absent; idempotent). Not writable: say the
   tracker won't carry to the next chat and deliver it with `write_workspace_file`.
3. No Python: do the arithmetic by hand, show it, and label it "not script-checked".
4. Mirror `checklists/booking-and-sweep.md` in `TodoWrite` for a booking.

## Procedure

### A. Keep the tracker (every run)

Read it fresh at the start; write it back at the end. The tracker outranks
anything said in chat. Import any new source with
`python3 scripts/merge_tracker.py import --list <candidates|roles|loops> --incoming <file> --dry-run`,
read what it dropped and flagged, then run it for real
(`references/ats-import-notes.md`). Column names are fixed; other skills read
them. Titles, stage names and notes stay in the owner's wording; only dates
and times get normalised. Candidate rows match on name plus role, loop rows
on candidate plus date; when two copies disagree, the newer wins and you say
what changed. Unparseable rows go on the needs-a-look list. Prospects stay
flagged as prospects. Protected-characteristic columns are dropped on import;
tell the owner in one line.

### B. Book, rebuild or move a loop

1. **Confirm the loop shape before looking for time:** the number of slots,
   their lengths, what each covers, and where the breathing room goes
   (default for a four-slot onsite: 10 minutes between interviews plus a
   proper break near the midpoint — confirm with the owner). Every window
   carries two labelled times, the candidate's and the owner's; a time with
   no zone never appears.
2. **Read availability** (read-only) per `references/calendar-and-booking.md`
   and write `/home/user/coord/availability.json` in the
   `templates/availability-example.json` shape.
3. **Offer two or three complete loop options:**
   `python3 scripts/tz_slots.py /home/user/coord/availability.json`. Show them
   strongest first, verbatim: the date, every slot in both timezones, who
   interviews in each, and the one compromise it makes (a tight turnaround or
   a stand-in). No fit: report the binding constraint it names and ask for
   wider windows, a stand-in or a split loop.
4. **Once the owner picks,** hand over three things at once: holds (a
   copyable table, or calendar holds / invites only on the owner's yes to
   that exact write, per `references/calendar-and-booking.md`); a brief email
   to the candidate covering times, what each conversation is about, and the
   whole process in one line (every stage, who they meet, when a decision
   comes; set this map at the screen stage and keep to it); and a note per
   interviewer with their slot and competency (`templates/messages.md`).
   Update `loops.csv`.
5. **Drop-outs and moves:** the competency still needs covering. Name a
   substitute who can take it (from the kit), rerun `tz_slots.py` with
   `alternates`, or tell the owner the slot has no owner yet.

### C. Write messages

Three to five sentences: lead with the answer or the request, state the next
step, give a reply date. Shapes in `templates/messages.md`: scheduling,
nudge, decline, offer follow-up, keep-warm, holding update.
- **Decline:** first ask whether a background check or consumer report played
  any part. Yes or not sure: draft nothing and route to the owner's FCRA
  process (`references/fcra-and-verification.md`). Otherwise brief and plain,
  no made-up reason, feedback only when the owner hands you real feedback.
  Late-stage declines happen by phone, so draft talking points instead.
- Default response promise: candidates hear back within 24 hours at every
  stage, 48 at most, unless the owner has set their own. If the owner has
  shown you how they write, sound like them. Times come from the tracker or
  the owner, never from you.

### D. Flag what is stalled / morning brief

`python3 scripts/merge_tracker.py refresh`, then
`python3 scripts/stall_sweep.py --tz <owner tz> [--holidays <file>]`.
Default thresholds (`templates/stall-thresholds.csv`), unless the owner set
their own:

| What | Stalled once |
|---|---|
| Candidate awaiting feedback after an interview | 2 business days |
| Scorecard not filed after the slot | 1 day |
| Offer still open | past its answer-by date |
| Scheduling request with no loop booked | 2 business days |
| Candidate with no reply | 3 touches |
| Interviewer invite not accepted | inside 24 hours of the loop |
| Decline not drafted after the decision | 48 hours |
| Any thread with no update sent | 3 business days |
| Candidate past the promised response window with no update drafted | at the window (24 h; 48 at most) |

Group by whoever holds each item, oldest first, one line each with the single
action that frees it, plus a drafted nudge. Items the script lists under
"Unchanged since an earlier brief" collapse into one rollup line; they are
not re-raised or re-nudged. An item the script marks
`SECOND STALL` gets escalated: who holds it, the days it has cost, and what
that does to the loop. The same read powers the morning hiring brief
(`templates/morning-brief.md`; today's interviews with each slot's
interviewer, who still needs scheduling by longest wait, and who each open
item waits on) and the mail sweep for anything that endangers a booked loop
(`references/brief-and-mail-sweep.md`; flags and drafts, never replies; one
flag per thread per day via `scripts/flag_ledger.py`).

### E. Remove a candidate (on the owner's request, same reply)

Do it immediately, without asking why:
1. `python3 scripts/forget_candidate.py --name "<full name>" [--role "<role>"] --dry-run`,
   then the same without `--dry-run`. If the dry run shows the name under two
   roles and the owner named one, ask which person first. When the request
   comes from the candidate, or is a do-not-contact request, add `--keep-dnc`
   (the name and the flag are all that is kept, so no later batch re-sources
   them). An existing do-not-contact row is always kept; `--drop-dnc` lifts it
   only on the owner's explicit order. A file listed as "skipped" is another
   candidate's scorecard filed by someone with the same name: leave it and
   tell the owner. Before applying, read the dry-run file list for any other
   person's name (a longer name that starts the same, a colleague); if one is
   there, stop and ask. "Check with owner" lines are mentions left untouched
   (another CSV column, or an interviewer context): name them to the owner.
2. Memory on: find facts with `memory_search("<name>")` and remove each with
   the memory-forget tool (`find_capability("memory forget")`, then
   `run_capability(id="tool:<that tool>", ...)`).
3. Delivered copies: `run_capability(id="tool:list_workspace_files", input={"include_all_sessions": true})`,
   then `run_capability(id="tool:delete_workspace_file", ...)` per file (irreversible; the gate may ask).
4. Report what was removed, what remains outside your reach (ATS, mailbox,
   calendar), and one line: record-retention rules can require keeping some
   hiring records; confirm with counsel if a claim is possible.

## Output contract

- Booking: ranked loop options; then the holds, candidate email and panel
  notes once one is picked, ready to copy or sitting unsent (Gmail drafts only
  via a draft tool, on a yes).
- Tracker: written back, with rows added and updated counted, the
  needs-a-look list, and today's snapshot in the same reply; saved as
  `~/workspace/hiring/tracker/{roles,candidates,loops}.csv`, delivered with
  `write_workspace_file(source_path=...)` when the owner wants a copy.
- Stalls / brief: grouped by holder, oldest first, one action each, nudges drafted.
- Every time with its zone; every figure from a script or labelled hand-computed.

## Guardrails

- Booking, inviting, cancelling, sending and declining each wait for the
  owner to approve that one action. Calendar events with attendees send real
  invitations: never add attendees without that exact yes. In an unattended
  routine run, make no external write at all (no Gmail, Calendar, Slack,
  Sheets or ATS change); saving to `~/workspace` (tracker, flag ledger,
  stall history) and attaching a file with `write_workspace_file` are
  allowed and expected.
- Candidate details stay out of group channels; a Slack delivery is a DM,
  verified as a DM first, and `post_to_chat_platform` asks the owner.
- Leave any protected-characteristic column (age or birth date, gender, race,
  nationality, religion, disability, marital or family status, EEO or
  self-ID) out of the tracker and every export, and tell the owner in one line.
- Contact details are recorded as given; never guess an email or phone
  number, and never go hunting for one.
- Identity verification is an owner-set step for every candidate at a stage;
  never infer fraud, or single anyone out, from a name, accent, nationality,
  location or photo.
- A decline that a background check touched goes to the owner's FCRA
  process; no plain decline is drafted.
- The mail sweep reads only threads with known candidate and interviewer
  addresses, never replies, and never summarises unrelated mail.
- Employment-law questions go to the owner's attorney with a one-line brief.

## Quality self-check

- [ ] Tracker read fresh and written back; counts and needs-a-look reported.
- [ ] Every time has a zone; options came from `tz_slots.py` (or are labelled hand-computed).
- [ ] Every slot in a booked loop has an interviewer and a competency, or the gap is named.
- [ ] No write happened without the owner's yes to that exact action; nothing was sent.
- [ ] Stall list grouped by holder with one action each; second stalls escalated.
- [ ] No protected column, no guessed contact detail, no candidate data in a group channel.

## Fallbacks

Only pasted availability to go on: use it and tell the owner that is what the
options rest on. No list of any kind yet: ask them to type five sample rows
and start the tracker from those. Calendar or Gmail not connected: say so in
one line and carry on from pastes; never wait on a connection. An XLSX or PDF
export: ask for CSV.

## Related skills

Load with `run_capability(id="skill:<slug>", input={})`:
interview-kit-design (slots, competencies, packets), hiring-debrief-and-decision
(scorecards, decisions; a no comes back here for the decline draft),
job-offer-and-close-plan (a yes), passive-candidate-outreach (outreach log),
hiring-pipeline-analytics (reads the same tracker), sofia-getting-started
(preferences and routines).

## Package files

- `scripts/tz_slots.py`, `merge_tracker.py`, `stall_sweep.py`,
  `flag_ledger.py`, `forget_candidate.py` (each has `--selftest`)
- `references/tracker-schema.md`, `ats-import-notes.md`,
  `calendar-and-booking.md`, `brief-and-mail-sweep.md`, `fcra-and-verification.md`
- `templates/tracker-headers/{roles,candidates,loops}.csv`,
  `stall-thresholds.csv`, `availability-example.json`, `messages.md`, `morning-brief.md`
- `checklists/booking-and-sweep.md`
- `examples/stall-sweep/` (tracker fixture, sweep and brief, end to end),
  `examples/rebuild-hard-case/` (drop-out across a DST change, FCRA decline,
  a location-based ID-check request refused, a removal request)

## Example

> **Example (fictional stall sweep, Thursday 8 Oct, times Europe/Lisbon).**
>
> **Waiting on Lena Ortiz (hiring manager)**
> - Priya Nair, Senior Backend: loop ended Mon 5 Oct; Lena's scorecard not
>   filed (3 days; bar is 1). Frees it: Lena files. Nudge drafted.
>
> **Waiting on Dev Rao**
> - Invite for Tom Becker, Fri 9 Oct 14:00 Lisbon / 15:00 Berlin, not
>   accepted inside 24 hours of the loop. Frees it: Dev accepts or names a
>   substitute for the billing-debugging slot. Nudge drafted.
>
> **Waiting on us**
> - Aisha Bello: asked for times on 2 Oct, no loop booked (4 business days).
>   Frees it: the owner picks one of two loop options (sent
>   in the same reply, both timezones on every slot).
>
> Nudge draft to Lena (not sent): "Lena, your scorecard for Priya Nair
> (Monday's close) is still open. The debrief is Friday 11:00; could you
> file by 17:00 today so it's in before anyone talks?"
>
> Tracker: 0 rows added, 3 updated (days in stage); needs-a-look: none.
