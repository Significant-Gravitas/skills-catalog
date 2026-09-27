# Hard case: Marco Silva, Account Executive, San Francisco (fictional)

What makes it hard: a sales role (base + OTE + commission plan), the
candidate volunteers his current pay, asks above band, cites a competing
offer, and the template has a background-check contingency with no
disclosure on record. Owner: Rita Cole (VP Sales), timezone
America/Los_Angeles. Band: USD 90,000-105,000 base, approved by Rita and
finance on 20 Sep. AE comp plan FY27: USD 95,000 on-target variable.

## 1. Volunteered pay history

Screen call note from the owner: "He said he's on 105 base now and wants a
step up." Sofia's reply, one line, then on:

> I won't record or use his current pay - the offer is built from the
> approved band and what he said matters to him ("a patch I can grow",
> "a plan I can actually hit").

The owner's first draft of terms (terms-first-draft.json) sourced base as
"matches his current base salary of 105k". `check_terms.py` refuses it:

```
cd ~/skills/job-offer-and-close-plan && python3 scripts/check_terms.py terms-first-draft.json --today 2026-10-20
ERROR entity: missing - mark [OWNER TO CONFIRM] in the draft and ask the owner
... (8 more "missing" errors: title, level, start_date, currency, pay_period, response_by, signatory, contact_for_questions)
ERROR base_pay: references current/past pay ('current base salary'). Salary history may not be asked for or used; remove it and re-source from the band
ERROR ote 190,000 != base 105,000 + variable 95,000 = 200,000
WARN  sales offer with OTE but no commission_plan_text: carry the approved plan wording, do not summarise it
WARN  contingency[0] background check: no standalone FCRA disclosure/authorisation on record. It must precede procuring the report; flag to the owner
11 errors, 2 warnings
```

(Abridged: 8 of the 9 missing-term errors are collapsed into one line.)

The OTE typo would have reached the approver: the script caught it.

## 2. Composition with OTE

```
cd ~/skills/job-offer-and-close-plan && python3 scripts/offer_math.py --band-min 90000 --band-max 105000 --currency USD \
  --band-approver "Rita Cole + finance" --band-approved-on 2026-09-20 \
  --base 100000 --variable-target 95000
```

Base USD 100,000 (66.7% of band), on-target variable USD 95,000, OTE
USD 195,000, pay mix 51/49. The commission plan is carried as the plan's
own words ("as set out in the FY27 Mid-Market AE Commission Plan, which
governs"); no "likely earnings" and no attainment guess. The ramp is not in
the plan the owner shared, so the letter shows `[OWNER TO CONFIRM: ramp_text]`.

## 3. Counter above band, with a competing offer

Marco: "I've got an offer at 230 OTE elsewhere. I need 115 base."

```
cd ~/skills/job-offer-and-close-plan && python3 scripts/offer_math.py --band-min 90000 --band-max 105000 --currency USD \
  --band-approver "Rita Cole + finance" --offer-base 100000 --offer-variable 95000 \
  --ask-base 115000 --ask-variable 95000 --proposal-base 105000 --proposal-variable 95000
```

| Element | Offer as extended | Candidate ask | Proposal |
|---|---|---|---|
| Base | USD 100,000 | USD 115,000 | USD 105,000 |
| Position in band | 66.7% | 166.7% | 100.0% |
| OTE | USD 195,000 | USD 210,000 | USD 200,000 |

FLAG: ask base is USD 10,000 above band max - escalate to Rita and finance;
do not counter above band.

In the brief:
- Competing offer: "230 OTE elsewhere" [candidate's words, unverified]. No
  request for the letter; no contact with the other company.
- The proposal at band max is Rita's call; the above-band ask is finance's.
- counter-log.csv row: `ask: base USD 115,000 ("I need 115 base"); history
  volunteered and not recorded`.

## 4. Contingency order

The template's section 7 makes the offer conditional on a background check.
No standalone FCRA disclosure and authorisation is on record, so Sofia
flags it and changes the **close plan**, not the letter:

| track | owner | due | tz |
|---|---|---|---|
| standalone disclosure + authorisation signed (before the check is ordered) | Jin Park | 2026-10-22 | America/Los_Angeles |
| background check ordered | Jin Park | 2026-10-23 | America/Los_Angeles |
| answer-by (Marco answers; Rita chases) | Rita Cole | 2026-10-23 | America/Los_Angeles |

The owner's first version of this plan had "Marco" as the answer-by owner.
`close_plan.py ... --candidate "Marco Silva" --assistant Sofia --terms terms.json`
caught it even though only the first name was written:

```
PROBLEM line 5 'answer-by': owner 'Marco' must be an internal person, not the assistant or the candidate (put the candidate in notes)
```

Had the plan also carried a medical exam or drug test dated before the
answer-by, the PROBLEM line says it breaks the skill's rule (after written
acceptance) and that the ADA itself requires only "after a conditional
offer"; a drug test is not an ADA medical exam, so state drug-testing rules
go to counsel.

This is a San Francisco hire, so a state and local layer may apply on top
of the FCRA steps: California's Fair Chance Act (Gov. Code 12952: conviction
history only after a conditional offer, with its own notice-and-respond
steps), ICRAA disclosures, Labor Code 1024.5 limits on credit reports, and
the San Francisco fair-chance ordinance. Sofia does not decide which apply:
she flags "may apply, confirm with counsel" and drafts the attorney
questions with templates/attorney-brief.md.

