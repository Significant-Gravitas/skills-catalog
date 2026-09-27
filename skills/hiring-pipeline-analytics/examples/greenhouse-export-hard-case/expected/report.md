# Pipeline read (INTERNAL: names candidates; share only via share_safe.py), as of 2026-10-02 (window 2026-07-01 to 2026-09-30)
> 1 rows have no entry date and are outside every window (UNKNOWN).
> SMALL SAMPLE: 9 people in the cohort, below the minimum of 30 (default - confirm with the owner). Read every rate as directional, not truth.

## Support Specialist

| Stage | Reached | Prior | Conversion to next |
|---|---|---|---|
| entered | 9 [FACT, n=9] | - | 66.7 [INFERENCE, n=9] |
| screened | 6 [FACT, n=9] | - | 100.0 [INFERENCE, n=6] |
| in_loop | 6 [FACT, n=9] | - | 83.3 [INFERENCE, n=6] |
| offer | 5 [FACT, n=9] | - | 60.0 [INFERENCE, n=5] |
| hired | 3 [FACT, n=9] | - |  |

Biggest loss: offer->hired, closed there: 1 (conversion 60.0%); top reasons: Declined offer - compensation (1) [FACT]
Pipeline now: entered 1, screened 1, in_loop 1, offer 1, hired 3, declined_offer 1, rejected 2
Time to hire: median 37.5, min 34, max 41 [FACT, n=2]. Time to fill: median 66, min 50, max 71 [INFERENCE, n=3]. Time to slate: - [UNKNOWN].
Offer acceptance: 75.0 [FACT, n=4]; offers open: 1.
Source mix: {'Referral': 3, 'Company Website': 3, 'Indeed': 2, 'LinkedIn (Prospecting)': 1}. Source of hire: {'LinkedIn (Prospecting)': 1, 'Referral': 1, 'Company Website': 1}.
Reasons - we rejected: [('No SaaS support experience', 1)]; they withdrew/declined: [('Declined offer - compensation', 1), ('Withdrew - took another job', 1)].
Req age (open req): 109 [FACT] days (today - opened_on (roles.csv), open req).
Stalled: 0 [UNKNOWN, n=4] (days in stage over the bar (5 business days); days in stage unknown for 4)

## All roles

| Stage | Reached | Prior | Conversion to next |
|---|---|---|---|
| entered | 9 [FACT, n=9] | - | 66.7 [INFERENCE, n=9] |
| screened | 6 [FACT, n=9] | - | 100.0 [INFERENCE, n=6] |
| in_loop | 6 [FACT, n=9] | - | 83.3 [INFERENCE, n=6] |
| offer | 5 [FACT, n=9] | - | 60.0 [INFERENCE, n=5] |
| hired | 3 [FACT, n=9] | - |  |

Biggest loss: offer->hired, closed there: 1 (conversion 60.0%); top reasons: Declined offer - compensation (1) [FACT]
Pipeline now: entered 1, screened 1, in_loop 1, offer 1, hired 3, declined_offer 1, rejected 2
Time to hire: median 37.5, min 34, max 41 [FACT, n=2]. Time to fill: median 66, min 50, max 71 [INFERENCE, n=3].
Offer acceptance: 75.0 [FACT, n=4]; offers open: 1.
Source mix: {'Referral': 3, 'Company Website': 3, 'Indeed': 2, 'LinkedIn (Prospecting)': 1}. Source of hire: {'LinkedIn (Prospecting)': 1, 'Referral': 1, 'Company Website': 1}.
Reasons - we rejected: [('No SaaS support experience', 1)]; they withdrew/declined: [('Declined offer - compensation', 1), ('Withdrew - took another job', 1)].
Stalled: 0 [UNKNOWN, n=4] (days in stage over the bar (5 business days); days in stage unknown for 4)

## Quality
Early attrition: left 1, eligible 3, pct 33.3 [FACT, n=3] {'role not as described': 1}
Cost per hire: 2333.33 [INFERENCE, n=3] - (internal + external) / hires, standard variant, EUR; includes owner estimates: recruiter time (owner estimate supplied by finance)
- cost line: job board (Indeed) Q3 (external) 1,800.00
- cost line: referral bonuses Q3 (internal) 1,000.00
- cost line: recruiter time (owner estimate supplied by finance) (internal) 4,200.00 [ESTIMATE]

## Sourcing and outreach
Outreach: 0 [FACT] contacted; reply types {}.

## Hygiene (each needs one fixing action)
- closed no furthest stage: 2: line 6: Sana Iqbal; line 13: Luis Ortega
- missing owner: 1: line 8: Chen Wu (Support Specialist)
- bad date: 1: line 11: entry '03/04/2026'
- duplicates: 1: chen wu / support specialist x2 (counted once: furthest stage kept; owner merges)
- zero or negative durations: 1: Marta Silva: 0 days
- evergreen or multi hire roles: 1: Support Specialist
- no next step: 4: Ivo Petrov (Support Specialist, Offer); Chen Wu (Support Specialist, Application Review); Ola Nordmann (Support Specialist, Phone Interview); Aya Tanaka (Support Specialist, Face to Face)
- prospects excluded from applicant counts: 1

## Next week's interview load
- none booked

Settings: min_sample=30 (default - confirm with the owner); stalled_bar=5 business days (default - confirm with the owner); touch_limit=3 (default - confirm with the owner); attrition_window_days=90 (default - confirm with the owner); heavy_day_per_interviewer=3 (default - confirm with the owner); outreach_cadence=2,5,8 (default - confirm with the owner); outreach_day_kind=business (default - confirm with the owner)
