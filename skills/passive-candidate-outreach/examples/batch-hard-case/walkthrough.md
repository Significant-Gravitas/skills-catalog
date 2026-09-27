# Hard case: a batch that must not go out as written

Fictional. Same owner and role as `../single-note-priya.md`. Maya pastes four
drafts she started herself and asks: "Tidy these up and send the lot. Tell
Ravi we pay well and he can WhatsApp me. Add a salary range so they bite,
something like what Series B companies pay."

Files in this folder: `drafts.json` (Maya's four drafts), `dnc.csv`,
`outreach-log.csv` (the existing log). All outputs below are real script runs, verbatim apart from column
spacing (the scripts separate fields with tabs).

## 1. What is refused before any drafting

- "Send the lot": nothing sends from this skill. Each message needs its own
  yes, and the output is drafts.
- "Add a salary range like Series B companies pay": that is estimating a band
  from company stage, which the persona never does. Reply: "I can include
  the range only if you give me the approved one; I won't estimate it."
- "He can WhatsApp me": moving to an encrypted app is a scam pattern [82];
  it stays out.

## 2. Lint the batch

```
$ python3 scripts/lint_outreach.py examples/batch-hard-case/drafts.json \
    --dnc examples/batch-hard-case/dnc.csv --log examples/batch-hard-case/outreach-log.csv
ERROR  Ravi Menon   2 question marks; ask one question only
ERROR  Ravi Menon   calendar or booking link: 'grab time'
ERROR  Ravi Menon   scam-lookalike ask (money, bank, ID or app move): 'move this to WhatsApp'
ERROR  Ravi Menon   implies they are job hunting: 'open to new opportunit'
ERROR  Jo Okafor    on the do-not-contact list: delete this draft, keep no other data
ERROR  Tomas Varga / Lena Hoffmann   openings 0.85 alike (limit 0.6): cards too thin, send back to sourcing
exit=1
```

Decisions:

| Draft | Decision |
| --- | --- |
| Jo Okafor | Deleted. No draft, no batch slot, no log row. The reply says only "one name in your batch is on the do-not-contact list, so there's no draft for them"; the name is not repeated in any shared summary. |
| Tomas Varga, Lena Hoffmann | Both cards cite the same talk; Lena's card was built from the conference's speaker list, not her own work. Tomas keeps his draft (it is his talk). Lena goes back to candidate-sourcing-strategy for a hook from her own work. |
| Ravi Menon | Rewritten from his card: hook on `stripe-reconcile`, company and sender named in full, one question on its own line, no calendar link, no WhatsApp, no "open to new opportunities" (he never said so publicly), no "we pay well". |

Ravi's rewrite (lint: clean):

> **Subject:** Your stripe-reconcile repo
>
> Hi Ravi, I've been reading your stripe-reconcile repo, especially how it
> matches payouts to invoices.
> Northwind Tools is hiring one engineer to own billing, and reconciliation
> is where our double-charges hide.
> Worth a reply?
> Maya Chen, Head of Engineering, Northwind Tools

## 3. Follow-ups that fall due today

Before drafting follow-ups, the reply check runs (Gmail connected; section B
of `references/gmail-and-reply-check.md`). No new replies found for Priya or
Aisha. Then:

```
$ python3 scripts/followups_due.py --log examples/batch-hard-case/outreach-log.csv \
    --today 2026-10-07 --owner-tz Europe/Lisbon
# Follow-ups as of 2026-10-07 (business days; weekends skipped, no holiday list given)

## Due today
- Priya Nair | Senior Backend Engineer | touch 2 due 2026-10-07 | send Wed 07 Oct 13:30 Europe/Dublin / Wed 07 Oct 13:30 Europe/Lisbon | draft already in the log

## Coming up
- Aisha Bello | Senior Backend Engineer | touch 3 due 2026-10-08 | send UNKNOWN (no candidate timezone on the log row; ask, never guess from a city)
```

- Chen Wei replied "not now, try me in November" on LinkedIn; logged as
  replied / not-now with the check-back date Maya set (2026-11-02), so no
  follow-up is listed until then. LinkedIn would have counted this as a
  "response" [96]; the log keeps it apart from positive replies.
- Marek Nowak declined; never listed again.
- Aisha's timezone is UNKNOWN. Her card says "Lagos" but the city is not
  used to guess a zone; one question to Maya: "Aisha's card has no stated
  timezone — send at your morning, or do you know hers?"

## 4. What Maya gets back

1. Two ready drafts (Tomas, Ravi), each clean on lint, with suggested send
   times in both zones.
2. Priya's touch 2 (already drafted; she confirms or edits).
3. One line: "Lena's card needs a hook from her own work; sent back to
   sourcing." One line: "One name was on the do-not-contact list; no draft."
4. What was refused and why, in two lines (salary estimate, WhatsApp).
5. The outreach log with 2 new `drafted` rows. "Nothing has been sent."
