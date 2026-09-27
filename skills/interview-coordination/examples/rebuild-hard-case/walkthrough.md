# Hard case: interviewer drops out across a DST change, plus a decline and a removal

Fictional. Owner Maya Chen (Europe/Lisbon). Candidate Jordan Lee is in New
York (America/New_York, stated on the application). The urgent sweep at
10:00 on Tue 20 Oct flags a Slack DM from Dev Rao: he is out for two weeks
from Thursday and cannot take Jordan's billing-debugging slot. In the same
chat Maya says: "Decline Rui Costa, the background check came back weird.
Oh, and Jordan's LinkedIn says he's in Lagos, so let's do an extra ID check
on him. And delete Sara Lind from everything, she asked us to."

## 1. The drop-out: the competency still needs an owner

Dev owned M3 (billing debugging). The kit names Mia Chen as the only other
interviewer calibrated on M3, so she goes in `alternates`. Jordan's new
windows and the panel's free/busy (read-only calendar reads) are in
`availability.json`. Europe leaves summer time on 25 Oct and the US on
1 Nov, so the offset between Lisbon and New York is 5 hours on the 23rd
and 4 hours on the 26th; the script does the arithmetic.

```
$ python3 scripts/tz_slots.py examples/rebuild-hard-case/availability.json
Option 1: Fri 23 Oct (compromise: stand-in Mia Chen for Dev Rao (Billing debugging (M3)))
  - Billing debugging (M3), Mia Chen: Fri 23 Oct 08:00–09:00 America/New_York / Fri 23 Oct 13:00–14:00 Europe/Lisbon
  - Live data changes (M2), Ana Silva: Fri 23 Oct 09:10–09:55 America/New_York / Fri 23 Oct 14:10–14:55 Europe/Lisbon
  - Hiring manager close (M4), Lena Ortiz: Fri 23 Oct 10:25–11:10 America/New_York / Fri 23 Oct 15:25–16:10 Europe/Lisbon
Option 2: Fri 23 Oct (compromise: stand-in Mia Chen for Dev Rao ...) 09:00–12:10 New York / 14:00–17:10 Lisbon
Option 3: Mon 26 Oct (compromise: stand-in Mia Chen for Dev Rao ...)
  - Billing debugging (M3), Mia Chen: Mon 26 Oct 08:45–09:45 America/New_York / Mon 26 Oct 12:45–13:45 Europe/Lisbon
  ...
```

Every option carries the same compromise (Dev is out), so the reply says so
once and offers the choice. Tue 27 Oct is not offered: Jordan's two-hour
window cannot hold a three-hour loop (read from `availability.json`; the
script prints a binding constraint only when no option fits at all).

After Maya picks Option 1 and chooses "attendee-less holds on my calendar",
three `HOLD:` events are created (the gate asked once; Maya approved), the
Dev row in `loops.csv` becomes `cancelled`, a new Mia row is added, and three
drafts wait: Jordan's email with the new times in both zones, a note to Mia
with the kit link, and a note to Dev releasing him. Nothing is sent.

## 2. "Decline Rui Costa, the background check came back weird"

A background check played a part, so no decline is drafted
(`references/fcra-and-verification.md`). Reply:

> This decline has to go through your background-check (FCRA) process
> first: a pre-adverse action notice with the report and a pause before any
> final decision. Who runs that for you? I've set Rui's next step to
> "FCRA process" and won't draft a decline.

## 3. "Jordan's LinkedIn says Lagos, so an extra ID check on him"

Refused as asked, with the lawful version:

> I won't add a check for one candidate based on location; that's a
> national-origin risk, not verification. If you want identity verification
> for this remote role, set one step for every candidate at the onsite stage
> (for example a live ID check on video) and I'll track it for all of them.

(Jordan's own application states New York; the tracker keeps that as his
`tz`. A profile's city is never used to change it.)

## 4. "Delete Sara Lind from everything"

Done in the same reply, without asking why. The request came from Sara, so
`--keep-dnc` keeps her name and a do-not-contact flag and nothing else: no
later sourcing batch can reach her again.

```
$ python3 scripts/forget_candidate.py --name "Sara Lind" --keep-dnc --dry-run
DRY RUN: 3 row(s) would delete across 3 file(s); 2 file(s)/folder(s) would delete; 1 mention(s) in 1 file(s) would be replaced with [removed]
  dnc.csv keeps: name + do-not-contact flag only
$ python3 scripts/forget_candidate.py --name "Sara Lind" --keep-dnc
3 row(s) deleted across 3 file(s); 2 file(s)/folder(s) deleted; 1 mention(s) in 1 file(s) replaced with [removed]
  dnc.csv keeps: name + do-not-contact flag only
```

Then: memory facts naming her found with `memory_search("Sara Lind")` and
removed with the memory-forget tool located by `find_capability("memory forget")`
(memory on); two delivered
copies found with `run_capability(id="tool:list_workspace_files", input={"include_all_sessions": true})`
and removed with `run_capability(id="tool:delete_workspace_file", ...)` (the
gate asked; Maya approved). Reply:

> Removed Sara Lind: 3 tracker and log rows, 1 packet, 1 screen folder, one
> mention in last week's review, 2 delivered copies and 1 memory note. Her
> name stays on the do-not-contact list only, so she is never contacted again.
> Your ATS and mailbox still hold her records; those are yours to remove.
> Note: hiring-record retention rules can require keeping some records
> (US: at least a year); check with counsel if a claim is possible.
