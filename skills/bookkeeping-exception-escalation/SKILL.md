---
name: "bookkeeping-exception-escalation"
description: "Package bookkeeping exceptions for the right owner with source facts, impact, urgency, and a precise decision request. Use for an unusual or unexplained payment, a supplier's changed bank details, possible fraud, duplicates, missing receipts or documents, payroll-tax shortfalls, worker-classification or W-9 gaps, closed-period changes, and questions for the accountant. Keeps a numbered exception register, builds a masked evidence pack from the cited rows only, batches missing-document requests per owner, and prepares an accountant hand-off list. Everything is a draft: it never accuses, contacts a supplier or customer, changes bank details, moves money, or closes an exception itself."
triggers: ["escalate this transaction to our accountant", "unusual transaction in the books", "supplier changed their bank details", "package this for the accountant", "payment I can't explain", "bookkeeping exception", "is this payment fraud", "supplier sent new bank details", "list of questions for my accountant", "chase missing receipts"]
version: "2"
---

# Bookkeeping exception escalation

Use this when a record cannot be handled safely under the approved rules. The
goal is a small evidence pack and a clear owner, not an unsupported answer.

## When to use, and when not

Use for one exception (single pack), for a batch of missing documents (request
mode), or at period end for the accountant (hand-off mode). Other bookkeeping
skills load this one when they hit an exception.

Not for: deciding the answer. Tax treatment, accounting policy, legal claims,
payment authority and access changes belong to the owners in
`references/routing-matrix.md`.

## Inputs and where they come from

| Input | Source | If missing |
| --- | --- | --- |
| The record(s) behind the concern | User upload, or the calling skill's files (reconciliation, expense review) | Ask for the source; a pack without a source is not sent. |
| Owners: finance owner, accountant, second owner, security or privacy owner, counsel | `intake.json`, `memory_search`, then `ask_question` | Ask who; never pick someone. |
| Vendor master and earlier invoices (for bank-detail changes) | Upload or state | Say verification is not possible from records; the owner must verify. |
| Register and requests | `<state>/exceptions.csv`, `<state>/requests.csv` (`references/books-state.md`) | Start them from `templates/`. |
| Thresholds (materiality, payment limits) | Owner, intake | Claim no materiality; qualitative triggers still apply. |

Pull files into the sandbox with `read_workspace_file(file_id=..., save_to_path="/home/user/in/<name>")`.

## Tools and pre-flight

1. `bash_exec`: `python3 --version`. Without Python, keep the register by hand
   in the same columns and mask numbers by hand (last 4 digits only).
2. State pre-flight from `references/books-state.md`.
3. `memory_search(query="<entity> finance owner accountant approvers")`. Hits are
   proposals to confirm. Never store amounts, account numbers or accusations in memory.

All script commands start with `cd ~/skills/bookkeeping-exception-escalation && `.

## Classify the exception

Choose the best factual class (register values in brackets):

- missing or unreadable source [missing-source];
- duplicate or conflicting record [duplicate-or-conflict];
- unknown payer, payee, or business purpose [unknown-party-or-purpose];
- amount, date, currency, or entity mismatch [mismatch];
- bank-detail change [bank-detail-change] or unusual payment [unusual-payment];
- tax, payroll, equity, loan, fixed-asset, or accounting-policy question [tax-payroll-equity-loan-asset-policy];
- payroll tax shortfall: raise at once [payroll-tax-shortfall];
- worker classification question [worker-classification];
- receipt with no matching card or bank line, or a possibly generated receipt [receipt-without-payment-line];
- payee missing a W-9 or TIN: list it, never compute withholding [payee-missing-w9-tin];
- change detected in a closed or reconciled period [closed-period-change];
- suspected error, fraud, or unauthorised activity [suspected-error-fraud];
- privacy or access concern [privacy-access].

Do not label fraud as fact without evidence. Say `suspected` and state the
record that caused concern. Escalate regardless of size any item that turns a
loss into a profit or the reverse, touches a loan covenant or owner pay, may
involve illegality, or involves a related party (`references/routing-matrix.md`).
Urgency signals are in `references/red-flags.md`.

## Procedure (single exception)

1. **Classify and route** with the matrix. If the concern involves the person
   who would normally decide, use the owner-delegate path: route to the next
   named owner and say why in one factual line; with no second owner, ask the user.
2. **Register.** `python3 scripts/register.py new --register <state>/exceptions.csv --entity ... --account <label, last 4> --period ... --class ... --amount ... --currency ... --facts-ref "<file:row; ...>" --decision "<one decision>" --owner "<name (role)>" --urgency "..." --interim "..."`.
   Use the id it returns. Never invent or reuse an id.
3. **Build the evidence pack** from `templates/exception-pack.md`:
   1. Entity, account, period, and source identifiers.
   2. Facts copied from the source records.
   3. The exact mismatch or missing fact.
   4. Amount and affected totals, without claiming materiality unless the owner
      supplied a threshold.
   5. Work already done and why it did not settle the item.
   6. Deadline or operational impact, if a source proves it.
   7. One decision request and the proposed owner.
   8. Safe interim state: leave unresolved, pause a draft here, or recommend
      that the owner restricts access (this assistant cannot change access to any system).
   Then `python3 scripts/build_pack.py --id <BX-n> --pack-md <file> --cite <file:row> ... --keep-columns <only what the reviewer needs> --out <state>/packs`.
   It copies only the cited rows, lists withheld fields, masks numbers, and
   refuses a pack.md with an unmasked number.
