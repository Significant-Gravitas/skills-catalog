# First session run sheet

Tick in order. Mirror in `TodoWrite`. Stop collecting the moment there is work.

**Before saying anything**
- [ ] `memory_search("hiring preferences")` (if memory tools exist)
- [ ] `cat ~/workspace/hiring/preferences.md 2>/dev/null` and `ls ~/workspace/hiring/roles/*/scorecard.md 2>/dev/null` — if any key is set (not `UNSET`) or a role has a scorecard, this is not a first run (a skipped timezone does not make it one)
- [ ] `find_capability` x 8 (gmail, google calendar, google sheets, google drive, slack, notion, linear, granola); no `run_capability` probes

**First message (two sentences + one ask)**
- [ ] Who you are, in one sentence
- [ ] One line: Connected / Not connected
- [ ] One ask: the role (paste, link, or a title and a line about the team)

**When the role arrives**
- [ ] Load `role-intake-and-scorecard`; draft bar in chat, "draft pending calibration"
- [ ] One pass of edits
- [ ] `cd ~/skills/sofia-getting-started && bash scripts/init_hiring_folder.sh` (from `~/skills/sofia-getting-started`)
- [ ] `prefs.py set roles_open "<role title>"` (add to any roles already listed)
- [ ] One line: where the tracker lives

**Preferences (one `ask_question` at a time, each with "Skip")**
- [ ] Hiring manager and others with a say
- [ ] Timezone (skippable; required before any routine or timed output, so ask it then if skipped)
- [ ] Interview hours; brief and prep hours
- [ ] Panel and competencies; loop shape
- [ ] Stalled bar; scorecard due window
- [ ] Pipeline source; weekly batch size; outreach sender and voice sample
- [ ] Do-not-contact names -> `prefs.py dnc-add` only
- [ ] Offer approval chain; first-week owner; brief destination
- [ ] Jurisdictions; candidate AI-use policy; retention and talent-pool policy; background-check owner
- [ ] Each answer: `prefs.py set` + `memory_store` (if memory is on)

**Offers**
- [ ] Connector pick-list once, not-connected only, then "paste works equally well"
- [ ] Starter menu via `ask_question`
- [ ] `list_routines`; describe the rest; one yes per routine; timezone saved first
- [ ] Jurisdiction flag line if NYC / Illinois / California / Colorado / EU / UK

**Hand back**
- [ ] Session summary (templates/session-summary.md)
- [ ] `prefs.py dump` matches what the owner said
- [ ] Nothing sent, posted, booked or scheduled without a yes
