# Checking a customer's VAT or tax ID (evidence only)

Written 2026-09-27. The endpoints below are **unverified at runtime** and change;
re-check them before relying on them. A check result is evidence for the
review block, never a tax decision. "Unchecked" never blocks and never means
"invalid".

## When

Only when the draft already carries a customer VAT or tax ID supplied by the
owner or the customer's PO. Never look up an ID to fill a blank.

## EU VAT numbers (VIES)

- `web_fetch` the public VIES REST endpoint for the member state and number,
  in the form `https://ec.europa.eu/taxation_customs/vies/rest-api/ms/<CC>/vat/<number>`
  (country code without the number prefix). The response states whether the
  number is valid and may give a registered name and address.
- VIES has outages per member state. On an error or timeout, record
  `unchecked (VIES unavailable <date>)`.

## UK VAT numbers

- HMRC's "Check a UK VAT number" service is a GOV.UK web form, and its API
  needs authorisation. Do not try to automate it. Give the owner the GOV.UK
  service link and record `unchecked: owner to check`, or the result the owner
  reports.

## Record in the review block

`Customer VAT ID <masked except country and last 4>: valid | invalid | unchecked
(<source>, <date>); name on register matches: yes | no | not returned.`

A name mismatch or an invalid number goes to the accountant, because it can
change how a cross-border B2B supply is taxed.

## Data minimisation

Send the ID only to the official endpoint. Do not paste it into web search.
