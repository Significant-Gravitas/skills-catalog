# Month-end close report: <entity>, <YYYY-MM>

Cutoff <date>. Reporting currency <code>. Basis <cash | accrual | open>.
Close owner <name>. Accountant reviewer <name>. Target review date <date>
(calendar: <agreed | default — confirm with the owner>).
Period state: **<prepared for review | not prepared for review (n controls open)>** (from close_status.py).
This report is preparation for review. It is not an approval and the period is not closed.

## Prior period

- Prior closing balances: <approved on <date> (approvals.csv) | not approved: carried as open item OI-n>
- Open items carried in: <n>, listed below with their original period.

## Sources

| Source | File | Covers | Rows | Control total | Received |
| --- | --- | --- | --- | --- | --- |

Late: <source, who owes it, expected date, follow-up scheduled yes/no>.

## Controls

<paste the table close_status.py wrote with --markdown>

## Control totals

| Account | Statement closing | Ledger closing | Unexplained | Status |
| --- | --- | --- | --- | --- |

## Ready for review

- <control: evidence link>

## Blockers and critical path

- Blocked: <control: blocker, owner, expected date>
- Critical path: <chain from close_status.py>; earliest possible review: <date or "after X arrives">

## Material changes

- <from the P&L brief, with basis and currency; "not yet available" until control 8>

## Proposed adjustments (drafts for the accountant; none posted)

| # | Source | Reason | Amount | Preparer | Approver | Approval ref |
| --- | --- | --- | --- | --- | --- | --- |

## Unresolved exceptions and open items

| Id | Opened | Period | Item | Amount | Owner | Next step |
| --- | --- | --- | --- | --- | --- | --- |

## Checks performed and not performed

- Performed: <list>
- Not performed: <list, with why>

## Approval

Owner reply (verbatim): <...>  Recorded: approvals.csv <timestamp>, SHA-256 of this file <...>.
Lock date as stated by the owner: <date | not yet locked>.
