---
name: "statement-reconciliation"
description: "Reconcile a bank or card statement to a ledger with control totals, matched items, timing differences, and owned exceptions. Also covers loan, petty cash and processor clearing accounts (Stripe, PayPal payouts), QuickBooks and Xero reconciliation differences, and PDF statements. Use when a statement arrives, at month-end, when a balance does not match the books, or when payouts cannot be found against invoices. Ties each period to the last approved one, matches one-to-one with scripts, never plugs a difference, and returns a workpaper for owner sign-off without changing the ledger."
triggers: ["reconcile this bank statement", "reconcile the card statement to the books", "bank balance doesn't match the ledger", "unmatched bank transactions", "statement-to-ledger reconciliation", "Stripe payout doesn't match", "reconcile in Xero", "QuickBooks reconciliation is off", "credit card reconciliation", "reconcile PayPal"]
version: "2"
---

# Statement reconciliation

A reconciliation explains every difference between two records for one account
and one period. It does not force them to agree.

## When to use, and when not

Use for one account and one period at a time: bank, credit card, loan, petty
cash, or a processor clearing account (Stripe, PayPal). For several accounts,
run once per account.

Not for: coding expenses (`expense-categorization`), chasing customers
(`accounts-receivable-follow-up`), the whole month-end (`month-end-close-checklist`,
which calls this skill), or deciding a correcting entry (the accountant decides;
this skill only drafts).

## Inputs and where they come from

| Input | Source | If missing |
| --- | --- | --- |
| Statement for the full period, with opening and closing balance | User upload (CSV preferred, PDF accepted); for processors, the payout or activity report | Ask for it. Never reconcile to a feed balance. |
| Ledger register for the same account and cutoff | User upload, or a read-only pull from a connected ledger (step 3) | Ask for it. |
| Prior approved closing and carried open items | `~/workspace/bookkeeping/<entity>/recs/<account>-<prior YYYY-MM>.json` and its `carried-next.csv` | First period: record "no prior approved rec" as an open item. |
| Entity, currency, sign convention, owners, window, aging buckets | `intake.json`, `memory_search`, then `ask_question` | Defaults are labelled "default — confirm with the owner". |

Find uploads with `run_capability(id="tool:list_workspace_files", input={"include_all_sessions": true})`.
Pull each into the sandbox with `read_workspace_file(file_id=..., save_to_path="/home/user/in/<name>")`;
inline reads stop at 32 KB, so never reconcile from an inline read. If the
file was uploaded in a chat this one cannot see, ask the user to upload it here.
No intake at all: load `run_capability(id="skill:bookkeeping-getting-started", input={})` first.

## Tools and pre-flight

1. `bash_exec`: `python3 --version`. If Python 3 is present, every figure in the
   output comes from a script and says "script-verified". If not, work by hand
   with `references/bank-rec-layout.md` and label each total "hand-computed, not
   script-verified". Scripts use the standard library only; no install is needed.
2. State: run the pre-flight in `references/books-state.md`. If it fails, say
   results will not carry to the next chat, and deliver files with `write_workspace_file`.
3. `memory_search(query="<entity> bookkeeping approvers basis reconciliation window")`.
   Treat hits as proposals to confirm. Never store amounts or account numbers in memory.

All script commands start with `cd ~/skills/statement-reconciliation && `.
Mirror the numbered steps below in `TodoWrite` when reconciling more than one account.

## Procedure

1. **Tie to last period.** Load the prior `recs/` file and check the owner
   signed it off or recorded it as reviewed
   (`python3 scripts/log_approval.py check --approvals <state>/approvals.csv --artefact <prior workpaper.md>`).
   Put its closing in `balances.json` as `prior_approved_closing` and pass its
   `carried-next.csv` as `--carried`. If the statement opening differs, the
   matcher stops (exit 3): report it as a suspected edit to a reconciled period
   and do nothing else. Never undo or re-reconcile.
2. **Set the controls.** Record entity, account label (last 4 digits only),
   currency, period, statement and ledger opening and closing balances, and the
   export cutoff and time zone. Keep pending and posted items separate. Build
   `/home/user/in/balances.json` from `templates/balances.json`; the schema is in
   `references/input-schema.md`; pick the account type and sign convention from
   `references/account-types.md`.
