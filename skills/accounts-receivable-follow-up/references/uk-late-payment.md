# UK statutory late-payment interest and fixed sums (opt-in only)

Checked 2026-09-27 against GOV.UK [30] and the Late Payment of Commercial
Debts (Interest) Act 1998, s.5A [47]. Re-read both pages before quoting any
figure, and quote the date you read them.

## Contents
1. When this may be mentioned at all
2. The rate
3. Fixed sums
4. Worked calculation
5. Wording

## 1. When this may be mentioned at all

All four must be true, and the owner must say so in this chat:
1. the owner opts in to claiming;
2. both parties are businesses (B2B);
3. the contract is under UK law;
4. there is no contract rate for late payment (a contract rate replaces the
   statutory one [30][47]).
Otherwise do not mention interest or fixed sums in any draft.

## 2. The rate

Statutory interest is 8% plus the Bank of England base rate [30]. The base
rate used is the reference rate fixed for each six months: the rate on 31
December for debts that become late between 1 January and 30 June, and the
rate on 30 June for 1 July to 31 December [30].

Never use a base rate from memory. Fetch it with `web_fetch` from the Bank of
England's Bank Rate history page, and quote the rate, the date it applies to,
the URL and the fetch date. If the page cannot be read (layout change, size
limit), ask the owner for the rate and label it "owner stated".

## 3. Fixed sums per invoice [47]

| Debt | Fixed sum |
| --- | --- |
| under £1,000 | £40 |
| £1,000 to £9,999.99 | £70 |
| £10,000 or more | £100 |

## 4. Worked calculation

`uk_late_interest.py` computes: daily interest = principal × annual rate ÷ 365;
interest to date = daily interest × days late [30].

Example (fictional, rate assumed for illustration only): £2,150.00 due 28
February 2026, calculated to 30 April 2026 (61 days), with a reference rate of
4% → 12% a year → £0.7068 a day → £43.12, plus a £70 fixed sum.

## 5. Wording

If the owner opts in, the draft states the facts and the basis, without
threat: "Under the Late Payment of Commercial Debts (Interest) Act 1998, we are
entitled to claim interest at 8% above the Bank of England reference rate
(<rate>% from <date>) and a fixed sum of £<x>. Interest to <date> is £<y>."
The owner decides whether to include it.
