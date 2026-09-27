# Inputs, files and column contracts

The hiring folder is `~/workspace/hiring/` (the durable volume; see
sofia-getting-started's references/hiring-folder.md). This skill **reads**
it and writes only to `reports/`. Column names below are fixed by the
skills that own each file; do not rename them.

| File | Owner skill | Columns this skill reads |
|---|---|---|
| tracker/candidates.csv | interview-coordination | name, role, stage, source, owner, next_step, waiting_on, days_in_stage, notes, is_prospect |
| tracker/roles.csv | interview-coordination / role-intake-and-scorecard | role, hiring_manager, stage; optional opened_on, slate_ready_on, evergreen, role_family |
| tracker/loops.csv | interview-coordination | candidate, role, date, interviewers, status, scorecards (in, out, or n/m) |
| shortlist.csv | candidate-sourcing-strategy | name, role, date_added, source_url, tier, reason |
| outreach-log.csv | passive-candidate-outreach | candidate, role, date, touch, status, reply_type |
| offers/<role>-<cand>/close-plan.csv | job-offer-and-close-plan | track, owner, due_date, status |
| preferences.md | sofia-getting-started | stalled_bar, min_sample, touch_limit, attrition_window_days, heavy_day_per_interviewer, outreach_cadence, timezone |
| reports/<date>-snapshot.json | this skill | written by snapshot_and_chart.py |

Optional columns funnel.py uses when a row carries them (usually from an ATS
export via normalize_export.py): applied_on (or sourced_on), stage_entered_on,
furthest_stage, reason, reason_type, offer_out_on, answer_by,
offer_resolved_on, accepted_on, role_family, opening_id.

Owner-supplied extras (templates/): hires.csv (early attrition),
cost-lines.csv (cost per hire; line,type,amount,currency,estimate; amount is a
plain number such as 1800 or 1800.00 - "1.800,00" or "4.200" is listed under
bad cost line and cost per hire stays UNKNOWN until fixed), hm-survey.csv, stage-map.csv (funnel_stage is one of
entered, prospect, screened, in_loop, offer, hired, rejected, withdrew,
declined_offer), export-map.csv (export_column,canonical_column for
normalize_export.py --map).

## Bringing a file in

- Upload in the workspace: `read_workspace_file(path="…", save_to_path="/home/user/pipeline/in/export.csv")`.
- Google Sheets or Drive: `find_capability("google sheets read")` (or
  "google drive download") -> `describe_capability` -> `run_capability`,
  then save the rows as CSV in the sandbox. A sign-in card means stop and
  ask the owner to connect; a paste or upload works just as well.
- ATS: only an export. Scripts never call an ATS, Google or Slack.
- Encoding and delimiter: an Excel "CSV (Comma delimited)" save on Windows
  is Windows-1252, not UTF-8, and Excel in pt-PT / de-DE writes semicolons.
  Every script reads both: a non-UTF-8 file is read as Windows-1252 with one
  "note: ... was not UTF-8" line (check accented names such as José Núñez),
  and a semicolon header is detected. Ask for "CSV UTF-8" next time.
  Regression: the same rows saved as cp1252 and as UTF-8 normalise to an
  identical candidates.csv.

## Pre-flight

`python3 --version` (3.8+). The scripts are standard library except:
matplotlib for charts and openpyxl for .xlsx in and out
(`python3 -c "import matplotlib" || pip install --user matplotlib`; same for
openpyxl). Without them the scripts skip charts and write CSV tables.
