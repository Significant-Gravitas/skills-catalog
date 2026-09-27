# Worked example: Priya Nair, Senior Backend Engineer (fictional)

End to end, from "Lena wants to hire Priya" to the first-week hand-off.
Files in this folder: terms.json, company-template.md (the company's own
template with placeholders), close-plan.csv, counter-log.csv, email.txt
(the clean email draft), email-mistake.txt (the earlier draft with wrong
figures), company-template-pt.md and letter-pt-DRAFT.md (the Lisbon
office's Portuguese-format letter), pt-euros-mistake.md and
de-euro-mistake.md (wrong-base drafts that spell the currency out).
Owner timezone Europe/Lisbon. Every
command below runs from the package dir as written.

## Step 1 - Band first (9 Oct)

User: "Lena said yes to Priya. What should we pay?"

Sofia asks one thing: "What's the approved band for the L5 backend role, and
who approved it?" Owner: "EUR 95-110k base, Lena and Tom in finance signed
it off on 1 Sep." Recorded FACT with source (offer approvals sheet).
No figure was suggested before this answer.

## Step 2 - Pre-close (screen notes, 18 Sep; call 10 Oct)

- Values (her words): "base matters most this year"; "I want to own
  billing, not maintain it." [FACT, screen notes]
- Other processes: "one other final round, decision next week" [candidate's
  words, unverified].
- Notice: "one month" [FACT, her words] -> start 1 Dec is realistic.
- Answer-by set with Lena before the offer: 16 Oct 17:00 Lisbon (inside the
  24-48 h default after the letter - default, confirmed by the owner).

## Step 3 - Compose from evidence (11 Oct)

```
cd ~/skills/job-offer-and-close-plan && python3 scripts/offer_math.py \
  --band-min 95000 --band-max 110000 --currency EUR \
  --band-approver "Lena Ortiz + finance (Tom Weber)" --band-approved-on 2026-09-01 \
  --base 104000 --equity-text "0.15% options, standard vesting"
```

Output pasted into the brief: position in band 60.0%, base 101.5% of
midpoint, room to ceiling EUR 6,000, first-year cash EUR 104,000.

| Element | Proposed | Evidence |
|---|---|---|
| Base | EUR 104,000 | In band (60%); base is her stated top priority [FACT, screen notes] |
| Equity | 0.15% options, standard vesting | L5 equity grid [FACT] |
| Start | 1 Dec | Her stated notice: "one month" [FACT] |

Likely negotiation: base. Paired give inside the band: up to EUR 108,000
base with no signing bonus. Walk-away line: band max EUR 110,000; an
above-band ask goes to Tom. Brief saved to
~/workspace/hiring/offers/senior-backend-priya-nair/brief-2026-10-11.md.

## Step 4 - Approvals (12 Oct)

Tom and Lena approve the brief.
`cd ~/skills/job-offer-and-close-plan && python3 scripts/check_terms.py examples/priya-nair-backend/terms.json --today 2026-10-12`
-> 0 errors, 0 warnings.

## Step 5 - Letter (13-14 Oct)

Lena makes the verbal offer on 13 Oct (talking points from
templates/close-messages.md). Then:

```
cd ~/skills/job-offer-and-close-plan && \
python3 scripts/fill_offer_template.py examples/priya-nair-backend/company-template.md \
  examples/priya-nair-backend/terms.json /tmp/priya/letter.md
# -> wrote /tmp/priya/letter-DRAFT.md; placeholders: 19 found, 19 filled, 0 left for the owner
#    approved terms with no placeholder in the template (...): monthly_base
#    (monthly_base belongs to the Portuguese-format letter below)
cd ~/skills/job-offer-and-close-plan && \
python3 scripts/check_terms.py examples/priya-nair-backend/terms.json --today 2026-10-14 \
  --text /tmp/priya/letter-DRAFT.md --text examples/priya-nair-backend/email.txt \
  --template examples/priya-nair-backend/company-template.md
# -> 0 errors, 0 warnings
```

Clauses 6 and 7 of the template came through untouched. The DRAFT goes to
the owner via write_workspace_file with a workspace:// link; the owner sends.

The same check reads a Word letter directly: with the company's
template.docx, `fill_offer_template.py` writes letter-DRAFT.docx and
`check_terms.py ... --text /home/user/offer/priya/letter-DRAFT.docx` reads
its body, headers and footers (0 errors, 0 warnings). A file that is neither
UTF-8 text nor a .docx exits 2 with "is not UTF-8 text", never a traceback.

The email draft (email.txt) carries Lena's phone (+351 912 345 678) and
the company footer (Rua Augusta 1250, 1100-048 Lisboa, HRB 123456). None of
those has a currency sign or code next to it, so none is read as money and
the check stays at 0 errors.

An earlier email draft (email-mistake.txt) said "EUR 106,000 base, signing
EUR 5k" by mistake. Both were caught (no signing bonus was approved):

```
cd ~/skills/job-offer-and-close-plan && python3 scripts/check_terms.py \
  examples/priya-nair-backend/terms.json --today 2026-10-14 \
  --text examples/priya-nair-backend/email-mistake.txt
ERROR examples/priya-nair-backend/email-mistake.txt: figure 'EUR 106,000' does not match any approved term
ERROR examples/priya-nair-backend/email-mistake.txt: figure 'EUR 5k' does not match any approved term
2 errors, 0 warnings
```

The Lisbon office also keeps a Portuguese-format letter
(company-template-pt.md; its draft is letter-pt-DRAFT.md). It writes
"EUR 104 000" (space-grouped), "14 payments of EUR 7.428,57" (decimal
comma) and a meal allowance of "9,60 EUR" per working day that the
template itself fixes. The monthly figure is derived, so it is its own
term (`monthly_base`, 7428.57, source "base_pay / 14 payments", approver
Tom); the allowance is template wording, so `--template` reports it as
INFO and the skill does not touch it:

```
cd ~/skills/job-offer-and-close-plan && python3 scripts/check_terms.py \
  examples/priya-nair-backend/terms.json --today 2026-10-14 \
  --text examples/priya-nair-backend/letter-pt-DRAFT.md \
  --template examples/priya-nair-backend/company-template-pt.md
INFO  examples/priya-nair-backend/letter-pt-DRAFT.md: figure '9,60 EUR' is fixed wording in the company template (binding; not a term, not edited)
0 errors, 0 warnings
```

Without `--template` the allowance is an ERROR ("does not match any
approved term"); the fix is to pass the template or add the allowance as
an approved term, never to ignore the line.

A figure in another currency ("USD 104,000" on this EUR offer) is also an
ERROR.

The currency is often spelled out rather than coded: "150.000 euros" in a
Portuguese draft, "150.000 Euro" in a German one for the GmbH, "R$
150.000,00" or "US$150,000" elsewhere. Those are money too, and a wrong
base written that way is caught:

```
cd ~/skills/job-offer-and-close-plan && python3 scripts/check_terms.py   examples/priya-nair-backend/terms.json --today 2026-10-14   --text examples/priya-nair-backend/pt-euros-mistake.md   --text examples/priya-nair-backend/de-euro-mistake.md
ERROR examples/priya-nair-backend/pt-euros-mistake.md: figure '150.000 euros' does not match any approved term
ERROR examples/priya-nair-backend/pt-euros-mistake.md: figure '10 714,29 euros' does not match any approved term
ERROR examples/priya-nair-backend/de-euro-mistake.md: figure '150.000 Euro' does not match any approved term
ERROR examples/priya-nair-backend/de-euro-mistake.md: figure '10.714,29 Euro' does not match any approved term
4 errors, 0 warnings
```

A bare "150.000" with no currency at all is a WARN ("has no currency and
matches no approved term"), never a silent pass.

## Step 6 - Counter (14 Oct)

Priya: "Could you get to 108 on base? That would make it easy."

```
cd ~/skills/job-offer-and-close-plan && python3 scripts/offer_math.py \
  --band-min 95000 --band-max 110000 --currency EUR \
  --band-approver "Tom Weber" --offer-base 104000 --ask-base 108000 \
  --proposal-base 108000 --proposal-signing 0
```

| Element | Offer as extended | Candidate ask | Proposal |
|---|---|---|---|
| Base | EUR 104,000 | EUR 108,000 | EUR 108,000 |
| Position in band | 60.0% | 86.7% | 86.7% |
| First-year cash | EUR 104,000 | EUR 108,000 | EUR 108,000 |

Paired give EUR 4,000; room left to ceiling EUR 2,000. Tom approves;
counter-log.csv gets the row with approver and date. terms.json base_pay is
updated, the letter is re-filled and re-checked, and a holding reply is
drafted for the owner.

## Step 7 - Close plan check (15 Oct)

```
cd ~/skills/job-offer-and-close-plan && python3 scripts/close_plan.py \
  ~/workspace/hiring/offers/senior-backend-priya-nair/close-plan.csv --today 2026-10-15 \
  --candidate "Priya Nair" --assistant Sofia --terms examples/priya-nair-backend/terms.json
```

```
- 2026-10-14 [OVERDUE] letter sent (after verbal yes) - Lena Ortiz (Europe/Lisbon)
- 2026-10-15 [DUE TODAY] questions answered - Dev Rao (Europe/Lisbon)
- 2026-10-16 [open] answer-by - Lena Ortiz (Europe/Lisbon)
- 2026-10-19 [open] signature - Lena Ortiz (Europe/Lisbon)
Overdue since 2026-10-14: letter sent (after verbal yes) - Lena Ortiz
Next check date: 2026-10-15
```

(Abridged: the "Close plan as of" header, the two done tracks and the
hand-off are omitted. Exit 1 because a track is overdue.) Every track
has an internal owner: Lena sends the letter and chases the answer and the
signature; Priya appears only in the notes. With `--candidate` and
`--assistant`, a plan that made Priya the answer-by owner (as "Priya",
"Priya Nair" or "Priya Nair (candidate)") or Sofia the sender would show a
PROBLEM line for each.

Reply to the owner leads with the overdue track: "The revised letter
(EUR 108,000) is drafted and approved but not sent - Lena, send it today? Dev owes
Priya the on-call answer today; nudge drafted." On the owner's yes, the
last action of the turn is
`run_capability(id="tool:schedule_followup", input={"message": "Check offer status for Priya Nair (Senior Backend): answer-by 2026-10-16 17:00 Europe/Lisbon", "delay_seconds": 86400})`.

## Step 8 - Signature and hand-off (19-20 Oct)

Priya signs on 19 Oct. On the owner's confirmation the candidates.csv row
moves to "accepted". With Linear connected and the owner's yes:
`find_capability("linear create issue")` -> `run_capability(...)` filing
"New hire: Senior Backend Engineer, starts 2026-12-01" for Marta, with no
comp or personal details. Onboarding is Marta's from here.
