# Bringing in scorecards and panel notes

Scorecards come from files first; notes from Granola, Gmail or Slack are
optional extras and are always marked **unfiled**. Integrations are reached
only through capabilities; scripts never see a Google, Slack or Granola token.
Never hard-code tool ids.

## 1. Scorecards

| Where they are | How to bring them in |
| --- | --- |
| Filed in the hiring folder | Already at `~/workspace/hiring/debriefs/<role-slug>/<candidate-slug>/scorecards/` |
| Uploaded by the owner | `read_workspace_file(file_id=..., save_to_path="/home/user/workspace/hiring/debriefs/<role-slug>/<candidate-slug>/scorecards/<interviewer-slug>.md")` |
| ATS export (CSV) | Save it, pass it to `collate_scorecards.py --scorecards <file.csv>` |
| Pasted in chat or mailed | Write it in `templates/scorecard-format.md` shape, quoting the interviewer's words exactly; mark `filed_at` from the message time; never fill a missing rating |
| Google Doc or Sheet | `find_capability("google drive read file")` or `("google sheets read range")` → `run_capability` (read-only), save the export, snapshot it |

Then `snapshot_scorecards.py` at roll-call.

## 2. Granola meeting notes (optional)

1. `find_capability(query="granola meeting notes")`. Not connected: skip,
   say so in one line.
2. Read only the loop's meetings, matched on the loop date and the
   candidate's name (from `loops.csv`).
3. Keep only job-related statements by panelists, quoted, each marked
   `[FACT, unfiled, meeting notes <date>]`. Never infer tone, confidence,
   nerves or honesty; never count notes as a scorecard; never store the
   transcript itself.

## 3. Gmail or Slack (optional)

- Gmail: `find_capability("gmail search messages")` → `run_capability`
  (read-only) with a query limited to the panel's addresses and the
  candidate's name after the loop date.
- Slack: `find_capability("slack search messages")` → `run_capability`
  (read-only), limited to DMs or threads with panelists that name the candidate.
- Same rules as notes: quoted, unfiled, job-related only; everything else is
  left unread. Candidate details are never posted back to a channel.

## 4. Delivering the brief

- Owner copy: `write_workspace_file(filename="<date>-<candidate-slug>-brief.md", source_path=...)`
  and link it.
- To the panel, only on the owner's yes to that send: a Gmail draft per
  panelist via a draft tool, or a Slack DM (`run_capability(id="tool:post_to_chat_platform", ...)`
  after confirming with `run_capability(id="tool:list_chat_platform_channels", ...)` that it
  is a DM; the gate asks). Never a group channel. In an unattended run, no
  write calls.

Source: capabilities ground truth [114] (call forms, sandbox credentials, approval gate).
