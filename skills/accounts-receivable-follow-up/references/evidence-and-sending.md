# Mailbox evidence and sending an approved reminder

## Contents
1. Reading the mailbox for evidence (optional)
2. Approval for one message
3. Sending through a connected mail tool
4. When there is no mail tool

## 1. Reading the mailbox for evidence (optional)

The last customer email is often the proof that an invoice is disputed, paid
or promised. If a mail integration is connected:

1. `find_capability(query="gmail search messages")` (or the user's provider).
2. `describe_capability(id=...)`: confirm it is a read.
3. Search only for threads matching the invoice number or the customer's
   domain since the invoice date. Do not read unrelated threads; they hold other
   customers' data.
4. Quote the dated line that proves a dispute, a remittance or a promised date,
   and add it to the dispute log or contact log with its date.
A sign-in card: stop the mailbox step, say which evidence is missing, and ask
the account owner instead.

## 2. Approval for one message

Each draft ends with the exact action awaiting a yes, for example "send this
email from accounts@ to priya@harbour.example". Ask with `ask_question`:

> Send the second reminder for INV-1039 (£2,150.00) exactly as shown, from
> accounts@bramble.example to accounts@kestrel.example?

Options: `Send exactly as shown` · `I will send it myself` · `Change it first` · `Not yet`

If `find_unapplied.py` reported `BANK_COVERAGE_GAP`, the question also says
"the bank export ends <d>; a payment after that would not show", and no
message is sent until the owner has answered the gap question (SKILL step 2).

Before asking, hash the draft file:
`cd ~/skills/accounts-receivable-follow-up && python3 scripts/log_approval.py hash <draft>`.
Record the answer with
`cd ~/skills/accounts-receivable-follow-up && python3 scripts/log_approval.py record --artefact <draft> --shown-sha <hash> --action "send <draft> to <address>" --approver "<as stated>" --option "<label exactly as picked>" --log <state>/approvals.csv`
(a typed answer goes in `--reply "<verbatim>"` instead). What each answer means:

| Answer | Meaning | log_approval.py |
| --- | --- | --- |
| `Send exactly as shown` | Mina may send this message to this recipient | records the approval |
| `I will send it myself` | The owner sends it; Mina sends nothing | refuses (not an approval); log `sent_by=owner` only when the owner says it was sent |
| `Change it first` | Edit, re-render, re-hash, ask again | refuses |
| `Not yet` | Nothing happens | refuses |
| Typed text | Only a bare "yes", "approve", "go ahead" or "send it" counts; anything conditional ("yes but…", "don't send yet") is not a yes | refuses unless exact |

The recipient address must equal the billing contact on file for that
customer; a different address is a question, not a send.

## 3. Sending through a connected mail tool

Only after
`cd ~/skills/accounts-receivable-follow-up && python3 scripts/log_approval.py verify --artefact <draft> --action "send <draft> to <address>" --log <state>/approvals.csv`
prints "approved by …":

1. `find_capability(query="gmail send email")` (or the user's provider).
2. `describe_capability(id=...)`.
3. `run_capability(id=..., input={...exact approved subject, body and recipient...}, validate_only=true)`.
4. `run_capability(id=..., input={...})`. The platform may hold it for its own
   approval (`approval_required`); wait for the held result. Under legacy review
   (`review_required`), resume with `resume_capability(review_id=...)` only for
   this approved message.
5. Log the message id in the contact log (`sent_by=Mina (approved by <name>)`,
   `sent_at`).
Send the approved text byte for byte. Any change means a new approval. One yes
covers one message to one recipient.

## 4. When there is no mail tool

On a sign-in card or no capability, stop and give the owner the draft to send.
Record `approval_state=approved, sent_by=owner` only when the owner says it was
sent.
