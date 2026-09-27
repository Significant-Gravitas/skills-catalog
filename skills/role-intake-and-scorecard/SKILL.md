---
name: "role-intake-and-scorecard"
description: "Use when a new role opens or a req needs rescoping: agree a checkable role scorecard and hiring plan with the hiring manager before any posting or sourcing."
triggers: ["scope this new role", "kick off a new req", "write a role scorecard", "agree the hiring bar", "intake with the hiring manager", "what should this role require", "calibrate on a benchmark hire"]
version: "2"
---

# Role intake and scorecard

Every search starts here. The role scorecard you write is the bar that
postings, sourcing, screening and interview kits all read, so it lives in one
file with numbered must-haves (M1, M2, ...) that every other skill cites.

**Use it for:** a new role, an unscoped req, a rescope, calibrating on a
benchmark person, "what should this role require".
**Do not use it for:** writing the public posting (`job-description-drafting`,
after this), finding names (`candidate-sourcing-strategy`), interview
questions and anchors (`interview-kit-design`), or pay figures (never
proposed here; see guardrails).

## Inputs and where they come from

| Input | Where from | If missing |
|---|---|---|
| The hiring manager's ask (call notes, rough req, old posting) | Paste or upload; Granola intake call; Google Drive old posting (see [references/integrations.md](references/integrations.md)) | Ask for it, one question at a time, and keep drafting |
| Team context: who the hire reports to, what gap opened the role | Owner or HM | Ask |
| Preferences (timezone, jurisdictions, panel, loop shape) | `cat ~/workspace/hiring/preferences.md` | Proceed; mark UNKNOWN |
| An existing scorecard for this role | `~/workspace/hiring/roles/<role-slug>/scorecard.md` | New role: start from the template |

## Procedure

Mirror the steps in `TodoWrite`. Show the bar in chat first; save and
validate after. The first view never waits on a script. Pre-flight once,
before the first script: `python3 --version`.

1. **Check for an existing scorecard.**
   `cat ~/workspace/hiring/roles/<role-slug>/scorecard.md 2>/dev/null`. If it
   exists and is approved, this is a rescope: go to step 10's revision path,
   never overwrite.
2. **Gather the ask.** If Granola is connected, list meetings from the last
   14 days that match the role or HM name and read only the one the owner
   confirms. If an old posting is in Drive, read it. Otherwise ask for a
   paste. Every quote is FACT with its source (meeting title and time, doc
   name); a paraphrase is INFERENCE. Quote only job-related sentences, and
   never store a transcript.
3. **Start from the work, not the title.** In plain outcomes, write what the
   hire must own by the end of year one, their closest collaborators, and the
   two or three problems the company needs solved. Quote the HM's sentence
   behind each point so misreadings surface now.
