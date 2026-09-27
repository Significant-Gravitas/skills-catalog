---
candidate: <Candidate name>
role: <role-slug>
interviewer: <Interviewer name>
slot: <slot number>
competencies: <M-id(s) owned>
filed_at: <YYYY-MM-DDTHH:MM+HH:MM>
---

<!-- The format scripts/collate_scorecards.py reads. It matches
     interview-kit-design's templates/scorecard-1to5.md. One file per
     interviewer in ~/workspace/hiring/debriefs/<role-slug>/<candidate-slug>/scorecards/.
     A scorecard pasted in chat, mailed, or exported from an ATS is saved in
     this shape first (quote the interviewer's words exactly; never fill a
     missing rating). An ATS CSV export can be read directly instead: columns
     candidate, interviewer, competency_id, competency, rating, evidence,
     recommendation, reason, filed_at. -->

## Ratings

| id | competency | rating | evidence |
| --- | --- | --- | --- |
| M<id> | <competency> | <1-5 or not assessed> | "<interviewer's evidence, verbatim>" |

## Overall

recommendation: <hire | no hire | no decision>
reason: <verbatim>
