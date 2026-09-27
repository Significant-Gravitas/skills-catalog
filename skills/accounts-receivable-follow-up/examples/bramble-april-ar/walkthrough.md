# Worked example: Bramble Design Ltd receivables at 30 April 2026 (fictional)

Inputs in this folder: `invoices.csv` (billing export, 30 Apr 17:00),
`payments.csv` (payment records to the same time, plus one dated 1 May),
`bank-main-2026-04.csv` (bank export; the owner confirmed day/month/year),
`dispute-log.csv`, `contact-log.csv`. `unapplied-expected.csv` is the correct
output of `find_unapplied.py`. Account owner: Sam.

Hard cases: a customer who has paid but the payment is not applied (the
original "overdue" chase would have gone to a customer who already paid); an
invoice with no due date; a part-payment; a disputed invoice; a promised date;
a payment dated after the cutoff; a second-stage reminder.

## 1. Unapplied payments first

```
cd ~/skills/accounts-receivable-follow-up && python3 scripts/normalize_export.py /home/user/in/bank-main-2026-04.csv --date-format %d/%m/%Y --currency GBP --out /home/user/work/bank.csv
cd ~/skills/accounts-receivable-follow-up && python3 scripts/find_unapplied.py --bank /home/user/work/bank.csv --invoices /home/user/in/invoices.csv --payments /home/user/in/payments.csv --cutoff "2026-04-30 17:00" --out /home/user/work/unapplied.csv
```

Result: `INV-1042 (Harbour Florists Ltd): 1800.00 on 2026-04-10 'HARBOUR
FLORISTS INV-1042' [invoice number in description]`. The billing export still
shows INV-1042 open. So INV-1042 gets no reminder; Sam is asked to apply the
10 April receipt.

The script also prints `bank export covers 2026-04-01 to 2026-04-12; cutoff
2026-04-30` and `BANK_COVERAGE_GAP: bank ends 2026-04-12, cutoff 2026-04-30`
(exit 1), and writes the same coverage to `/home/user/work/unapplied.coverage.json`
for the aging step. A payment from Kestrel or Tallow & Wick received 13-30 April would
be invisible, so before any draft is offered for sending Sam gets one question:

> The bank export ends 12 April; payments after that cannot be seen. How
> should I proceed?

Options: `I will upload a newer bank export` · `Chase anyway: I confirm nothing
arrived after 12 Apr` · `Not yet`. The answer is recorded verbatim in the
contact log. The aging and drafts below are prepared meanwhile, and each
approval question repeats the gap.

The Oriel credit of 3,500.00 on 1 April is not offered to INV-1045: it predates
that invoice (issued 2 April) and names INV-1038. The Tallow & Wick credit of
640.00 on 9 April matches the recorded part-payment in `payments.csv`, so it is
treated as applied.

If Sam uploads a bank export to 30 April that shows `KESTREL JOINERY LTD
1000.00` on 20 April, the script lists INV-1039 with `customer name, amount
differs (possible part or combined payment)`: INV-1039 moves to `status
unconfirmed` and gets no second reminder for the full 2,150.00 until Sam says
whether the 1,000.00 is a part-payment.

## 2. Aging

```
cd ~/skills/accounts-receivable-follow-up && python3 scripts/ar_aging.py --invoices /home/user/in/invoices.csv --payments /home/user/in/payments.csv --cutoff "2026-04-30 17:00" --disputes <state>/dispute-log.csv --contact-log <state>/contact-log.csv --unapplied /home/user/work/unapplied.csv --out /home/user/work/aging.csv
```

| Invoice | Customer | Due | Open | Days past due | Bucket | Group | Next stage |
| --- | --- | --- | --- | --- | --- | --- | --- |
| INV-1039 | Kestrel Joinery Ltd | 28 Feb | £2,150.00 | 61 | 61-90 | past due, no known dispute | hold: bank export ends 2026-04-12 (planned: second reminder) |
| INV-1047 | Tallow & Wick | 15 Apr | £640.00 of £1,280.00 (part-paid 9 Apr) | 15 | 1-30 | past due, no known dispute | hold: bank export ends 2026-04-12 (planned: first reminder) |
| INV-1051 | Greyline Studio | 20 Apr | £2,400.00 | 10 | 1-30 | disputed: email of 22 Apr says phase 2 not delivered; routed to Sam | — |
| INV-1042 | Harbour Florists Ltd | 31 Mar | £1,800.00 | 30 | 1-30 | status unconfirmed: bank shows £1,800.00 on 10 Apr naming INV-1042; Sam to apply | — |
| INV-1055 | Pell Cafe | none on record | £350.00 | — | unconfirmed | status unconfirmed: ask Sam for the agreed terms | — |
| INV-1049 | Marsh & Co | 25 Apr | £900.00 | 5 | 1-30 | promised payment not yet due (5 May, per reply of 27 Apr) | — |
| INV-1045 | Oriel Health Ltd | 2 May | £3,500.00 | due in 2 days | Current | due soon | — |

Open by bucket (GBP): Current 3,500.00; 1-30 5,740.00; 61-90 2,150.00;
unconfirmed 350.00. Ignored: a £900.00 payment for INV-1049 dated 1 May
(after the cutoff); it will count in the next run. The two holds come from
`unapplied.coverage.json`; they lift when a bank export to 30 April is run
through steps 1-2 again, or when Sam picks `Chase anyway` and the aging is
rerun with `--coverage-confirmed "<Sam's words>"`.

## 3. Drafts (awaiting Sam's approval to send)

INV-1039, second reminder (first reminder sent 10 March, no reply):

> Subject: Second reminder: invoice INV-1039, GBP 2,150.00
>
> Hi, following our note of 10 March, invoice INV-1039 for GBP 2,150.00 (due
> 28 February) is still open in our records as at 30 April. Could you confirm
> the payment date, or tell us if anything is holding it up? If you have paid,
> a remittance would help us match it. Thanks, Sam

Awaiting approval: "send this email from accounts@bramble.example to
accounts@kestrel.example".

INV-1047, first reminder for the £640.00 balance (says the £640.00 received on
9 April is applied). Greyline gets a dispute acknowledgement only, for Sam
to approve. No interest or fees are mentioned: Sam has not opted in.

## 4. Approval and logs

One `ask_question` card with three questions (one per draft), each naming the
draft, amount, mailbox and recipient and repeating "bank export ends 12 April"
until Sam answers the gap question; options `Send exactly as shown` · `I will
send it myself` · `Change it first` · `Not yet`. Each answer recorded with
`log_approval.py record --option "<label as picked>"`; only `Send exactly as
shown` is recorded as an approval, and a send also needs the gap answered. Contact log rows appended, for example:
`INV-1039 | second reminder | evidence cutoff 30 Apr 17:00 | owner Sam |
approval pending | next review 7 May`.

Offered at the end: a follow-up on 7 May (`schedule_followup`, last call of the
turn) and a weekly Monday review (`schedule_routine`); neither created without
Sam's yes.

## What a wrong answer would look like

- A reminder to Harbour Florists for INV-1042.
- "INV-1055 is 10 days overdue" (no terms on record).
- Chasing Greyline for £2,400.00 or arguing about phase 2.
- Counting the 1 May payment, or chasing Marsh before 5 May.
- Sending the Kestrel or Tallow reminder while the bank export still stops on
  12 April and Sam has not answered the gap question.
- Logging "I will send it myself" as Sam's approval for Mina to send.
- "Statutory interest of £43.12 now applies" without Sam's opt-in.
- One email listing Kestrel's and Tallow's invoices together.
