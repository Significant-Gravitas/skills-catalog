---
name: "hiring-pipeline-analytics"
description: "Use when the user asks how hiring is going, wants funnel numbers per role, or needs a hiring report for the team. Also the pass behind the Friday weekly pipeline review routine: funnel and conversion, time to hire and time to fill, stalls, source of hire, offer acceptance, cost per hire, and data hygiene from the tracker or an ATS export."
triggers: ["how is hiring going", "hiring funnel numbers", "time to hire report", "recruiting metrics for the team", "which stage loses candidates", "offer acceptance rate", "hiring pipeline review", "are our reqs aging", "weekly hiring pipeline review", "friday hiring review"]
version: "2"
---

# Hiring pipeline analytics

Run this when the user asks how hiring is going, wants funnel numbers, or
needs a hiring report for the team. It is also the pass behind the Friday
`weekly-pipeline-review` routine and any on-demand weekly review. Package
files are at `~/skills/hiring-pipeline-analytics/`.

**Not for:** the daily stall sweep and nudges (interview-coordination),
sourcing or ranking new names (candidate-sourcing-strategy), follow-up
drafts (passive-candidate-outreach), offer status for one finalist
(job-offer-and-close-plan). **Never** adverse-impact or any rate by a
protected group: that is HR or counsel's work on aggregated self-ID data.

## Inputs and where they come from

