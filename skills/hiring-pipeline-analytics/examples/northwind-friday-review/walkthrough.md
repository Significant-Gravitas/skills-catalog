# Worked example: Northwind's Friday pipeline review (fictional)

Friday 9 Oct 2026, 16:00 Europe/Lisbon: the `weekly-pipeline-review`
routine fires. Two open roles. Files in this folder mirror
`~/workspace/hiring/`: tracker/ (Sofia's standard headers, no entry dates),
shortlist.csv, outreach-log.csv, preferences.md, stage-map.csv, and
prior-week/candidates.csv (last Friday's tracker). expected/ holds the real
script output for this data.

## 1. Last week's snapshot (already on disk in a live run)

Last Friday's run left `reports/2026-10-02-snapshot.json`. To reproduce it:

```
cd ~/skills/hiring-pipeline-analytics
python3 scripts/funnel.py --tracker examples/northwind-friday-review/prior-week \
  --roles examples/northwind-friday-review/tracker/roles.csv \
  --prefs examples/northwind-friday-review/preferences.md --today 2026-10-02 --out /home/user/pipeline/2026-10-02
python3 scripts/snapshot_and_chart.py /home/user/pipeline/2026-10-02/report.json --reports /home/user/pipeline/reports --no-charts
```

## 2. This week's run

```
cd ~/skills/hiring-pipeline-analytics
H=~/workspace/hiring
python3 scripts/funnel.py --tracker $H/tracker --shortlist $H/shortlist.csv \
  --outreach $H/outreach-log.csv --prefs $H/preferences.md --stage-map $H/stage-map.csv \
  --history $H/reports --offers $H/offers \
  --window 2026-10-03:2026-10-09 --today 2026-10-09 --out /home/user/pipeline/2026-10-09
python3 scripts/snapshot_and_chart.py /home/user/pipeline/2026-10-09/report.json --reports $H/reports
```

The first run stopped on "Portfolio review", a stage the defaults do not
know; Sofia asked the owner once ("Is Portfolio review a screen?") and
saved stage-map.csv. Banners in expected/report.md:

- no entry dates in the tracker -> the funnel covers all rows; the prior
  column is last Friday's snapshot;
- SMALL SAMPLE: 16 people, below 30.

expected/diff.md gives movement (6 stage changes), 7 new names (one a
prospect), 3 new stalls and one ROLLUP (Maya Chen, stalled since first
reported 2 Oct).

## 3. The review the owner reads (from the outputs; under 300 words)

> **Week to 9 Oct vs the 2 Oct snapshot. n=16, below 30: directional.**
>
> **Product Designer (5 in pipeline)**
> - Movement: Tariq Aziz screen -> rejected ("portfolio lacks research work").
> - Stalled: Leo Brandt, screen, 11 days, waiting on Ana (new). ROLLUP:
>   Maya Chen sourced, 8 days, stalled since 2 Oct; follow-up (touch 4,
>   the last in the sequence) was due 30 Sep, 7 working days late - draft
>   ready via outreach; if there is no reply after it, stop.
>
> **Senior Backend Engineer (11)**
> - Movement: Priya onsite -> offer; Tom screen -> onsite; Lucas and Nora
>   rejected; Paulo withdrew ("declined on location").
> - New sourcing: 4 added. First three by the tier sourcing recorded: Ines
>   Duarte (tier 1, invoice-reconciliation talk), Clara Voss (tier 1,
>   idempotent billing jobs), Hugo Lam (tier 2, payments retry library) -
>   links in the report. One more had no link and is not a card.
> - Stalled: Aisha, screen, 7 days (waiting on us - book the loop); Tom,
>   onsite, 6 days, Lena's scorecard missing (2 of 3 in).
> - Follow-up due today: Mia Keller, touch 3 (draft ready via outreach).
>
> **Look ahead:** Tue 13 Oct: Dev 2 interviews, Ana, Joana, Sam 1 each;
> Thu 15 Oct: Lena 1 - no day over 3. **Decisions:** Lena files Tom's scorecard before the debrief;
> Ana books Leo or releases him.
>
> **No movement:** none. **Scorecard signal** [INFERENCE: all 3 backend
> rejections cite "no billing evidence"; the 4th closure was a withdrawal
> on location]: the billing must-have is where most people fall out; worth
> Lena's look. Her call.
>
> Hygiene: Eva Novak has no owner and no furthest stage - assign one.

The funnel, the rollup and the heavy-day check all come from the script
output; no number was typed by hand. The two follow-ups use
passive-candidate-outreach's rule (first note + 3 follow-ups on business
days 2, 5 and 8), so this list matches that skill's `followups_due.py` for
the same log. For each one Sofia loads that skill with
`run_capability(id="tool:read_skill", input={"name": "passive-candidate-outreach"})`
and drafts the follow-up there, unsent, linked in the review.

## 4. Save and deliver

- report.md, diff.md, funnel.png and tables are in
  /home/user/pipeline/2026-10-09/; the review is saved to
  `~/workspace/hiring/reports/2026-10-09-weekly-review.md` and pushed with
  `write_workspace_file(source_path=...)`, linked as `workspace://…`.
- The routine does not post or email. The owner later says "post it to
  #hiring": Sofia runs

```
cd ~/skills/hiring-pipeline-analytics && \
python3 scripts/share_safe.py /home/user/pipeline/2026-10-09/report.json \
  --names $H/tracker/candidates.csv --names $H/shortlist.csv --names $H/outreach-log.csv
```

  The share copy is built from report.json: funnel tables, conversions,
  stalled counts by stage, hygiene counts and next week's load by
  interviewer, with no per-candidate line. The residue check still refuses
  (exit 1): "Ana" remains in the load line - Ana Costa, the design hiring
  manager, shares a first name with candidate Ana Ruiz. Sofia checks the
  hit, reruns with `--allow Ana`, and gets expected/report-share.md
  ("role-level summary, no candidate details"). Then
  `run_capability(id="tool:list_chat_platform_channels", input={})`
  confirms #hiring, and
  `run_capability(id="tool:post_to_chat_platform", input={...})` goes to the
  gate, which asks the owner. While it is held, Sofia finishes the
  follow-up drafts.
