# Pay history, pay transparency and where comp evidence may come from

Dated 2026-09-27. Numbers in brackets are the recruiting dossier's sources
(references/sources.md). Laws change; every line is "may apply; confirm with
counsel", and no deadline here is quoted as settled.

## Contents
1. The rule the skill follows
2. Why (the law behind it)
3. Allowed comp evidence
4. When pay history is volunteered anyway
5. Pay transparency in the offer and posting

## 1. The rule

**Ask about expectations and priorities, never current or past pay. If pay
history is volunteered, do not record it or use it, and say so in one
line.** This is stricter than some laws on purpose, and it is the same rule
in every jurisdiction so the skill never has to decide which law applies.

## 2. Why

- California Labor Code 432.3: employers may not seek salary history, and
  may not rely on it in deciding whether to offer or what to pay; an
  applicant may volunteer it. Any employer must give the pay scale for the
  position on reasonable request; employers with 15+ employees must include
  it in postings [56]. The skill does not use
  volunteered history either, because that line is easy to cross by accident.
- Many other states and cities ban salary-history questions; the list moves,
  so it is tracked by an external legal tracker [75] rather than restated here.
- Anchoring an offer on prior pay can carry forward existing pay gaps
  (practitioner judgement, unsourced).

## 3. Allowed comp evidence (the only three)

1. The approved band and who approved it, from the owner or finance.
2. The company's own level grid, equity grid, bonus plan or commission plan,
   as written.
3. Posted or public pay data **with a link** (for example, a competitor's
   posting that shows a range), labelled FACT with the link. This informs the
   approver; it never replaces or widens the band.

Never: a band estimate, a percentile, "the market pays about", or a figure
inferred from the company's stage, size or funding.

## 4. When pay history is volunteered

- In chat: reply with one line - "I won't record or use current pay; the
  offer is built from the approved band and what you've told me matters to
  them." - and continue.
- In the counter log: record the ask in the candidate's words **minus the
  history**. "I make 115 now so I need 120" becomes `ask: base EUR 120,000;
  history volunteered and not recorded`.
- A competing offer is different from pay history: it is a current offer
  from another employer. Record it as the candidate's words, unverified
  unless they showed it, and never ask for the document.
- `scripts/check_terms.py` and `scripts/fill_offer_template.py` share one
  detector (`scripts/pay_history.py`) and refuse a term whose value, source
  or notes use a common pay-history phrasing ("current base salary",
  "per prior employer's package", "she earns 100k today"). It catches common
  phrasings; the rule is yours to apply. A term that passes the script but
  was worked out from what the candidate earns is still pay history: drop it.

## 5. Pay transparency

- Some jurisdictions require the pay range (and, in Colorado, a general
  benefits description) in postings [56][57]. That is the posting skill's
  job; here, check that the offer sits inside any range that was posted for
  the role, and flag it if not.
- A posted range the offer falls outside of is an escalation flag for the
  owner and, if they ask, the attorney.
