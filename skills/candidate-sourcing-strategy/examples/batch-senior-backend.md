# Worked example: a batch for Senior Backend Engineer, with hard cases

Fictional throughout. The raw cards are in [batch-raw.json](batch-raw.json)
and the fetched-link record in [links-verified.csv](links-verified.csv); the
script outputs below are what those files actually produce.

## Setup

- Scorecard: `roles/senior-backend-engineer/scorecard.md`, v1, approved by Lena
  Ortiz. M1 on-call, M2 zero-downtime Postgres migration, M3 design docs, M4
  billing debugging. Boundaries: Paywise is a customer, off limits.
- Preferences: `weekly_batch_size: 10`, `timezone: Europe/Lisbon`,
  `retention_policy: UNSET`.
- Shortlist already holds "Thomas Becker, PayWise GmbH". Pipeline holds
  "Robert Smith". DNC holds one name.

**Target.** "Aiming for 10 names. For outreach I'll track against 20% replies
within 30 days, a starting default, not a benchmark. Keep or change?" Owner:
keep.

**Warm first.** Two near-misses from April. `retention_policy` is UNSET, so
Sofia asks once: "How long do you keep records of people you didn't hire, and
were they told you might contact them later?" Owner: "12 months, and yes,
it's in our privacy notice." Both are inside 12 months: listed as
re-engagements first.

## Search

Queries (each logged with `append_rows.py search`):

| id | engine | query |
|---|---|---|
| S-2026-09-28-01 | web_search | `postgres "zero downtime" migration engineering blog` |
| S-2026-09-28-02 | gh | `search/repositories q='stripe webhook retry'` |
| S-2026-09-28-03 | web_search | `"online schema change" "lock_timeout" postmortem` (dark matter) |

GitHub: `gh auth status` showed not logged in, so Sofia ran
`run_capability(id="tool:connect_integration", input={"provider": "github"})`,
said so in one line, and kept going on web sources until the owner connected.

Three target-company clusters ran as `Task` sub-agents with the subtask
prompt. Their cards came back `unranked`; Sofia gave each a tier and a
one-line reason (as she would in step 8) and merged them into `batch.json`
(7 cards).

## Gates

```
$ python3 scripts/dedupe_names.py /home/user/sourcing/batch.json --out /home/user/sourcing/kept.json
{"kept": 5, "exact": [{"name": "Tom Becker", "company": "Paywise", "matched_in": "shortlist"}],
 "check_these": [], "dnc_excluded": 1, "files_missing": []}
```
"Tom Becker, Paywise" is "Thomas Becker, PayWise GmbH" after the nickname and
company-suffix normalisation: an exact duplicate, dropped. (Paywise is also
off limits; had it not been a duplicate, `card_check.py` would have dropped
it as an off-limits company.) One person was on the do-not-contact list:
dropped, name not shown anywhere. The DNC test also catches the same person
written differently: a DNC entry "Marta Silva" excludes "Marta Silva
Pereira", "Marta P. Silva" and "Silva, Marta" (token subset), and "Marta
Silva Pereira" on the list excludes "Marta Pereira".

```
$ python3 scripts/card_check.py /home/user/sourcing/kept.json --links /home/user/sourcing/links.csv \
    --scorecard ~/workspace/hiring/roles/senior-backend-engineer/scorecard.md --out /home/user/sourcing/ready.json
WARN  Aisha Bello (Cloudkite): only 1 verified evidence line; thin card
DROP  Jonas Weber (Fintra): links behind a login/403 wall; could not verify (ask for an export or another public link)
ERROR dropped Lee Park (Shiftly): claims they want a move without a quoted, verified public statement
ERROR dropped Sam O'Neil (Bigco): reason rests on pedigree ('Stanford'); rank on evidence against the bar only
summary: 2 ready, 3 dropped (1 could not verify, 0 off limits); written to /home/user/sourcing/ready.json
```

The hard cases, and what Sofia says about each:
- **Jonas Weber:** only a LinkedIn profile, which is login-walled. "I can't
  verify Jonas from here; if you export him from Recruiter or know another
  public link, I'll add him."
- **Lee Park:** the sub-agent wrote "open to work per his profile". No quoted
  public statement backs it, so the card is dropped. It can come back with the
  intent claim removed and "Next move: nothing said publicly".
