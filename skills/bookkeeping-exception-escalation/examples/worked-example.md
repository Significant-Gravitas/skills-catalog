# Worked examples: a payment-redirection attempt, and the approver involved

Fictional. Files for example 1 are in `examples/bank-detail-change/`
(`python3 scripts/build_pack.py --selftest` builds the pack from them).

## Example 1: supplier bank details changed before a payment run

Northgate Joinery Ltd. The owner, Sam, forwards a supplier email: "Kestrel
Timber sent new bank details, can you update the payment run?" Finance owner
(payment authority) per intake: Alex.

1. **Classify.** Bank-detail change, suspected (not confirmed) payment
   redirection. Urgency: at once, before the 5 June run (routing matrix).
2. **Facts.** Bill 8812, 4,960.00 GBP, due 6 June (bills export row 2); new
   account ending 0937 in the 28 May email; the last three payments went to the
   account ending 2210 (bank rows 1-3), verified by phone on 14 Nov 2025
   (vendor master).
3. **What is not done.** No update to the payment run. No web search for
   Kestrel's number and no use of the phone number in the email. No reply to
   the email. The contact to use is the one on file before the change.
4. **Register.** `register.py new ... --class bank-detail-change ...` returns
   BX-7 (six earlier exceptions exist; ids are never reused).
5. **Pack.** `pack-BX-7.md` written from `templates/exception-pack.md`, then
   `build_pack.py --id BX-7 --cite bills.csv:bill=8812 --cite bank.csv:3 --keep-columns ...`.
   `evidence.csv` shows `bank_account=**-**-** ****0937`; `approver_email` is
   listed under "Fields withheld".
6. **Second check.** Sam's team includes a compliance expert, so the pack is
   checked with `run_capability(id="tool:consult_teammate", input={"expert_id": "<id>", "work": "<pack text>", "authority": "records cited in the pack; no owner approval yet"})`.
   Result "pass". The pack does not say "reviewed by compliance": the routing
   target stays Alex.
7. **Deliver as a draft.** The pack zip goes out with `write_workspace_file`.
   `ask_question`: "Send pack BX-7 to Alex (finance owner) at the address in
   intake?" Options: Send to Alex / I'll forward it myself / Not yet. Sam
   picks "I'll forward it myself"; the reply is logged with `log_approval.py`.
8. **Deadline.** The run is 5 June; Sam agrees to a reminder, so the last call
   of the turn is `run_capability(id="tool:schedule_followup", input={"message": "Exception BX-7: decision still needed before the 5 June payment run; check exceptions.csv and re-raise if open. Do not contact Kestrel or change any payment.", "delay_seconds": 259200})`.
9. **Decision.** Next day Alex writes: "Called Kestrel on the old number. They
   never changed banks. Hold 8812 and report it." Recorded verbatim with
   `register.py decide`. Status: decided, not closed; Alex closes it when the
   report to the bank is made.

## Example 2 (hard case): the concern involves the approver

Bramble Design Ltd. While reconciling, three payments of 480.00 on the 1st of
February, March and April go to "J. Rowe Consulting". There is no bill, no
contract and no vendor record. The payments were released by Jo, the owner
named as approver in intake; the payee shares Jo's surname.

- **Classify:** unusual-payment, and suspected-error-fraud only as "suspected":
  the records show payments without support, nothing more.
- **Route:** the usual decider (Jo) released the payments and may be related to
  the payee, so the owner-delegate path applies. Intake names Dev Patel
  (accountant) as the second owner. The pack goes to Dev with one factual line:
  "Routed to you rather than Jo because Jo released these payments."
  If intake had no second owner, the user would be asked who should receive it;
  the assistant would not pick someone.
- **Wording:** "Three payments of 480.00 to J. Rowe Consulting (bank rows 14,
  37, 61) have no bill, contract or vendor record on file." Not: "Jo is paying
  a relative." No accusation, no contact with J. Rowe Consulting, no change to
  any record.
- **Interim state:** the three lines stay unresolved in the reconciliation as
  `investigate`, each pointing to BX-4.
- **Delivery:** as a draft; sending needs a yes naming Dev as recipient. If the
  person in the chat is Jo, the assistant says plainly that this item is
  routed to Dev under the owner-delegate rule, and does not hide the pack from Jo.

## Missing-documents request (batch mode)

Nine Amex lines have no receipts. `register.py request` adds RQ-1 to RQ-9 for
Jo (who is in the chat), and one `ask_question` card asks about each, with
options "Uploading now" / "No receipt exists" / "Personal: not a business
cost" / "Ask someone else". Answers are recorded with `register.py answer`.
For an owner not in the chat, the same items go into
`templates/missing-documents-request.md` as a draft file.

## The original example (kept from version 1)

> **Exception BX-07: supplier bank details changed before a payment run**
> Entity: Northgate Joinery Ltd. Account: Business current, ending 4411.
> Period: May 2026.
>
> **Facts (from records):** Bill #8812 from Kestrel Timber, £4,960.00, due 6
> June (bills export, 31 May). Kestrel's email of 28 May gives new bank details
> ending 0937. The previous three payments went to the account ending 2210
> (bank statements Feb to Apr).
> **Mismatch:** payee details on the bill differ from every earlier payment. No
> call-back to a known Kestrel number is on file.
> **Class:** bank-detail change; suspected, not confirmed, payment redirection.
> **Done so far:** checked the vendor file and the last three statements. That
> did not settle it because nothing independent confirms the change.
> **Deadline:** payment run 5 June (payment calendar).
> **Decision requested from Alex (finance owner):** confirm the change through a
> known contact before the payment run, or hold bill #8812.
> **Interim state:** bill #8812 left unapproved in the draft run. No one has
> contacted Kestrel from here.
