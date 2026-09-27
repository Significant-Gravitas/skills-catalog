---
name: "monthly-profit-and-loss-summary"
description: "Draft a sourced monthly profit-and-loss summary with coverage, comparisons, drivers, and unresolved accounting items. Use when the owner asks how last month went, why profit changed, for management accounts, P&L vs budget, or year-to-date profit. Prints period, basis and currency on every figure, refuses comparisons across cash and accrual bases, computes changes and plan variances with a script, traces each driver to invoices and bills with the untraced amount stated, and lists unmapped accounts and open items. Always a draft for the owner and accountant; never final accounts, tax advice or a solvency forecast."
triggers: ["monthly P&L summary", "profit and loss for last month", "explain this month's P&L", "why did profit change this month", "income statement summary", "management accounts", "how did we do last month", "P&L vs budget", "year to date profit", "are we making money"]
version: "2"
---

# Monthly profit-and-loss summary

This skill explains supplied records. It does not create final accounts or give
accounting, tax, or investment advice.

## When to use, and when not

Use for one entity and one month (or a year-to-date run of months) when the
owner wants to know what happened and why. It works from a ledger P&L export,
a read-only ledger report, or a stored draft.

Not for: building a P&L from raw bank lines without an account mapping (code
them first with `expense-categorization`); balance sheet or cash-flow
statements; tax, financing, solvency or investment questions ("are we making
money" is answered with the sourced result, never a forecast or advice).

## Inputs and where they come from

| Input | Source | If missing |
| --- | --- | --- |
| Current period P&L by account, with basis | User upload (`templates/pl-export.csv` shape), or a read-only ledger report (step 2) | Ask for it. |
| Comparison period on the **same basis** | Upload, ledger report, or `<state>/pl/<YYYY-MM>.csv` | Summarise the current month alone. |
| Report totals | The export's total rows, each mapped to a group name in `templates/reported-totals.csv` (for example "Total Income" → revenue, "Net Profit" → net_result). The script refuses any other label. | Say the detail-to-total check was not possible. |
| Entity, basis, currency, fiscal year, tax treatment (gross or net), thresholds | `intake.json`, `memory_search`, then `ask_question` | Unknown basis: header says "basis: unknown (open)" and no comparison is made. |
| Budget or plan (optional) | Owner file in `templates/budget-template.csv` shape | No plan column. Never create one. |
| Source rows for tracing | Preferred: the ledger's transaction detail by account (general ledger) export for both periods, or the same report read-only through the ledger tool. Also `<state>/invoice-register.csv` with an owner-confirmed `line-accounts.csv` (stable key → account; accrual revenue only), and the owner-approved rows of `<state>/expenses/<YYYY-MM>-review.csv` (outflows, so reshaped with `--negate`) | Driver stays "not traced". |

`<state>` is `~/workspace/bookkeeping/<entity-slug>/` (`references/books-state.md`).
Find uploads with `run_capability(id="tool:list_workspace_files", input={"include_all_sessions": true})`
and pull each with `read_workspace_file(file_id=..., save_to_path="/home/user/in/<name>")`.
No intake at all: load `run_capability(id="skill:bookkeeping-getting-started", input={})` first.

## Tools and pre-flight

1. `bash_exec`: `python3 --version`. With Python 3, every figure comes from
   `pl_variance.py` or `trace_movement.py` and the brief says "script-verified".
   Without it, compute by hand and label each total "hand-computed, not script-verified".
2. State pre-flight from `references/books-state.md`.
3. `memory_search(query="<entity> accounting basis fiscal year P&L groups threshold")`.
   Hits are proposals to confirm; never store amounts in memory.

All script commands start with `cd ~/skills/monthly-profit-and-loss-summary && `.

## Procedure

1. **Fix the scope.** State entity, period, currency, accounting basis, source
   export and export date, comparison period, whether figures are gross or net
   of tax, and whether intercompany items are included. Mark any unknown as open.
2. **Get the figures.** If intake marks the ledger as live:
   `find_capability("<ledger> profit and loss report")`, `describe_capability`,
   then a read-only `run_capability` with the period and the accounting method
   set to the intake basis. Compare the basis in the returned header with the
   one requested; if they differ or the basis is "open", pull nothing and ask.
   A sign-in card means stop and ask the user to connect, or to upload an export.
   If a file or tool fails twice, stop and report the gap.
3. **Map and check coverage.** Every account needs a group (revenue,
   direct_costs, operating_expenses, other_income, other_expenses) from the
   supplied chart; leave unknown groups blank. Never reclassify an account.
4. **Run the variance.**
   `python3 scripts/pl_variance.py --current ... --current-period <YYYY-MM> --current-basis <basis> --prior ... --prior-period <YYYY-MM> --prior-basis <basis> --currency <code> [--reported-current ...] [--plan ...] --entity "<entity>" --source "<export, date>" --out /home/user/out/pl/<YYYY-MM>`.
   - Exit 2 "NOT COMPARABLE": do not compute changes. Ask for the comparison
     period on the same basis, or summarise the current month alone.
   - Unmapped accounts are excluded from subtotals and listed; the net result
     is shown only when nothing is unmapped and detail ties to report totals.
     Without `--reported-current` the script reports `detail_to_total: not
     checked` and hides the net result; say so in the brief's Coverage section.
     It says "ties" only when revenue and at least one cost group were compared
     and every group with detail had a total; otherwise it names what was not
     checked and keeps the net result hidden.
   - An account unmapped in the comparison period makes every subtotal change
     "n/m (prior has unmapped accounts)"; list it in Coverage.
   - Default comparisons: prior month, and the same month last year from
     `<state>/pl/` when its basis matches (say if it is a draft).
   Traps the script flags (sales tax in the P&L, 1099-K revenue, owner items,
   holding accounts) and those it cannot see are in `references/pl-traps.md`.
   - **Year to date.** Take the fiscal-year start from intake (ask if it is not
     there; never assume January). Preferred: a YTD P&L export from the ledger
     for fiscal-year start to the month end, and the same span last year, both
     on one basis. Otherwise add the stored monthly files with
     `python3 scripts/pl_variance.py --sum-months <state>/pl/<YYYY-MM>.csv ... --span <FY start YYYY-MM>:<YYYY-MM> --sum-out /home/user/in/pl-ytd.csv`;
     it refuses a missing or repeated month, mixed bases or currencies, and a
     YTD file; a missing month means no YTD figure, never an estimate. Run
     `pl_variance.py` on the result with period labels `ytd-<YYYY-MM>` and
     `ytd-<prior year YYYY-MM>` (a plan compares only if it has rows with that label).
     Store YTD results as `<state>/pl/ytd-<YYYY-MM>.csv`, never under the
     month's name, so next month's prior-month comparison is never a YTD total.
5. **Trace the largest movements.** The trace needs rows with a date, a P&L
   account and an amount. Get them, in this order of preference:
   - The ledger's **transaction detail by account** (general ledger) export for
     both periods, uploaded or pulled read-only as in step 2
     (`find_capability("<ledger> transaction detail by account report")`). It
     already carries the account the ledger booked.
   - The kit invoice register has no account column, and its `line_key` is one
     contract line for one period (`SOW-014/retainer/2026-04`). Use it only with an
     owner-confirmed `<state>/line-accounts.csv` (`templates/line-accounts.csv`:
     key, account) keyed on the stable part (`SOW-014/retainer`) and pass
     `--key-strip-period`; ask the owner for any key that is missing. Never assign
     an account to an invoice yourself. Only `issued_per_owner` rows count (the
     default); voided, draft and approved-to-issue rows are skipped and listed,
     never given a date. It traces accrual revenue only: on a cash basis use the
     GL detail export or the payments.
   - The expense review table: only rows with status `approved`, with
     `--account-col proposed_account --date-col txn_date --negate` (card and bank
     outflows are negative; a source with the opposite sign to the P&L line is refused).
   Reshape each source (read-only), then trace:
   `python3 scripts/trace_movement.py --reshape --in <export> --date-col <col> --amount-col <col> [--ref-col <col>] (--account-col <col> | --key-col line_key --key-strip-period --account-map <state>/line-accounts.csv) [--include-status <status,...>] [--negate] --out /home/user/in/trace-<name>.csv`
   (the script's docstring has the three worked commands). Unmapped rows are listed
   in `<out>.unmapped.csv` and skipped rows in `<out>.skipped.csv`; both stay untraced. Then, for each of the top movements:
   `python3 scripts/trace_movement.py --account "<line>" --current-period ... --prior-period ... --pl /home/user/out/pl/<YYYY-MM>/pl_variance.json --sources /home/user/in/trace-*.csv --out /home/user/out/pl/<YYYY-MM>/trace.csv`.
   Quote traced and untraced amounts. A cause the records do not prove is a hypothesis.
6. **Accrual limits.** A P&L built from bank data alone is cash basis. When the
   owner wants accrual figures, list prepaid, deposit, unbilled and
   unreceived-bill candidates for the accountant (`references/basis-and-comparability.md`); never estimate them.
7. **Optional views.** By class, job, location, fund or property only when the
   export carries that dimension. A cash movement section only from reconciled
   bank totals, kept apart from profit. A bridge chart:
   `python3 scripts/pl_chart.py --pl .../pl_variance.json --out .../bridge.png`
   (needs matplotlib; skip if it cannot be installed).
8. **Write the brief** from `templates/pl-brief.md`: lead with three to five
   supported points (what changed, the amount, the period, the record behind
   it), then open exceptions and the decisions needed from the owner or
   accountant. State whether the draft includes or excludes each material open item.
9. **Review pass.** Run `checklists/review-pass.md`. For a first month with a
   client, or any movement above the owner's threshold, also run a clean-context check:
   save the brief, `pl_variance.json` and `trace.csv` with `write_workspace_file`, then
   `run_sub_session(prompt="Check the P&L brief at <workspace path>: for each numbered point confirm the amount against pl_variance.json and trace.csv at <paths>; flag any cause not proven by a record. Do not edit.", wait_for_result=300)`.
   Fix flagged points or relabel them as hypotheses.
10. **Deliver and store.** `write_workspace_file` the brief, table and chart, with
    `workspace://` links. Copy `pl_state.csv` to `<state>/pl/<YYYY-MM>.csv` (a
    year-to-date run to `<state>/pl/ytd-<YYYY-MM>.csv`) and the
    brief to `<state>/pl/<YYYY-MM>-brief.md`, status `draft`. The status becomes
    `reviewed` only after the owner or accountant says so in an `ask_question`
    reply logged with `python3 scripts/log_approval.py record ...` against the brief's hash.
11. **Route.** Material misstatements, unusual entries, tax matters, fraud,
    policy decisions and qualitative-materiality items go to the accountant or
    finance owner through `run_capability(id="skill:bookkeeping-exception-escalation", input={})`.

## Output contract

1. Header: entity, period and comparison, basis (or "unknown (open)"), currency,
   gross or net of tax, source export and date, "DRAFT for review, not final accounts",
   "script-verified" or "hand-computed".
2. Coverage: detail-to-total result, unmapped accounts and total, missing
   periods, adjustments awaiting approval.
3. Table from the supplied chart: revenue and major revenue groups; direct costs
   and gross result; operating expense groups; operating result; other income
   and expense; net result only when the source supports it. For each line:
   current, prior, change, percentage (or "n/m" with the reason), share of revenue.
4. Three to five sourced points with traced and untraced amounts; hypotheses labelled.
5. Plan comparison, only from a supplied plan, with its source.
6. Open exceptions (included or excluded), decisions needed, and links.

## Guardrails

- Never fill missing figures, choose a policy, reclassify an account, or call an
  unreviewed draft final.
- Never compare figures on different or unknown bases; print the basis beside every table.
- Do not compute a percentage from a zero or near-zero base without saying so.
- Keep cash movement apart from profit.
- Never create a plan or budget figure.
- Do not forecast solvency or advise on tax, financing or investment.
- Route material misstatements, unusual entries, tax matters, fraud,
  qualitative-materiality items and policy decisions to the accountant or finance owner.
- Ledger access is read-only: never call a tool that creates, edits or posts.

## Quality self-check

`checklists/review-pass.md`: numbers from the script, one basis, drivers
traced, hypotheses labelled, exceptions listed, DRAFT at the top.

## Files in this package

- `references/basis-and-comparability.md`, `pl-traps.md`, `books-state.md`
- `scripts/pl_variance.py`, `trace_movement.py`, `pl_chart.py`, `log_approval.py`
  (`pl_variance.py`, `trace_movement.py` and `log_approval.py` have `--selftest`)
- `templates/pl-export.csv`, `reported-totals.csv`, `budget-template.csv`, `trace-sources.csv`, `line-accounts.csv`, `pl-brief.md`
- `examples/worked-example.md` (cross-basis refusal, untraced driver) and `examples/april-2026/`
- `checklists/review-pass.md`

## Related skills

`bookkeeping-getting-started`, `expense-categorization`, `statement-reconciliation`,
`month-end-close-checklist` (runs this as control 8), `bookkeeping-exception-escalation`.
