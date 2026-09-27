---
name: "candidate-sourcing-strategy"
description: "Use when the user wants named candidates for an open role, more people for a thin slate, lookalikes of a benchmark person, or a read on how hard the search will be."
triggers: ["source candidates for this role", "find more candidates for this req", "build a candidate shortlist", "how hard is this hiring search", "find people like this hire", "talent market read for this role", "who else is hiring for this profile", "run a sourcing batch"]
version: "2"
---

# Candidate sourcing strategy

You find real, named people who clear the role scorecard, show the evidence
behind each, and keep the shortlist current. The same pass runs a scheduled or
on-demand sourcing batch (the persona's daily candidate batch runs this in a
fresh session, so everything it needs is in files).

**Use it for:** names for a role, more people for a thin slate, lookalikes of
a benchmark person, a market read ("how hard is this search", "who else is
hiring for this profile").
**Do not use it for:** contacting anyone (`passive-candidate-outreach`),
screening people who applied (`resume-screening`), or setting the bar
(`role-intake-and-scorecard`).

## Inputs and where they come from

| Input | Where from | If missing |
|---|---|---|
| Role scorecard (M-ids, B-ids, title variants, target companies, boundaries) | `~/workspace/hiring/roles/<role-slug>/scorecard.md` and `target-companies.csv` | Run `role-intake-and-scorecard`, or say you are sourcing against an uncalibrated bar and flag every batch |
| Shortlist, pipeline, do-not-contact | `~/workspace/hiring/shortlist.csv`, `tracker/candidates.csv`, `dnc.csv` | Ask who is already in play; name and company will do |
| Batch size, timezone, retention policy | `~/workspace/hiring/preferences.md` (`weekly_batch_size`, `timezone`, `retention_policy`) | Defaults below; ask for retention before re-engaging |
| Owner exports (LinkedIn Recruiter CSV, ATS) | Upload -> `read_workspace_file(file_id, save_to_path="/home/user/in/<name>.csv")` | — |

## Procedure

Mirror the steps in `TodoWrite`. Pre-flight once: `python3 --version`.
All script commands start with `cd ~/skills/candidate-sourcing-strategy &&`.
Work files for this run go in `/home/user/sourcing/` (scratch); the record is
`~/workspace/hiring/`.

1. **Set the target.** Names wanted: `weekly_batch_size` is a weekly number.
   An on-demand batch aims for the number the owner asks for, else
   `weekly_batch_size`. A scheduled routine run aims for `weekly_batch_size`
   divided by the routine's runs per week, rounded up (the weekday
   `daily-candidate-batch` runs five times, so "50 a week" is 10 per run).
   If `weekly_batch_size` is `UNSET`, use 10 per run (the persona routine's
   default). A reply-rate goal for the outreach that follows
   (default: 20 percent within 30 days) and an owner per channel. Both
   defaults are starting points, not benchmarks: say so, ask the owner to
   confirm or change them, and save their numbers.
2. **Load what is known.** Read the scorecard, the shortlist, the pipeline and
   the do-not-contact list. Any scorecard status other than approved
   (`approved` or `approved by <HM> on <date>`) — `draft`,
   `draft-pending-calibration`, anything else — means every card and the
   batch header say "bar uncalibrated (status: <status>)". Off-limits
   companies from the scorecard's boundaries are skipped.
3. **Go warm before cold.** Surface recent near-misses first as
   re-engagements (default window: the past 12 to 18 months — confirm with the
   owner); they already know the company. Only within `retention_policy`: if
   it is `UNSET`, ask once; if the policy excludes someone, skip them and say
   how many. In an unattended routine run there is nobody to ask: with
   `retention_policy` `UNSET`, skip all re-engagements, say in the batch header
   how many were skipped and why, and ask at the next interactive chat. Why: [references/sourcing-guardrails.md](references/sourcing-guardrails.md).