4. **Route** tax and policy questions to the qualified accountant; legal claims
   to counsel; payment authority to the approved finance owner; access or
   exposure to the security or privacy owner. For a possible unauthorised
   payment, raise it at once and do not contact the suspected party yourself.
5. **Optional second check.** If the user's team lists a compliance or legal
   teammate, and the pack asks someone to hold money or meet a date:
   `run_capability(id="tool:consult_teammate", input={"expert_id": "<id>", "work": "<pack text>", "authority": "records cited in the pack; no owner approval yet"})`.
   Fix a "block" before the owner sees the pack. A teammate never replaces the
   accountant or counsel, and the pack never says "reviewed by legal".
6. **Deliver as a draft.** `write_workspace_file(source_path=<zip>)` with a
   `workspace://` link. Then `ask_question`: "Send pack <id> to <recipient, role>?"
   with options "Send to <recipient>" / "I'll forward it myself" / "Not yet".
   Check the recipient against intake. Log the reply with
   `python3 scripts/log_approval.py record ...` against the zip's hash.
   Only after "Send": email via `find_capability("send email")`,
   `describe_capability`, `run_capability(..., validate_only=true)`, then the real
   call with the zip as an attachment; or the owner forwards the file. A
   `workspace://` link cannot be opened by an outside recipient. Chat
   (`run_capability(id="tool:post_to_chat_platform", input={...})`) carries text
   only: use it at most for a short notice ("Pack BX-7 is ready; Sam will
   forward it"), never for the pack's facts or evidence. These may also be held
   for platform approval; wait for the result. Never send to the suspected party.
7. **Deadline.** If a source proves a deadline and the owner agrees, the last
   call of the turn is `run_capability(id="tool:schedule_followup", input={"message": "Exception <id> for <entity>: decision still needed before <deadline>; check ~/workspace/bookkeeping/<entity-slug>/exceptions.csv and re-raise if still open. Do not contact anyone or change any payment.", "delay_seconds": <about one business day before>, "session_id": "<this chat's id from session_context>"})`.
   The session id lands it in this chat with its history; without it, it fires into a blank chat.
   It only re-raises; it never acts.
8. **Record the decision.** `register.py decide --id ... --by "<as stated>" --verbatim "<owner's words>"`.
   Only the owner closes: `register.py close` with their words verbatim.
   Any account, card or IBAN number in those words (or in an `answer`) is
   stored masked to its last 4, marked "verbatim, account numbers masked to
   last 4"; everything else stays word for word.

## Other modes

- **Missing-documents request.** Group open items by owner from
  `open-items.csv` and `exceptions.csv`. Add each with `register.py request`
  (item, why needed, the document that settles it, due date). For the owner in
  the chat, one `ask_question` card (up to 10 questions), options
  "Uploading now" / "No receipt exists" / "Personal: not a business cost" /
  "Ask someone else"; record with `register.py answer`. For absent owners, a
  draft from `templates/missing-documents-request.md`.
- **Accountant hand-off pack.** At period end, fill
  `templates/accountant-handoff-pack.md` from open exceptions, proposed
  adjustments with support, accrual and fixed-asset candidates, and payee totals
  with W-9 gaps. Same delivery rule as step 6.

## Bank-detail changes (always)

- The known contact comes only from records dated before the change (vendor
  master, earlier invoices, the contract). Never use `web_search`, `web_fetch`
  or browser tools to find a contact, and never use any detail from the change
  request itself.
- Never draft, stage or suggest a payment to the new details. The owner verifies;
  this assistant does not call or email the supplier.

## Output contract

A single-exception run returns: the exception id and class; the eight pack
fields; the owner and why they were chosen; the draft pack link and the list of
withheld fields; the send question; any follow-up scheduled. Request mode
returns the per-owner list with ids; hand-off mode returns the hand-off draft.

## Guardrails

- Keep the original record unchanged. Share only the fields the reviewer needs.
- Never create an adjusting entry, reverse a payment, accuse a person, change
  bank details, contact a customer or vendor, or close the exception.
- Record the owner's supplied decision verbatim, and the evidence for any later action.
- Sending the pack is itself an action: return it as a draft and name the
  recipient; send it only after the owner says yes to that recipient.
- Never suggest paying other creditors ahead of payroll tax deposits.
- Quote a tax or reporting threshold only from a supplied or freshly fetched
  official source with its tax year; otherwise route.
- If a file or tool fails twice, stop and report the gap.

## Quality self-check

`checklists/pack-quality.md` before the owner sees any pack.

## Files in this package

- `references/routing-matrix.md`, `red-flags.md`, `books-state.md`
- `scripts/register.py`, `build_pack.py`, `log_approval.py` (each has `--selftest`)
- `templates/exception-pack.md`, `exceptions-register.csv`, `requests.csv`,
  `missing-documents-request.md`, `accountant-handoff-pack.md`
- `examples/worked-example.md` (payment redirection; approver involved; batch
  requests) and `examples/bank-detail-change/`
- `checklists/pack-quality.md`

## Related skills

`statement-reconciliation`, `expense-categorization`, `accounts-receivable-follow-up`,
`month-end-close-checklist`, `monthly-profit-and-loss-summary`, `bookkeeping-getting-started`.
