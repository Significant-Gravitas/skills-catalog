# Expense review table: column guide

File: `expense-review-template.csv`. One row per source row, in source order.
`write_review.py` refuses a table that drops, repeats or edits a source row.
Quote any field that contains a comma; a shifted column stops the run.

| Column | Rule |
| --- | --- |
| source_file | Export file name as supplied, or `ledger API, <timestamp>` |
| source_row | Line number in that file (from the canonical CSV) |
| split_part | Blank, unless the owner split the line: then one row per part numbered 1..n, each with the part's amount, the source currency, and parts adding up exactly to the source amount |
| txn_date | Transaction date from the source |
| posting_date | Posting date if the source gives one; keep it separate, never merged with txn_date |
| vendor | Receipt or source text; do not infer a legal name |
| amount | Exactly as in the canonical CSV, with sign (money out negative) |
| currency | Source currency; for a foreign-currency line, note the original amount in `reason` |
| evidence | Receipt, invoice or contract id and whether it ties (`R3 receipt (ties)`), or `missing` |
| payment_line | The card or bank row that pays for the evidence (`amex:6`); `none` for a receipt with no payment line |
| proposed_account | Exact approved account name, or `unresolved` |
| dimension | Class, location, job or fund from supplied lists only; blank otherwise |
| reason | One sentence tied to the evidence, citing the account definition where one exists |
| confidence | `high`, `medium` or `low` |
| review_need | The one fact or owner needed next; blank only when nothing is needed |
| basis | From `propose_from_history.py` (`rule R1`, `history: 2 approved rows`, `conflict: …`, `none`) |
| special | Kinds from `expense_checks.py`, or `none` |
| excluded_reason | Why a row is left out of the expense total (for example "card payment, coded on card export"); required when status is `excluded` |
| status | `proposed`, `excluded`, or after the owner answers, `approved` with the account they chose |

Footer (from `write_review.py`, pasted as is): source rows and amount; Ready to
post rows and amount; Needs review rows and amount; unresolved; excluded; tie
to the control total.
