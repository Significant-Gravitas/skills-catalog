# Worked example: kit to packet, end to end

Fictional. Owner: Maya Chen (Europe/Lisbon). Hiring manager: Lena Ortiz.
Role: Senior Backend Engineer, Billing. The role scorecard has four
must-haves (M1-M4). Files in `hiring/` mirror `~/workspace/hiring/`.
Every output below is a real run of the scripts on these files.

## 1. Map competencies to slots

Loop shape from preferences (`loop_shape.senior-backend-engineer`): a 30-minute
screen, then three slots on one day. Knockout first (M3 billing debugging,
the competency most likely to rule people out), deep-dive next (M2 live data
changes), hiring manager's close last (M4). M1 (running a service) is
checked at the screen.

| Slot | Interviewer | Owns | Length | Clock |
| --- | --- | --- | --- | --- |
| 1 Screen | Sam Lee | M1 | 30 | 5 / 20 / 5 |
| 2 Billing debugging | Dev Rao | M3 | 60 | 5 / 40 / 15 |
| 3 Live data changes | Ana Silva | M2 | 45 | 5 / 30 / 10 |
| 4 Hiring manager close | Lena Ortiz | M4 | 45 | 5 / 25 / 15 |

## 2. Write, lint and check the kit

Lena pasted four questions of her own. Each was tightened or replaced (see
the kit's "Dropped or rewritten" table): the Stripe question was leading, the
"where are you from" question was national origin, the on-call health
question became a "with or without reasonable accommodation" statement of the
on-call requirement, and "five years" became a Most Significant
Accomplishment question.

```
$ cd ~/skills/interview-kit-design && python3 scripts/question_lint.py ~/workspace/hiring/roles/senior-backend-engineer/kit.md
clean: no drift or drop-rule hits (a lexicon check, not a legal review)

$ python3 scripts/check_kit.py ~/workspace/hiring/roles/senior-backend-engineer/kit.md \
    --scorecard ~/workspace/hiring/roles/senior-backend-engineer/scorecard.md
4 slot(s), 4 must-have(s)
ok: every must-have has exactly one owner and every clock adds up
```

`--scorecard` reads the must-haves from the role scorecard
(`hiring/roles/senior-backend-engineer/scorecard.md`, from role intake) and
fails the kit if any of them is missing from it; here all four are there.
Without a role scorecard that cross-check is skipped, and the hand-back says
so.

Kit: `hiring/roles/senior-backend-engineer/kit.md`. Interviewer scorecard: the
package template `templates/scorecard-1to5.md`, one per interviewer.

## 3. Evening before the loop: packets

The evening-interview-prep routine runs at 18:00 Lisbon on 28 Oct:

```
$ python3 scripts/build_packets.py --date tomorrow --tz Europe/Lisbon
packets/2026-10-29-senior-backend-engineer-priya-nair-1000-slot2.md
packets/2026-10-29-senior-backend-engineer-priya-nair-1110-slot3.md
packets/2026-10-29-senior-backend-engineer-priya-nair-1230-slot4.md  FLAGS: NO INTERVIEWER
```

The 12:30 slot has no interviewer in the loop log (Lena was moved from it
this afternoon). That is one line in the hand-back, and the coordination
skill owns the fix.

## 4. Fill and verify the summary

The summary is five lines at most, each a direct quote with its source
(`packet-slot3-filled.md`):

```
$ python3 scripts/verify_quotes.py ~/workspace/hiring/packets/2026-10-29-senior-backend-engineer-priya-nair-1110-slot3.md
OK  exact   "Led the migration of our 4TB invoices table ..." — source: screens/priya-nair-resume.txt
OK  exact   "using a shadow-copy tool I wrote (pg-shadow-copy)" ...
OK  exact   "Primary on-call for the payments ledger service (Go), one week in four." ...
OK  exact   "cut unmatched items from 2.1% to 0.3%" ...
OK  gap marked not stated   Rollback approach on that migration: not stated
```

(Abridged: the script prints the status and reason on one line and the full
summary line under it.) Every line is OK. Had a line read "4GB" for "4TB",
or dropped a "not", it would be a FAIL with exit 1, and the line is fixed
from the source or dropped: there is no "approximate" quote.

Nothing about Priya's age, background or location beyond the stated
timezone appears. The packet carries the screen's two open questions, so
Ana's slot knows to close the rollback question.

## 5. Hand-back to the owner

1. Three packets, delivered with `write_workspace_file(source_path=...)`
   and linked.
2. One line: "The 12:30 close with Priya has no interviewer. Want the
   coordination fix drafted?"
3. Nothing sent to the panel. "Say yes and I'll put each packet in a Gmail
   draft to its interviewer, or DM it on Slack."
