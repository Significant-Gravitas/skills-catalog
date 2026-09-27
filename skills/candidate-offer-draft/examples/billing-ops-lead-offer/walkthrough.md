# Worked example: offer draft for Sam, Billing Operations Lead (fictional)

Everything here is fictional: Acme Ltd, Maya Chen (hiring manager), Luis
Ortega (people lead, pay approver and signatory), and candidate Samira
"Sam" Okafor (B-011). The files beside this walkthrough are the real inputs.
The date is 2026-09-27.

## Request (hard case)

> Maya: "We're hiring Sam! Draft the offer. She told me she's on £59k, so
> match that plus 10%. Start 20 October, give her until the 24th. Add a
> background check. Template's in Drive."

## Step 1. Approval gate

The decision record shows Maya as the decision-maker, "hire", on
2026-09-26. The offer terms need an authorised approver. The hiring plan
names Luis Ortega for pay and offers, and the hiring jurisdiction (UK,
England), which Harper records as `jurisdiction` in `terms.json`.

## Step 2. Get the template

`find_capability(query="google drive download file")` → `describe_capability`
→ `run_capability(..., validate_only=true)` → download "Acme offer template
v3". Saved to `/home/user/offer/template.docx`. (The markdown copy in this
folder, `offer-template.md`, stands in for it.)

## Step 3. First pass at terms, and the check

Harper writes Maya's instructions into `terms-draft.json` exactly as given,
so the check can show her what is wrong. Nothing is filled from Harper's own
judgement.

```
python3 scripts/check_terms.py terms-draft.json --email email-draft.txt --today 2026-09-27
```

```
ERROR   PAY_HISTORY            base_pay: refers to pay history ('current salary'); never use or derive terms from it
ERROR   NO_SOURCE              response_by: filled without a source
ERROR   NO_APPROVER            response_by: filled without an approver
ERROR   START_BEFORE_RESPONSE  start_date: start 2026-10-20 is before response-by 2026-10-24
ERROR   CONTINGENCY_SOURCE     contingencies: contingency lines come only from the company's offer template
ERROR   EMAIL_MISMATCH         email-draft.txt: amount '£65k' is not in the approved terms
ERROR   EMAIL_MISMATCH         email-draft.txt: date '9 October 2026' is not an approved term date
ERROR   AMBIGUOUS_DATE         email-draft.txt: '06/01/2027' can be read two ways; write '6 January 2027'
WARNING OPEN                   bonus_text: no approved value: [OWNER TO CONFIRM]
WARNING OPEN                   equity_text: no approved value: [OWNER TO CONFIRM]
WARNING LOCAL_CHECK_RULES      contingencies: background-check contingency, jurisdiction 'UK (England)': US FCRA wording does not apply; local background-check rules may (e.g. UK DBS, UK GDPR Art. 10). Confirm the notice/consent step with the people lead
8 error(s), 3 warning(s).
```

What Harper tells Maya:

> I can't set pay from Sam's current salary. Our process never uses current
> pay, wherever the hire is, and some jurisdictions also ban relying on it
> (for example California [56][75]). Could Luis confirm the base pay from the
> approved L4 band? I've also held three other things:
> - The start date is before the response date. Which one moves?
> - The background check has to come from the template's own clause (section
>   4.2), and Sam's separate written consent must be on record before the
>   check runs, as the clause says. This is a UK hire, so US FCRA forms do not
>   apply, but UK rules on criminal-record checks may (for example DBS and UK
>   GDPR Article 10). Luis, please confirm the consent step.
> - The draft email's £65k and 06/01/2027 don't match any approved term.

## Step 4. Approved terms, and the check passes

Luis emails the approved base pay (£62,000 from the L4 band) and confirms
that bonus does not apply. Maya confirms a 6 January 2027 start and a
9 October 2026 response date. The contingencies are the template's
sections 4.1 and 4.2, with Sam's consent step on record
(`fcra_disclosure_on_record: true`; for a non-US hire this field records the
local notice/consent step).

```
python3 scripts/check_terms.py terms.json --email email.txt --today 2026-09-27
WARNING OPEN                   equity_text: no approved value: [OWNER TO CONFIRM]
0 error(s), 1 warning(s).
```

## Step 5. Fill the template

```
python3 scripts/fill_offer_template.py offer-template.md terms.json \
  ~/workspace/hiring/billing-ops-lead/offers/B-011/letter.md
```

This writes `DRAFT-letter.md`. Only placeholders change. The start and
response dates are written out ("6 January 2027", "9 October 2026"; use
`--date-style iso` only if the template requires ISO dates), and equity shows
`[OWNER TO CONFIRM: equity_text]`. The report says that `contingencies` is
an approved term the template never uses, as a placeholder. That is
expected: the template writes its conditions in full. Then:

```
python3 scripts/check_terms.py terms.json --letter .../DRAFT-letter.md --today 2026-09-27
```

This passes with the same one warning.

The check also catches the core pay term written the wrong way. Each of these
fixtures beside this walkthrough fails against `terms.json`:

| File | Text | Result |
|---|---|---|
| `email-bare-amount.txt` | "a base salary of 65,000 a year" | `EMAIL_MISMATCH` (65,000 is not approved) and `NO_CURRENCY` |
| `email-wrong-currency.txt` | "$62,000 per year" | `CURRENCY_MISMATCH` ($ against GBP) |
| `email-wrong-period.txt` | "62,000 per month" | `PAY_PERIOD_MISMATCH` (month against year) |
| `email-currency-word.txt` | "62,000 euros a year" | `CURRENCY_MISMATCH` (EUR against GBP) |
| `email-yearless-date.txt` | "Please reply by Friday 16 October." | `EMAIL_MISMATCH` ("16 October", no year, matches no approved date) |
| `email-unapproved-percent.txt` | "plus a 10% annual bonus" (bonus is "Not applicable") | `EMAIL_MISMATCH` (no approved term states 10%) |
| `email-extra-amount.txt` | "Sign-on bonus: £2,026." | `EMAIL_MISMATCH` (2026 is only a year in the dates, never an approved amount) |
| `email-hourly-wrong-rate.txt`, against `terms-hourly.json` (£18.50 per hour, start 15 November) | "£15 an hour" | `EMAIL_MISMATCH` (15 is a day of the start date, not the approved rate) |

Approved amounts come only from money-bearing terms (`base_pay`, and
amounts written in terms such as `bonus_text`), never from the digits of a
date, level, location or template section number. An amount shown as the
pay rate ("salary ... £2,000 per month") must equal `base_pay`, even if the
same figure is approved elsewhere as a bonus. "65.000 €" and "65 000 GBP"
are each read as one amount.

A yearless date that does match an approved one ("reply by 9 October") gives
a `YEARLESS_DATE` warning: add the year. An amount written only in words
("sixty-five thousand pounds") is a `SPELLED_AMOUNT` error, because the check
cannot verify it; write it in figures with the approved currency.

## Step 6. Output returned

1. `DRAFT-letter.md` (or `.docx`) link, with one open term: equity.
2. Email draft (`email.txt`), matching the letter.
3. Internal checklist (`templates/offer-checklist.md` filled): every term
   with its source, approver and date; the pay basis line "approved band
   only; current pay was volunteered and not used"; the background-check
   consent step on record (UK, so not a US FCRA disclosure); the reviews
   still needed from Luis (people lead), counsel if Acme requires it, and
   the signatory.
4. "Status: DRAFT, not sent. One term open."

Harper does not send the email, share the letter with Sam, negotiate, or
record acceptance. If Sam comes back asking for £66,000, Harper logs it for
Luis and drafts nothing until Luis gives fresh written approval.