4. **Write the bar** (three to six must-haves; the persona's day-one promise).
   Each must-have:
   - is confirmable from public work or a structured interview question, so
     two reviewers with the same evidence would agree. "Has run on-call for a
     service with paying customers" passes; "great ownership mentality" fails
     until you ask what ownership looks like in practice and write that;
   - passes the **three-part test**: objective (no judgement call needed to
     see if it is met), non-comparative (not "among the best"), and
     job-relevant (say what fails without it) [49][36];
   - names its **evidence method** (the interview question, work sample, or
     public-work check that will test it), so screening and the loop actually
     score what the posting asks for [111];
   - replaces years-of-experience floors and degree requirements with the
     outcome behind them unless the HM defends them in one line, which you
     record verbatim ("HM defended: ...").
   **Nice-to-haves** are labelled separately; they break ties and never keep
   anyone out. **Disqualifiers** go in the HM's words, then through the
   fairness check. Three straight jobs under a year each is a note on the
   candidate card for the interviewer, never a disqualifier.
5. **Keep it fair and job-related.** Every line must tie to the work. None may
   name or proxy for a protected characteristic such as age, race, ethnicity,
   national origin, sex, gender identity, sexual orientation, religion,
   disability, pregnancy or family status. "Digital native", "native English
   speaker", "culture fit" and graduation-year cut-offs become the real skill
   underneath ("writes customer-facing docs in English") or get cut, and you
   say which. Location is written as work terms (hours, on-site days, travel),
   never a postcode, ZIP or commute radius [72]. Physical or schedule demands
   are written as "can do X, with or without reasonable accommodation" [46].
   Rewrites: [references/protected-traits-and-proxies.md](references/protected-traits-and-proxies.md).
6. **Calibrate against one real person.** Ask whether someone's work, inside
   the company or out, sets the bar. If it does, list four to six checkable
   things that make that person the benchmark (B1, B2, ...): keep what
   transfers (owning a hard problem end to end), drop the incidental (school,
   employer brand, exact tools). Take one round of edits; sourcing's lookalike
   search runs from this list.
7. **Map where the people are** (guide:
   [references/target-map-guide.md](references/target-map-guide.md)):
   - **Target companies:** where this work really happens (stage, size,
     product), 10 to 20 named examples (default — confirm with the owner).
     Find them with `web_search` (quick; `deep=true` only if the owner asks
     for a market study). Confirm each company's site with `web_fetch` and
     record `link_status` (`ok`, `blocked` for a 403 or login wall = check
     manually, `dead`). A company from memory with no working link is
     dropped. Write them to
     `~/workspace/hiring/roles/<role-slug>/target-companies.csv`
     ([templates/target-companies.csv](templates/target-companies.csv)).
   - **Boundaries:** whether direct competitors are fair game, and which
     companies are off limits (customers, partners, a non-solicit clause).
   - **Title variants:** five to ten current and adjacent titles (default),
     including at least two "dark matter" variants that do the work under a
     different name [37].
   - **Evidence sources:** engineers show public code and packages;
     designers, portfolios and case studies; marketing and research, articles
     and talks; support and solutions, forum answers and help-center writing;
     sales and finance, panels, podcasts and published decks.
8. **Agree the hiring plan in the same sitting.** Order stages so
   deal-breakers are tested first: screen, knockout competency, deep-dive,
   hiring-manager close. Name the panel and each interviewer's competency (map
   each must-have to one stage), the target slate size, the fill date, and who
   sets compensation and how. Never propose a pay figure yourself. If the
   owner plans a referral-only slate, say once that it narrows the pool and
   tends to reproduce the current team, and that referral advantages fade if
   the referrer leaves [34][36]; the owner decides.
9. **Save and validate.** Fill
   [templates/role-scorecard.md](templates/role-scorecard.md) into
   `~/workspace/hiring/roles/<role-slug>/scorecard.md`, then run
   `cd ~/skills/role-intake-and-scorecard && python3 scripts/scorecard_check.py ~/workspace/hiring/roles/<role-slug>/scorecard.md --companies ~/workspace/hiring/roles/<role-slug>/target-companies.csv`.
   Fix every `ERROR` (or take it back to the HM); show `WARN` lines to the
   owner. The lexicon sometimes hits a plain job word: a preschool bar that
   says "children aged 3 to 5", a clinic's "medical history records", a
   "maternity ward", "disability insurance claims". Only for those terms
   (children, kids, childcare, pregnancy, maternity, disability, medical
   history, photo), and only when the line tests the work and not the person,
   add a child line under that item: `  - lint_ok: <term> - <why it is
   job-related>`. The script then prints it as a `WARN ... kept as
   job-related`, which you read out to the HM before approval. Never use it to
   keep a proxy; every other term is rewritten or cut. Counts are not ages:
   "over 10 direct reports" passes, "candidates over 50" does not. Deliver a copy with
   `write_workspace_file(filename="scorecard-<role-slug>.md", source_path="/home/user/workspace/hiring/roles/<role-slug>/scorecard.md")`
   and link it as `workspace://<file_id>#text/markdown`.
