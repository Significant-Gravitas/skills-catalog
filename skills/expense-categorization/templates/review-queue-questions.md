# Settling the review queue with `ask_question`

One call, at most 10 questions, highest amounts first. Each question names the
row id so the answer can be written back. More than 10 open items: ask the ten
largest and list the rest in the table.

Question pattern:

> `<row id>` `<date>` `<vendor>` `<amount>`: `<evidence>`. Which account?

Options, in this order:
1. The 2 to 5 approved accounts that could fit (exact chart names only)
2. `Personal / owner item`
3. `Split: I will give the amounts`
4. `Duplicate or refunded: do not code` (only for flagged duplicate pairs)
5. `Not sure: send to the accountant`

Never offer a tax treatment ("deductible", "50%", "capitalise") as an option.

Follow-up per answer:
- Write the answer into `status=approved` and `proposed_account`, and quote
  who answered as the user stated it.
- If the user says "always", add a rule to `coding-rules.csv`
  (`status=approved`, approver, date) and, when memory is on, store it as a
  rule for this entity (see `references/books-state.md`, section 5).
- `Split`: ask for the amounts; enter one row per part with `split_part`
  1..n. `write_review.py` refuses parts that do not add up exactly to the
  source amount or change its currency.
- `Not sure: send to the accountant`: load
  `run_capability(id="skill:bookkeeping-exception-escalation", input={})`
  and pass the row's facts.

Example (Bramble, April):

| # | Question | Options |
| --- | --- | --- |
| 1 | amex:4 09 Apr AMZN MKTP UK -612.99: no receipt. Which account? | Office supplies · Equipment (fixed asset review) · Personal / owner item · Split: I will give the amounts · Not sure: send to the accountant |
| 2 | amex:3 07 Apr TRAINLINE -118.40: receipt says "client visit, Leeds". Which account? | Travel · Staff training · Personal / owner item · Not sure: send to the accountant |
| 3 | amex:5 15 Apr FIGMA -45.00 and amex:8 22 Apr FIGMA REFUND +45.00: second seat or refunded double charge? | Second seat: Software subscriptions · Duplicate or refunded: do not code · Not sure |
