# Tracker schema and sync

The tracker is the record and chat is not (persona). It lives at
`~/workspace/hiring/tracker/` (the durable volume; in an expert chat it is
the expert's own volume and survives across chats and routine runs).
Other Sofia skills read these files by column name, so the names are fixed.
Known gap: hiring-pipeline-analytics' `funnel.py` looks for the answer-by
date as `answer_by`/`offer_answer_by` and stage entry as
`stage_entered_on`/`in_stage_since`, not `due_by`/`stage_since`. Until it
reads these names, its "offers past answer-by" and time-in-stage figures
miss rows kept here: say so whenever those figures are quoted, and use
`stall_sweep.py` (which reads `due_by`) for overdue offers.
The first columns of each file are the original contract; the later ones are
optional additions that scripts use when present.

Contents: 1 Roles · 2 Candidates · 3 Loops · 4 Keys and merge rules ·
5 Google Sheets as the tracker · 6 What never goes in

## 1. roles.csv (one row per open req)

| Column | Meaning |
| --- | --- |
| role | Role title in the owner's wording |
| level | As the owner states it |
| hiring_manager | Name |
| target_start | ISO date |
| panel | Who interviews (names, `;`-separated) |
| stage | Req stage in the owner's wording (e.g. "sourcing", "on hold") |
| notes | Free text, owner's wording |

## 2. candidates.csv (one row per person per role)

| Column | Meaning |
| --- | --- |
| name | As the candidate gives it |
| role | Matches roles.csv `role` |
| stage | Owner's wording ("Onsite", "To schedule", "Offer out", "Rejected") |
| source | Sourced, referral, applied, agency... (keep the ATS value) |
| owner | Who moves them forward |
| last_contact | ISO date of the last message to or from the candidate |
| next_step | The single next action, with a date if there is one |
| waiting_on | A **person**, not a task |
| days_in_stage | Calendar days since `stage_since` (`merge_tracker.py refresh`) |
| notes | Owner's wording; nothing protected |
| stage_since | ISO date they entered the current stage (optional) |
| due_by | ISO answer-by or reply-by date, e.g. for an offer (optional) |
| tz | Candidate's stated IANA timezone, or blank (never guessed) (optional) |
| is_prospect | yes / no. Prospects are not applicants [86] (optional) |
| verification_step | Owner-set identity verification step and its status (optional; `fcra-and-verification.md`) |

## 3. loops.csv (one row per scheduled interview)

| Column | Meaning |
| --- | --- |
| candidate, role | As in candidates.csv |
| date | ISO date, local to `tz` |
| start, end | HH:MM, local to `tz` |
| tz | IANA zone the times are written in. Required: a time with no zone never appears |
| interviewers | Name(s) |
| coverage | The competency (kit M-id) this interview owns |
| status | invited / booked / confirmed / done / cancelled (owner's wording is fine; scripts read these words) |
| scorecards | in / out, or "2/4" |
| candidate_tz | Candidate's stated zone for the two-zone display (optional) |
| location | Room or video link (optional) |

## 4. Keys and merge rules

- Candidate rows match on name + role, loop rows on candidate + date (+ start),
  role rows on role; matching folds case, accents and spacing.
- When two copies disagree, the newer wins and you say what changed
  (`merge_tracker.py` prints every field old -> new). Candidates: the later
  `last_contact`; roles and loops: the incoming copy.
- Titles, stage names and notes stay in the owner's wording; only dates and
  times are normalised (ISO dates, 24-hour times, IANA zones).
- Never merge on a guess. Close names for the same role go to
  `tracker/needs-a-look.csv` as "possible duplicate" for the owner.
- Unparseable rows go on the needs-a-look list, never into the tracker.
- Read the tracker fresh at the start of each run; write it back at the end.

## 5. Google Sheets as the tracker

If the owner keeps the tracker in Google Sheets:

1. Start of run: `find_capability(query="google sheets read range")` →
   `describe_capability` → `run_capability` to read each tab (Roles,
   Candidates, Loops). Save each as CSV under `/home/user/coord/` and import
   with `merge_tracker.py import --list <tab> --incoming <csv>`; the local
   CSVs are the working copy.
2. End of run: show the owner the diff (rows added, fields changed). Only on
   their yes to that write: `find_capability(query="google sheets update values")`
   → `run_capability(..., validate_only=true)` → write only the changed cells.
   The gate may also ask (`approval_required`); wait and carry on with
   independent work. Never overwrite the whole sheet: it clobbers edits the
   owner made by hand.
3. Not connected: work from the CSVs and say so in one line; never wait on it.

## 6. What never goes in

Protected-characteristic columns (age or birth date, gender, race,
nationality, religion, disability, health or medical notes, genetic
information, marital or family status, criminal or arrest history, visa or
immigration status, EEO or self-ID) are dropped on import (`merge_tracker.py` prints "Dropped: ...");
tell the owner in one line. Greenhouse's Harvest v3 EEOC endpoint returns
row-level self-ID keyed by application [118], so an API-built export can
carry them even when the in-app report is anonymised [89]. Contact details
are recorded as given; never guessed, never hunted for.

Sources: [86] https://support.greenhouse.io/hc/en-us/articles/200670155-Prospects-overview ·
[89] https://support.greenhouse.io/hc/en-us/articles/204636035-Equal-Employment-Opportunity-Commission-EEOC-report ·
[118] https://harvestdocs.greenhouse.io/reference/get_v3-eeoc ·
platform behaviour (paths, Sheets via capabilities, approval gate): capabilities ground truth [114].
