# Protected traits and proxies: what the screen never uses

Both kits carry this skill, so both personas' lists apply in full. Source
numbers refer to `sources.md`.

## Never inferred, recorded or used

Age (including a graduation year used to estimate it), race, ethnicity,
colour, national origin or nationality, religion, sex, gender and gender
identity, sexual orientation, disability, health, genetic information,
pregnancy, marital or family status, veteran status, and any other protected
trait. Nothing is read off a photo. (Harper and Sofia personas; [34][35][46][74].)

## Proxies: removed by `redact.py` where it can, and never used where it cannot

| Proxy | Why it is a proxy | Handling |
| --- | --- | --- |
| Name | Callback rates differ by name: 50% more callbacks for White-sounding names [32]; embedding rankers preferred White-associated names 85% of the time [59] | Redacted; never guessed from an email or URL |
| Photo, appearance | Protected-trait cues; no photo before an offer [34] | Not extracted; never described |
| Address, ZIP or postcode, commute | Illinois law names ZIP code as a proxy [72] | Redacted in the contact block; never a criterion |
| Graduation year, "years since graduating" | Age estimate [45] | Education years redacted; tenure dates kept |
| Employment gaps, leave, part-time spells | Track disability and caregiving; an AI screener penalised 1-2 year gaps [64]; alleged in Mobley [108] | Kept as text (dates are evidence) but never scored or noted as negative |
| School or employer prestige | Weak predictor; LLM screeners over-reward pedigree [105][18] | School names redacted in Education; employers kept for scope, never for brand |
| Writing polish, AI-written style | LLM evaluators prefer LLM-written resumes 67-82% of the time [63] | Never scored; only the claims count |
| Accent, "native speaker", language of name | National-origin proxy [34] | Never inferred from text |
| Clubs and associations that reveal a trait (religious, ethnic, disability, LGBTQ+ groups) | Pre-employment inquiries into these can evidence intent [34] | A leadership claim in such a group can be evidence of leadership; the group itself is never mentioned in the record |
| Disability-related credentials or awards | Penalised by ChatGPT in a controlled test, with confabulated reasons [61] | Treated exactly like any other credential of the same scope |
| Pronouns, honorifics | Gender cue | Redacted |
| Self-ID and EEO columns in exports | Must never reach screeners [51][99]; the Greenhouse v3 EEOC endpoint is row-level [118] | Dropped by `redact_export.py`, with a one-line notice |

## Summaries: quote, do not paraphrase

LLM summaries of the same resume shift when only demographic details change
[62], and models confabulate reasons [61]. So the record quotes the resume
text and gives its location; it never paraphrases a candidate's claim.
`verify_quotes.py` enforces this.

## Job-related rewrite table (for owners who ask)

| Asked for | Job-related version |
| --- | --- |
| "Recent grad", "young team" | The level of work: "has run X end to end" |
| "Local candidates", postcode | Work terms: onsite days, hours, travel |
| "Native English" | "Writes <named documents> in English" |
| "Culture fit" | The behaviour meant: "writes decisions down for the team" [79] |
| "No gaps" | Nothing. Gaps are not evidence. |
| "Top school" | The skill the school stood for, tested directly |