3. **Get complete sources.**
   - PDF statement: `python3 scripts/extract_statement.py --pdf /home/user/in/stmt.pdf --date-format "<as printed>" --closing <closing> --out /home/user/in/statement.csv`.
     It must print PROVEN. If the proof fails twice, stop and ask for the
     bank's CSV export.
   - Connected ledger or processor (only if intake marks it live):
     `find_capability("<ledger> account transactions")`, `describe_capability`,
     then a **read-only** `run_capability` for the period. Save the result to
     `/home/user/in/` with its time zone and treat it as an export. Never call a
     reconcile, match, unreconcile, undo, create or update tool. A sign-in card
     means stop and ask the user to connect, or to upload an export instead.
   - Compare any feed or ledger "statement balance" with the real statement
     closing. A difference means the feed is incomplete: stop and say so.
   - If any file or tool fails twice, stop and report the gap. Do not continue on partial data.
4. **Match.** `python3 scripts/rec_match.py --statement ... --ledger ... --balances ... [--carried ...] --out /home/user/out/rec/<account>-<YYYY-MM>`.
   Passes run in order: bank id (FITID); date + amount + reference; date +
   amount if unique; within the window with reference; within the window if
   unique; batches that share one reference (up to 6 parts, a script limit; larger batches are left for a person). Every match is one-to-one.
   Ambiguous pairs, duplicates and out-of-period rows are left unmatched and listed.
   Carried rows appear as `carried:<YYYY-MM>:<id>`, so they never collide with
   this period's line numbers. Every output masks long numbers in descriptions
   and references to the last 4 digits; never paste the raw text back in.
5. **Processor clearing (Stripe, PayPal).** `python3 scripts/payout_breakdown.py stripe|paypal --report ... --bank /home/user/in/statement.csv --cutoff <period end> --out ...`.
   For a PayPal export holding more than one currency, add `--currency <the one paid to this bank>`;
   the script refuses to add currencies together. Method and traps: `references/processor-clearing.md`.
