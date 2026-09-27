# Preference questions, keys and options

Ask one at a time with `ask_question` (one question, options where shown, and
always a "Skip" option). Never as a form. Store with
`cd ~/skills/sofia-getting-started && python3 scripts/prefs.py set <key> "<value>"`. Order below is the suggested
order after the first artefact is on screen; drop any question whose answer is
already on file or already visible from a connected tool.

`roles_open` is not a question: it is set from the role the owner hands over
(step 5 of the skill, once the folder exists), `prefs.py set roles_open "<role title>"`, with further
roles added to the comma-separated list. A skipped timezone is asked again
only when a routine or a timed output needs it.

Numbers shown as options are **defaults — confirm with the owner**; none is a
benchmark.

| # | Question | Key | Options offered |
|---|---|---|---|
| 1 | Who is the hiring manager for this role, and who else has a say? | `hiring_manager.<role-slug>` | free text |
| 2 | What timezone should I work in? | `timezone` (IANA city zone, e.g. `Europe/Lisbon`; "EST"/"PST" become `America/New_York`/`America/Los_Angeles`, since `prefs.py` refuses fixed-offset zones that ignore daylight saving) | the zone implied by their calendar if connected, "Skip" |
| 3 | When can interviews be booked? | `interview_hours` (e.g. `10:00-17:00 Mon-Thu`) | free text |
| 4 | What time should the morning hiring brief land? | `morning_brief_hour` (HH:MM) | "08:00", "09:00", "Skip" |
| 5 | What time should evening prep packets land? | `evening_prep_hour` (HH:MM) | "17:00", "18:00", "Skip" |
| 6 | Who normally sits on the panel for this role, and which competency does each cover? | `panel.<role-slug>` | free text |
| 7 | What does a typical loop look like: how many slots, how long each? | `loop_shape.<role-slug>` | free text |
| 8 | When should I call something stalled? | `stalled_bar` | "2 business days", "3 business days", "5 business days", "Skip" |
| 9 | How long do interviewers have to file a scorecard? | `scorecard_due_hours` | "24", "48", "Skip" (existing Sofia default 24/48 h; confirm) |
| 10 | Where are candidates tracked now? | `pipeline_source` | "ATS export", "Google Sheet", "Email", "Nowhere yet", "Skip" |
| 11 | How many freshly sourced names a week can you actually use? | `weekly_batch_size` | "10", "25", "50", "Skip" (the daily routine uses 10 per run unless set) |
| 12 | Who sends outreach, and can you paste a sample of their writing? | `outreach_sender`, `outreach_voice_sample_ref` | free text; store the sample as a file under `roles/` or paste reference, not in memory |
| 13 | Anyone who must never be contacted? | `dnc.csv` via `prefs.py dnc-add` | free text; name only |
| 14 | Who signs off an offer, in order? | `offer_approval_chain` | free text |
| 15 | Who owns a new hire's first week? | `first_week_owner` | free text |
| 16 | Where should briefs and packets go? | `brief_destination` | "Here in chat", "A Slack channel", "A Notion page", "Skip" |
| 17 | Where will this role be posted or based (state, city, country)? | `hiring_jurisdictions` | free text |
| 18 | Do you have a policy on candidates' use of AI in applications and interviews? | `candidate_ai_policy` | "Allowed to draft, not in live interviews", "Not allowed", "No policy yet", "Skip" [104] |
| 19 | How long do you keep records of people who were not hired, and are candidates told you may contact them later? | `retention_policy` | free text [100] |
| 20 | Who runs background checks, and through which process? | `background_check_owner` | free text (routes FCRA-type declines later) |
| 21 | Which Linear team should approved reqs go to? (only if Linear is connected) | `linear_team` | the team names Linear returns, "Skip" |

Why 17-20 exist: posting-law fields depend on the location [56][57]; the
AI-use line in postings reads `candidate_ai_policy` [104]; re-engaging past
candidates depends on the retention and notice policy [100]; a decline that
rests on a background check must go through the owner's adverse-action
process, not a plain decline [48][76].

Full citations: [sources.md](sources.md).
