# Worked example: Senior Backend Engineer intake, with a hard case

Fictional throughout: hiring manager Lena Ortiz, Northwind Tools. The saved
result is [scorecard-senior-backend-engineer.md](scorecard-senior-backend-engineer.md)
with [target-companies-senior-backend-engineer.csv](target-companies-senior-backend-engineer.csv);
both pass `scripts/scorecard_check.py` with 0 errors.

## 1. Gather

- `cat ~/workspace/hiring/roles/senior-backend-engineer/scorecard.md` -> none. New role.
- Granola connected: `find_capability("granola meeting notes")` -> list meetings
  from the last 14 days matching "Lena" or "backend". Two found; the owner
  confirms "Backend hire intake, 2026-09-21 14:00". Sofia reads only that one.
- Drive: the old posting "Backend Engineer 2024.docx" is read for its
  requirements list.

## 2. What the HM said, and the hard case

From the call (FACT, quoted): "Billing pages us twice a week and nobody owns
it." "Failed renewals are the number I get asked about." "I need someone who's
done zero-downtime migrations on Postgres."

And the hard part. Lena, also on the call: "Honestly I want a digital native,
native English speaker, 5+ years, and local; ideally postcode 1000-1200 so they
can come in. Someone who fits the culture. And no job-hoppers."

## 3. The bar in chat (within the minute)

> **Year one:** own the billing service's reliability and cut failed renewals.
> FACT: "Billing pages us twice a week and nobody owns it" (Lena, intake call
> 2026-09-21 14:00 Europe/Lisbon).
>
> **Must-haves**
> - M1. Has run on-call for a service with paying customers. *Tested by:* incident walk-through in the screen.
> - M2. Has shipped a schema migration on a live Postgres database without downtime. *Tested by:* deep-dive (Ana).
> - M3. Has written design docs other engineers acted on. *Tested by:* a doc sample against the design-doc anchors.
> - M4. Has debugged payment or billing flows end to end. *Tested by:* the billing debugging exercise.
>
> **Nice-to-haves:** Go in production; Stripe webhooks.
> **Disqualifier (Lena's words):** "won't do on-call". Fairness check: job-related, kept.
>
> **What I changed from the call, and why**
> - "5+ years" became M1: the outcome behind it. If you want the years floor
>   itself, tell me why in one line and I'll record it verbatim.
> - "Digital native": an age proxy. Cut; M2 and M4 name the actual skills.
> - "Native English speaker": a national-origin proxy. M3 covers the writing
>   the job needs.
> - "Local, postcode 1000-1200": postcode filters work as a proxy and are named
>   in Illinois law as one. Written as a work term instead: remote from the
>   EU within CET +/- 1 hour, or from the US with a daily 15:00-17:00 CET
>   overlap (you said US contractors are welcome). If you need on-site days,
>   tell me how many.
> - "Culture fit": cut. There was no job-related behaviour underneath it. If
>   you mean something specific (e.g. "reviews others' designs in writing"),
>   I'll add that.
> - "No job-hoppers": not a disqualifier. Three straight jobs under a year
>   each becomes a note on the candidate card for the interviewer.
>
> Status: **draft**. Nothing goes to a posting or a screen until you approve.

Lena replies: "Fine on all of it, except I do want 5+ years." Sofia asks once
for the reason. Lena: "I don't really have one; it's what we always write."
Not defended, so the line stays as M1. Sofia records the cut in the scorecard's
"Cut or rewritten" section.

## 4. Benchmark

Lena names Dev Rao (internal). Transfers: owned an outage post-mortem to
closure; wrote the migration runbook; reviews other teams' designs in writing;
debugged a payment-provider integration from logs. Dropped: his school, his
previous employer, his editor of choice.

## 5. Target map

`web_search("subscription billing platform Postgres engineering blog Europe")`
and two more variants. Each company's site is fetched with `web_fetch`;
`link_status` is recorded. One company recalled from memory ("Billsy") has no
site that resolves: dropped, and Sofia says so. Paywise is a customer: kept on
the list as `off limits (customer)` so sourcing skips it.

The CSV beside this example shows 3 of the rows (a cut-down copy, not the
saved size); a real target map keeps the default 10 to 20 companies.

Title variants include two dark-matter ones ("Revenue Engineer",
"Monetisation Engineer"): people doing billing work under names a keyword
search for "billing" would miss.

## 6. Plan

Screen (30, M1) -> billing debugging (60, Dev, M4) -> deep-dive (60, Ana,
M2 and M3) -> hiring-manager close (30, Lena). Each must-have has one stage. Slate target and
fill date: UNKNOWN (asked). Compensation: set by Lena and finance; no figure
proposed. Referral-only: no.

EU hiring, so one line: "Recruitment AI is treated as high-risk in the EU and
decisions solely by automated means are restricted; counsel decides what
applies."

## 7. Save, validate, approve

```
$ cd ~/skills/role-intake-and-scorecard && python3 scripts/scorecard_check.py \
    ~/workspace/hiring/roles/senior-backend-engineer/scorecard.md \
    --companies ~/workspace/hiring/roles/senior-backend-engineer/target-companies.csv
summary: 4 must-haves, 0 errors, 0 warnings, status=draft, version=1
```
Copy delivered with `write_workspace_file(... source_path=...)` and linked.

Lena: "Yes, that's the bar."
```
$ python3 scripts/scorecard_check.py .../scorecard.md --approve "Lena Ortiz" "Yes, that's the bar"
approved: v1 by Lena Ortiz on 2026-09-21
```

Linear is connected; Sofia asks "File 'Req approved: Senior Backend Engineer'
in Linear?" Owner: yes. The create call is held for approval; Sofia hands over
to `job-description-drafting` meanwhile.

## 8. A week later: the rescope

Lena: "Add Kafka as a must-have." Sofia runs `--revise` (v1 kept as
`scorecard-v1.md`, now v2 draft), asks what fails without Kafka (answer:
"nothing yet, it's next year's project"), and proposes it as N3 instead. She
notes that the posting and two sourcing batches were built on v1 and that the
posting must be re-checked if v2 is approved.