6. **Classify what is left.** Read `unmatched_*.csv`, `ambiguous.csv`,
   `duplicates.csv` and the diagnostics. For each item decide:
   - bank-side timing (clears without an entry) → leave as timing. The script
     defaults a ledger-only row to timing only if it is dated within
     `stale_days` (the matching window unless the owner set one) of period end
     or `--next-statement` shows it cleared. A row the next statement shows
     clearing later than that is kept as timing. If it is a deposit it is
     marked "late clearing" in the diagnostics: escalate it under step 7. A
     payment (a cheque the payee banks late) is only noted as routine. An
     older one, or a timing item carried from last month that still has not
     cleared, defaults to `investigate` ("stale timing item"). Classify it as
     timing only when the owner confirms why it has not cleared;
   - book-side (fee, interest, unrecorded receipt, wrong amount, duplicate) →
     `correction` or `ledger-error`, a draft for the accountant. Each one
     is carried forward in `carried-next.csv` as an owned statement-side
     `correction` until the accountant's correcting entry is in the ledger,
     where it matches and clears;
   - cause unknown → `investigate`, with an owner and next step.
   Review fees, interest, refunds, reversals, transfers and foreign-currency
   settlements separately: a transfer needs its other side in the other
   account; a foreign-currency settlement is matched on the account-currency
   amount with the original currency and rate quoted from the source, and any
   FX difference is left for the accountant, never computed as a plug.
   Ask the owner the smallest settling question with `ask_question` (one
   question per item, with options, up to 10 per card). Write answers to
   `/home/user/in/classify.csv` with the owner's words as the note, then re-run
   step 4 with `--classify` (and `--next-statement` if next month's lines exist).
   Diagnose any remaining difference with `references/ledger-diagnostics.md`.
7. **Escalate at once** (do not keep matching that item) for: an unknown
   withdrawal, changed payee bank details, a duplicate payment, a large or
   repeated difference, a deposit in transit that has not cleared within a few
   business days (an unrecorded-deposit or lapping signal), or suspected fraud. Load
   `run_capability(id="skill:bookkeeping-exception-escalation", input={})`, build
   the pack from the statement line and ledger evidence, and put its exception
   id in the item's next step.
8. **Workpaper.** `python3 scripts/write_workpaper.py --rec /home/user/out/rec/<account>-<YYYY-MM> --entity "<entity>" --owners /home/user/in/owners.csv [--xlsx]`.
   Every open item needs an owner and next step before review. The script will
   not print "Ready for owner sign-off" while any item is UNASSIGNED.
9. **Independent re-check (for 3 or more accounts, or any difference not 0.00).**
   Save the output folder with `write_workspace_file`, then
   `run_sub_session(prompt="Load skill:statement-reconciliation. Re-verify the reconciliation files <workspace paths>: recompute both adjusted balances from matches.csv and the unmatched files; confirm every match has one row id per side and dates in the period; report any mismatch. Do not change files.", wait_for_result=300)`.
   Fix or report what it finds. For several accounts, one Task per account (at most 3 at once).
10. **Sign-off.** Hash the workpaper (`python3 scripts/log_approval.py hash <workpaper.md>`),
    deliver it with `write_workspace_file(source_path=...)` and a `workspace://` link, then
    `ask_question`: "Sign off <account> <period> reconciliation (unexplained <x>)?".
    Options when the difference is 0.00: "Signed off" / "Not yet: I have questions".
    Otherwise: "Reviewed, items owned" / "Not yet". Record the reply with
    `log_approval.py record --expect-sha <hash> ...`. The approver is whoever the
    user says; never infer identity.
11. **Write state.** Copy the output folder to `<state>/recs/<account>-<YYYY-MM>/`,
    `rec-state.json` to `<state>/recs/<account>-<YYYY-MM>.json` (with
    `approval_ref` set to the approvals.csv timestamp only if step 10 approved),
    and add each open item to `open-items.csv`. Nothing is deleted.

## Output contract

Return, in this order:

1. Header: entity, account label, period, currency, sources and export times, status
   (RECONCILED, NOT RECONCILED or STOPPED), and "script-verified" or "hand-computed".
2. The layout from `references/bank-rec-layout.md`: both opening and closing
   balances, both adjusted balances, and the unexplained difference.
3. Matched count and value; totals of debits and credits (or charges and payments).
4. Timing items with dates (cleared or unconfirmed); statement-only and
   ledger-only items; duplicates or possible duplicates; refused out-of-period rows.
5. Each open item with class, age, owner and next step; exception ids raised.
6. Proposed corrections, each marked "draft for accountant review".
7. Links: workpaper, CSVs, and the state path written.

"Reconciled" is used only when the unexplained difference is exactly 0.00 and
every remaining item is timing or a drafted correction. Otherwise the status is
"open, not reconciled", with every item owned.

## Guardrails

- Do not create, delete, merge, match, un-match or edit transactions in any
  ledger. Do not undo a reconciliation or edit a closed or reconciled period;
  propose a current-period correction to the accountant.
- **Never pull a transaction from another period, account or entity to close a gap.**
  Never post or propose a balancing, suspense or plug entry.
- Never match on amount alone when duplicates exist. Keep a row id for both
  sides of every match. Leave every uncertain pair unmatched.
- The real statement is the authority, never a feed balance.
- Stop on source failure: a file or tool that fails twice is reported, not worked around.
- Do not propose an adjusting entry unless the source and approved policy
  support it; present it as a draft for accountant review.
- Recommend Exclude, never delete, for a feed duplicate; the owner performs it.
- Escalate unknown withdrawals, changed bank details, duplicate payments,
  large or repeated differences and suspected fraud at once (step 7).
- Store and show only the last 4 digits of any account or card number.

## Quality self-check

Run `checklists/before-release.md`. At minimum: prior tie checked; both files
prove; no plug; every open item owned; defaults labelled; nothing posted.

## Files in this package

- `references/bank-rec-layout.md` (layout, item classes, aging), `account-types.md`,
  `processor-clearing.md`, `ledger-diagnostics.md`, `input-schema.md`, `books-state.md`
- `scripts/rec_match.py`, `payout_breakdown.py`, `extract_statement.py`,
  `write_workpaper.py`, `log_approval.py` (each has `--selftest`)
- `templates/` input files and the hand-fallback workpaper
- `examples/worked-example.md` (end to end, with the plugging trap) and `examples/scenarios/`
- `checklists/before-release.md`

## Related skills

`bookkeeping-getting-started` (intake), `expense-categorization` (coding the
lines this finds), `month-end-close-checklist` (runs this as control 1),
`monthly-profit-and-loss-summary`, `bookkeeping-exception-escalation`.
