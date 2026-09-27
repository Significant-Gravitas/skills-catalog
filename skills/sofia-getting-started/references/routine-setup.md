# Standing rhythms: what each one is and how to switch it on

The five routines are defined in Sofia's persona (crons, asks, session mode).
This file does not change them. It only says how to offer each one and switch
it on after an explicit yes. Nothing goes on a schedule unasked, and none of
them sends anything.

## Before offering

1. `run_capability(id="tool:list_routines", input={})`. Leave out any routine
   already on. **Unverified:** whether persona routines exist in a disabled
   state or are created on first yes; listing first covers both [114].
2. The timezone must be saved (`prefs.py get timezone`). If it is `UNSET`, ask
   for it first; a routine without a zone fires at the wrong hour.

## The five

| Routine key | Plain-language offer | Persona cron (owner's zone) | Session | Needs | Preference keys it reads |
|---|---|---|---|---|---|
| `daily-hiring-brief` | A morning brief: today's interviews, who is waiting for a slot, who is holding what up | `H 8 * * 1-5` | THREAD | tracker; calendar if connected | `timezone`, `morning_brief_hour`, `brief_destination` |
| `daily-candidate-batch` | A fresh sourced batch each weekday, deduped against the pipeline | `H 9 * * 1-5` | FRESH | an approved or draft scorecard; `shortlist.csv` | `timezone`, `weekly_batch_size` |
| `evening-interview-prep` | Prep packets the evening before interviews | `H 18 * * 1-5` | FRESH | `tracker/loops.csv`; calendar if connected | `timezone`, `evening_prep_hour` |
| `urgent-thread-check` | A daytime watch for candidate or interviewer mail that puts a booked loop at risk; flags and drafts, never replies | `H 9-17 * * 1-5` | THREAD | Gmail or Slack connected (otherwise it outputs nothing) | `timezone` |
| `weekly-pipeline-review` | A Friday review per open role | `H 16 * * 5` | THREAD | tracker, shortlist, outreach log | `timezone`, `stalled_bar` |

`H` in the persona crons means the platform picks the minute. If the owner
gave a preferred hour (`morning_brief_hour`, `evening_prep_hour`), use that
hour instead of the persona default and say so.

Each persona routine carries two asks; the second is always "What time should
this land, and in which timezone?". Answer them from `preferences.md` and ask
only what is still `UNSET`.

## Switching one on (after "yes" to that routine by name)

1. `describe_capability(id="tool:schedule_routine")` to read the input shape.
2. `run_capability(id="tool:schedule_routine", input={...})` with the
   routine's key or title, its prompt as defined in the persona, the cron in
   the owner's timezone, and the session mode above. If `list_routines`
   showed it exists but is off, enable that one instead of creating a second.
3. If the call returns `approval_required`, tell the owner it is waiting on
   their approval and continue the onboarding.
4. Confirm back in one line: "Morning brief: weekdays 08:00 Europe/Lisbon,
   posts here. Switch it off any time."
5. Record it: `cd ~/skills/sofia-getting-started && python3 scripts/prefs.py set routines_on "<comma list>"`.

## Never

- Never bundle ("I've set up all five"). One yes, one routine.
- Never schedule a routine that posts to a channel without the owner naming
  the channel; posting to chat is an external action and asks each time.
- Never create a duplicate: always list first.
