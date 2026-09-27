# Pipeline read (INTERNAL: names candidates; share only via share_safe.py), as of 2026-10-09 (window 2026-10-03 to 2026-10-09, prior 2026-09-26 to 2026-10-02)
> No entry dates (applied_on / sourced_on) in the tracker: the funnel covers every row in the tracker, not the window. Window comparisons come from snapshots only.
> Some entry dates come from the first snapshot a person appeared in; they are used only for time to hire, labelled INFERENCE (accurate to the snapshot interval).
> Prior column = previous snapshot of 2026-10-02 (same all-rows basis).
> SMALL SAMPLE: 16 people in the cohort, below the minimum of 30 (preferences.md). Read every rate as directional, not truth.

## Product Designer

| Stage | Reached | Prior | Conversion to next |
|---|---|---|---|
| entered | 5 [FACT, n=5] | 3 | 80.0 [FACT, n=5] |
| screened | 4 [FACT, n=5] | 2 | 25.0 [FACT, n=4] |
| in_loop | 1 [FACT, n=5] | 0 | 0.0 [FACT, n=1] |
| offer | 0 [FACT, n=5] | 0 | - [FACT, n=0] |
| hired | 0 [FACT, n=5] | 0 |  |

Biggest loss: screened->in_loop, closed there: 1 (conversion 25.0%); top reasons: portfolio lacks research work (1) [FACT]
Pipeline now: entered 1, screened 2, in_loop 1, rejected 1
Time to hire: - [UNKNOWN, n=0]. Time to fill: - [UNKNOWN, n=0]. Time to slate: - [UNKNOWN].
Offer acceptance: - [UNKNOWN, n=0]; offers open: 0.
Source mix: {'inbound': 3, 'sourced': 2}. Source of hire: none in window.
Reasons - we rejected: [('portfolio lacks research work', 1)]; they withdrew/declined: [].
Req age (open req): - [UNKNOWN] days (no opened_on in roles.csv; ask the owner when the req opened).
Stalled: 2 [FACT, n=4] (days in stage over the bar (5 business days))
- Leo Brandt (Recruiter screen): 11 days, owner Sofia, waiting on Ana Costa
- Maya Chen (Sourced): 8 days, owner Sofia, waiting on Maya Chen

## Senior Backend Engineer

| Stage | Reached | Prior | Conversion to next |
|---|---|---|---|
| entered | 11 [FACT, n=11] | 7 | 45.5 [INFERENCE, n=11] |
| screened | 5 [FACT, n=11] | 4 | 40.0 [INFERENCE, n=5] |
| in_loop | 2 [FACT, n=11] | 1 | 50.0 [INFERENCE, n=2] |
| offer | 1 [FACT, n=11] | 0 | 0.0 [INFERENCE, n=1] |
| hired | 0 [FACT, n=11] | 0 |  |

Biggest loss: entered->screened, closed there: 2 (conversion 45.5%); top reasons: no billing evidence (1); declined on location (1) [FACT]
Pipeline now: entered 3, screened 2, in_loop 1, offer 1, rejected 3, withdrew 1
Time to hire: - [UNKNOWN, n=0]. Time to fill: - [UNKNOWN, n=0]. Time to slate: - [UNKNOWN].
Offer acceptance: - [UNKNOWN, n=0]; offers open: 1.
Source mix: {'sourced': 6, 'inbound': 4, 'referral': 1}. Source of hire: none in window.
Reasons - we rejected: [('no billing evidence', 3)]; they withdrew/declined: [('declined on location', 1)].
Req age (open req): - [UNKNOWN] days (no opened_on in roles.csv; ask the owner when the req opened).
Stalled: 2 [FACT, n=7] (days in stage over the bar (5 business days))
- Aisha Bello (Recruiter screen): 7 days, owner Sofia, waiting on Sofia
- Tom Becker (Onsite): 6 days, owner Sofia, waiting on Lena Ortiz

## All roles

| Stage | Reached | Prior | Conversion to next |
|---|---|---|---|
| entered | 16 [FACT, n=16] | 10 | 56.2 [INFERENCE, n=16] |
| screened | 9 [FACT, n=16] | 6 | 33.3 [INFERENCE, n=9] |
| in_loop | 3 [FACT, n=16] | 1 | 33.3 [INFERENCE, n=3] |
| offer | 1 [FACT, n=16] | 0 | 0.0 [INFERENCE, n=1] |
| hired | 0 [FACT, n=16] | 0 |  |

Biggest loss: screened->in_loop, closed there: 2 (conversion 33.3%); top reasons: no billing evidence (1); portfolio lacks research work (1) [FACT]
Pipeline now: entered 4, screened 4, in_loop 2, offer 1, rejected 4, withdrew 1
Time to hire: - [UNKNOWN, n=0]. Time to fill: - [UNKNOWN, n=0].
Offer acceptance: - [UNKNOWN, n=0]; offers open: 1.
Source mix: {'sourced': 8, 'inbound': 7, 'referral': 1}. Source of hire: none in window.
Reasons - we rejected: [('no billing evidence', 3), ('portfolio lacks research work', 1)]; they withdrew/declined: [('declined on location', 1)].
Stalled: 4 [FACT, n=11] (days in stage over the bar (5 business days))
- Leo Brandt (Recruiter screen): 11 days, owner Sofia, waiting on Ana Costa
- Maya Chen (Sourced): 8 days, owner Sofia, waiting on Maya Chen
- Aisha Bello (Recruiter screen): 7 days, owner Sofia, waiting on Sofia
- Tom Becker (Onsite): 6 days, owner Sofia, waiting on Lena Ortiz

## Quality
Early attrition: - [UNKNOWN, n=0] 
Cost per hire: - [UNKNOWN] - no cost lines supplied by the owner

## Sourcing and outreach
- Senior Backend Engineer: 4 [FACT] added; first three by recorded tier: Ines Duarte (tier 1) https://example.org/ines-billing-talk; Clara Voss (tier 1) https://example.org/clara-blog; Hugo Lam (tier 2) https://example.org/hugo-repo
Outreach: 1 [FACT] contacted; reply types {'no reply': 1}.
- follow-up due: Mia Keller (Senior Backend Engineer): touch 3 due 2026-10-09 (today)
- follow-up due: Maya Chen (Product Designer): touch 4 due 2026-09-30, 7 working days late
Cadence: touches on day 2,5,8 after the first note, business days, first note + 3 follow-ups (passive-candidate-outreach's rule; drafts come from that skill).

## Hygiene (each needs one fixing action)
- missing owner: 1: line 12: Eva Novak (Senior Backend Engineer)
- closed no furthest stage: 1: line 12: Eva Novak
- scorecards overdue: 1: Tom Becker (Senior Backend Engineer) 2026-10-05: scorecards '2/3'
- no next step: 2: Rui Santos (Senior Backend Engineer, Sourced); Maya Chen (Product Designer, Sourced)
- prospects excluded from applicant counts: 1

## Next week's interview load
- 2026-10-13: Ana Costa 1, Joana Reis 1, Dev Rao 2, Sam Lee 1
- 2026-10-15: Lena Ortiz 1

Settings: min_sample=30 (preferences.md); stalled_bar=5 business days (preferences.md); touch_limit=3 (preferences.md); attrition_window_days=90 (default - confirm with the owner); heavy_day_per_interviewer=3 (default - confirm with the owner); outreach_cadence=2,5,8 (default - confirm with the owner); outreach_day_kind=business (default - confirm with the owner)
