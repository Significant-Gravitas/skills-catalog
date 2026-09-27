# Worked example: Oriel Health, April 2026 (fictional)

Request from Jo: "Invoice Oriel for April: the retainer plus the extra
workshop day." Inputs: SOW-014 (signed 2 Jan 2026: retainer £3,500 a month,
cl. 4; extra days £850, cl. 5; net 30, cl. 6), PO 7781, an email from M. Ode
(Oriel) on 10 April approving an extra workshop day "at £900", `intake.json`
(UK, VAT registered, approver Jo), and the register in this folder
(`invoice-register.csv`). The first draft is `draft.json`.

Hard cases: the April retainer was already approved to issue early (INV-1045);
a rate conflict between the SOW and an email; VAT treatment and payment
details not supplied; a register with gaps because it is only a working index.

## 1. Build the draft

`draft.json` built from `templates/draft.json`, one line per approved charge,
each with a source and a line key. VAT fields left blank: the rate was not
supplied. Payment details blank: not in the approved record.

## 2. Scripts

```
cd ~/skills/invoice-drafting-and-issue && python3 scripts/invoice_totals.py /home/user/work/draft.json --write
cd ~/skills/invoice-drafting-and-issue && python3 scripts/field_check.py /home/user/work/draft.json --regime uk-vat
cd ~/skills/invoice-drafting-and-issue && python3 scripts/register_check.py /home/user/work/draft.json --register ~/workspace/bookkeeping/bramble-design/invoice-register.csv
```

- Totals: line 1 £3,500.00; line 2 £900.00; subtotal £4,400.00; total before
  tax £4,400.00; no rounding.
- Fields (uk-vat), BLOCKS APPROVAL: payment instructions; seller VAT number;
  VAT rate per line (lines 1, 2); VAT total; unresolved conflict on line 2 rate
  (£850 per SOW-014 cl. 5 vs £900 per M. Ode email). BLOCKS ISSUE: invoice
  number; customer VAT number not supplied.
- Register: `REPEAT SOW-014/retainer/2026-04: already in register as ['INV-1045']`.
  Gaps INV-1039, 1040, 1043, 1044, 1046, 1048 to 1054: the register is incomplete, so
  ask for the billing export before trusting the sequence. Next number
  suggestion INV-1056 (suggestion only).

## 3. What the repeat means

INV-1045 was approved on 2 April for the April retainer ("issued early, per
Jo"). Billing the retainer again would double-bill Oriel £3,500. The draft
drops line 1 and says why; if Jo says INV-1045 was never actually issued, the
register row changes only on Jo's word and a billing export.

## 4. Review block (to Jo)

**DRAFT, not issued.** Oriel Health Ltd · GBP 900.00 or 850.00 before VAT
(rate to settle) · approver Jo.

| Check | Result |
| --- | --- |
| Totals | 1 line; £900.00 or £850.00 before VAT; no rounding (invoice_totals.py) |
| Double billing | April retainer already on INV-1045 (approved 2 Apr): removed from this draft |
| Required fields (UK VAT) | missing: seller VAT number, VAT rate, VAT total, payment details |
| Conflict | extra-day rate: £850 (SOW-014 cl. 5) vs £900 (M. Ode email, 10 Apr) |
| Numbering | to be assigned; register incomplete, billing export requested |

One `ask_question` card: Q1 rate (`£850 per SOW-014 cl. 5` · `£900 per M. Ode
email 10 Apr` · `Neither: I will type it`); Q2 VAT (`I will supply the rate` ·
`Ask the accountant` · `Leave VAT blank on this draft`); Q3 payment details;
Q4 "Was INV-1045 issued to Oriel?". No action question yet, because approval is
still blocked.

Awaiting approval: none of assign, create or send can happen until the rate,
the VAT treatment and the payment details are settled.

## 5. After the answers (continuation)

Jo: Q1 "£900 per M. Ode email" (the customer agreed a higher rate in writing;
Jo accepts it); Q2 "Ask the accountant"; Dev later supplies "20% standard rate,
per-invoice rounding"; Q3 Jo types the bank details; Q4 "Yes, INV-1045 went out
2 April".

- Re-run `invoice_totals.py`: net £900.00; VAT £180.00; total £1,080.00; per-line
  and per-invoice VAT equal.
- `field_check.py`: BLOCKS APPROVAL (0); BLOCKS ISSUE: invoice number;
  customer VAT number not supplied (only needed for some supplies; noted for
  Dev).
- Render: `render_invoice.py ... --out /home/user/out/draft-oriel-2026-04.html --pdf`
  (HTML delivered if no headless Chrome). Hash it.
- Before the action card: `find_capability("xero create invoice")` finds
  nothing in this workspace, so there is no Draft-capable tool and the card
  does not offer to create it in Xero.
- Action card (draft oriel-2026-04, £1,080.00 including VAT £180.00; suggested
  next number INV-1056 shown as a suggestion; "I cannot create invoices in Xero
  from here; you will enter it"):
  `Approve exactly as shown: I will number and issue it myself` ·
  `Approve with the changes I type` · `Not yet`.
  Jo picks "I will number and issue it myself". It is noted in the register
  (`approved_to_issue`, Jo's answer as evidence), not logged as an action for
  Mina; Mina gives Jo the PDF and the figures to enter. Nothing was created.
- Jo later says "Issued as INV-1056 today". Register row appended:
  `INV-1056, Oriel Health Ltd, SOW-014, SOW-014/extra-day/2026-04-14, 1080.00,
  GBP, issued_per_owner, 2026-05-02, Jo, , Jo in chat 2026-05-02`.

## What a wrong answer would look like

- A £4,400 draft that bills the April retainer twice.
- Picking £850 because "the contract wins", or £900 because it is newer.
- "VAT at 20%" before the accountant said so.
- Copying bank details from INV-1041.
- "Invoice INV-1056 has been sent to Oriel."
