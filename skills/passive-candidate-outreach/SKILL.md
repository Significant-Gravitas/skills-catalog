---
name: "passive-candidate-outreach"
description: "Drafts first notes and follow-ups to sourced passive candidates, each hooked on the person's own published work, checked for honesty and scam-lookalike wording, and logged in the outreach log with reply types. Use when the user picks a sourced candidate to approach and needs a first note, a follow-up, or individual drafts for a batch; when a candidate never replied and a follow-up is due; or when a reply (yes, not now, no, stop contacting me) needs logging. Drafts only; the user sends."
triggers: ["message this candidate", "write candidate outreach", "cold note to a passive candidate", "follow up with the candidate", "outreach for this batch", "how do I approach this person", "candidate never replied"]
version: "2"
---

# Passive candidate outreach

Passive candidates aren't looking, so a first note must prove at a glance that
someone read their work. You draft it and its follow-ups from the candidate
card and the role scorecard, check them with a script, and log every touch.
You draft; the user sends.

**Use when:** the owner picks a sourced person to approach; a batch needs one
note each; a follow-up is due; a reply needs logging; someone asks not to be
contacted.
**Do not use for:** finding people (candidate-sourcing-strategy), messages to
people already in process — scheduling, nudges, declines, keep-warm notes
(interview-coordination), or offers (job-offer-and-close-plan).

## Inputs and where they come from

| Input | Source |
| --- | --- |
| Candidate card: name, title, company, stated location, 2-4 evidence lines with links, published contact route | `~/workspace/hiring/shortlist.csv` or the card in chat (candidate-sourcing-strategy). No link, no note. |
| Role scorecard (why their work fits) | `~/workspace/hiring/roles/<role-slug>/scorecard.md` or the owner |
| Sender, sender voice sample, cadence, word limit, owner timezone | `~/workspace/hiring/preferences.md` keys `outreach_sender`, `outreach_voice_sample_ref`, `outreach_cadence`, `outreach_max_words`, `timezone`; else `memory_search("hiring preferences")`; else ask once with `ask_question` |
| Pay, title, start date | Only if the owner supplied them. Never estimated. |
| Outreach log, do-not-contact list | `~/workspace/hiring/outreach-log.csv`, `~/workspace/hiring/dnc.csv` |
| Replies | The owner, or a read-only Gmail search (`references/gmail-and-reply-check.md` B) |

## Pre-flight

Every `python3 scripts/...` command in this skill runs as `cd ~/skills/passive-candidate-outreach && python3 scripts/...`: `bash_exec` starts in `/home/user`, not the package folder.

1. `bash_exec`: `mkdir -p ~/workspace/hiring && cd ~/skills/passive-candidate-outreach && python3 --version && python3 scripts/log_touch.py init`.
   If `~/workspace` is not writable, say "the log won't carry to the next
   chat" and deliver the log with `write_workspace_file` at the end.
   No Python: apply every rule by hand and label the output "not script-checked".
2. Batches of three or more: mirror `checklists/before-showing-drafts.md` in `TodoWrite`.

## Procedure

1. **Check who may be contacted.** Anyone on the do-not-contact list, or who
   has already said no, gets no draft and no batch slot; say "one name is on
   the do-not-contact list" without repeating it in shared output. If a
   teammate owns the relationship, say so instead of drafting. Use only a
   contact route they published professionally or one the owner gives you;
   never guess or pattern-build an email and never write to their current
   work inbox. No route: draft anyway, and say it can't go until there is one.
2. **Write the first note** from `templates/first-note.md`. Four to six short
   sentences (default: under 60 words — the owner can change it):
   1. The hook: a specific piece of their work and where you saw it. Naming
      the source is honest and shows the note was written for them.
   2. The role in one line, and why their work fits it.
   3. Why it might interest them: the problem, scope, people or stage.
   4. One question on its own line, answerable in a word. No calendar link.
   The subject line is the hook, never "Quick question". Name the company,
   the role and the real sender. Working opener:
   > Saw your PGConf talk on online schema changes. Your rollback checklist
   > is exactly what our platform team keeps getting wrong.
3. **Batches:** every person gets their own hook. List drafts strongest fit
   first (fit to the scorecard, with the reason shown). If two drafts open
   alike, the cards are too thin: send them back to sourcing.
4. **Lint.** Write the drafts to `/home/user/outreach/drafts.json` (shape:
   `templates/drafts.json`) and run
   `cd ~/skills/passive-candidate-outreach && python3 scripts/lint_outreach.py /home/user/outreach/drafts.json --max-words <outreach_max_words or 60>`.
   Fix every ERROR and rerun until exit 0; explain any WARN you keep.
   The checks and their sources are in `references/outreach-honesty-rules.md`.
5. **Log** each draft: `python3 scripts/log_touch.py add --candidate "<name>" --role "<role>" --touch <n> --channel <email|linkedin|...> --route-source "<where the route was published>" --sender "<sender>" [--candidate-tz <IANA>]`.
   A refusal (DNC, already declined, touches out of order) means no draft.
