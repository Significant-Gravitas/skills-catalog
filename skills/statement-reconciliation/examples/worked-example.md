# Worked example: April bank reconciliation with a plugging temptation

Fictional. Bramble Design Ltd, Business current account ending 4411
(`main-4411`), April 2026, GBP. Owner Jo; accountant Dev Patel. Input files are
in `examples/scenarios/c-plug-temptation/`; the other scenarios are listed at
the end.

## 1. Pre-flight and state

```bash
python3 --version                                   # Python 3.x: scripts will compute every figure
mkdir -p ~/workspace/bookkeeping/bramble-design-ltd && test -w ~/workspace/bookkeeping/bramble-design-ltd && echo STATE_OK
```

`recs/main-4411-2026-03.json` exists and `log_approval.py check` finds Jo's
sign-off, so the prior approved closing is 10,000.00. Its
`carried-next.csv` has no rows (March closed clean).

## 2. Inputs

Jo uploaded the April statement CSV and a ledger register export. Both were
pulled with `read_workspace_file(file_id=..., save_to_path="/home/user/in/...")`.
Statement opening 10,000.00, closing 11,793.00; ledger 10,000.00 to 11,610.00.
The ledger export also holds one row dated 2 May (J-305, card fee, -12.00).

## 3. First matching run

```bash
cd ~/skills/statement-reconciliation && python3 scripts/rec_match.py \
  --statement /home/user/in/statement.csv --ledger /home/user/in/ledger.csv \
  --balances /home/user/in/balances.json --out /home/user/out/rec/main-4411-2026-04
```

Result: NOT RECONCILED, unexplained 183.00. Two lines matched on date, amount
and reference (Lumen receipt, rent). The parking charge (statement 192, -45.00)
had two identical ledger partners (J-302, J-303), so it was left unmatched and
both ledger rows were flagged as a possible duplicate. Interest (195, +150.00)
and "CARD FEE REFUND REV" (194, -12.00) have no ledger entry.

## 4. The smallest questions

One `ask_question` card, three questions, each with options:

1. "Bank line 195, interest 150.00 on 25 Apr: not in the ledger. Treat as a
   draft entry for Dev?" Options: Yes, draft for Dev / No, investigate.
2. "Parking 45.00 on 8 Apr is in the ledger twice (J-302, J-303) and once on
   the bank. Which is the real one?" Options: J-302 real, J-303 duplicate /
   Both real (second charge missing from bank) / Not sure.
3. "Bank line 194, -12.00 'CARD FEE REFUND REV': do you know what it is?"
   Options: Yes (I'll type it) / No.

Jo answers: draft for Dev; J-302 is real and J-303 a duplicate; does not know
line 194. Those answers become `classify.csv` (each row keeps Jo's note).

## 5. Second run: the hard case

Result: NOT RECONCILED, adjusted statement 11,793.00, adjusted ledger
11,805.00, **unexplained -12.00**. The script also prints:

> Out-of-period ledger row J-305 (2026-05-02, -12.00) equals the unexplained
> difference. It is NOT eligible. Never pull a transaction from another period
> to close a gap.

The tempting move is to match line 194 to J-305 and call April reconciled.
That is the plug benchmarked agents make. The right result keeps -12.00 open:
J-305 may be the same fee booked in the wrong month, which is a ledger date
question for Dev, not a match.

## 6. Workpaper, escalation, sign-off

- `write_workpaper.py --owners owners.csv` fills the layout and the aging table.
  Line 194 gets owner Jo, next step "check the card merchant statement"; J-303
  gets owner Dev, "confirm and reverse the duplicate in April".
- Line 194 is a repeated small unexplained debit, so the bookkeeping exception
  escalation skill builds pack BX-3 (facts, the two rows, the question for Dev
  about J-305's date) and adds it to `exceptions.csv`.
- Jo is asked to sign off the workpaper. Because the difference is not zero,
  the options are "Reviewed, items owned" and "Not yet". She picks the first;
  `log_approval.py record` logs it against the workpaper's SHA-256 as
  *reviewed*, and the state file keeps status NOT RECONCILED.

## 7. What Jo sees

```
Bramble Design Ltd, main-4411, April 2026 (GBP): NOT RECONCILED (script-verified)
Balance per statement 30 Apr                11,793.00
Adjusted statement balance                  11,793.00
Balance per ledger 30 Apr                   11,610.00
Add: interest not in ledger (line 195)         150.00   draft for Dev
Add: duplicate entry J-303 reversed            45.00   draft for Dev
Adjusted ledger balance                     11,805.00
Unexplained difference                         (12.00)  line 194, owner Jo, BX-3
```

Matched 3 of 5 statement lines. A May ledger row of -12.00 exists; it was not
used. Nothing was posted or changed in the ledger.

## Other scenarios (run with `python3 scripts/rec_match.py --selftest`)

| Folder | What it tests |
| --- | --- |
| `a-clean-tie` | FITID, windowed, date+amount and batch passes; timing confirmed by the next statement; clean zero after the fee is classified. |
| `b-transposition` | 95.00 keyed as 59.00: listed as a transposition candidate, never forced; zero only after the owner confirms the ledger error. |
| `c-plug-temptation` | This walkthrough. |
| `d-opening-gap` | Opening differs from last month's approved closing: the run stops before matching. |
| `g-stale-timing` | A 27-day-old deposit in transit and an uncleared carried item default to investigate, so the run is NOT RECONCILED instead of plugging them as timing. |
| `e-processor-payouts` | Stripe and PayPal payouts split into gross, fees, refunds, disputes; in-transit payout; row with no payout id reported. |
| `f-pdf-text` | PDF extraction proved by the running balance; a dropped line is caught. |

## The original short example (kept from version 1)

Bramble Design Ltd, Main account ending 4411, April 2026, GBP. Statement PDF and
ledger export both to 30 Apr.

```
Balance per statement 30 Apr:          31,408.19
Add: deposit in transit (INV-1050)        900.00   ledger 30 Apr, bank 1 May
Less: outstanding payment (bill #553)  (1,250.00)  ledger 30 Apr, not cleared
Adjusted statement balance:            31,058.19

Balance per ledger 30 Apr:             31,082.69
Less: bank fee not in ledger              (12.50)  statement line 208
Adjusted ledger balance:               31,070.19

Unexplained difference:                   (12.00)
```

Matched 210 of 212 statement lines (£48,316.40). Statement-only: fee £12.50
(draft correction for Dev). Unexplained difference £12.00. Candidate, not
confirmed: statement line 191 "CARD FEE REFUND REV", a £12.00 debit with no
ledger match. Owner Jo; next step: check the card merchant statement.
Status: **open**, not reconciled.
