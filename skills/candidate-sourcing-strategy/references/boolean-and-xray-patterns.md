# Query craft: variants, dark matter, X-ray and Boolean

## Contents
1. Why several variants
2. Building variants from the scorecard
3. web_search X-ray forms
4. LinkedIn Recruiter Boolean (owner-run)
5. Forbidden query terms
6. Worked query set (Senior Backend Engineer, Billing)
7. Logging

## 1. Why several variants

Every search returns results, but keyword and title searches systematically
miss qualified people whose profiles do not use the expected terms. Cathey's
examples: tens of thousands of Java engineers who never mention "Java", and
accountants at the Big Four who never mention "CPA" [37]. Never present one
search as the whole market.

Rule: at least three variants per must-have you search on (default — confirm
with the owner), including one "dark matter" variant that leaves out the
obvious keyword and searches for the work instead. Cap: 15 queries per batch
(default — confirm with the owner); log every one.

## 2. Building variants from the scorecard

For each must-have (M-id):
1. **Direct:** the obvious term. `postgres "zero downtime" migration`
2. **Synonym/adjacent title:** from the scorecard's title variants.
   `"revenue engineer" OR "billing engineer"`
3. **Dark matter (evidence of the work, not the word):** what someone who did
   it would publish. `"online schema change" "lock timeout" blog`
4. **Venue:** where that work gets presented. `site:pgconf.org speaker`

## 3. web_search X-ray forms

`web_search` is a search engine answer with citations [114]; X-ray operators
may or may not be honoured, so check results by fetching them.

| Goal | Form |
|---|---|
| Public code by topic | `site:github.com "stripe webhook" retry` |
| Talks | `site:speakerdeck.com postgres migration`, `site:youtube.com PGConf "zero downtime"` |
| Engineering blogs | `"engineering blog" "billing" "idempotency" -jobs` |
| Team pages | `"<target company>" "our team" engineer` |
| Packages | `site:pypi.org` / `site:npmjs.com` + topic |

Use `deep=true` only when the owner asks for a market study (about 100x the
cost) [114].

## 4. LinkedIn Recruiter Boolean (owner-run)

Sofia cannot log in to LinkedIn; profile pages are login-walled and cannot be
verified from the sandbox. If the owner runs a Recruiter search and exports
it, these are the rules to give them [95]:

- Operators in UPPERCASE: `AND`, `OR`, `NOT`; quotes for phrases; parentheses
  for grouping. `+` and `-` are not officially supported.
- Overly long queries can break results: move terms into filters (title,
  company, skills) instead.
- Example: `("billing" OR "payments" OR "revenue") AND (postgres OR postgresql) NOT (recruiter OR sales)`

Exports [97]: CSV exports exclude member-entered contact data, are capped at
5,000 profiles per month per seat, and Recruiter Lite cannot export CSV. An
InMail "response" includes "Not interested" replies [96] (matters for the
outreach reply-rate, not here).

## 5. Forbidden query terms

Never put these in a query, even to "narrow the pool": age, birth year,
graduation year, gender, pronouns, race, ethnicity, religion, nationality,
health, disability, pregnancy, marital or family status, "young", "mom",
"dad", church or mosque or temple names, disability-group names. GINA treats
an internet search likely to turn up genetic information (including family
medical history) as a "request" [47]. Location only as work terms, never a
postcode or radius [72].

## 6. Worked query set (Senior Backend Engineer, Billing)

| M-id | Variant | Query |
|---|---|---|
| M2 | direct | `postgres "zero downtime" migration engineering blog` |
| M2 | dark matter | `"online schema change" "lock_timeout" postmortem` |
| M2 | venue | `PGConf Europe speakers migration` |
| M4 | direct | `site:github.com stripe webhook retry idempotency` |
| M4 | adjacent title | `"revenue engineer" OR "monetisation engineer" blog` |
| M4 | dark matter | `"dunning" "failed renewal" engineering blog` |
| M1 | direct | `"on-call" runbook site:github.com payments` |
| M1 | dark matter | `"incident review" billing outage engineering blog` |
| M1 | venue | `SREcon talk payments incident` |

## 7. Logging

Log each query as you run it:
`cd ~/skills/candidate-sourcing-strategy && python3 scripts/append_rows.py search --role <slug> --engine web_search --query "<q>" --results <n> --cards <n>`.
The search log is good practice; federal contractors also had a duty to keep
resume-database search records under 41 CFR 60-1.12, in force until the
rescission takes effect on 2026-10-26 [98][50]. Confirm current duties with
counsel.

Sources: [sources.md](sources.md).
