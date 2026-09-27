# Data hygiene before any cycle-time number

Run before reporting a clock. `normalize_export.py` and `funnel.py` flag
most of these; the rest are questions for the owner. Every item gets the one
action that fixes it. Sources in references/sources.md.

## Date and record traps (from Greenhouse's data-accuracy guide [84] where cited)
- **Opening open dates** wrong or reset -> time to fill is wrong [84].
  Action: the owner confirms the open date per req.
- **Zero-day fill** [84]: a hire marked on the same day the opening was
  marked open, so Days to Hire / time to fill is 0. `funnel.py` keeps it
  out of the time-to-fill median and lists it under hygiene
  ("fill 0 days (hired the day the opening opened ...)"). Action: the
  owner corrects the opening's open date.
- **Unresolved offers** (offer out, never marked accepted or declined) ->
  acceptance rate wrong [84]. Action: resolve each in the ATS.
- **Zero-day hires** (applied and hired the same day; practitioner
  judgement, unsourced) -> a data-entry artefact. `normalize_export.py`
  flags it as zero_day_hire. Action: excluded from averages; the owner
  corrects the dates.
- **Backfilled hire dates** (entered weeks later; practitioner judgement,
  unsourced) -> clocks too long or too short. Action: check hires whose
  hire date equals the entry date.
- **Backdated entries** (practitioner judgement, unsourced) -> stage
  durations wrong. Action: note in the report; do not "correct" dates
  yourself.

## Structural traps
- **Evergreen roles** need their own opening IDs [85]; one opening with
  several hires makes time to fill per hire unreliable (labelled INFERENCE).
- **Prospects mixed into applicants** [86]: excluded by flag.
- **Merges** drop the secondary profile's source and referral credit [91];
  Workday's auto-merge is narrow, so name-variant duplicates survive [92].
  Action: list duplicates; the owner merges; re-run.
- **Lever** counts contacts and opportunities separately and stores archive
  reasons as IDs [93]: ask for the export with reason names.
- **Ashby** passthrough is a closed cohort, treats skipped stages as passed,
  and exports only as PDF [94]: ask for the application-level CSV.
- **Greenhouse Harvest v1/v2 were removed on 2026-08-31** [88]: an old
  integration or script built on them fails. Ask for a UI export or a v3
  connector.
- **LinkedIn Recruiter CSV** excludes member-entered contact data, is capped
  at 5,000 a month per seat, and Recruiter Lite cannot export CSV [97].
- **Protected columns**: the Harvest v3 EEOC endpoint returns row-level
  self-ID keyed by application [118]. Dropped on read, listed in one line to
  the owner, never used.

## Tracker traps (Sofia's own files)
- Rows missing stage or owner; duplicate name + role rows.
- Closed rows with no furthest stage (count at entry only).
- Active rows with no next step.
- Loops past with scorecards not all in.
- Outreach sequence complete (first note + `touch_limit` follow-ups) with no reply: stop.
- `touch_limit` different from the number of `outreach_cadence` days: listed
  as "outreach cadence mismatch"; a follow-up with no cadence day is listed
  for the owner, never dropped. Action: align the two in preferences.md.
- Offers past their answer-by date (offers/*/close-plan.csv).
- Ambiguous dates such as 03/04/2026: ask the owner once whether dates are
  day-first, then pass `--date-order`.
