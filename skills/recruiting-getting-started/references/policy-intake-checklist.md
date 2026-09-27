# Policy intake checklist

What to ask at kickoff, what each answer can trigger, and who confirms. Harper
flags; Harper never advises. Every flag goes to the people lead or counsel with
"may apply; confirm with counsel". The law changes: every line is dated, and
the data rows in `jurisdiction-triggers.csv` carry a checked-on date. Content
as of 2026-09-27 (dossier date). Source numbers refer to `sources.md`.

## Contents

1. Questions to ask
2. What `policy_flags.py` checks
3. Things Harper never does, whatever the answers
4. How to word a flag

## 1. Questions to ask

| Ask | Why it matters | Record as |
| --- | --- | --- |
| Where will the role be posted and hired? | Pay-transparency posting rules [56][57] and AI-screening rules [52][72][71][53] depend on location. | "Hiring jurisdictions" in the plan |
| Does any AI tool screen, rank or interview candidates? | NYC, Illinois, California and EU rules attach to the tool, not to the recruiter [52][72][71][109]. | Policy row "AI tools used in screening or interviews" |
| What is your policy on candidates' own AI use? | Candidates need to know what is allowed at each stage; one employer publishes "draft yourself, then refine with AI" for applications and "no AI in live interviews unless told" [104]. | Policy row "Candidates' AI use" |
| Accommodation route | Every posting and interview note names it; ability questions use "with or without reasonable accommodation" [35][46]. | Policy row "Accommodation route" |
| Data retention and talent pool | US: at least 1 year for hiring records [44]. UK: no longer than needed, with notice before keeping a talent pool [100]. | Policy row "Data retention and talent pool" |
| Is the company a US federal contractor? | Section 503 record-keeping applies to contractors; EO 11246 duties end 2026-10-26 [116][98][50]. | Policy row "US federal contractor" (yes / no), read by step 5 as `--federal-contractor` |
| Background checks | US FCRA steps before any decline based on a report [48][76]. | Policy row "Background checks" |
| Federal contractor? | Section 503 record-keeping [116]; EO 11246 duties end 2026-10-26 [98][50]. | Open question for the people lead if unknown |
| Required posting text | Legal or brand text that must appear. | Policy row "Required posting text" |

## 2. What `policy_flags.py` checks

Regions it recognises from the location text: NYC, Illinois, California,
Colorado, other US (state codes such as ", TX", full state names such as
"Texas", and "US", "U.S." or "USA"), UK, EU member states and a few EU cities.
A bare "New York" is flagged as both NYC and US, with a note asking whether it
means the city or the state. An unrecognised location prints "location not
recognised by this checklist"; a recognised one with no matching row prints
"recognised as ..., but no row in this checklist applies there"; both ask the
people lead. Remote roles print a note asking which countries or states the
company will hire in. The script's patterns are heuristics; the owner's stated
jurisdictions win.

| Region | Condition | Flag in short | Sources |
| --- | --- | --- | --- |
| US | always | keep hiring records at least 1 year | [44] |
| US | always | salary-history bans; never ask for past pay | [56][75] |
| US | always | other states and cities also require pay in postings; only CA and CO are covered here | [75] |
| US | federal contractor | Section 503 records; EO 11246 duties end 2026-10-26 | [116][98][50] |
| US | background checks | FCRA disclosure, pre-adverse and adverse action | [48][76] |
| NYC | AI screening | Local Law 144: bias audit under 1 year old, public summary, notice 10 business days ahead | [52][69] |
| Illinois | AI screening | HB 3773: notice; no discriminatory effect; ZIP code as proxy | [72] |
| Illinois | AI video interviews | notice, explanation, consent, deletion within 30 days of request | [55] |
| California | always | pay scale in postings (15+ employees); no salary history | [56] |
| California | AI screening | FEHA automated-decision rules from 2025-10-01; 4-year records; agent liability | [71] |
| Colorado | always | closed pay range, benefits, how and when to apply | [57] |
| Colorado | AI screening | SB 26-189 (from 2027-01-01): notice before automated decision tech is used, disclosure after an adverse outcome, 3-year records | [120] |
| EU | AI screening | AI Act high-risk (Annex III 4(a)); applies from 2027-12-02 | [53][109][119] |
| EU | AI screening | GDPR Art. 22 solely automated decisions | [54] |
| EU | AI video interviews | emotion inference prohibited | [73][53] |
| UK | always | no health questions before an offer (s.60) | [58] |
| UK | AI screening | UK GDPR Arts. 22A-22D (DUAA 2025): safeguards for significant decisions with no meaningful human involvement | [121] |
| UK | talent pool | retention limit and prior notice | [100] |

A condition answered "unknown" still prints the flag, prefixed with "If ...",
so the owner sees what the answer would change.

Context the owner may ask about (do not volunteer as advice): NYC's own audit
of Local Law 144 enforcement found far more potential non-compliance than the
city had recorded [70]; federal AI guidance was withdrawn in 2025 but the
underlying statutes still apply [43][68].

## 3. Things Harper never does, whatever the answers

- States that a law applies or does not apply. It says "may apply; confirm with counsel".
- Supplies a pay figure or estimates a band.
- Advises deleting or keeping records beyond what the owner's policy says.
- Writes a policy on the owner's behalf. A missing policy is `OPEN` with an owner.

## 4. How to word a flag

Good: "Hiring in Denver: Colorado postings may need a closed pay range,
benefits and an apply-by route [57]. Pay is OPEN. People lead to confirm."

Bad: "Colorado law requires you to post $85-95k." (a legal conclusion and an
invented figure)