10. **Approval and versions.** You recommend; the hiring manager decides.
    Stamp approval only on the HM's explicit yes, quoting it:
    `cd ~/skills/role-intake-and-scorecard && python3 scripts/scorecard_check.py <file> --approve "<HM name>" "<their words>"`.
    If it warns that the approver is not the header's `hiring_manager`, stop
    and confirm who owns the bar before you rely on the approval.
    Later edits: `cd ~/skills/role-intake-and-scorecard && python3 scripts/scorecard_check.py <file> --revise` (keeps
    `scorecard-v<N>.md`, bumps the version, drops status to draft); the edit
    goes back to the HM, and you tell the owner which skills were working
    against the old version (posting, sourcing batches, screens).
11. **After approval (optional, on a yes).** If Linear is connected and the
    owner says yes, file one issue "Req approved: <role>" with the scorecard
    link, role-level only, no candidate data
    ([references/integrations.md](references/integrations.md)). The write is
    approval-gated; keep going while it is held. Add the role to
    `~/workspace/hiring/tracker/roles.csv` only on the owner's yes.

## Decisions inside the procedure

- **No hiring manager to hand?** Take the title and ask four questions: what
  the hire must deliver in year one, which two things rule a candidate out,
  whether anyone's work sets the bar, and when the seat must be filled. Label
  the result `draft-pending-calibration`. Sourcing against it is allowed if
  every batch flags the bar as uncalibrated.
- **HM defends a years or degree floor?** Keep it, verbatim with "HM defended:",
  and note that the screen and loop must then test it the same way for all.
- **HM insists on a proxy** ("native speaker", "young team", a postcode)?
  Offer the job-related rewrite; if refused, cut the line and say so. Never
  keep a protected-trait proxy on the bar. Legal questions go to the attorney
  with a one-line brief.
- **Role in NYC, Illinois, California, Colorado, the EU or the UK?** One line:
  posting-law and AI-screening rules may apply; the people lead or counsel
  decides.

## Output contract

In chat, in this order: year-one outcomes (each with its FACT quote and
source), must-haves M1..Mn (each with evidence method), nice-to-haves,
disqualifiers (with the fairness result), what was cut or rewritten and why,
benchmark traits, target companies (linked) and boundaries, title variants,
evidence sources, then the hiring plan. Status line: `draft`,
`draft-pending-calibration`, or `approved by <HM> on <date>`.
On disk: `~/workspace/hiring/roles/<role-slug>/scorecard.md` and
`target-companies.csv`, validated; a delivered copy linked. Unknowns (slate
size, fill date, comp owner) are written UNKNOWN, never guessed.

## Guardrails

- Nothing reaches a posting, screen or sourcing run until the HM approves the
  scorecard. The one exception is sourcing, which may run against a
  `draft-pending-calibration` bar if every batch says so. Later edits go back
  to the HM too.
- Never propose, estimate or infer a pay figure or band.
- Never invent a company, a quote, or a benchmark trait. A company with no
  working link is dropped.
- No line names or proxies for a protected characteristic; no postcode or
  commute filters; no health questions.
- Linear, Granola and Drive writes or reads carry role-level facts only; no
  candidate data, no transcript storage.

## Quality self-check

- [ ] 3-6 must-haves, each objective, non-comparative, job-relevant, with an evidence method.
- [ ] Every year-one outcome has a quoted source, or is marked INFERENCE.
- [ ] Years/degree terms only with "HM defended:".
- [ ] `scorecard_check.py` exits 0.
- [ ] Every target company links to a site you fetched.
- [ ] Nothing about pay beyond "who sets compensation and how".
- [ ] Status and version are right; approval quoted, not assumed.

Checklist for the sitting: [checklists/intake-sitting.md](checklists/intake-sitting.md).
Worked example with a hard case: [examples/senior-backend-intake.md](examples/senior-backend-intake.md).
Why the rules: [references/requirement-inflation.md](references/requirement-inflation.md).
Citations: [references/sources.md](references/sources.md).

## Siblings

Posting: `job-description-drafting` (reads M1..Mn verbatim). Names and
lookalikes: `candidate-sourcing-strategy` (reads B1..Bn, target companies,
title variants). Screening: `resume-screening`. Loop and anchors:
`interview-kit-design` (one owner per must-have). First chat:
`sofia-getting-started`.
