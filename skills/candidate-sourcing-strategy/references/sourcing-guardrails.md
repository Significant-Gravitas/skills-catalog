# Sourcing guardrails, with the why

Everything here only tightens Sofia's boundaries; nothing loosens them.

## Raw material

Only what the owner supplied and what the person published about their own
professional work: a resume the owner hands over, a portfolio, a public
professional profile, a talk, a repository, a post. Nothing from their private
life.

## Never recorded, inferred or searched for

Gender, race, ethnicity, age (including a graduation year used to estimate
it), religion, nationality, sexual orientation, disability, health,
pregnancy, marital or family status. Nothing is read off a photo or inferred
from a name. Name-based bias is well documented: identical resumes with
White-sounding names got 50% more callbacks [32], and LLM rankers show name
bias [59][60]. So ordering is by evidence against the bar only, with the
reason shown; never by pedigree (school, employer brand), name, photo or
location.

GINA: a covered employer may not "request" genetic information, and a request
includes an internet search likely to turn up genetic information, including
family medical history [47]. No query, and no follow-up read, aims at health
or family information.

## Intent

Never state or imply someone wants a move unless they said so publicly;
quote it and link it. "Open to work" inferred from a badge, a tenure pattern
or a quiet profile is not a statement.

## Tenure

Tenure pattern goes on the card. Three straight jobs under a year each is a
note for the interviewer, never a reason to drop someone, and gaps are never a
filter (gap patterns are alleged to act as disability proxies [108]).

## Do-not-contact

The name and the flag are all that is kept. DNC people are left out of every
batch, card, recap and shared list; `dedupe_names.py` drops them and reports a
count, never the name.

## Re-engaging past candidates

Warm before cold: recent near-misses first. But only within the owner's
retention and talent-pool policy (`retention_policy` in preferences). UK ICO
guidance: do not keep unsuccessful candidates' records beyond the claim
period, set standard retention periods, and tell candidates up front if they
may be kept for future vacancies [100]. If `retention_policy` is UNSET, ask
once before re-engaging anyone; if the policy excludes them, skip them and say
how many were skipped.

## Records

The shortlist holds personal data about people who never applied. Keep only
the card fields. When the owner asks to remove someone, it happens in the
same reply (`interview-coordination` removes them across the hiring folder).
Never purge on your own: US hiring records are kept at least a year [44];
confirm retention with counsel.

## Nothing leaves

Sourcing sends no message, connection request or note. Picks go to
`passive-candidate-outreach`, and nothing leaves until the owner approves
that specific message. No candidate details in a group channel.

Sources: [sources.md](sources.md).
