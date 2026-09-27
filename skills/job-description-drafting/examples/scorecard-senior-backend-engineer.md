---
role: Senior Backend Engineer, Billing
role_slug: senior-backend-engineer
version: 1
status: approved
approved_by: Lena Ortiz
approved_on: 2026-09-21
approval_quote: "Yes, that's the bar"
hiring_manager: Lena Ortiz
reports_to: Lena Ortiz
location_terms: Remote from the EU within CET +/- 1 hour, or from the US with a daily 15:00-17:00 CET overlap; on-call one week in five
---

# Senior Backend Engineer, Billing — role scorecard

<!-- Fictional. Copy of the approved scorecard from role-intake-and-scorecard, used as the input to scripts/mirror_check.py in the worked example. -->

## Mission

Billing is where our revenue lives and nobody owns it. This hire makes renewals boring.

## Year-one outcomes

- O1: Own the billing service's reliability and lead its on-call rotation.
  - source: FACT "Billing pages us twice a week and nobody owns it" (Lena, intake call 2026-09-21 14:00 Europe/Lisbon)
- O2: Cut failed renewals.
  - source: FACT "Failed renewals are the number I get asked about" (Lena, same call)

## Must-haves

- M1: Has run on-call for a service with paying customers.
  - evidence_method: structured interview, "walk me through an incident you owned end to end"; public runbook if any
  - agree_test: the answer names a real incident, their role, and what changed after
  - what_fails_without_it: O1 needs someone who can lead the rotation from week one
- M2: Has shipped a schema migration on a live Postgres database without downtime.
  - evidence_method: deep-dive interview (Ana Costa); public write-up if any
  - agree_test: they can describe the migration steps and the rollback plan they used
  - what_fails_without_it: the billing schema must change twice this year with no maintenance window
- M3: Has written design docs other engineers acted on.
  - evidence_method: work sample (a doc they wrote, public or shared) reviewed against the design-doc anchors
  - agree_test: the doc states a decision, the options, and who acted on it
  - what_fails_without_it: billing changes touch three teams and ship by design review
- M4: Has debugged payment or billing flows end to end.
  - evidence_method: billing debugging exercise (60 min, Dev Rao)
  - agree_test: reaches root cause of the seeded webhook retry bug or explains the next step correctly
  - what_fails_without_it: O2 is a debugging problem first

## Nice-to-haves

- N1: Go in production.
- N2: Stripe webhooks.

## Disqualifiers

- D1: "Won't do on-call."
  - fairness_check: job-related, kept (O1 requires it)

## Cut or rewritten

- "5+ years backend experience" -> M1 (the outcome behind it)
- "Culture fit" -> cut; no job-related behaviour underneath it
- "Native English speaker" -> M3 covers the writing; cut
- "Local to Lisbon, postcode 1000-1200" -> location_terms: remote (EU within CET +/- 1 hour, or US with a 15:00-17:00 CET overlap)

## Benchmark

- benchmark_person: Dev Rao (internal)
- B1: Owned an outage post-mortem to closure, including the follow-up fixes.
- B2: Wrote the migration runbook the team still uses.
- B3: Reviews other teams' designs in writing.
- B4: Debugged a payment-provider integration from logs alone.
- dropped_as_incidental: his school, his previous employer, his editor

## Where the people are

- target_companies_file: target-companies.csv (the example CSV is cut down to 3 rows; the default map holds 10 to 20)
- boundaries: direct competitors fair game (Lena, FACT); Paywise is a customer, off limits
- title_variants: Backend Engineer; Senior Software Engineer, Payments; Billing Engineer; Platform Engineer; Site Reliability Engineer; Payments Infrastructure Engineer; Revenue Engineer (dark matter); Monetisation Engineer (dark matter)
- evidence_sources: GitHub and package registries; PGConf and FOSDEM talks; company engineering blogs

## Hiring plan

| Stage | Length | Interviewer | Tests |
|---|---|---|---|
| Screen | 30 min | Sofia's owner (recruiter) | M1 |
| Knockout competency | 60 min | Dev Rao | M4 |
| Deep-dive | 60 min | Ana Costa | M2, M3 |
| Hiring-manager close | 30 min | Lena Ortiz | D1, O1 |

- slate_target: UNKNOWN (asked)
- fill_date: UNKNOWN (asked)
- compensation: set by Lena and finance; no figure proposed here
- referral_only: no
- jurisdiction_flags: EU hiring; recruitment AI is high-risk under the AI Act and GDPR Art. 22 applies; confirm with counsel

## Change log

- v1 2026-09-21: created from Lena's intake call and old posting.
- v1 2026-09-21: approved by Lena Ortiz.
