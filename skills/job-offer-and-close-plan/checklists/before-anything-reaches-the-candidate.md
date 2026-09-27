# Before anything reaches the candidate

Tick every line before a verbal-offer script, letter, email or number goes
to the owner as "ready to send". Any unticked line is said out loud in the
reply, first.

## Money
- [ ] The band came from the owner or finance, with the approver and date recorded.
- [ ] Every figure in the brief is from `offer_math.py` output, not typed by hand.
- [ ] Nothing is above band without a named approver's yes for that amount (`above_band_approval` with approver, date and an amount at least the base).
- [ ] No term is sourced from, or mentions, current or past pay.
- [ ] Equity, bonus, commission and benefits are the approver's text, unedited.
- [ ] Sales: OTE = base + on-target variable; commission plan quoted as approved.

## Letter
- [ ] Filled from the company template with `fill_offer_template.py`; the filename says DRAFT.
- [ ] Every `[OWNER TO CONFIRM: …]` is listed in the reply.
- [ ] `check_terms.py terms.json --text <letter> --text <email> --template <template>` shows 0 errors, reached by fixing the draft or adding an approved term, never by ignoring an ERROR.
- [ ] Contingencies in template order; background check has a standalone disclosure on record; any medical exam is post-offer and for all entrants in the category.
- [ ] Start date fits the candidate's stated notice.

## Approvals and dates
- [ ] The band approver and the owner said yes to this exact composition.
- [ ] `close_plan.py --candidate … --assistant … --terms …` shows one internal named owner and a dated, zoned due date per track, and no contingency-order PROBLEM.
- [ ] The answer-by date was agreed before the offer lands.

## Data
- [ ] No protected characteristic or health information anywhere (brief, log, plan, tracker).
- [ ] Competing offers are the candidate's words, labelled unverified.
- [ ] Files saved under ~/workspace/hiring/offers/<role>-<candidate>/; nothing posted to a channel.
