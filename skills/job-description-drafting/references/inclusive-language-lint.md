# What the language lint checks, and how to use its output

`scripts/jd_lint.py` reads `references/lint-terms.csv`. It flags; the owner
decides. Never rewrite silently: show each hit, the swap, and let the owner
accept, reject or defend it.

## Contents
1. Categories
2. Severities
3. Known benign uses
4. What the lint cannot see
5. Extending the lexicon

## 1. Categories

| Category | Why it matters | Source |
|---|---|---|
| `age` | The ADEA help-wanted rule names "young", "recent college graduate", "college student", "age 25 to 35", "boy", "girl" and similar terms as violations unless an exception applies | [45] |
| `age` (also) | "someone under 35", "no older candidates" and other age limits. "Under/over NN" is flagged only when it reads as an age: after a person word ("candidates over 50", "be over 18"), before "years old"/"years of age", or at the end of a clause. A count ("over 60 clinicians", "over 50 employees") is not an age | [45] |
| `age-proxy` | "Digital native", "digitally native" and a graduation year ("Graduated in 2018 or later", "class of 2020") stand in for age; "overqualified" is a CHECK | [34][45]; "high energy"/"energetic" are practitioner judgement (unsourced) |
| `national-origin-proxy` | "Native English speaker", "native-level" screen by origin, not by the language task; "US citizen" is a CHECK (usually a work-authorisation question in disguise) | [34] |
| `class-proxy` | "Culture fit" works as a class and demographic proxy | [79] |
| `disability` | No disability questions pre-offer; physical demands are phrased "with or without reasonable accommodation" | [46][35] |
| `appearance` | No photograph before an offer ("photo", "photograph", "send a picture"); no grooming or looks rule ("clean-shaven") unless a job-related safety rule | [34] |
| `gender` | "he/his/she/her" for the hire, "male/female/man/woman" (CHECK: fine for a named person or an equal-opportunity close) | [34] |
| `religion` | Any religious term ("Christian values") | [34] |
| `family-status` | Marital status, "mothers returning to work", pregnancy; "parents", "children" and "childcare" are a CHECK ("parental leave" and "childcare vouchers" are fine as benefits; a childcare line as a requirement is not) | [74] |
| `gap-proxy` | Gap and medical-leave patterns are alleged (not ruled) to screen out disabled applicants | [108] |
| `location-proxy` | ZIP code used as a proxy is named in Illinois HB 3773 | [72] |
| `label` | "Rockstar", "ninja": say nothing about the work and read as a culture signal | practitioner judgement (unsourced) |
| `posting-law` | Colorado: "open until filled" is not a compliant application window [57]. California: never seek salary history ("include your salary history", "current salary") [56] | [57][56] |
| `masculine-coded` | Masculine-coded wording (e.g. "leader", "competitive", "dominant") reduced women's sense of belonging; neutral swaps exist (e.g. "excellence" for "dominance") | [31] |
| `feminine-coded` | Reported for balance only; no action | [31] |

The gendered-word stems follow the Gaucher, Friesen and Kay (2011) word lists
as commonly reproduced [31]. Their finding is about the overall balance of a
posting, so a single masculine-coded word in job content ("analyse the
data") is not a problem; a posting full of "dominant, competitive,
assertive" is.

## 2. Severities

- `FLAG`: change it, or record the owner's one-line defence.
- `CHECK`: context decides. Read the sentence.
- `info`: count only.

Exit code 1 means at least one FLAG is unhandled.

## 3. Known benign uses

| Hit | Fine when | Not fine when |
|---|---|---|
| lead | Job title ("Lead Engineer"), "lead the on-call rotation" | "a natural leader" as a trait |
| competitive | "competitive salary" (but give the range if stated) | "a competitive person" |
| challenging | "challenging problems" | "thrives on challenge" as a trait |
| force | "workforce" | "forceful" |
| persist | "persistent storage" | "persistent personality" |
| healthy | "healthy pipeline" | describing people |
| fresh | "fresh approach" | "fresh graduates" |

## 4. What the lint cannot see

The lint is a backstop, not the review. Zero FLAGs does not mean the posting is
clean: read every line against
[protected-traits-and-proxies.md](protected-traits-and-proxies.md) and report
proxies the lint missed, with line numbers, next to the lint's hits.

A seven-line adversarial posting used to test the lexicon (every line should be
reported; the lint gives 14 FLAG and 5 CHECK):

```
We want recent graduates or someone under 35 with native-level English.
Must be a native English speaker. Ideal for a digitally native self-starter.
Perfect for young professionals; no older candidates. Overqualified applicants need not apply.
He will own the rotation and his work matters. Must have own car. Send a photograph.
Please include your salary history. Must be a US citizen. Candidates should be able-bodied.
Mothers returning to work welcome. Christian values. Clean-shaven.
Graduated in 2018 or later.
```

Also read for these yourself:
- Laundry lists of nice-to-haves posing as requirements (anything beyond the
  scorecard's must-haves under "You have").
- Jargon a strong outsider would not know (internal team names, acronyms).
- Must-haves reworded from the scorecard (that is `mirror_check.py`'s job).
- Pay, benefits or deadlines that the owner never stated.

## 5. Extending the lexicon

Add rows to `lint-terms.csv` with a source or "practitioner judgement
(unsourced)". `match` is `word` (whole word), `phrase` (whole phrase; a space
or hyphen in the term matches either), `stem` (word start) or `regex` (a
case-insensitive pattern, bounded so it never matches inside a longer word;
quote it if it has a comma). `word` and `phrase` also match a plural
(-s/-es), so "recent graduate" catches "recent graduates". Keep one canonical copy: the same
lexicon is used by Harper's JD skill as a separate file.

Sources: [sources.md](sources.md).
