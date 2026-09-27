# Worked example: April close with a late statement

Fictional. Bramble Design Ltd, April 2026, cutoff 30 Apr, GBP. Close owner
Jo; accountant reviewer Dev Patel; target review 8 May. The status file this
example ends with is `examples/close-2026-04/status.csv`
(`python3 scripts/close_status.py --selftest` checks it).

## 1. Open the close (6 May)

- Pre-flight: `python3 --version` ok; state root
  `~/workspace/bookkeeping/bramble-design-ltd/` writable; `intake.json` present
  (basis: accrual per Dev; accounts main-4411 and amex-1009; no processors, no loans).
- Prior period: `close/2026-03/status.csv` shows March prepared and approved;
  `open-items.csv` holds one open item from March: bank fee 12.50, owner Jo.
- `close_status.py init --period 2026-04 --prior close/2026-03/status.csv`.
- `list_workspace_files` against the intake sources: main statement, billing
  export and bills export are there; the Amex April statement and the payroll
  report are not.
- Controls mirrored to `TodoWrite` from `close_status.py report --todo`.

## 2. Work the controls

| Control | What happened |
| --- | --- |
| S1 | Blocked: Amex April statement not yet issued (due 3 May per last three statements; still missing 6 May). |
| S2, 2 | Billing export: 18 invoices, 22,750.00, ties to the invoice register. Ready for review. |
| S3 | In progress: 9 card receipts missing. Missing-documents request drafted via `bookkeeping-exception-escalation` (BX-4). |
| S4 | Blocked: payroll report not supplied. |
| S5, S6, 6, 10 | Not applicable, each with a reason from intake. |
| 12 | OBE 0.00 at 30 Apr. Ready for review. |
| 1 | `statement-reconciliation` loaded for main-4411: NOT RECONCILED, -12.00 on line 194 owned by Jo (BX-3). Amex waits on S1. In progress. |

## 3. The hard case: "just draft the P&L so Dev can start"

Jo asks for the P&L to be marked ready so Dev can begin. The dependency map
puts the P&L (control 8) after the reconciliations (1), the bills (3), the
accountant items (7) and Undeposited Funds (11). The script refuses:

```
$ python3 scripts/close_status.py set --status-file .../status.csv --id 8 --status ready_for_review --evidence "draft P&L"
refused: control 8 cannot be ready_for_review: it depends on 1 Bank and card statements reconciled (in_progress);
3 Bills receipts expenses and employee claims complete through cutoff (not_started); ...
```

The right response: the P&L skill may still produce a **draft** brief for Jo
now, labelled DRAFT with Amex, payroll and the 9 receipts listed as excluded,
but control 8 stays open and the period is not prepared for review. Nothing is
worked around, and the Amex month is not estimated from the feed.

## 4. Follow-up offer

The Amex statement is late. Jo is asked with `ask_question`:
"Check again on 8 May at 9:00 whether the Amex April statement has been
uploaded, and continue the close if it has?" Options: Yes / No. On yes:
`run_capability(id="tool:schedule_followup", input={"message": "Check whether the Amex April 2026 statement for Bramble Design Ltd has been uploaded; if so, continue the April close from close/2026-04/status.csv. Prepare and report only.", "delay_seconds": 172800})`,
called last in the turn because it ends the turn.

## 5. Close report (extract)

```
Period state: not prepared for review (14 controls open), from close_status.py
Critical path: S1 Amex statement -> 1 reconciliations -> 7 accountant items -> 8 P&L -> 15 lock
Earliest possible review: after the Amex statement arrives and is reconciled.
Ready for review: S2, 2 (18 invoices, 22,750.00), 12 (OBE 0.00)
Blocked: S1 Amex statement (Jo, expected any day); S4 payroll report (Jo)
Open items carried from March: bank fee 12.50 (Jo)
Exceptions: BX-3 (-12.00 unexplained, main-4411), BX-4 (9 receipts)
Proposed adjustments: none yet
Checks not performed: payroll tie-out, Amex reconciliation, accruals
```

Status: not `prepared for review`. The report is saved as
`close/2026-04/report.md` and delivered with `write_workspace_file`. No binder
is built yet; it is built when the period is prepared for review, and sent to Dev
only after Jo says yes to sending it to Dev.

## The original example table (kept from version 1)

| # | Control | Status | Evidence / blocker | Owner |
| --- | --- | --- | --- | --- |
| 1 | Bank reconciled | in progress | £12.00 unexplained (statement line 191); 2 timing items | Jo |
| 1 | Amex reconciled | blocked | April statement not yet issued (due 3 May) | Jo |
| 2 | Sales invoices to cutoff | ready for review | 18 invoices, £22,750.00, ties to billing export | Jo |
| 3 | Bills and receipts | in progress | 9 card receipts missing | Jo |
| 5 | Payroll tie-out | blocked | payroll report not supplied | Jo |
| 7 | Accountant items | not started | waits on 1 and 3 (dependency map level 3) | Dev |

Proposed adjustments: none yet. Unresolved exceptions carried from March: 1
(bank fee £12.50, owner Jo). Checks not performed: payroll, Amex. Status: not
`prepared for review`; earliest possible is after the Amex statement arrives.
