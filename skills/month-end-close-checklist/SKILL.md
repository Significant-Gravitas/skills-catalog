---
name: "month-end-close-checklist"
description: "Run a controlled month-end review with evidence, owners, blockers, and a clear distinction between prepared and approved work. Use at period end, when the owner asks what is left to close, or when books must be made ready for the accountant. Tracks sources, reconciliations, receivables and payables, payroll tie-out, processor clearing, Undeposited Funds, Opening Balance Equity and accrual candidates in dependency order with a script, loads the bookkeeping skill that performs each control, carries open items forward, and returns a close report and review binder. Never posts, locks, backdates or approves; the owner closes the period."
triggers: ["month-end close checklist", "are we ready to close the month", "what is blocking month-end", "help me close the books this month", "month-end close status", "close last month", "period end checklist", "get the books ready for the accountant", "close calendar", "what is left to close"]
version: "2"
---

# Month-end close checklist

Use this to coordinate preparation and review. Do not mark the books closed on
the owner's behalf.

## When to use, and when not

Use once per entity and period, at period end or whenever the owner asks where
the close stands. This skill is the orchestrator: it tracks controls and loads
the skill that performs each one.

Not for: a single reconciliation (`statement-reconciliation`), a P&L question on
its own (`monthly-profit-and-loss-summary`), one odd transaction
(`bookkeeping-exception-escalation`). Never for posting, locking, filing or tax
decisions.

## Inputs and where they come from

| Input | Source | If missing |
| --- | --- | --- |
| Entity, period, cutoff, currency, basis, close owner, accountant reviewer, target review date | `intake.json`, `memory_search`, then `ask_question` | No intake: load `run_capability(id="skill:bookkeeping-getting-started", input={})` first. |
| Expected sources with covered dates and control totals | `intake.json` source list; uploads found with `run_capability(id="tool:list_workspace_files", input={"include_all_sessions": true})` | Mark the source late; never estimate it. |
| Last period's status, approvals and open items | `<state>/close/<prior>/status.csv`, `approvals.csv`, `open-items.csv`, `exceptions.csv` | First close: say so; carry nothing. |
| Close calendar and thresholds | Memory or intake | Use `references/close-calendar.md`, labelled "default — confirm with the owner". |

`<state>` is `~/workspace/bookkeeping/<entity-slug>/` (layout and pre-flight in
`references/books-state.md`). Pull files into the sandbox with
`read_workspace_file(file_id=..., save_to_path="/home/user/in/<name>")`.

## Tools and pre-flight

1. `bash_exec`: `python3 --version`. With Python 3, every status change goes
   through `scripts/close_status.py` and the report quotes its output. Without
   it, track by hand against `references/close-dependency-map.md` and label the
   report "hand-tracked, not script-verified".
2. State pre-flight from `references/books-state.md`; if it fails, say results
   will not carry to next month and deliver every file with `write_workspace_file`.
3. `memory_search(query="<entity> close calendar approvers basis materiality")`.
   Hits are proposals to confirm. When the owner states a durable rule (for
   example "close by day 7"), store it with `run_capability(id="tool:memory_store", input={...})`
   after checking its schema with `describe_capability(id="tool:memory_store")`.
   Never store amounts or account numbers in memory.

All script commands start with `cd ~/skills/month-end-close-checklist && `.

## Controls at a glance

Statuses: not started, in progress, ready for review, approved, blocked, not applicable.
Sources S1-S6: statements, sales list, bills and receipts, payroll report,
loan and owner statements, processor reports.

1. Bank and card statements reconciled.
2. Sales invoices complete through cutoff; credits and refunds recorded.
3. Bills, receipts, expenses and employee claims complete through cutoff.
4. Receivables and payables aged; disputes and stale items listed.
5. Payroll records received and tied to approved payroll reports.
6. Loans, interest, transfers, and owner or intercompany items reconciled.
7. Fixed-asset, accrual, prepayment, tax and revenue-policy work sent to the accountant.
8. P&L and balance movements reviewed against prior period and plan, if supplied.
9. Every adjustment has a source, reason, preparer and approver.
10. Processor clearing reconciled.
11. Undeposited Funds and suspense at zero or explained.
12. Opening Balance Equity zero or routed.
13. Bills not yet received checked.
14. Owner sign-off recorded on each bank reconciliation.
15. Lock date recorded as the owner states it (after the close report is approved; it does not gate "prepared for review").

