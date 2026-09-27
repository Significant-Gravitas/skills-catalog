# Batch run sheet

**Load**
- [ ] `cat` scorecard (status, version, M-ids, B-ids, boundaries) and target-companies.csv; status not `approved` -> "bar uncalibrated (status: <status>)" on every card and the header
- [ ] `cat` preferences (batch size, timezone, retention_policy)
- [ ] Shortlist, pipeline, dnc present? (if not, ask who is in play)
- [ ] `mkdir -p /home/user/sourcing`

**Target**
- [ ] Names wanted (on demand: asked-for or weekly_batch_size; routine run: weekly_batch_size / runs per week, rounded up; UNSET: 10 per run), reply-rate goal (default 20% / 30 days), channel owners: confirmed or flagged as defaults

**Warm**
- [ ] Near-misses in the window (default 12-18 months) AND inside retention_policy (ask once if UNSET; unattended run with UNSET: skip them all, state the count, ask next chat)

**Search**
- [ ] 3+ variants per searched must-have incl. dark matter; cap 15 per batch
- [ ] Every query logged (`append_rows.py search`)
- [ ] Engineering: `gh auth status`; connect_integration if needed; GitHub commands
- [ ] Clusters > 1: up to 3 Task sub-agents with the subtask prompt; tier and reason every returned (`unranked`) card before batch.json
- [ ] No protected or health/family terms in any query; no postcode filters
- [ ] Blocked sites named; export requested

**Gate**
- [ ] Every evidence URL fetched; links.csv filled one row per person per URL (name, status, name_found); a URL on two cards has two rows
- [ ] `dedupe_names.py` -> kept.json; check-these listed; DNC count only; `files_missing` empty (else named in the header; unattended with DNC missing: hold the batch)
- [ ] `card_check.py` -> ready.json (off-limits companies too); drops explained; thin cards labelled "thin, 1 line"
- [ ] Every card in ready.json read against the guardrails (the script is a backstop)

**Show**
- [ ] First cards early; tiers with evidence reasons; five at a time, strongest first
- [ ] Short batch says short and why
- [ ] Three passes with one reason -> propose the scorecard change

**Save (on a yes)**
- [ ] `append_rows.py shortlist --approved ...`
- [ ] Batch file delivered via write_workspace_file
- [ ] Nothing sent to anyone; picks handed to passive-candidate-outreach
