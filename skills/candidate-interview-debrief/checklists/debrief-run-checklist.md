# Debrief run checklist

Mirror in `TodoWrite`. `[n]` citations are in `references/sources.md`.

## Before the meeting
- [ ] Approved rubric and loop located (`~/workspace/hiring/<role-slug>/rubric.csv`, `loop.csv`).
- [ ] Filed scorecards in `~/workspace/hiring/<role-slug>/scorecards/<candidate-id>/filed/`.
- [ ] `snapshot_scorecards.py` run on arrival; ledger exists.
- [ ] Debrief start time recorded, with its zone.
- [ ] Owner asked whether peer scores were visible before filing; the answer recorded [90].
- [ ] `collate_scorecards.py` run; every needs-a-look item resolved by asking the interviewer, never guessed.
- [ ] `flag_remarks.py` run on the collation and any panel notes; each proposal confirmed or kept by the owner.
- [ ] Background or consumer report involved? Asked, with the answer recorded [48].
- [ ] Pack built from `templates/debrief-pack.md`: splits first, then the evidence table, missing evidence, exclusions, process risks.

## In the meeting (Harper supports; people decide)
- [ ] One criterion at a time, in rubric order [21].
- [ ] Estimate-talk-estimate if the owner chose it [21].
- [ ] New remarks that name no criterion or behaviour are noted for exclusion.
- [ ] The overall view comes last, from the named decision-maker [20].

## After the meeting
- [ ] `snapshot_scorecards.py` re-run; any CHANGED file reported.
- [ ] Decision record filled in the decision-maker's words, or `needs human confirmation`.
- [ ] FCRA routing line present if a consumer report is involved.
- [ ] Nothing written to the ATS without the owner's yes to that exact update.
- [ ] Pack and record saved under `debriefs/<candidate-id>/` and delivered as links.