- **Sam O'Neil:** the tier reason was a school and an employer brand. Re-tiered
  on evidence (one M3 design doc) it would be a stretch; Sofia rebuilds the
  card with that reason and reruns the gate.
- **A borrowed link (not in this batch's files, shown for the rule):** a
  sub-agent returns a card for "Tom Becker, Cloudkite" whose evidence is
  Priya's runbook repo and her Ledgerline post. `links.csv` has those URLs
  only as `...,Priya Nair,ok,yes,...` (and the runbook once as
  `...,Tom Becker,ok,no,...`: his name is not on it). The gate prints
  `WARN  Tom Becker (Cloudkite): https://ledgerline.example/blog/zero-downtime-migrations checked only for Priya Nair, not for this person; line removed`
  and `DROP  Tom Becker (Cloudkite): no verified evidence link (no link, no card)`.
  A co-authored post that really names both people gets two rows, one per
  name, each checked on the page.

## What the owner sees

> **Batch 1 — Senior Backend Engineer** (bar v1, approved). Target 10;
> **short batch: 3 ready** after re-running Sam's card. Searched: web
> (3 queries), 3 target-company clusters. Blocked: LinkedIn (asked for an
> export); GitHub pending connection.
>
> **Re-engagements (inside your 12-month policy):** 2 from April, listed first.
>
> **Strong fit — Priya Nair**, Staff Engineer, Ledgerline (Dublin, as stated)
> - M2: wrote "Zero-downtime migrations at 4TB" — [blog post](https://ledgerline.example/blog/zero-downtime-migrations)
> - M1: on-call runbook author — [repo](https://github.com/priya-nair-example/oncall-runbook)
> - Tenure: 3.5 and 4 years in her last two roles
> - Next move: nothing said publicly
> - Gap: no public evidence on billing flows (M4); UNKNOWN, not a no
>
> **Stretch — Aisha Bello**, SRE, Cloudkite (remote, as stated)
> - M1: incident write-ups on the company blog — [post](https://cloudkite.example/blog/incident-2026-03)
> - Gap: nothing public on migrations or billing; thin, 1 line
>
> **Stretch — Sam O'Neil**, Engineer, Bigco (London, as stated)
> - M3: design doc on the Bigco blog — [doc](https://bigco.example/design)
> - Why this tier: M3 only; thin, 1 line
>
> Dropped: 1 duplicate (already shortlisted), 1 do-not-contact, 1 could not
> verify, 1 unsupported "looking for a move" claim (card can return without it).
> Why short: M2 and M4 public evidence is rare; GitHub will help once connected.
>
> Add Priya, Aisha and Sam to the shortlist?

Owner: "Priya and Aisha." ->
`append_rows.py shortlist --role senior-backend-engineer --cards ready.json --approved "Priya Nair;Aisha Bello"`
-> `shortlist: 2 added, 0 skipped, dated 2026-09-28`.

## Review, and a bar signal

Over the next two batches the owner passes on three people with the same
reason: "never led an on-call rotation, only joined one". Sofia: "Three passes
for the same reason. Make M1 'has led an on-call rotation for a service with
paying customers'? It would go back to Lena as scorecard v2." Applied only on a
yes, through `role-intake-and-scorecard`; then the shortlist is re-ranked.

## Market read (on request, after batch 3)

> This draws on public sources and my own batches (3 batches, 11 cards), not a
> market study.
>
> **Posted pay** (n = 3 postings read):
>
> | company | title | min | max | currency | period |
> |---|---|---|---|---|---|
> | Ledgerline | Senior Backend Engineer | 150,000 | 185,000 | $ (unspecified) | year |
> | Cloudkite | Backend Engineer | 95,000 | 110,000 | EUR | year |
>
> Fintra: no range parsed; Sofia read the posting and it prints no pay. One
> more row the script matched, "raised $20 - 30 million", was skipped as
> funding, not pay. No average or band: three postings is a small, non-random
> sample.
>
> **Bar pressure:** M4 (8 of 11 cards lack public evidence for it; UNKNOWN is
> not a no). **Time to slate:** about 3.7 ready cards per batch; a slate of 8
> takes about 2 more batches (INFERENCE from the hit rate so far).
