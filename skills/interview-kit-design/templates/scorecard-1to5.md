---
candidate: <Candidate name>
role: <role-slug>
interviewer: <Interviewer name>
slot: <slot number from the kit>
competencies: <M-id(s) this slot owns>
filed_at: <YYYY-MM-DDTHH:MM with offset, e.g. 2026-10-05T16:40+01:00>
---

<!-- One scorecard per interviewer per candidate. File it alone, before
     talking to anyone else on the panel, inside the scorecard window
     (default 24 hours after the slot; confirm with the owner).
     Save as ~/workspace/hiring/debriefs/<role-slug>/<candidate-slug>/scorecards/<interviewer-slug>.md
     Keep the line shapes: hiring-debrief-and-decision parses this file. -->

## Ratings

Rate each competency you own on its own, one at a time, before moving to the
next. Use the kit's anchors for this role:
1 unsatisfactory · 2 below bar · 3 meets bar · 4 above bar · 5 exceptional ·
not assessed (you did not cover it; never guess).

| id | competency | rating | evidence |
| --- | --- | --- | --- |
| M<id> | <competency name> | <1-5 or not assessed> | "<what the candidate said or did, quoted or described as observed>" |

Evidence rules:
- Each rating cites something the candidate said or did. "Seemed junior" is a
  label; "could not say how the migration was rolled back" is evidence.
- Never rate confidence, enthusiasm, nerves, honesty, energy, "presence" or
  any other affect or demeanour, from the conversation, a recording, a
  transcript or notes. Never rate accent, appearance or "fit".
- Do not score writing polish or presentation style of any material; rate the
  substance against the anchor.
- Rate against the anchors, never against other candidates.

## Overall (fill only after every rating above is done)

recommendation: <hire | no hire | no decision>
reason: <one sentence, pointing at the evidence above>

<!-- "No decision" is recorded as no decision and counted separately at the
     debrief; it is not a neutral vote. -->