Dependencies: `references/close-dependency-map.md` (enforced by the script).

## Procedure

1. **Open the close.** Set entity, period, cutoff date, reporting currency, close
   owner, accountant reviewer and target review date.
   `python3 scripts/close_status.py init --period <YYYY-MM> --out <state>/close/<YYYY-MM>/status.csv --prior <state>/close/<prior>/status.csv`.
   Mirror the controls into `TodoWrite` from `close_status.py report --status-file ... --todo`
   (one todo per control; a blocked control stays pending with its blocker in the text).
2. **Tie to last period.** The close starts only when last period's closing
   balances are approved (`python3 scripts/log_approval.py check ...` on last
   month's report), or the gap is carried as a named open item. Carry every
   `open` row of `open-items.csv` and `exceptions.csv` from earlier periods into
   this report with its original period and owner.
3. **Check sources (S1-S6).** Compare the workspace file list with the intake
   sources; record file, dates covered, rows and control total for each. A
   missing source is `blocked` with who owes it and the expected date. If the
   due date is known, offer a check-back with `ask_question` ("Check again on
   <date> whether <source> has arrived and continue the close?" Yes / No); on yes, call
   `run_capability(id="tool:schedule_followup", input={"message": "Check whether <source> for <entity> <period> has been uploaded; if so continue the close from ~/workspace/bookkeeping/<entity-slug>/close/<YYYY-MM>/status.csv. Prepare and report only; do not post, send or contact anyone.", "delay_seconds": <seconds>, "session_id": "<this chat's id from session_context>"})`
   (the session id lands the check-back in this chat with its history; without it, it starts a blank chat)
   as the **last** call of the turn (it ends the turn).
4. **Work the controls in dependency order.** `close_status.py report` lists what
   can start now. For each eligible control, when the user asks to proceed,
   load the skill named in `templates/close-controls.csv`:
   - 1, 6, 10 → `run_capability(id="skill:statement-reconciliation", input={})`
   - 3 → `skill:expense-categorization`; 4 → `skill:accounts-receivable-follow-up`
   - 7, 11, 12 and any exception → `skill:bookkeeping-exception-escalation`
   - 8 → `skill:monthly-profit-and-loss-summary`
   Load a skill only when its control is reached. Bring back only its summary
   and file links; keep details in files. What each control needs as evidence is
   in `references/controls-guide.md`.
5. **Record each change** with `close_status.py set --status-file <state>/close/<YYYY-MM>/status.csv --id <id> --status <status> --evidence "..." --owner <name>`.
   The script refuses `ready_for_review` while a dependency is open, `approved`
   unless `--approval-ref <timestamp>[;<timestamp>...] --approvals <state>/approvals.csv --artefact <file> [--artefact <file> ...]`
   points to a recorded approving reply for each named file whose logged
   SHA-256 still equals the file (control 14 needs one for every
   `<state>/recs/*-<YYYY-MM>/workpaper.md`, and it is never `ready_for_review`:
   the sign-off is approved or not), `blocked` without a blocker and
   `not_applicable` without a reason, and it reopens downstream controls if an
   input is reopened. A refusal is reported as a blocker, never worked around.
6. **Review the balance sheet items** (controls 11, 12, 13): Undeposited Funds
   and suspense at zero or explained; Opening Balance Equity zero or routed;
   bills not yet received listed as accrual candidates. Accrual candidates below
   the owner's stated threshold are listed, not proposed; with no threshold, list
   them all. Qualitative materiality applies whatever the size
   (`references/controls-guide.md`).
7. **Route judgement.** Tax, payroll, equity, impairment, revenue recognition,
   going concern, fraud, material estimates and any payroll-tax shortfall go to
   the accountant or named finance lead through the escalation skill. Never
   suggest paying other creditors ahead of payroll tax deposits.
8. **Write the close report** from `templates/close-report.md`, pasting the
   table from `close_status.py report --markdown ...`. Save it to
   `<state>/close/<YYYY-MM>/report.md` and deliver it with
   `write_workspace_file(source_path=...)` and a `workspace://` link.
9. **Approval.** Only when `close_status.py` says "prepared for review": hash
   the report (`log_approval.py hash`), ask with `ask_question` "Approve the
   <period> close report as prepared for review?" (Approve exactly as shown /
   Not yet), and record the reply verbatim with `log_approval.py record`. Only
   after that approval, ask the owner for the lock date they set in their own
   system and record it as stated (control 15). Never ask for a lock before the
   review: the accountant's adjustments land in the open period.
10. **Binder for the accountant.** First list any exception in `exceptions.csv`
    whose routing excludes the recipient (for example one sent by the
    owner-delegate path because it concerns them) and ask the owner whether to
    leave it out. Then
    `python3 scripts/build_binder.py --state-root <state> --period <YYYY-MM> [--exclude-exception BX-n ...] --out /home/user/out/<entity>-<YYYY-MM>-close-binder.zip`
    (shared registers are cut to this period's rows and still-open items),
    then `write_workspace_file`. If it refuses an unmasked number, re-run the
    skill it names for that file; never hand-edit an approved file (its hash
    approval breaks). Sending it is a separate action: ask for a yes
    that names the recipient (check it against the accountant in intake); then
    send the file as an email attachment with `find_capability("send email")`,
    `describe_capability`, `run_capability(..., validate_only=true)` and the real
    call, or hand the file to the owner to forward. A `workspace://` link cannot
    be opened by an outside accountant. `tool:post_to_chat_platform` carries text
    only: use it at most for a short notice ("April close binder is ready; Sam
    will forward it"), never for the binder's contents.
    Those external writes may also be held for platform approval; wait for the
    result and carry on with independent work meanwhile.
11. **Optional cadence.** If the owner wants a monthly kick-off, show the exact
    wording and schedule, and only after a yes check the input with
    `describe_capability(id="tool:schedule_routine")`, then call
    `run_capability(id="tool:schedule_routine", input={"title": "Month-end close kick-off", "prompt": "Load skill:month-end-close-checklist for <entity>, period = last month. State is in ~/workspace/bookkeeping/<entity-slug>/. Prepare and report only; do not post, send, lock or contact anyone.", "crons": ["<cron in the user's timezone>"], "session_mode": "THREAD", "enabled": true, "grants_credentials": false})`.
    Routine runs have no one to approve, so the prompt forbids external actions
    and `grants_credentials` is false: the routine cannot use the owner's connected accounts.

## Output contract

The close report (`templates/close-report.md`) with: period state from the
script; prior-period tie; sources with coverage and control totals and any late
source; the controls table (status, evidence or blocker, owner); control totals
per account; tasks ready for review; blockers and the critical path; material
changes (from the P&L brief); proposed adjustments as drafts; unresolved
exceptions and carried open items; checks performed and not performed; the
approval record once given. Plus links to the status file, report and binder.

## Guardrails

- Call the period `prepared for review` at most, until the named owner confirms
  approval. Preserve the owner's approval record verbatim.
- Do not choose accounting or tax policy, post entries, backdate records, lock a
  period, bypass or ask to bypass a lock, remove exceptions, or approve your own work.
- A task is not ready for review while an input it needs is missing or blocked.
  A late source delays everything after it; say so rather than working around it.
- Never estimate a missing month or reconcile to a feed instead of a statement.
- Never propose editing a locked or reconciled period; propose a current-period
  correction to the accountant.
- Never suggest ordering payments ahead of payroll tax deposits.
- Sending the report or binder needs the owner's yes naming the recipient.
- If a file or tool fails twice, stop and report the gap.

## Quality self-check

Run `checklists/close-quality.md` before sending the report.

## Files in this package

- `references/close-dependency-map.md`, `close-calendar.md`, `controls-guide.md`, `books-state.md`
- `templates/close-controls.csv` (controls, levels, dependencies, skill to load), `close-status.csv`, `close-report.md`
- `scripts/close_status.py`, `build_binder.py`, `log_approval.py` (each has `--selftest`)
- `examples/worked-example.md` (late statement, refused shortcut) and `examples/close-2026-04/status.csv`
- `checklists/close-quality.md`

## Related skills

`bookkeeping-getting-started`, `statement-reconciliation`, `expense-categorization`,
`accounts-receivable-follow-up`, `invoice-drafting-and-issue`,
`monthly-profit-and-loss-summary`, `bookkeeping-exception-escalation`.
