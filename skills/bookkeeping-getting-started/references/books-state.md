# Books state: where the bookkeeping kit keeps its working files

The same file ships in every bookkeeping package (packages cannot share files).
It describes the working index that lets month N+1 start from month N.

## Contents
1. Where state lives and the pre-flight
2. Layout
3. Rules
4. Inputs and outputs (getting files in and out)
5. Memory (optional)
6. Files used by reconciliation, close, P&L and escalation

## 1. Where state lives and the pre-flight

State root: `~/workspace/bookkeeping/<entity-slug>/` on the durable sandbox
volume. In an expert chat this is the expert's own volume; in a plain chat it is
the user's. `/home/user` scratch is lost when the chat expires; `~/workspace` is not.

Pre-flight, once per run:

```
bash_exec: mkdir -p ~/workspace/bookkeeping/<entity-slug> && test -w ~/workspace/bookkeeping/<entity-slug> && echo STATE_OK
```

If `STATE_OK` does not print (the volume did not mount), say so in one line:
"State will not carry to the next chat; I will deliver every file to you
instead." Then deliver everything with `write_workspace_file` and continue.

Never reuse a folder for a different entity. If two entities would get similar
slugs, ask which folder is which before writing.

## 2. Layout

| Path (under the entity folder) | Written by | Columns / content |
| --- | --- | --- |
| `intake.json`, `intake.md` | bookkeeping-getting-started | see `templates/intake.json` in that package |
| `profile/<YYYY-MM>.json` | bookkeeping-getting-started | output of `profile_sources.py` |
| `coding-rules.csv` | expense-categorization | pattern, account, dimension, rule_source, approved_by, approved_on, status |
| `expenses/<YYYY-MM>-review.csv` | expense-categorization | the review table (see that package's template) |
| `invoice-register.csv` | invoice-drafting-and-issue | number, customer, contract_ref, line_key, amount, currency, status, issued_on, issued_by, ledger_id, evidence |
| `invoices/<draft-id>/` | invoice-drafting-and-issue | draft.json, draft.html or draft.pdf, review.md |
| `ar/<YYYY-MM-DD>-aging.csv` | accounts-receivable-follow-up | aging output |
| `contact-log.csv`, `dispute-log.csv` | accounts-receivable-follow-up | see that package's templates |
| `open-items.csv` | any kit skill | id, origin_skill, period, account, amount, currency, owner, next_step, opened_on, status, closed_by_record |
| `approvals.csv` | any skill with an approval step | timestamp, artefact_path, artefact_sha256, action, approver_as_stated, verbatim_reply |

Other kit skills (statement-reconciliation, month-end-close-checklist,
monthly-profit-and-loss-summary, bookkeeping-exception-escalation) may add
their own folders; leave files you did not write alone.

## 3. Rules

- State is a working index, never the source record for an amount. Every row
  cites a source file and row, or a system record id.
- A newer source always wins over state. Before using a state file, check it
  against the current export's control totals; if they disagree, report the
  difference and use the source.
- Nothing is deleted. Rows change status (`open` → `closed`, `draft` →
  `issued_per_owner`) and keep their history.
- Store masked account numbers only (last 4). No card numbers, full account
  numbers, passwords or tax IDs beyond what an invoice legally shows.
- Entity folders never mix. A file for another entity is a stop, not a merge.

## 4. Inputs and outputs

- Find the user's files: `run_capability(id="tool:list_workspace_files", input={"include_all_sessions": true})`.
  An expert chat may not see uploads made in an unrelated chat; if a file is
  missing, ask the user to upload it here.
- Bring each file into the sandbox before reading it (inline reads stop at 32 KB):
  `read_workspace_file(file_id=..., save_to_path="/home/user/in/<name>")`.
- Work in `/home/user/work/`, write deliverables to `/home/user/out/`.
- Deliver: `write_workspace_file(filename="<name>", source_path="/home/user/out/<name>")`
  and link the result as `workspace://<file_id>`. Copy durable results into the
  state root as well.
- If a file read or a tool fails twice, stop that step and report the gap. Do
  not continue on partial data.

## 5. Memory (optional)

When memory tools are available:

- Start: `memory_search(query="<entity> bookkeeping approvers basis rules")`.
  A hit is a proposal to confirm with the owner, never a fact.
- When the owner states a durable rule ("always code Figma to Software"), check
  the input shape with `describe_capability(id="tool:memory_store")`, then store it with
  `run_capability(id="tool:memory_store", input={...})` as a rule scoped to
  this entity (for example scope `project:books-<entity-slug>`).
- Never store amounts, account numbers, card data or customer personal data in
  memory. A remembered rule never overrides a newer written rule.
- If memory tools are hidden, skip this section; the state files are enough.

## 6. Files used by reconciliation, close, P&L and escalation

These four skills add the following under the entity folder. `<account>` is a
short label with only the last 4 digits of any number (`main-4411`, `amex-1009`).

| Path (under the entity folder) | Written by | Columns / content |
| --- | --- | --- |
| `recs/<account>-<YYYY-MM>.json` | statement-reconciliation | balances, open items, status, `approval_ref` (empty until approved) |
| `recs/<account>-<YYYY-MM>/` | statement-reconciliation | rec_match outputs, `workpaper.md`, `carried-next.csv` |
| `close/<YYYY-MM>/status.csv`, `report.md` | month-end-close-checklist | control status (see that package's `templates/close-status.csv`), close report |
| `pl/<YYYY-MM>.csv`, `pl/<YYYY-MM>-brief.md` | monthly-profit-and-loss-summary | period, account, group, amount, currency, basis, source, status (`draft` or `reviewed`) |
| `exceptions.csv` | bookkeeping-exception-escalation | id, raised_on, entity, account, period, class, amount, currency, facts_ref, decision_requested, owner, urgency, interim_state, status, decision_verbatim, decided_by, decided_on, evidence_path |
| `requests.csv` | bookkeeping-exception-escalation | id, owner, item, why_needed, settles_with, asked_on, due_on, answered_on, answer, exception_id |
| `packs/<exception-id>/` | bookkeeping-exception-escalation | pack.md, evidence.csv (masked), zip |

Additional rules for these files:

- **Approved means logged.** An artefact counts as approved or reviewed only if
  `approvals.csv` holds a row with its SHA-256 (`scripts/log_approval.py`). An
  approval covers that exact file; any edit needs a new one.
- **Only the owner closes an exception.** Its status becomes `closed_by_owner`
  only with the owner's reply recorded verbatim. Ids (`BX-n`, `RQ-n`) are never reused.
- **Chaining.** Before relying on last month's reconciliation, close or P&L,
  confirm it is approved or reviewed and that its closing figures still agree
  with the current source. If not, stop and report.
- Money is written as a plain decimal (`1250.00`, `-12.50`); dates `YYYY-MM-DD`.
