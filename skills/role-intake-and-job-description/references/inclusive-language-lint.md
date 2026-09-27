# Inclusive-language lint: what `jd_lint.py` flags and why

The lint makes the review repeatable: the same draft gives the same list every
time, with line numbers. It suggests; the owner accepts or rejects each hit.
Harper never silently rewrites flagged words. Source numbers refer to `sources.md`.

## Levels

| Level | Meaning | What Harper does |
| --- | --- | --- |
| flag | Likely to screen people out with no work reason | Raise it with the swap; the owner decides |
| check | Fine only with a work reason from the requirement sort | Ask for the reason, or suggest the swap |
| suggest | Gender-coded wording | Offer the swap; mention the balance line |
| info | Counted for the balance only | Not listed individually |

## Categories and evidence

- **age** (flag): "young", "recent college graduate", "college student",
  "boy", "girl", "age 25 to 35", "aged 25-35" are named in the ADEA
  help-wanted rule [45]. Age limits such as "under 40", "40 and over" or
  "over the age of 18" are flagged too. A minimum age ("at least 21 years
  old", "minimum age of 18") is a check: the law that sets it is named and
  confirmed with counsel, not assumed.
- **age-proxy** (flag): "digital native" [34]; experience ceilings such as
  "no more than 5 years' experience" [34][45]; graduation-date limits
  ("graduated within the last 3 years", "class of 2024", "graduation year")
  [34]. "Energetic" and "overqualified" are raised as checks [34].
- **requirement-check** (check): years of experience and degree words. Allowed
  only with a work reason in `requirements.csv` [36][111].
- **proxy** (flag): "culture fit" [79]; photo requests [34]; "native speaker",
  "native-level", "(native)", "mother tongue" (practitioner judgement,
  unsourced). Citizenship-only wording ("US citizens only") is a check: state
  the work-authorisation need and confirm it with counsel.
- **location-proxy** (flag): commute radius, "local candidates only", postcode
  or ZIP. Illinois law names ZIP code as a proxy [72]. Write work terms instead.
- **pay** (flag): salary-history and current-salary asks [56][75]. Ask for
  expectations only.
- **family** (flag): marital status, childcare, "no family commitments",
  any mention of pregnancy [34][74]. State the schedule or travel the work
  needs instead.
- **religion** (flag): faith words such as "Christian values", "faith-based",
  "church" [34]. Remove; a religious employer confirms any exemption with counsel.
- **appearance** (flag): grooming rules such as "clean-shaven", "no beards",
  "hairstyle" can screen people out by religion or race [34]. State a safety
  need only if the work has one.
- **disability** (flag or check): "able-bodied", "in good health", physical
  requirements without "with or without reasonable accommodation" [35][46][58].
  "Own car" or a driving licence is a check: keep it only if driving is an
  essential function [35][46].
- **label** (flag): "rockstar", "ninja", "guru", "self-starter", "hungry",
  "high energy", "work hard play hard". Personality labels, not evidence
  (practitioner judgement, unsourced; the original skill already banned them).
- **masculine-coded / feminine-coded** (suggest / info): word stems from
  Gaucher, Friesen and Kay. Masculine-coded wording lowered women's sense of
  belonging and the appeal of the job; the paper suggests neutral swaps such as
  "excellence" for "dominance" [31]. Feminine-coded words are counted so the
  owner sees the balance; they need no change.

## Known benign hits (tell the owner, do not push a change)

- "Lead" or "Leader" in a job title, or when the role manages people.
- "Competitive pay" when a pay range is stated. ("Competencies" is not
  matched: the masculine-coded row lists the compete/competitive forms only.)
- "Challenging" when it describes the work itself ("challenging reconciliations").
- "Independent" in "independent contractor" (a work term).
- "Support" in "customer support" (a team name).
- "Must be able to drive" for a driving job, with the accommodation phrase.

## How to present hits

```
Language flags (jd_lint.py, 4 to review)
- L3 "rockstar" [label] -> describe the work and the result expected
- L9 "recent graduates" [age] -> "early-career", or name the skill needed [45]
- L12 "digital native" [age-proxy] -> name the tools or skills needed [34]
- L15 "5+ years" [requirement-check] -> keep only with a work reason, else name the outcome [36]
Gender-coded balance: masculine 3, feminine 1 (masculine-leaning) [31]
```

List every flag and check hit. For suggest hits, list them only if the balance
is masculine-leaning, and say they are optional.