6. **Follow-ups.** First, if Gmail is connected, check for replies
   (`references/gmail-and-reply-check.md` B) and log what the owner confirms.
   Then `python3 scripts/followups_due.py --owner-tz <tz> [--cadence <owner cadence>]`
   and draft only for rows it lists, from `templates/follow-ups.md`. Up to
   three follow-ups (default cadence: day 2, day 5 and day 8 after the first
   note — an adjustable starting point; use the owner's saved cadence, ask
   once if none). Each gives something the last did not, never "just bumping
   this": a short useful nudge, then a new angle or proof point, then a brief
   close-out that leaves the door open. The ask is a reply, never a meeting.
   First send on a weekday morning in their timezone, then vary day and
   time; stop after the third follow-up unless the owner says otherwise.
7. **Replies.** Log against the latest touch marked `sent` (the one they
   answered): `python3 scripts/log_touch.py update --candidate "<name>" --touch <latest sent touch> [--role "<role>" when they have two roles] --status ...`.
   positive → `--status replied --reply-type positive` (cadence stops; owner
   takes it on); not now → `--status replied --reply-type not-now`, with
   `--check-back` only if the owner sets a date; no → `--status declined`,
   logged at once, ends it; "don't contact me" → `log_touch.py dnc`, which
   keeps the name and flag only and deletes their log rows.
8. **Hand back** (output contract below). With Gmail connected and the
   owner's yes to a specific message, place it in Gmail drafts per
   `references/gmail-and-reply-check.md` A.

## Output contract

1. Each draft in chat, ready to copy: subject, body, suggested send time in
   the candidate's zone and the owner's (or UNKNOWN), and the evidence link
   behind the hook.
2. For batches: strongest fit first; one line each for anyone left out
   (do-not-contact, no route, thin card), without repeating DNC names.
3. The lint result ("clean" or what was fixed), or "not script-checked".
4. The outreach log rows added or changed; `sent` appears only after the
   owner says they sent it.
5. Gmail: "N drafts in your Gmail, none sent" only for calls that returned
   success; otherwise "here to copy".
6. The closing line: nothing has been sent.

## Guardrails

- Nothing sends without a yes: each message, follow-ups and batch notes
  included, needs its own explicit approval. There is no send step here.
  In an unattended run, make no external write at all (no Gmail draft or
  send, no Calendar, Slack, Sheets or ATS change); saving to `~/workspace`
  and attaching a file with `write_workspace_file` are allowed.
- Facts come only from the card: no invented mutual connections, no claiming
  to have read what you haven't, no generic "saw your profile" when the talk
  or repo could be cited. No hype, no flattery, nothing personal, never imply
  they are job hunting. Use the sender's voice sample if saved; otherwise
  plain and friendly.
- Never ask for money, ID documents or bank details, or to move to WhatsApp,
  Telegram or another app; every note names the company, role and real sender.
- Pay, title and start date only if the owner supplied them; never estimate a band.
- No protected characteristics, stated or guessed, in any note or log.
- The do-not-contact list is honoured by every future batch; it holds the
  name and flag only.
- A reply check reads only threads with the candidate's published address.

## Quality self-check

- [ ] Every hook links to the person's own work on the card.
- [ ] `lint_outreach.py` exited 0 on the final drafts (or output says "not script-checked").
- [ ] Every time carries a zone; unknown zones say UNKNOWN.
- [ ] Every draft has a `drafted` log row; no row says `sent` without the owner's word.
- [ ] No DNC name appears anywhere in the reply.
- [ ] The reply says nothing was sent.

## Fallbacks

A thin card gets the shorter honest version plus the one fact that would
strengthen it. With no contact route, stop at the draft and say so. No
Python: apply the checklist by hand and label the result. No `~/workspace`:
deliver the log with `write_workspace_file` and say it won't persist.

## Related skills

Load with `run_capability(id="skill:<slug>", input={})`:
candidate-sourcing-strategy (cards, thin-card returns), interview-coordination
(anyone who says yes moves into the tracker), hiring-pipeline-analytics
(reply rates by reply type), sofia-getting-started (saved sender, cadence).

## Package files

- `scripts/lint_outreach.py` (per-draft and batch checks), `scripts/log_touch.py`
  (log and DNC), `scripts/followups_due.py` (cadence dates); each has `--selftest`
- `references/outreach-honesty-rules.md`, `references/gmail-and-reply-check.md`
- `templates/first-note.md`, `templates/follow-ups.md`, `templates/drafts.json`,
  `templates/outreach-log.csv`, `templates/dnc.csv`
- `checklists/before-showing-drafts.md`
- `examples/single-note-priya.md` (end to end), `examples/batch-hard-case/`
  (DNC hit, twin hooks, scam-lookalike draft, not-now reply, unknown timezone)

## Example

> **Example (fictional; card: Priya Nair, Staff Engineer, Ledgerline).**
>
> **Subject:** Your zero-downtime Postgres migration post
>
> Hi Priya, I read your post on moving a 4TB Postgres table with zero
> downtime.
> We're hiring one engineer at Northwind Tools to own billing end to end,
> and live migrations on a revenue path are most of the job.
> Open to a short chat?
> Maya Chen, Head of Engineering, Northwind Tools
>
> *Suggested send: Tue 13 Oct 09:30 Europe/Dublin (her stated location) /
> 09:30 Europe/Lisbon. Lint: clean (52 words; `lint_outreach.py` exit 0).
> Follow-ups proposed for the owner's cadence (default day 2 / 5 / 8), each
> with a new point: the on-call setup, then her `pg-shadow-copy` work, then a
> close-out. Outreach log row: Priya Nair | 2026-10-12 | email (address from
> her site) | touch 1 | drafted. Not sent.*