If the report comes back adverse, Sofia stops: no decline draft, no close
message; the owner's FCRA adverse-action process and the attorney take it.

## 5. The letter: template figures and 401(k)

The Harbor template (company-template-us.md) fixes a "$1,000 annual
learning budget" and a "401(k) plan" in its benefits clause.
Its variable-pay clause also carries a `{{ramp_text}}` placeholder, and
the ramp term is still empty, so the fill stops short (exit 1):

```
cd ~/skills/job-offer-and-close-plan && python3 scripts/fill_offer_template.py   examples/marco-silva-sales-hard-case/company-template-us.md   examples/marco-silva-sales-hard-case/terms.json   examples/marco-silva-sales-hard-case/letter-us-DRAFT.md
wrote examples/marco-silva-sales-hard-case/letter-us-DRAFT.md
placeholders: 16 found, 15 filled, 1 left for the owner
  [OWNER TO CONFIRM: ramp_text] - no value
```

letter-us-DRAFT.md shows "Ramp for the first quarter: [OWNER TO CONFIRM:
ramp_text]." until Rita supplies the approved ramp wording. Then:

```
cd ~/skills/job-offer-and-close-plan && python3 scripts/check_terms.py \
  examples/marco-silva-sales-hard-case/terms.json --today 2026-10-20 \
  --text examples/marco-silva-sales-hard-case/letter-us-DRAFT.md \
  --template examples/marco-silva-sales-hard-case/company-template-us.md
WARN  contingency[0] background check: no standalone FCRA disclosure/authorisation on record. It must precede procuring the report; flag to the owner
INFO  examples/marco-silva-sales-hard-case/letter-us-DRAFT.md: figure '$1,000' is fixed wording in the company template (binding; not a term, not edited)
0 errors, 1 warnings
```

"401(k)" and "401k" are plan names, not money, so they are ignored. The
remaining WARN is the disclosure gap handled in section 4.

## 6. What the owner sees first

> Three items before anything reaches Marco: (1) he asked for USD 115,000
> base, USD 10,000 over band - Rita and finance decide; the in-band
> proposal is USD 105,000 base / USD 200,000 OTE. (2) The background-check
> contingency has no standalone disclosure on file - Jin needs to send it
> before the check. (3) California and San Francisco fair-chance and
> credit-check rules may add steps around the check - may apply, confirm
> with counsel; attorney brief drafted. Letter drafted with one open term
> (ramp). Want the holding reply to Marco drafted?