4. **Pick the search.**
   - **Pattern search** is the default. Turn the scorecard's title variants,
     target companies and evidence sources into queries; at least three
     variants per must-have you search on, including one "dark matter"
     variant without the obvious keyword; cap 15 queries per batch (defaults
     — confirm with the owner). Look where people leave a public trace:
     company team pages and speaker bios (who works where); GitHub profiles,
     package maintainers, release credits, portfolios, case studies (what they
     built); blog posts, articles, talks, podcasts (what they said); public
     professional profiles on the open web. Patterns:
     [references/boolean-and-xray-patterns.md](references/boolean-and-xray-patterns.md).
   - **Benchmark search** runs when the user names someone to clone or a
     candidate they rate. List the four to six checkable traits that make that
     person the bar (the scorecard's B-ids, if intake listed them), ignoring
     school, brand and tools. Search their orbit first: teammates from the same
     product and era, co-authors, fellow speakers, co-maintainers, people
     linked by citations. Then widen to peer companies. Rank by benchmark match
     and name any trait nobody matched, saying whether it is scarce or just
     unproven in public. With no public trail, ask the user for three traits
     and search from those.
   - **Engineering roles:** add GitHub. `gh auth status`; if not
     authenticated, `run_capability(id="tool:connect_integration", input={"provider": "github"})`
     and continue with other sources meanwhile. Commands:
     [references/github-sourcing.md](references/github-sourcing.md).
   - **Engines:** `web_search` quick mode (`deep=true` only for an explicit
     market study); `web_fetch` for known pages. Never a query for health,
     family or genetic information, or any protected characteristic.
   - **Log every query as you run it:**
     `cd ~/skills/candidate-sourcing-strategy && python3 scripts/append_rows.py search --role <slug> --engine <engine> --query "<q>" --results <n> --cards <n>`.
   - **More than one cluster** (e.g. 15 target companies plus a benchmark
     orbit)? Run up to 3 `Task` sub-agents at once, each with
     [templates/source-subtask-prompt.md](templates/source-subtask-prompt.md)
     filled for one cluster; they return JSON cards, links and queries. Log
     their queries. Their cards come back with tier `unranked`: give every
     one a tier and a one-line evidence reason (step 8's rules) before writing
     `batch.json`, because `card_check.py` refuses `unranked`. The gates in
     steps 5-6 apply to their cards like any other.
     (Unverified whether sub-agents carry web tools; if one returns no
     queries, run that cluster yourself.)
   - **Blocked?** If a site blocks you, name it and ask for an export or a few
     profile links rather than guessing around it. Login-walled profiles
     (LinkedIn) cannot be verified from here.
5. **Verify every link.** For each evidence URL, `web_fetch` it and record in
   `/home/user/sourcing/links.csv` ([templates/links.csv](templates/links.csv)),
   one row per person per URL: `name` (the person on the card you checked it
   for), `status` ok / blocked (403 or login wall) / dead, and `name_found`
   yes/no (that person's name is on the page). A link verifies only the card
   whose name is on its row, so a card built on someone else's repo or post
   is dropped. A URL cited on two cards (a co-authored post, a shared repo)
   needs a row for each person, each checked on the page. URLs printed by
   `gh api` for a login count as fetched; put the login in the card's
   `github` field.
6. **Dedupe, then gate.** Write the cards to `/home/user/sourcing/batch.json`
   ([templates/batch-card.json](templates/batch-card.json)), then:
   - `cd ~/skills/candidate-sourcing-strategy && python3 scripts/dedupe_names.py /home/user/sourcing/batch.json --out /home/user/sourcing/kept.json`
     drops exact duplicates (name plus company after normalising case,
     accents, punctuation, nicknames and company suffixes, so "Bob Smith,
     Acme" and "Robert Smith, ACME Inc." collide), holds near-matches on a
     "check these" list (never merged on a guess), and drops do-not-contact
     people (count only). If it prints `WARN ... not found` (see
     `files_missing` in its JSON), that list was never checked. A missing
     `dnc.csv` puts "do-not-contact list not found; not checked" in the batch
     header; in an unattended routine run, hold the batch (show nothing) and
     say why at the next interactive chat.
   - `cd ~/skills/candidate-sourcing-strategy && python3 scripts/card_check.py /home/user/sourcing/kept.json --links /home/user/sourcing/links.csv --scorecard ~/workspace/hiring/roles/<slug>/scorecard.md --out /home/user/sourcing/ready.json`
     removes unverified evidence lines (including a link checked only for
     another person), drops any card with no verified link,
     any card from an off-limits company (read from `target-companies.csv`
     next to the scorecard, or `--companies <file>`), any card carrying
     protected data or an unquoted claim that the person wants a move, and any
     tier reason that rests on pedigree. Evidence may cite M-ids or B-ids
   (benchmark traits). A card with one verified line is marked
   `"thin": "thin, 1 line"` and is never tiered strong. The script is a backstop, not the
     whole check: its word lists cannot catch every phrasing. Read every card
     in `ready.json` against the guardrails below before it is shown, and pull
     or fix any card the script missed. Its word lists also over-catch: a card
     dropped for "protected wording" that is plainly the person's own name, a
     place or the product's domain ("Christian's talk", "Temple, TX", "a
     sick-leave accrual engine") may be rerun with that text rephrased, never
     with anything about the person removed or added; note it in the batch
     header ("1 card rephrased after a false protected-wording hit").
7. **Show names early.** Get the first cards up quickly and keep adding; a
   partial batch to react to beats a polished one after ten minutes. Only
   cards in `ready.json` are shown, in the format of
   [templates/card.md](templates/card.md).
8. **Rank, record and review.** Tier the batch as strong fit, worth a look, or
   stretch, giving each person a one-line reason tied to the evidence against
   the bar. Ordering is by evidence-to-bar match with the reason shown, never
   by pedigree, name, photo or location. Review five cards at a time,
   strongest first: keep, pass or maybe, with a few words of reason on every
   pass. When three passes share a reason, the bar is off, not the candidates:
   propose the exact scorecard change ("three passes for never having managed
   anyone; make leading two or more reports a must-have?") and apply it only on
   a yes, through `role-intake-and-scorecard`, then re-rank.
9. **Save on a yes.** Once the owner says yes, add the approved people:
   `cd ~/skills/candidate-sourcing-strategy && python3 scripts/append_rows.py shortlist --role <slug> --cards /home/user/sourcing/ready.json --approved "Name;Name"`
   (or `--all-approved` when they said yes to the whole batch). Each row gets
   date (owner's timezone), source link, tier, reason, search id and channel;
   `stage` tracks sourced -> contacted -> replied -> screened -> in loop, so
   the next batch leans on the channels that get replies. Deliver the batch as
   a CSV or markdown file via `write_workspace_file` too.
10. **Read the market when asked.** Open by saying this draws on public
    sources and your own batches, not a market study. Cover: competing demand
    (live postings for the same profile, and the five companies likeliest to
    chase your shortlist, linked); where the people are (company types,
    cities and communities behind your strongest cards, counted from your
    batches); pay (only figures printed in postings or public pay data, each
    linked: `web_fetch` each posting, save the text with `url:`, `company:`,
    `title:` lines at the top, run `cd ~/skills/candidate-sourcing-strategy && python3 scripts/posted_pay.py <files>`,
    then read the matched text of every row and drop any that is not pay (a
    funding round, revenue, headcount) before showing the table; a row marked
    `CHECK` is shown only once the posting confirms it, a row whose `kind` is
    `OTE/variable` is labelled OTE and never read alongside base pay, and "no range parsed"
    means read that posting yourself. Never estimate a band or infer one from
    company stage); bar pressure (the must-have that screens out the most
    people); time to slate at your current hit rate, and the one change that
    would help most. Template: [templates/market-read.md](templates/market-read.md).

## Decisions inside the procedure

- **No scorecard?** Run `role-intake-and-scorecard` first, or source against
  an uncalibrated bar and say so on every batch.
- **Short batch?** It ships short, with what blocked it (a site, a narrow
  must-have, a thin public trail); never pad to hit the number. None found:
  one line saying so, and where you searched.
- **Too few batches for a market read?** Say so and offer it after the next.
- **No pipeline list?** First ask who is already in play; name and company
  will do.
- **Owner asks for people "who are looking", "young", "local to <postcode>",
  or from "top schools"?** Offer the job-related version (public statements
  of intent only; work terms; evidence against the bar) and say why in one
  line. Never search or rank on those.
- **A card only has a login-walled link?** It is dropped as "could not
  verify"; ask the owner for an export or another public link.

## Output contract

1. Header: role, scorecard version and status ("bar uncalibrated (status:
   <status>)" unless `approved`), batch size target, sources searched,
   sources blocked, and any list dedupe could not find (e.g. "do-not-contact
   list not found; not checked").
2. Ranked cards (strong -> worth a look -> stretch), each: name, current
   title and company, location as stated; two to four evidence lines, each
   tied to an M-id (or B-id) and linked to its verified proof (a card with a
   single verified line is shown only labelled "thin, 1 line" and never
   ranked strong fit); tenure pattern
   plus the short-tenure note if it applies; anything they have publicly said
   about their next move, quoted and linked, or "nothing said publicly"; one
   line on the biggest gap or risk; the tier reason.
3. "Check these": possible duplicates, never merged.
4. Counts: kept, duplicates dropped, do-not-contact excluded (count only),
   cards dropped for no verified link, could-not-verify.
5. Queries run (from `searches.csv`), and the market read when asked.
6. After a yes: shortlist updated, file delivered.

## Guardrails

- No working source link, no card (`card_check.py` enforces it).
- Never state or imply someone wants a move unless they said so publicly.
- Use only what the user supplied and what the person published about their
  professional work; nothing from their private life.
- Never record, guess or infer age, gender, race, ethnicity, religion,
  nationality, health, disability or family status, and draw nothing from a
  photo or a name. Never search for health, family or genetic information.
- Never invent a person, an employer, a link or a number; never estimate a pay
  band.
- Anyone on the do-not-contact list is excluded from every batch, card and
  shared list; their name is never echoed.
- Sourcing only: nothing here sends a message, connection request or note. The
  user's picks go to `passive-candidate-outreach`, and nothing leaves until the
  owner approves that specific message. No candidate details in a group
  channel.

## Quality self-check

- [ ] Every shown card came out of `card_check.py` (verified link per evidence line) and was read against the guardrails.
- [ ] Scorecard status `approved`, or "bar uncalibrated (status: <status>)" on every card and the header.
- [ ] Dedupe ran against shortlist, pipeline and DNC before anything was shown; any `files_missing` named in the header (unattended with DNC missing: batch held).
- [ ] One-line cards labelled "thin, 1 line", never strong fit.
- [ ] Three or more query variants per searched must-have, incl. dark matter; all logged.
- [ ] Tier reasons cite evidence against the bar, not pedigree.
- [ ] Re-engagements respected `retention_policy` (unattended and `UNSET`: none, count stated).
- [ ] Short batch reported as short, with the blocker.
- [ ] Market read: posted pay only, each row's matched text read, n stated, no average.

Batch run sheet: [checklists/batch-run.md](checklists/batch-run.md).
Worked example with hard cases: [examples/batch-senior-backend.md](examples/batch-senior-backend.md).
Citations: [references/sources.md](references/sources.md).

## Siblings

Bar: `role-intake-and-scorecard`. Contact: `passive-candidate-outreach`.
Inbound applicants: `resume-screening`. Removals and tracker:
`interview-coordination`. Funnel numbers: `hiring-pipeline-analytics`.
