# Reminder stages (placeholders only; no threats)

Every draft states the invoice number, issue and due dates, open balance and
currency, and the requested next step. Calm tone. Ask whether payment has been
made or a record is missing. No late fee, interest, service stop, collection
action or legal consequence unless an approved policy and an owner instruction
support it (see `references/uk-late-payment.md` for the only interest wording).
Each draft ends with the exact action awaiting approval.

## Stage 1: first reminder

> Subject: Invoice {{invoice}}, {{currency}} {{open_balance}}, due {{due_date}}
>
> Hi {{contact_first_name}}, our records show invoice {{invoice}} (issued
> {{issue_date}}, due {{due_date}}) for {{currency}} {{open_balance}} is still
> open. If it has already been paid, could you send the remittance so we can
> match it? If not, please let us know when to expect payment. Thanks,
> {{owner_name}}

## Stage 2: second reminder

> Subject: Second reminder: invoice {{invoice}}, {{currency}} {{open_balance}}
>
> Hi {{contact_first_name}}, following our note of {{last_contact_date}},
> invoice {{invoice}} for {{currency}} {{open_balance}} (due {{due_date}}) is
> still open in our records as at {{cutoff_date}}. Could you confirm the payment
> date, or tell us if anything is holding it up? If you have paid, a remittance
> would help us match it. Thanks, {{owner_name}}

## Stage 3: statement of account

Cover note plus `statement-of-account.html` (rendered by `render_statement.py`
for this customer only):

> Hi {{contact_first_name}}, attached is a statement of the open invoices on
> your account as at {{cutoff_date}}, totalling {{currency}} {{total}}. If any
> are already paid or do not match your records, please let us know. Thanks,
> {{owner_name}}

## Stage 4: owner call

No email. Brief for the owner: invoices, open balance, contact history, any
promise or dispute, and the question to ask.

## Dispute acknowledgement (any stage)

> Hi {{contact_first_name}}, thank you for letting us know about {{stated_issue}}
> on invoice {{invoice}}. I have passed this to {{account_owner}}, who will come
> back to you. Thanks, {{owner_name}}

Do not argue the contract, restate the amount as owed, or ask for payment in a
dispute acknowledgement.

## Footer for Mina's internal use (not sent)

Awaiting approval: "send this email from {{mailbox}} to {{recipient}}" ·
evidence cutoff {{cutoff}} · draft file {{path}} · hash {{sha}}.
