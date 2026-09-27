# The hiring folder

Source for the storage facts: the platform capabilities audit [114].
Full citations: [sources.md](sources.md).

## Why `~/workspace/hiring/`

- `bash_exec` and the sandbox file tools start in `/home/user`. Scratch there
  survives turns in a session but is lost when the chat is deleted or expires.
- `~/workspace` (`/home/user/workspace`) is the durable volume: in an expert
  chat it is the expert's own volume and it survives box death, so it is shared
  by Sofia's chats, delegations and routine runs, including the FRESH ones
  (daily candidate batch, evening prep) that start with no conversation [114].
- `write_workspace_file` defaults to a session-scoped path
  (`/sessions/<id>/...`). Use it to **deliver a copy** the owner can open,
  linked as `workspace://<file_id>#<mime>`; never treat that copy as the record.
- **Unverified:** whether the owner can browse `~/workspace` in the UI. That is
  why deliverables are also pushed with `write_workspace_file(source_path=...)`.

## Layout (created by `scripts/init_hiring_folder.sh`)

```
~/workspace/hiring/
  preferences.md            one "key: value" per line (scripts/prefs.py)
  dnc.csv                   name,flag  (do-not-contact: name and flag only)
  shortlist.csv             sourced people, one row each (candidate-sourcing-strategy)
  searches.csv              search log: every query run (candidate-sourcing-strategy)
  outreach-log.csv          every touch (passive-candidate-outreach)
  tracker/roles.csv         fixed columns (interview-coordination owns them)
  tracker/candidates.csv
  tracker/loops.csv
  roles/<role-slug>/        scorecard.md, target-companies.csv, posting-v<N>.md ...
  packets/  debriefs/  offers/  reports/  flags/  screens/
```

Column headers are in `templates/tracker-headers/`. They match the names the
other Sofia skills read; do not rename a column.

## Rules

1. Re-read the file before a run; write it back after. The tracker is the
   record, chat is not.
2. Create files only if absent. The init script never overwrites.
3. No protected characteristic, photo, salary history or health detail is
   ever written to any file here.
4. Removal requests are handled by `interview-coordination` across every file
   in this folder, in the same reply.
5. Retention: US hiring records are kept at least one year, and all relevant
   records once a charge is filed [44]; UK guidance is no longer than the
   claim period, with notice before keeping a talent pool [100]. Never purge
   on your own; confirm with counsel.
