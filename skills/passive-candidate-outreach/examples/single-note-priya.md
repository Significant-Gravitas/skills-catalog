# Worked example: one first note, end to end

Fictional. Owner: Maya Chen, Head of Engineering, Northwind Tools
(timezone Europe/Lisbon). Role: Senior Backend Engineer, Billing.
Candidate card (from candidate-sourcing-strategy, shortlist row 2026-10-02):

> Priya Nair — Staff Engineer, Ledgerline — Dublin (as stated on her site)
> - FACT: "Moving a 4TB Postgres table with zero downtime" (blog post,
>   priyanair.dev/zero-downtime, March 2026)
> - FACT: maintainer of `pg-shadow-copy` (github.com/pnair/pg-shadow-copy)
> - Contact: "email me at hello@priyanair.dev" (priyanair.dev/contact)
> - Gap: no public evidence of payments work (UNKNOWN)

## 1. Checks

- `dnc.csv`: not listed. Outreach log: no rows. Tracker: no owner other
  than Maya. Route: published on her own site (FACT, linked).
- Pay, title, start: Maya has not supplied a band, so none goes in.
- Preferences: `outreach_cadence` UNSET, so the default 2/5/8 is proposed
  and Maya is asked once (`ask_question` with options "2/5/8 (default)",
  "3/7/14", "No follow-ups", "Skip").

## 2. Draft (written into `/home/user/outreach/drafts.json`)

> **Subject:** Your zero-downtime Postgres migration post
>
> Hi Priya, I read your post on moving a 4TB Postgres table with zero
> downtime.
> We're hiring one engineer at Northwind Tools to own billing end to end,
> and live migrations on a revenue path are most of the job.
> Open to a short chat?
> Maya Chen, Head of Engineering, Northwind Tools

## 3. Lint

```
$ cd ~/skills/passive-candidate-outreach && python3 scripts/lint_outreach.py /home/user/outreach/drafts.json
clean: 1 draft(s) pass
```

## 4. Log

```
$ python3 scripts/log_touch.py add --candidate "Priya Nair" --role "Senior Backend Engineer" \
    --touch 1 --channel email --route-source "priyanair.dev contact page" \
    --sender "Maya Chen" --candidate-tz Europe/Dublin
ok: touch 1 drafted for Priya Nair
```

## 5. What Maya sees

The draft above, then:

- Suggested send: Tue 13 Oct 09:30 Europe/Dublin / 09:30 Europe/Lisbon
  (weekday morning in her stated timezone).
- Follow-ups (default day 2 / 5 / 8 after the first note, confirm or change):
  touch 2 adds the on-call setup; touch 3 a new angle (her `pg-shadow-copy`
  work and our backfill problem); touch 4 a short close-out.
- Log: Priya Nair | 2026-10-12 | email | touch 1 | drafted.
- "Nothing has been sent. Say yes to this message and I'll put it in your
  Gmail drafts, or copy it from here."

## 6. After Maya's yes

Maya: "Yes, put it in Gmail." Gmail is connected, so the
`references/gmail-and-reply-check.md` section A sequence runs: a draft-type
tool is found, validated, called once. The result is `approval_required`, so
the reply is "The Gmail draft is waiting on your approval card; nothing is
sent." After Maya approves the card and the call returns success: "1 draft
is in your Gmail, not sent."

On Tuesday Maya says she sent it:
`log_touch.py update --candidate "Priya Nair" --touch 1 --status sent`.
