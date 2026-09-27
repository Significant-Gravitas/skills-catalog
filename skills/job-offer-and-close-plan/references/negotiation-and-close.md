# Pre-close, counters and the close plan

Most of this file is **practitioner judgement (unsourced)** and says so.
Sourced lines carry the dossier number (references/sources.md).

## Contents
1. Why the close matters
2. Pre-close questions
3. Counters: the comparison first
4. Paired gives
5. Competing offers
6. Close plan tracks and dates
7. Follow-ups and the answer-by check
8. After the signature

## 1. Why it matters

Offer strategy and closing appears in 11 of 17 recruiter postings sampled in
2026 [1]. 61% of job seekers report being ghosted after an interview [80]: a
close plan with dated, single-owner tracks is how nobody waits in silence.

## 2. Pre-close (before anything is composed)

Practitioner judgement (unsourced):
- What matters to them: comp, growth, team, mission, flexibility. Ask
  directly; record their words. Never build on assumed motivations.
- Other processes: "Where else are you in process, and how far along?" and
  "What would make you choose one over the other?" Ask early and again
  before the offer.
- Expectations: "What are you hoping for in base?" Never "What do you earn
  now?" (references/pay-history-and-transparency.md).
- Timing: their notice period in their words, and any date they are holding.
- Set the answer-by expectation before the offer lands (default 24-48
  hours after the written offer - default, confirm with the owner).
- Line up the hiring manager's follow-up call for right after the verbal.

## 3. Counters

1. Put the comparison first: offer as extended vs the candidate's ask vs
   the proposal, one evidence line each (`offer_math.py --offer-* --ask-*
   --proposal-*`).
2. Then the paired give and the walk-away line from the band.
3. Above-band ask: escalate to the band approver. Never counter above band;
   never hint that the band can move.
4. Log every concession in counter-log.csv with who approved it and when.
   The log is append-only; a changed decision is a new row.

## 4. Paired gives (practitioner judgement, unsourced)

A give is traded, not conceded: more base for no signing bonus; an earlier
start for a signing bonus; a later start for the same terms. Each give sits
inside the band and has an approver before it is mentioned.

## 5. Competing offers

Record in the candidate's words and label: "competing offer, EUR 115,000
base [candidate's words, unverified]". Never ask for the letter, never call
the other company, never treat it as FACT. Shape the plan on what you can
verify: the band, the approver's give, the dates.

## 6. Close plan tracks

One owner and one date with timezone per track. The owner is an internal
named person: never the assistant, never the candidate (the candidate goes
in the notes; an internal person owns chasing their answer and signature).
Tracks:
approvals, verbal offer, letter sent, questions answered, answer-by,
signature, first-week hand-off. Add tracks for contingencies in their legal
order (disclosure before a background check; medical exam only after
acceptance - references/contingency-order.md). Run `scripts/close_plan.py`
(with `--candidate` and `--assistant`) to check single internal owners,
zones, dates, contingency order and what is due.

## 7. Follow-ups

Each follow-up carries the open question, the agreed deadline and who to
talk to (templates/close-messages.md). The answer-by check is scheduled with
`run_capability(id="tool:schedule_followup", …)` on the owner's yes, as the
last action of the turn. An offer past its answer-by date is a stall the
morning brief and the stall sweep also pick up.

## 8. After the signature

Hand off to the first-week owner with the start date and the team; onboarding
is theirs. With Linear connected and the owner's yes, file one issue with
role-level details only (no comp, no personal data).
