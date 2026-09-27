# Contingency order and wording

Read when the offer carries any condition (background check, credit or
consumer report, medical exam, right to work, references, licences). The
rule for the skill: **contingency wording and order come from the company
template only**; this file tells you what to check and what to flag. It is
not legal advice. Anything outside it goes to the attorney.

Dated 2026-09-27. Sources are numbered as in the recruiting dossier
(docs/research/recruiting.md, section 8); see references/sources.md.

## 1. Background checks and consumer reports (US, FCRA)

- Before the employer procures a consumer report for employment purposes,
  the candidate must get a **clear and conspicuous disclosure in a document
  that consists solely of the disclosure**, and give **written
  authorisation** [48][76]. The disclosure is a standalone step; it is not
  a clause buried in the offer letter.
- If the result may lead to withdrawing the offer, the employer runs the
  **two-step adverse-action process**: a pre-adverse-action notice with a
  copy of the report and the summary of rights, time for the candidate to
  respond, then the adverse-action notice [48][76].
- What the skill does:
  - When the template has a background-check contingency, set
    `fcra_disclosure_on_record` in terms.json only if the owner confirms the
    standalone disclosure and authorisation are on file. Otherwise
    `scripts/check_terms.py` warns and you flag it to the owner in one line.
  - State and local fair-chance and credit-check laws (for example
    California Gov. Code 12952, the Fair Chance Act: conviction history only
    after a conditional offer, with its own notice-and-respond steps; ICRAA
    disclosures; California Labor Code 1024.5 limits on credit reports; San
    Francisco and New York City fair-chance ordinances) may add steps before
    or after the check. The FTC guidance itself tells employers to review
    state law [76]. Dated 2026-09-27; may apply, confirm with counsel. Flag
    it to the owner in one line and route the question to the attorney with
    templates/attorney-brief.md.
  - If a check comes back adverse, **stop**. Draft no plain decline and no
    close-plan message about it. Route to the owner's FCRA adverse-action
    process and the attorney.

## 2. Medical examinations (US, ADA)

- No medical questions or exams before an offer. After a conditional offer
  and before duties start, an exam is allowed only if **all entering
  employees in the same job category** are required to take it, and the
  results are kept confidential and separate [46].
- What the skill does: a medical-exam contingency needs `post_offer: true`
  and `all_entrants_in_category: true` in terms.json, confirmed by the owner;
  `check_terms.py` errors otherwise. Never record a result, a condition, or
  anything health-related in the brief, the close plan, the tracker or chat.
- UK: no pre-offer health questions except narrow exceptions [58]; route to
  the people lead.

## 3. Right to work, references, licences

- Right-to-work wording comes from the template only; never paraphrase it
  and never infer eligibility from nationality, name, accent or location.
- Reference checks happen only "where their process allows"; the skill
  records the owner's plan but does not design the calls (dossier 7.3 lists
  structured reference checks as an uncovered gap).
- Identity verification for remote hires (deepfake and stolen-identity
  schemes are documented [81][103]): if the owner reports a mismatch between
  the ID name and the interviewed identity, record it as a FACT with its
  source and hand the verification step to the owner. Never infer fraud
  from accent, nationality, location or name.

## 4. Order in the letter

1. Keep the template's order. `fill_offer_template.py` does not reorder
   clauses; do not move them by hand either.
2. If the template lists a background check but the close plan dates the
   check before the disclosure track, fix the **close plan** (disclosure
   and authorisation track first), not the letter.
3. Medical exam and drug-test tracks are dated after the offer is accepted
   in writing. That is this skill's house rule and is stricter than the
   law: the ADA [46] allows an exam after a conditional offer and before
   duties start (section 2). A drug test is not an ADA medical exam
   (42 U.S.C. 12114(d)); state drug-testing laws vary, so confirm them with
   counsel. `scripts/close_plan.py` reports a PROBLEM when a background,
   consumer report or credit track (also "BGC", "Checkr" and similar vendor
   names) has no disclosure + authorisation track or is dated on or before
   it, and when a medical, physical exam or drug-test track is dated before
   the answer-by or signature track; the line says which part is the skill
   rule. With `--terms terms.json` it also reports a background or medical
   contingency that has no track in the plan. It matches words in the track
   name, so copy the optional contingency rows from templates/close-plan.csv.
4. The answer-by date and the start date never depend on a contingency the
   candidate has not yet been told about.
