# AI-assisted screening: law watch

Dated one-liners so the owner hears once, before screening, that rules about
AI-assisted screening may apply where they hire. The skill never says a law
applies, never says the owner is compliant, and never advises. Each line ends
"may apply; confirm with counsel", addressed to the people lead or counsel.
Checked 2026-09-27; laws change. Source numbers refer to `sources.md`.

This skill is AI-assisted screening: an AI reads resumes and records evidence
for a human. Whether it "substantially assists" a decision in a legal sense is
for counsel.

| Region | One-liner for the owner | Sources |
| --- | --- | --- |
| New York City | Local Law 144: an automated tool that substantially assists screening may need a bias audit no older than one year, a public summary, and candidate notice 10 business days before use. A state audit found far more potential non-compliance than the city had recorded. May apply; confirm with counsel. | [52][69][70] |
| Illinois | HB 3773 (in force 2026): notice when AI is used in hiring decisions; discriminatory effect is prohibited; ZIP code is named as a proxy. The AI Video Interview Act covers AI analysis of video interviews. May apply; confirm with counsel. | [72][55] |
| California | FEHA automated-decision rules (from 2025-10-01): vendors can be liable as agents; keep automated-decision records for 4 years. May apply; confirm with counsel. | [71] |
| Colorado | SB 26-189 (signed 2026-05-14, effective 2027-01-01) replaced the stayed 2024 AI Act: notice before automated decision-making technology is used in a consequential decision such as hiring, a disclosure after an adverse outcome, limited applicant rights, and records kept for at least 3 years. May apply; confirm with counsel. | [120] |
| UK | UK GDPR Arts. 22A-22D (as amended by the Data (Use and Access) Act 2025, in force 2026-02-05): a significant decision with no meaningful human involvement needs safeguards (information, a way to contest, human review), and one based on special-category data is restricted. May apply; confirm with counsel. | [121] |
| EU | AI Act: AI used in recruitment or selection is high-risk (Annex III 4(a)); high-risk obligations apply from 2027-12-02 under Regulation (EU) 2026/1744. GDPR Art. 22 restricts decisions based solely on automated processing. May apply; confirm with counsel. | [53][109][119][54] |
| US (federal) | Title VII disparate-impact rules still apply to every selection step, informal ones included; federal AI guidance was withdrawn in 2025 but the statutes stand. Records: at least 1 year. May apply; confirm with counsel. | [40][42][68][44] |

## Background: what went wrong elsewhere (for the owner, only if asked)

- An EEOC settlement over software that auto-rejected older applicants [66].
- An ADEA collective action against an HR software vendor was conditionally
  certified in 2025; the vendor can be liable as the employer's agent [67][107].
  Disability claims about gap and leave patterns were re-pleaded in 2026; these
  are allegations, not rulings [108].
- A scorer that learned gender proxies from past hiring data [65].
- LLM rankers showing name bias [59][60], and a counter-analysis finding
  ChatGPT close to random at predicting interview outcomes [105].

## How the skill uses this file

1. `find_rubric.py` prints `law_watch` regions from the hiring plan (Harper) or
   preferences (Sofia).
2. For each region listed, add its one-liner to the batch output once, before
   the first record, addressed to the people lead or counsel.
3. Continue screening unless the owner says stop. The skill does not block on
   it and does not advise on it.
4. If no jurisdiction is recorded, say "hiring jurisdictions are not recorded;
   AI-screening rules depend on them" once.
5. A consistency check (`counterfactual_pairs.py`) is not a bias audit under
   any of these laws; say so if the owner asks.
