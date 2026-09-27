# Connectors: how to check them and how to offer them

## Check without probing

Run `find_capability(query="<name>")` for each of these, one call each:
"gmail", "google calendar", "google sheets", "google drive", "slack",
"notion", "linear", "granola". Read the connected state on the top result
only if its name matches what you asked for; a vague query can rank another
server first. Never call `run_capability` to test a connection: an
unconnected integration answers with a sign-in card, and the persona never
waits on a connection [114].

Report in one line: `Connected: ... Not connected: ...`.

Integrations are reached only through `find_capability` ->
`describe_capability` -> `run_capability(validate_only=true)` -> the real call.
Scripts in the sandbox cannot reach Gmail, Calendar, Sheets, Drive, Slack,
Notion, Linear or Granola; only GitHub has a token in the sandbox [114].

## The pick-list (offer once, not-connected ones only)

One short reason each, then move on:

- **Gmail**: read candidate threads and leave every message as an unsent draft
  in their own account.
- **Google Calendar**: see real interviewer availability and stage holds
  without booking them.
- **Google Sheets**: keep the tracker in a sheet they can edit themselves.
- **Google Drive**: resumes, postings, packets, and offer files.
- **Slack**: post a brief or interviewer nudge once they have approved it, in
  the channel the team already reads. Posting to chat always asks first.
- **Notion**: the tracker, scorecards, and debrief write-ups sit where the
  hiring team looks.
- **Linear**: file a task when a req is approved, a take-home needs reviewing,
  or a new hire starts.
- **Granola**: bring interview notes and action items in from the meeting
  itself.
- **Anything else** (their applicant tracker): an export pasted or uploaded.
- **GitHub** (for engineering roles): lets sourcing read public code evidence
  through the sandbox `gh` CLI; `candidate-sourcing-strategy` asks for it when
  it needs it.

Then say plainly that pasting, uploading, or sharing a link works equally
well, and start without waiting.

## Which skill uses what

So the pick-list is not a promise nobody keeps:

| Connector | Used by (in this kit) |
|---|---|
| Granola | `role-intake-and-scorecard` reads the intake call the owner confirms; debrief notes are read by the debrief skill |
| Linear | `role-intake-and-scorecard` files "Req approved: <role>" on a yes; the other uses belong to the skills that own those steps |
| Google Drive | `role-intake-and-scorecard` and `job-description-drafting` read old postings and call notes |
| Sheets, Calendar, Gmail, Slack, Notion | `interview-coordination`, the routines, and the brief destinations |
| GitHub | `candidate-sourcing-strategy` evidence for engineering roles |

Every write through a connector is gated by the platform: it asks or is judged
by its own effect. Keep working on independent steps while a call is held.
