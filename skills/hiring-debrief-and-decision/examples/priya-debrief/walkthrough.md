# Worked example: a four-scorecard debrief, end to end

Fictional. Owner Maya Chen (Europe/Lisbon). Role: Senior Backend Engineer.
Hiring manager and decision-maker: Lena Ortiz. The loop ended Thu 29 Oct;
the debrief is Fri 30 Oct 11:00 Lisbon. The files under `hiring/` are the
loop log and the four filed scorecards. Every output below is a real run.

## 1. Freeze the scorecards (roll-call time)

```
$ cd ~/skills/hiring-debrief-and-decision
$ python3 scripts/snapshot_scorecards.py --dir ~/workspace/hiring/debriefs/senior-backend-engineer/priya-nair/scorecards \
    --tz Europe/Lisbon --debrief-start 2026-10-30T11:00
4 new scorecard(s) frozen; 0 changed since filing; 0 filed late
```

Maya is asked once whether panelists could see each other's feedback before
filing (Greenhouse has that setting [90]). Answer: "No, hidden until you
submit." Recorded under process notes.

## 2. Collate

```
$ python3 scripts/collate_scorecards.py --candidate "Priya Nair" --role "Senior Backend Engineer" \
    --scorecards ~/workspace/hiring/debriefs/senior-backend-engineer/priya-nair/scorecards \
    --order "Dev Rao,Ana Silva,Sam Lee,Lena Ortiz" \
    --out ~/workspace/hiring/debriefs/senior-backend-engineer/2026-10-30-priya-nair-brief.md
## Roll-call (4 of 4 filed; bar 90%)
...
## M2 Designs live data-store changes with a rollback path
- Ana Silva, 2: "Could not say how the migration would roll back if step 3 failed." [FACT, scorecard]
- Lena Ortiz, 4 [outside this slot]: "Strong architecture instincts." [FACT, scorecard]
- Outside the owning slot (not counted for splits): Lena Ortiz (4). Challenge: which slot's question produced this, and what did you see?
...
- Challenge: M2: Lena Ortiz (4) rated outside their slot; which evidence, from which question?
...
- Minutes: opening 5, decision 5, M1 8, M2 8, M3 7, M4 7 (of 40)
```

(Abridged: `...` marks lines left out.) Maya gave the order (Dev and Ana
are the most junior; Lena, the hiring manager, speaks last). Lena's slot
owns M4 only (her scorecard header and the loop log agree), so her M2 rating
is shown but is not counted as a split: the kit gives M2 one owner, Ana.
With `--include-outside` the same run marks M2 "Split first" and gives it
10 minutes.

## 3. Flag remarks

```
$ python3 scripts/flag_remarks.py ~/workspace/hiring/debriefs/senior-backend-engineer/priya-nair/scorecards
ASK  Lena Ortiz · M2 rating 4 · label-no-behaviour ('Strong')
     -> What did you see or hear that puts this at a 4?
ASK  Lena Ortiz · overall reason · label-no-behaviour ('strong')
     -> What did you see or hear that is behind this?
```

Nothing to cut. Sam's "3" and Dev's "4" carry observed behaviour; their
INFERENCE lines say the evidence supports the rating.

## 4. The brief Maya gets (filled)

> **Live data changes (M2)** (owner: Ana's slot)
> - Ana, 2: "Could not say how the migration would roll back if step 3
>   failed." [FACT, scorecard] INFERENCE: concrete, and it matches the
>   anchor for 2 ("ran migrations ... without a rollback path").
> - Lena, 4, outside her slot: "Strong architecture instincts." [FACT,
>   scorecard] INFERENCE: a label, not evidence, on a competency her slot
>   did not cover; not counted as a split. Ask Lena what she saw.
>
> **Billing debugging (M3)**
> - Dev, 4: "Traced a double-charge to webhook retries and added
>   idempotency keys; showed the reconciliation drop from 2.1% to 0.3%."
>   [FACT] INFERENCE: evidence supports a 4 (changed the system so the
>   class of bug stopped).
>
> **Open questions:** rollback thinking on a live migration (cheapest fix:
> 30-minute follow-up with Ana); what she personally fixed on-call
> (reference check, if the process allows one).
>
> **Running order:** Dev, Ana, then Sam, Lena last; 8 of 40 minutes on M2.
> Challenge line for Lena's out-of-slot 4: "Which question in your slot
> produced this, and what did you see or hear that puts it at a 4?"

## 5. After the meeting

Lena, in her words: "I want Ana's rollback question answered before I
decide. Book the 30 minutes." Category confirmed with her: hold.

```
$ python3 scripts/decision_log.py append --date 2026-10-30 --role "Senior Backend Engineer" \
    --candidate "Priya Nair" --decision hold --decider "Lena Ortiz" \
    --reason "I want Ana's rollback question answered before I decide. Book the 30 minutes." \
    --splits 0 --filed-ratio 1.0 --no-decision-count 0 \
    --stage "Follow-up call" --next-step "30-min rollback follow-up with Ana by Wed 4 Nov"
recorded: Priya Nair, Senior Backend Engineer: hold (by Lena Ortiz)
tracker: Priya Nair stage 'Onsite done' -> 'Follow-up call'
tracker: Priya Nair stage_since '2026-10-29' -> '2026-10-30'
tracker: Priya Nair next_step 'Debrief Fri 30 Oct' -> '30-min rollback follow-up with Ana by Wed 4 Nov'
```

(The tracker row was changed after Maya said "yes, update it".) The
follow-up call goes to interview-coordination to book. Sofia did not rate
Priya, recommend hire or no hire, or settle the M2 disagreement. Nothing reached Priya.
