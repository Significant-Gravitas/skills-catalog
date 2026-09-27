# Settling an invoice draft with `ask_question`

One call. First the conflicts and missing fields, then (only if nothing still
blocks approval) the action question. At most 10 questions.

## Conflict: one question per conflicting term, each source an option

> Q1. SOW-014 clause 5 sets extra days at £850; M. Ode's email of 10 April says
> £900. Which rate goes on line 2?

Options: `£850 per SOW-014 cl. 5` · `£900 per M. Ode email 10 Apr` · `Neither: I will type it`

## Missing field: never a guessed value as an option

> Q2. VAT treatment for this invoice has not been supplied. What should I do?

Options: `I will supply the rate` · `Ask the accountant` · `Leave VAT blank on this draft`

(Offer a tax rate as an option only if the accountant supplied it for this
customer and supply.)

> Q3. Payment details are not in the approved records. How should I get them?

Options: `I will type them` · `Use the details on invoice <number> (I confirm they are current)` · `Leave blank`

Bank details are never copied from another invoice without that confirmation.
A change to bank details is an exception: load
`run_capability(id="skill:bookkeeping-exception-escalation", input={})` [61].

## Action: only when field_check.py shows nothing blocking approval

Before writing Q4, check the billing system:
`find_capability(query="<system> create invoice")`, then
`describe_capability(id=...)` (`references/approval-and-ledger-draft.md`
section 3, steps 1-2). Offer the create option only when a tool is present
that can create the invoice with status Draft. Never ask the owner to approve
an action Mina cannot take.

With a Draft-capable Xero tool:

> Q4. Draft oriel-2026-04, £1,080.00 including VAT £180.00, hash 3f9a1c… What
> may I do now? If I create it in Xero as a Draft, Xero may assign the next
> invoice number to the draft; I will record that number and tell you.

Options: `Approve exactly as shown: I will number and issue it myself` · `Approve exactly as shown: create it in Xero as a Draft (status Draft only)` · `Approve with the changes I type` · `Not yet`

With no such tool (the question says so: "I cannot create invoices in Xero
from here; you will enter it"):

Options: `Approve exactly as shown: I will number and issue it myself` · `Approve with the changes I type` · `Not yet`

(Use the billing system's own name in both the question and the option, for
example QuickBooks; `log_approval.py` matches the option text exactly.)

The suggested next number (INV-1056 from `register_check.py`) is shown in the
question text as a suggestion; the owner or billing system assigns it, and the
billing system's number may differ from the suggestion.

Record the answer with `log_approval.py record --option "<label as picked>"`.
Only `create it in <system> as a Draft`, or a typed reply that itself names
creating it in that system ("yes, create it in Xero"), is recorded as an
approval for Mina to act. A bare typed "yes" is refused for Q4: with two
approving routes it is ambiguous, so ask again with the card. `I will number and issue it myself` is noted in the register
(`approved_to_issue`, verbatim answer as evidence); Mina does nothing further.
"Approve with the changes I type" means edit, re-render, re-hash and ask again;
it is not an approval. If the user picks two actions in two answers, record
each separately.
