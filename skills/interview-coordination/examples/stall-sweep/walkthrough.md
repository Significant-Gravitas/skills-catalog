# Worked example: stall sweep and morning brief, end to end

Fictional. Owner: Maya Chen, timezone Europe/Lisbon. Thursday 8 Oct 2026,
15:00. The files in `hiring/tracker/` are the tracker as it stands. Every
output below is a real script run on them.

## 1. Read the tracker fresh

```
$ cd ~/skills/interview-coordination && python3 scripts/merge_tracker.py refresh --today 2026-10-08
candidates: days_in_stage updated on 3 row(s) (calendar days since stage_since)
```

## 2. Sweep

```
$ python3 scripts/stall_sweep.py --tz Europe/Lisbon --today 2026-10-08 --now 2026-10-08T15:00
# Stalled as of 2026-10-08 (business days skip weekends only; no holiday list given)

## Waiting on Maya Chen
- Aisha Bello, Senior Backend Engineer: scheduling unbooked; since 2026-10-02 (4 business days; bar 2). Frees it: owner picks one of the loop options.

## Waiting on Lena Ortiz
- Priya Nair, Senior Backend Engineer: scorecard late (M4 2026-10-05); since 2026-10-05T13:15 (3 days; bar 1). Frees it: Lena Ortiz files the scorecard (alone, before the debrief).
- Priya Nair, Senior Backend Engineer: response window; since 2026-10-06 (63 hours; bar 24). Frees it: send the candidate a holding update (drafted) while Lena Ortiz decides.

## Waiting on Dev Rao
- Tom Becker, Senior Backend Engineer: invite unaccepted (M3 2026-10-09 14:00 Europe/Lisbon); since 2026-10-09T14:00 (23.0 hours to start; bar 24). Frees it: Dev Rao accepts, or names a substitute who can take the competency.
```

Chen Wei is a prospect, so no stall is raised for him. Aisha is also past
the 3-day no-update bar and Priya will be on Friday, but no separate
"no update" line is raised for either: the scheduling and response-window
items already cover that missing update, so it is one line, not two.

## 3. What Maya gets (the reply)

> **Waiting on Lena Ortiz (hiring manager)**
> - Priya Nair, Senior Backend: loop ended Mon 5 Oct; Lena's scorecard not
>   filed (3 days; bar is 1). Frees it: Lena files. Nudge drafted.
> - Priya hasn't heard from us since Tue 6 Oct (promise: 24 hours). Holding
>   note drafted: "Hi Priya, the team is finishing its feedback from Monday;
>   you'll hear from me by Monday 12 Oct either way."
>
> **Waiting on Dev Rao**
> - Invite for Tom Becker, Fri 9 Oct 14:00 Lisbon / 15:00 Berlin, not
>   accepted inside 24 hours of the loop. Frees it: Dev accepts or names a
>   substitute for the billing-debugging slot. Nudge drafted.
>
> **Waiting on us**
> - Aisha Bello: asked for times on 2 Oct, no loop booked (4 business days).
>   Frees it: you pick one of two loop options (below, both timezones on
>   every slot). Update to Aisha drafted.
>
> Nudge draft to Lena (not sent): "Lena, your scorecard for Priya Nair
> (Monday's close) is still open. The debrief is Friday 11:00 Lisbon; could
> you file by 17:00 today so it's in before anyone talks?"
>
> Tracker: 0 rows added, 3 updated (days in stage); needs-a-look: none.
> Nothing sent.

The stall history (`flags/stall-history.csv`) now holds these four items.
At Friday's 08:00 brief (`--today 2026-10-09 --now 2026-10-09T08:00`) the
four still-open items are not re-raised: the sweep prints only

```
Unchanged since an earlier brief (4; one rollup line in the brief): Priya Nair scorecard late (Lena Ortiz, since 2026-10-08); Tom Becker invite unaccepted (Dev Rao, since 2026-10-08); Priya Nair response window (Lena Ortiz, since 2026-10-08); Aisha Bello scheduling unbooked (Maya Chen, since 2026-10-08).
```

and the brief carries that as its single rollup line. Priya's no-update,
now at its 3-day bar, is not a new line: her response-window item already
holds it. An item is
marked `SECOND STALL` only when it cleared and came back, or when it is
still open twice its bar after first being flagged: Lena's scorecard (bar
1 day) escalates at Saturday's run or later, with who holds it, the days
lost, and what it does to the debrief.
