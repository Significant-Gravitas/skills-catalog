# Follow-ups (touches 2-4)

Default cadence: day 2, day 5 and day 8 after the first note (default; the
owner's saved `outreach_cadence` wins; ask once if none is saved). Compute
dates with `scripts/followups_due.py`; never by hand. Each follow-up gives
something the last one did not. The ask stays a reply, never a meeting.

## Touch 2 — a short, useful nudge

```
Subject: Re: <original subject>          <- only if it is truly the same thread

Hi <first name>, one more detail in case it helps: <a concrete fact about
the role or problem not in the first note, e.g. the on-call setup, the team
size, the stack, the first project>.
<Same one-word question, reworded.>
<Sender>, <Company>
```

## Touch 3 — a new angle or proof point

```
Hi <first name>, <a different reason the work might matter to them, tied to
something else on the card, with its source>. <One line of proof: a
public, checkable fact about the team or product, owner-supplied>.
<One-word question.>
<Sender>, <Company>
```

## Touch 4 — brief close-out, door open

```
Hi <first name>, I'll leave it here so I'm not crowding your inbox. If
<the problem> is ever interesting to you, my door's open: <sender email>.
<Sender>, <Company>
```

Rules:
- "Re:" only when the note is a reply in the same thread; never fake a thread.
  In `drafts.json`, a "Re:" follow-up carries `"thread_subject"`: the exact
  subject of touch 1 (from the log or the owner's sent mail). `lint_outreach.py`
  errors on "Re:" in touch 1, on any "Fwd:", and on a "Re:" subject that differs
  from `thread_subject`. With no touch-1 subject to hand, drop the "Re:" and
  use a new hook subject.
- No "just bumping", "circling back" or "any update?".
- Stop after touch 4 unless the owner says otherwise (logged with `--allow-extra`).
- A reply of any kind stops the cadence: log it with `log_touch.py update`
  before drafting anything else.
