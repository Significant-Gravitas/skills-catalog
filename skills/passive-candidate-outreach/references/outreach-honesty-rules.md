# Outreach honesty rules

Why each rule exists, with its source. `[n]` numbers follow the recruiting
research dossier (`docs/research/recruiting.md`, section 8) so they can be
checked; the sources used here are listed at the end. "Practitioner judgement
(unsourced)" marks a rule that rests on craft, not on a cited source.

Contents
1. Look like a real recruiter, never like a scam
2. Say only what the card proves
3. Contact routes
4. What never goes in a note
5. Reply semantics (why "response" is not "yes")
6. Keeping people on file
7. Sources

## 1. Look like a real recruiter, never like a scam

Job scams that impersonate recruiters are rising sharply in FTC complaint
data [82], and job scams also appear inside recruiter postings' own warnings
[9]. A cold note from a stranger is judged against that background, so every
note must pass these checks (enforced by `scripts/lint_outreach.py`):

| Rule | Why |
| --- | --- |
| Name the real company, the real role and the real sender (full name, title) in the note | A verifiable sender is the first thing a cautious reader checks [82] |
| Send from the company's own domain or the sender's real, published profile | Free-mail or lookalike domains read as impersonation [82]; practitioner judgement (unsourced) for the domain detail |
| Never ask for money, fees, bank or card details, ID documents or equipment purchases | These are the classic scam asks [82] |
| Never ask to move the conversation to WhatsApp, Telegram, Signal or another encrypted app | Same pattern [82] (dossier section 6 tightening) |
| Never fake a thread ("Re:" / "Fwd:" on a first note; a follow-up's "Re:" must repeat touch 1's exact subject, given as `thread_subject`) | Deceptive framing; practitioner judgement (unsourced) |
| No calendar link in a cold note; the ask is a one-word reply | Skill rule (keeps the ask small and the note unlike a mass campaign) |

## 2. Say only what the card proves

- Facts come only from the sourced candidate card, each with its link
  (persona: "a sourced card that cannot point to at least one link ... does
  not get made").
- Never claim to have read or watched something you have not; if the card has
  only the title of a talk, the hook says "your talk on X at Y", not
  "loved your point about Z".
- Never invent a mutual connection, a referral or an interest in the role.
- Never describe the person as looking for a job unless they said so
  publicly themselves (persona boundary). The linter blocks "since you're
  looking", "open to new opportunities" and similar.
- Pay, title and start date only if the owner supplied them. Never estimate a
  band or infer one from company stage (persona boundary). Where a posting
  jurisdiction requires pay in postings, that is the job description skill's
  concern, not a cold note's [56][57].

## 3. Contact routes

- Use only a route the person published professionally (their site, a public
  profile's contact field, a conference speaker page) or one the owner gives
  you. Record where it came from in `route_source`.
- Never guess or pattern-build an email (first.last@...), never use a commit
  email scraped from code history, and never write to their current employer
  inbox. Practitioner judgement (unsourced), matching the persona's
  "never guess an email or phone number, and never go hunting for one".
- LinkedIn Recruiter CSV exports do not carry member-entered contact data
  [97]; an export is not a contact route.
- No route: stop at the draft and say so.

## 4. What never goes in a note

- Anything about age, graduation year, family, health, religion, nationality,
  ethnicity, sexual orientation, disability, pregnancy or marital status,
  stated or guessed (persona boundary). Also nothing read off a photo.
  The linter makes bare "health", "family", "photo", "young", "older",
  "retire", "crypto" and "pay the" a WARN, not an ERROR, so a company called
  "Oscar Health", a hook on a crypto library, "an older ledger schema" or
  "retire our billing monolith" can pass. Personal phrasings ("you're
  older", "your retirement") and crypto asks ("send us crypto", "paid in
  crypto") stay ERRORs. Treat each such WARN as this rule: keep the
  word only when it names the company, the product or the person's published
  work, and say so in the lint result.
- Nothing found by searching for health or family information: under GINA a
  search likely to turn up family medical history can count as requesting
  genetic information [47].
- No flattery, hype or pressure ("dream job", "rockstar", "only a few spots").

## 5. Reply semantics

LinkedIn counts a "Not interested" answer to an InMail as a *response* [96].
A raw "response rate" therefore mixes yeses and nos. This skill logs each
reply with a `reply_type`:

| reply_type | Status | What happens next |
| --- | --- | --- |
| positive | replied | Cadence stops. Owner takes it forward (screen or call). |
| not-now | replied | Cadence stops. One check-back only if the owner sets a date. |
| not-interested | declined | Cadence stops for good. Logged at once. |
| none | drafted / sent | Cadence continues per `followups_due.py`. |

"Don't contact me" (or any request to stop) is a do-not-contact: run
`log_touch.py dnc`. Only positive replies count toward a reply-rate figure;
report not-now and not-interested separately.

## 6. Keeping people on file

- The do-not-contact list keeps the name and the flag only (persona).
- Under UK GDPR, keeping unsuccessful or unconverted people for future roles
  needs a stated retention period and notice before you keep them [100].
  If the owner hires in the UK or EU and has no retention policy recorded,
  say so in one line and route it to the owner or counsel; never advise
  deleting or keeping records on your own authority.

## 7. Sources

| # | Source | URL |
| --- | --- | --- |
| 9 | Anduril, Contract Recruiter posting (scam warning) | https://boards.greenhouse.io/andurilindustries/jobs/5236226007?gh_jid=5236226007 |
| 47 | 29 CFR 1635.8 (GINA) | https://www.law.cornell.edu/cfr/text/29/1635.8 |
| 56 | California Labor Code 432.3 | https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=LAB&sectionNum=432.3 |
| 57 | Colorado CDLE INFO #9A | https://cdle.colorado.gov/ (INFO #9A, pay transparency) |
| 82 | FTC, job scam data (Dec 2024) | https://www.ftc.gov/news-events/news/press-releases/2024/12/new-ftc-data-show-skyrocketing-consumer-reports-about-game-online-job-scams |
| 96 | LinkedIn Help, InMail Policy | https://www.linkedin.com/help/recruiter/answer/a413279 |
| 97 | LinkedIn Help, Export profiles in Recruiter | https://www.linkedin.com/help/recruiter/answer/a412149 |
| 100 | UK ICO, Keeping recruitment records | https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/employment/recruitment-and-selection/keeping-recruitment-records/ |

Legal lines here are orientation, dated 2026-09; confirm with counsel before
relying on any of them.
