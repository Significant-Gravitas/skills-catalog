# Debrief day

Before the meeting
- [ ] Scorecards in `~/workspace/hiring/debriefs/<role-slug>/<candidate-slug>/scorecards/`.
- [ ] `snapshot_scorecards.py` run; changes and late filings noted.
- [ ] Owner asked whether peer scores were visible before filing; answer recorded.
- [ ] `collate_scorecards.py` run; roll-call and filed share vs the bar.
- [ ] Nudge drafted per late interviewer (via interview-coordination's message shape).
- [ ] `flag_remarks.py` run; every CUT confirmed by a human, every ASK
      turned into a challenge question.
- [ ] Each "[removed #n]" in the brief checked against its flagged word (stderr);
      restored with `--keep n` only when the word is plainly a technical term.
- [ ] Each rating has a one-line INFERENCE; empty ratings flagged with what sits there.
- [ ] Two or three open questions, each with its cheapest fix.
- [ ] Running order: junior first, hiring manager last; minutes weighted to splits.

In the meeting (facilitator notes)
- [ ] Anyone unfiled writes a rating down before discussion starts.
- [ ] One competency at a time; splits first; overall last.
- [ ] Optional silent re-rate after each split (owner's choice).
- [ ] Nobody (including you) breaks a tie or states who to hire.

After the meeting
- [ ] Snapshot re-run before the record is written.
- [ ] Decision in the decision-maker's words; category confirmed with them.
- [ ] A no's stated reason kept verbatim.
- [ ] Background check involved? The record says FCRA applies; no decline drafted.
- [ ] `decision_log.py append` (tracker row only after the owner confirms).
- [ ] `decision_log.py report`: anchors flag raised if over the bar.
- [ ] Brief and record saved and delivered; nothing reached the candidate.
