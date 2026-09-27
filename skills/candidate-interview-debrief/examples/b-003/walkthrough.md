# Worked example: debrief pack for candidate B-003 (fictional)

Fictional company Acme Ltd, role Billing Operations Lead, rubric v1 (3
criteria, 1-4 scale). The panel is Maya Chen (hiring manager and named
decision-maker), Tom Reyes and Priya Nair. The debrief starts on 2026-10-03
at 10:00 (+01:00). The files beside this walkthrough are the real inputs.

## Request

> Maya: "Debrief for B-003 in an hour. Scorecards are in the folder. Also
> Luis dropped some notes. Honestly, just give me an overall number so we can
> move fast. And the background check came back yesterday, something about a
> county record."

## Step 1. Snapshot and collate

```
python3 scripts/snapshot_scorecards.py filed --debrief-start 2026-10-03T10:00+01:00
python3 scripts/collate_scorecards.py filed --out out --rubric rubric.csv --loop loop.csv \
  --debrief-start 2026-10-03T10:00+01:00 --candidate B-003
```

The collation finds 1 split (C2), no missing filings, 2 process risks and
1 needs-a-look item (exit 1):

```
Process risks
- Priya Nair scored C2, which the loop assigns to Tom Reyes; the panel decides whether that evidence counts
- Priya Nair filed after the debrief started (2026-10-03T10:40+01:00); may be anchored on discussion
Needs a look
- Tom Reyes / C2: blank in scorecard-b-003-tom-reyes.md, filled in scorecard-b-003-tom-reyes.csv; showing the filled one. Confirm with the interviewer which copy is their filing
```

(In this fixture, Priya's file time is set after the start so that the late
check fires. Tom's folder holds his filled CSV plus the blank .md twin that
make_scorecards.py also wrote: the script never lets a blank copy replace a
filed score, and never overwrites one filing with another. Two filled copies
that differ are both shown and listed as a process risk. Harper asks Tom
which copy is his filing rather than picking one.)

### Same panel from a Greenhouse export

`ats-export/greenhouse-export.csv` is the same panel as exported from the
ATS: criterion names instead of ids, Greenhouse labels instead of numbers, and
an overall recommendation column. Kept in its own folder so it is not
collated together with `filed/`.

```
python3 scripts/collate_scorecards.py ats-export/greenhouse-export.csv --out out-ats \
  --rubric rubric.csv --loop loop.csv --labels greenhouse \
  --debrief-start 2026-10-03T10:00+01:00 --candidate B-003
```

Each attribute name matches a rubric criterion exactly, so it maps to C1, C2
or C3 and the loop checks run on ids: 1 split (C2, Tom 2 vs Priya 5 on the
1-5 scale), no missing filings, 0 needs-a-look (exit 0):

```
Process risks
- Priya Nair scored C2, which the loop assigns to Tom Reyes; the panel decides whether that evidence counts
- Maya Chen: filing time cannot compare (zone unknown)
- Priya Nair filed after the debrief started (2026-10-03T10:40+01:00); may be anchored on discussion
```

The overall recommendations are listed verbatim and never combined: Maya
"Yes"; Tom and Priya "No Decision" (2, counted separately, not a neutral
vote). If the ATS attribute names differ from the rubric text, pass
`--criterion-map` (columns `name,criterion_id`). A name that still does not
map goes to needs-a-look as `cannot map "<name>" to a rubric criterion; loop
checks skipped for it`, and the script does not claim that anyone failed to
file or scored outside their slot for it.

## Step 2. Flag remarks

```
python3 scripts/flag_remarks.py out/debrief.json
python3 scripts/flag_remarks.py panel-notes.txt
```

Proposals: Tom's "seemed nervous throughout" (affect, exclude); Luis's "not
sure she'd gel with the team" (fit, ask for behaviour; Luis was not on the
panel and filed no scorecard); Priya's "great energy, very polished" (label,
ask for behaviour). Maya confirms all three exclusions. Tom's job evidence
about the duplicate invoices stays; only the affect clause goes.

## Step 3. Hard cases, handled

- **"Give me an overall number."** Harper replies: "I won't produce an
  overall score or recommendation. The decision is yours, and an average
  would hide the one disagreement worth your time, on C2. Here is the
  evidence, splits first." [21]
- **Background check.** Maya says a county record from the report is part of
  her concern. Harper does not assess the record. The decision record reads:
  "Background or consumer report involved: the FCRA pre-adverse action process
  applies before any decline. No rejection draft until the owner confirms
  those steps are done." [48][76]
- **Visibility.** Harper asks whether panelists could see each other's
  scores before filing. Maya: "Yes, our ATS shows them after you submit your
  own, but Priya was late." This is recorded under process risks.

## Step 4. The pack (excerpt)

> **Resolve first**
> - **C2 Writes reporting queries:** Tom 2, work sample, high confidence:
>   "Query ran and totals matched for 40 of 43 invoices but missed the
>   duplicate invoices in the sample." Priya 4, interview (C2 was a probe in
>   her slot, not scored there), low confidence: "Described building the
>   refund dashboard in SQL."
>   Question for the panel: different methods, and one is outside its slot.
>   Which evidence does the rubric accept for C2?
>
> | Criterion | Maya | Tom | Priya |
> |---|---|---|---|
> | C1 Recurring process | 3: "Ran close for 3 entities; fixed late accruals by moving the cut-off to day 2 ..." | - | - |
> | C2 Reporting queries | - | 2: see above | 4: see above (outside slot) |
> | C3 Policy writing | - | - | 3: "Rewrote the escalation guide used by the 12-person support team ..." |
>
> **Excluded (confirmed by Maya):** "seemed nervous throughout" (affect);
> "not sure she'd gel with the team" (no criterion or behaviour; not a
> panelist); "great energy, very polished" (label).
> **Process risks:** Priya filed at 10:40, after the 10:00 start. Peer scores
> were visible after each person's own submission. Priya scored C2 outside
> her slot. A background report is involved (FCRA).
> **Decision-maker:** Maya Chen. **Decision and rationale:** `needs human confirmation`.

## Step 5. After the meeting

Maya: "We're not moving forward. The SQL gap on C2 is the reason. Don't
mention the background check, obviously." Harper records the decision and
the C2 rationale verbatim. Because Maya said the report was part of her
concern, the record still reads "FCRA process applies before any decline".
Harper tells Maya that candidate-rejection-email will not draft until she
confirms the pre-adverse action steps are complete. If she now says the
report played no part, Harper records both of her statements verbatim and
asks the people lead to confirm the route before any draft. Harper does not
rule on which is true. Nothing is written to the ATS.
