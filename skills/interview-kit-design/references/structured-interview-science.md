# Structured interview science: what the kit rests on

`[n]` numbers follow the recruiting research dossier (section 8); the sources
used are listed at the end. Dated 2026-09.

Contents
1. Why structure
2. The 15 components, and where the kit covers each
3. Anchored scales
4. Independent ratings, overall last
5. How many interviews
6. Question types
7. Anti-patterns ("voodoo hiring")
8. Sources

## 1. Why structure

- Structured interviews are the strongest common predictor of job
  performance in the 2022 re-estimate: r = .42, ahead of job-knowledge tests
  (.40), work samples (.33) and cognitive ability (.31) [77]. The older canon
  put structured at .51 against .38 for unstructured [18]. Validities vary with
  design quality [77], which is why the kit's details matter.
- Structure raises interviewer agreement and lowers adverse impact [27].

## 2. The 15 components [19]

| Component | Where the kit covers it |
| --- | --- |
| Questions from a job analysis | Every question maps to a must-have (M-id) from the role scorecard |
| Same questions for every candidate | "Core questions never change between candidates" |
| Better question types (behavioural, situational, background) | `question-bank-patterns.md` |
| Limited prompting | Probes are written in advance; follow-ups only to clarify |
| Longer interviews / more questions | 4-6 questions per slot (skill default), a clock per slot |
| Rate each answer | Scorecard rates each owned competency with evidence |
| Multiple scales | One 1-5 scale per competency, not one global score |
| Anchored scales | Five anchors per competency in this role's real work |
| Detailed notes | Evidence field is mandatory |
| Multiple interviewers | One owner per competency across the loop |
| Trained interviewers | Out of scope for this skill (gap: interviewer training); packets carry reminders |
| No discussion between interviews | Scorecards filed alone before any discussion |

The dossier's summary of [19] lists the twelve components above. The
original paper lists a few more; three are covered here by the packet rules
(sourced quotes only, which controls ancillary information), the clock's
closing segment for the candidate's questions, and one fixed owner per slot.
Mechanical (statistical) combination of ratings is deliberately **not**
adopted: the persona never scores, averages or ranks a candidate; the debrief
keeps ratings visible per competency and a named human decides. Check [19]
before quoting the full list.

## 3. Anchored scales

- Google re:Work's four-level anchors (poor, borderline, solid, outstanding)
  with illustrative answers [28]; OPM's customised scales with behavioural
  examples per level, fixed in advance, so candidates are rated against the
  standard and not against each other [78].
- This kit keeps the persona's 1-5 scale (1 unsatisfactory, 2 below bar, 3
  meets bar, 4 above bar, 5 exceptional) plus "not assessed". Each level is
  one line of this role's real work. `scripts/check_kit.py` refuses a kit
  where an owned competency lacks any of the five anchors.

## 4. Independent ratings, overall last

- Kahneman's protocol: a handful of traits (about six), factual questions,
  each trait scored 1-5 before moving to the next ("do not skip around"),
  and the overall judgement formed only after [20].
- Noise's Mediating Assessments Protocol: independent assessments, each
  reviewed separately, estimate-talk-estimate, intuition last [21].
- Applied here: the scorecard's hire / no-hire block sits last and is filled
  only after every competency rating; interviewers file alone before any
  discussion; the debrief skill runs the meeting.
- Greenhouse lets admins show interviewers each other's feedback before they
  file; that visibility breaks independence [90]. Ask the owner how it is set.

## 5. How many interviews

Google's analysis found four interviews predicted the hiring decision with
86% confidence [29]. The kit defaults to four slots or fewer;
`check_kit.py` warns on a fifth and asks for the reason (default — confirm
with the owner).

## 6. Question types

Behavioural questions do better for complex or managerial roles; situational
questions also work [27]. Patterns and probes: `question-bank-patterns.md`.

## 7. Anti-patterns [23]

Gut instinct, unfocused group interviews, trick questions, selling instead of
assessing, pet questions, casual chat, hypothetical "fortune-teller"
questions. `scripts/question_lint.py` warns on fortune-teller and brainteaser
wording.

## 8. Sources

| # | Source | URL |
| --- | --- | --- |
| 18 | Schmidt & Hunter 1998 (course outline) | https://web.pdx.edu/~mccunee/quant_621/Outlines/Schmidt%20&%20Hunter%20(1998).doc |
| 19 | ScienceForWork summarising Campion, Palmer & Campion 1997 | https://scienceforwork.com/blog/you-are-who-you-select/ |
| 20 | Ed Batista, Kahneman on conducting better interviews | https://edbatista.com/2021/02/daniel-kahneman-on-conducting-better-interviews.html |
| 21 | The Uncertainty Project, Mediating Assessments Protocol | https://www.theuncertaintyproject.org/tools/the-mediating-assessments-protocol |
| 23 | Smart & Street, Who (excerpt) | https://geoffsmart.com/books/who-the-a-method-for-hiring/who-the-book-excerpt/ |
| 27 | OPM, Structured Interviews | https://www.opm.gov/policy-data-oversight/assessment-and-selection/other-assessment-methods/structured-interviews/ |
| 28 | Google re:Work, structured interviewing guide | https://rework.withgoogle.com/intl/en/guides/a-guide-to-structured-interviewing-for-better-hiring-practices |
| 29 | Knowledge at Wharton, Laszlo Bock interview | https://knowledge.wharton.upenn.edu/article/open-sourcing-googles-hr-secrets/ |
| 77 | SIOP summary of Sackett et al. 2022 | https://www.siop.org/tip-article/is-cognitive-ability-the-best-predictor-of-job-performance-new-research-says-its-time-to-think-again/ |
| 78 | OPM, customised rating scales | https://www.opm.gov/frequently-asked-questions/assessment-policy-faq/structured-interviews/how-do-i-develop-a-customized-rating-scale-for-structured-interviews/ |
| 90 | Greenhouse Support, Scorecards FAQ | https://support.greenhouse.io/hc/en-us/articles/15756249510427-Scorecards-FAQ |
