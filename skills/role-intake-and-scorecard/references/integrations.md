# Integrations used by intake

All integrations go through the platform: `find_capability` ->
`describe_capability` -> `run_capability(validate_only=true)` -> the real call.
Never hard-code a tool id; resolve it each time. An unconnected integration
returns a sign-in card: stop that branch, ask for a paste instead, and keep
going [114]. Scripts in the sandbox cannot reach any of these.

## Granola (intake call notes) — read

1. `find_capability(query="granola meeting notes")`; use the top result only if
   it is Granola.
2. List meetings from the last 14 days (default — confirm with the owner) whose
   title or attendees match the role or the HM's name.
3. Show the owner the matches (title, time with timezone) and read only the one
   they confirm.
4. Quote job-related sentences as FACT with "(<meeting title>, <date time zone>)".
   Never store the transcript in the hiring folder; never quote remarks about
   anyone's personal life.

## Google Drive (old posting, call notes) — read

`find_capability(query="google drive search files")` -> search by role title ->
read the file the owner confirms. For an uploaded file, use
`read_workspace_file(file_id, save_to_path="/home/user/in/<name>")`.

## Linear (req approved) — write, on a yes

Only after the HM's approval is stamped and the owner says yes to this issue.

1. `prefs`: read `linear_team` from `~/workspace/hiring/preferences.md`. If
   `UNSET`, ask once which team, then store it with the getting-started
   `prefs.py` if that skill is loaded, or tell the owner it will be asked again.
2. `find_capability(query="linear create issue")` -> `describe_capability` ->
   `run_capability(..., validate_only=true)`.
3. Create one issue: title "Req approved: <role>", body with the scorecard
   version, the HM, and the delivered scorecard link. Role-level facts only;
   no candidate names, no pay.
4. The write is gated (`approval_required` or `review_required`). Keep working
   while it is held; `resume_capability(review_id)` only for `review_required`.

## Web research (target companies)

- `web_search(query, max_results<=20)` quick mode. `deep=true` only when the
  owner asks for a market study (about 100x the cost) [114].
- `web_fetch(url)` to confirm each company site: public URLs only, 100 KB cap,
  15 s timeout [114].