| Input | Source | If missing |
|---|---|---|
| Tracker (roles, candidates, loops) | `~/workspace/hiring/tracker/*.csv` (interview-coordination's columns) | Use what exists; ask for the one export that fills the gap |
| ATS export | Upload -> `read_workspace_file(..., save_to_path="/home/user/pipeline/in/export.csv")`; Sheets/Drive via `find_capability` -> `run_capability` | Tracker only |
| Shortlist, outreach log, close plans | `~/workspace/hiring/shortlist.csv`, `outreach-log.csv`, `offers/*/close-plan.csv` | Those sections read "none" |
| Window and prior window | The user; routine = the week to today | Default: last 7 days vs the 7 before - name it up front |
| Stalled bar, min sample, touch limit, attrition window | `~/workspace/hiring/preferences.md`; else `memory_search("hiring preferences")` | Script defaults, each printed as "default - confirm with the owner" |
| Hires with start/leave dates, cost lines, HM survey | The owner (templates/) | That metric is UNKNOWN |

Column contracts: references/inputs-and-files.md.

## Procedure

Mirror the steps in `TodoWrite`. Pre-flight: `python3 --version`; charts
need `python3 -c "import matplotlib" || pip install --user matplotlib`
(skipped cleanly if unavailable).

1. **Name the window** and the comparison (prior window or previous
   snapshot), never vibes. Re-read the files fresh; the tracker outranks chat.
2. **Normalise any export first:**
   `cd ~/skills/hiring-pipeline-analytics && python3 scripts/normalize_export.py <export> --out /home/user/pipeline/in --vendor <greenhouse|lever|ashby|workday|linkedin>`.
   Tell the owner in one line which protected columns were dropped. A PDF
   (Ashby passthrough) is refused: ask for the application CSV.
   Unmapped columns or stages, ambiguous dates: ask once
   (`ask_question`), then `--map`, `--stage-map`, `--date-order`. Never guess.
3. **Hygiene before any clock** (references/data-hygiene-checklist.md):
   state which clock the source uses; zero-day hires, evergreen openings,
   unresolved offers and duplicates are listed, not averaged (funnel.py counts
   a duplicate name + role once, at its furthest stage, until the owner merges).
4. **Compute everything with the script:**
   `cd ~/skills/hiring-pipeline-analytics && python3 scripts/funnel.py --tracker ~/workspace/hiring/tracker [--candidates /home/user/pipeline/in/candidates.csv] --shortlist … --outreach … --offers ~/workspace/hiring/offers --prefs ~/workspace/hiring/preferences.md --history ~/workspace/hiring/reports --window A:B --out /home/user/pipeline/<date>`
   (add `--hires`, `--costs`, `--hm-survey` when supplied). Every FACT
   number comes from report.json/report.md; you type no number by hand.
5. **Snapshot and diff:**
   `cd ~/skills/hiring-pipeline-analytics && python3 scripts/snapshot_and_chart.py /home/user/pipeline/<date>/report.json --reports ~/workspace/hiring/reports`.
   Its diff gives movement, new names, cleared stalls and ROLLUP lines for
   stalls already reported; on the first Friday of the month it adds the
   time-to-hire trend by role family and offer acceptance over the
   previous calendar month.
6. **Read it for the user** (templates/funnel-read.md; the routine uses
   templates/weekly-pipeline-review.md):
   - Funnel: counts per role and stage, conversion, the stage losing the
     most people with the top two reasons in plain words.
   - Pacing: time to hire and time to fill, labelled separately
     (references/metric-definitions.md); time to slate; days in stage; roles
     with no movement and the age of each open req; the oldest five stuck
     with owner and days.
   - Quality and mix: source mix, source of hire, offer acceptance, decline
     reasons split "we rejected" vs "they withdrew", early attrition
     (default 90 days - confirm) with exit notes, cost per hire only with
     the owner's cost lines (references/cost-per-hire.md), HM satisfaction
     only from their survey.
   - Weekly review extras: new sourcing per role with the first three in
     the tier order candidate-sourcing-strategy recorded (this skill does
     not re-rank), follow-ups due on passive-candidate-outreach's cadence
     (report.md lists them; for each one load that skill with
     `run_capability(id="tool:read_skill", input={"name": "passive-candidate-outreach"})`
     and draft it there, unsent, then link the draft), roles with no
     movement, and whether pass
     reasons suggest the scorecard should change (INFERENCE, the hiring
     manager's call).
   - Hygiene: every item with the one action that fixes it.
   - Close on the calls that need a human, a line apiece, and next week's
     interview load by day with any day too heavy for the panel.
7. **Decompose every move:** what changed, by how much, and the driver.
   FACT (from a named file), INFERENCE (arithmetic and assumptions shown),
   or UNKNOWN (missing, never estimated silently). Below the minimum sample
   (default 30 - confirm), say the sample is small and read it as directional.
8. **Save and deliver:** save the read to
   `~/workspace/hiring/reports/<date>-<pipeline-read|weekly-review>.md`, push
   report.md, funnel.png (trend.png monthly) and the tables with
   `write_workspace_file(source_path=...)`, and link them as `workspace://`.

## Output contract

- The funnel read in chat, under 300 words unless the full table was asked
  for, with the window, the comparison basis and any SMALL SAMPLE banner
  first.
- Files: report.md (internal; names candidates), report.json, diff.md,
  report-share.md only when a share was asked for,
  funnel.png, tables, and the dated snapshot in `~/workspace/hiring/reports/`.
- Every number labelled; defaults shown as defaults.

## Guardrails

- Post to a channel or mail the team only when asked for that specific
  send. Shared copies carry role-level numbers only and no per-candidate
  line: build them from report.json with
  `cd ~/skills/hiring-pipeline-analytics && python3 scripts/share_safe.py /home/user/pipeline/<date>/report.json --names ~/workspace/hiring/tracker/candidates.csv --names ~/workspace/hiring/shortlist.csv --names ~/workspace/hiring/outreach-log.csv`;
  never share report.md or a hand-edited copy of it. Exit 1 means
  `--allow` a checked interviewer name or leave the line out, never skip.
  Then `run_capability(id="tool:list_chat_platform_channels", input={})`
  and `run_capability(id="tool:post_to_chat_platform", input={...})`; the
  gate asks, so keep working while it is held. Email = a Gmail draft, never
  a send. The routine itself never posts or emails.
- Never compute or display any rate, count or ratio by gender, race,
  ethnicity, age, disability, veteran status or any protected group, and
  never infer demographics. Protected columns are dropped on read.
- Never invent a stage change, a number, a reason or a commitment; a gap
  stays UNKNOWN. Never call a cost "comparable" without the owner's lines.
- Candidate details stay out of anything shared; snapshots hold names and
  fall under delete-on-request with the rest of the hiring folder.

## Fallbacks

Thin or stale tracker: report what is there, name the gaps, ask for the one
export that fills them. No entry dates: all-rows view against the previous
snapshot (the report says so). No snapshot yet: the first run says movement
starts next week. Python unavailable: count by hand from the files, show
the arithmetic, label every rate INFERENCE, and say the script check is
pending.

## Quality self-check

Run checklists/run-and-share.md. At minimum: every number traces to
report.json; the view (cohort or all-rows) and the clocks are named; the
small-sample banner is carried; no protected-group figure; every hygiene
item has one fixing action; nothing was sent.

## Examples and references

- examples/northwind-friday-review/walkthrough.md - the Friday routine end
  to end from Sofia's tracker, with the share step (expected/ holds real
  output).
- examples/greenhouse-export-hard-case/walkthrough.md - self-ID columns, a
  gender-breakdown request, zero-day hire, evergreen opening, duplicates,
  ambiguous dates, cost per hire.
- references/: metric-definitions.md, data-hygiene-checklist.md,
  cost-per-hire.md, inputs-and-files.md, protected-columns.txt, sources.md.

Siblings in this kit: interview-coordination (tracker and stall sweep),
candidate-sourcing-strategy (shortlist and tiers), passive-candidate-outreach
(follow-up drafts), job-offer-and-close-plan (close plans and answer-by
dates), sofia-getting-started (preferences and routines).
