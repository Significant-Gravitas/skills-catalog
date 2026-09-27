# Worked example: rewriting an old posting, with a hard case

Fictional throughout (Northwind Tools, hiring manager Lena Ortiz). Files in
this folder:

- [scorecard-senior-backend-engineer.md](scorecard-senior-backend-engineer.md): the approved bar (v1).
- [old-posting-senior-backend.md](old-posting-senior-backend.md): what the owner linked.
- [posting-senior-backend-v1.md](posting-senior-backend-v1.md): the result.

## 1. Load the bar

`cat ~/workspace/hiring/roles/senior-backend-engineer/scorecard.md` ->
`status: approved`, `approved_by: Lena Ortiz`, M1-M4, N1-N2.
`preferences.md`: `hiring_jurisdictions: Portugal, Spain (EU); Colorado (US)`
(the scorecard's work terms allow the US with a daily 15:00-17:00 CET overlap,
and the owner expects Colorado applicants),
`candidate_ai_policy: Allowed to draft, not in live interviews`.

## 2. Bring in the old posting

Owner: "Rewrite our old one: https://careers.northwind.example/backend".
`web_fetch` returns 310 characters (a JavaScript board), so Sofia runs
`run_capability(id="tool:browser_navigate", input={"url": ...})`, reads the
snapshot, extracts only the backend role, and asks "Is this the one?" Yes.
Saved as `/home/user/old-posting.md`.

## 3. Lint the old one first (so the owner sees why)

```
$ cd ~/skills/job-description-drafting && python3 scripts/jd_lint.py /home/user/old-posting.md
L1:11 FLAG "Rockstar" [label] -> describe the outcome
L3:34 FLAG "young" [age] -> describe the work pace instead ([45] 29 CFR 1625.4)
L3:41 FLAG "energetic" [age-proxy] -> describe the pace of the work
L3:59 FLAG "ninja" [label] -> describe the outcome
L8:3 FLAG "Native English" [national-origin-proxy] -> writes/speaks English at <the level the tasks need> ([34])
L9:3 FLAG "Digital native" [age-proxy] -> name the tool or skill ([34])
L9:31 FLAG "crush it" [label] -> describe the outcome
L10:10 FLAG "culture fit" [class-proxy] -> name the job behaviour or cut ([79])
L12:4 FLAG "work hard and play hard" [label] -> describe the working hours honestly
L12:29 FLAG "Open until filled" [posting-law] -> state how and when to apply (not compliant in Colorado per state guidance) ([57])
L3:77 CHECK "competitive" [masculine-coded] -> fine for 'competitive salary'; avoid 'competitive person' ([31])
summary: 10 FLAG, 1 other
```

## 4. Draft, save as v1, lint, mirror

Drafted from `templates/posting.md`; saved as
`~/workspace/hiring/roles/senior-backend-engineer/posting-v1.md`.

```
$ python3 scripts/jd_lint.py .../posting-v1.md
L9:49 CHECK "lead" [masculine-coded] -> fine in a job title or 'lead the rotation'
summary: 0 FLAG, 1 other
$ python3 scripts/mirror_check.py .../scorecard.md .../posting-v1.md
MATCH   M1: Has run on-call for a service with paying customers.
MATCH   M2: Has shipped a schema migration on a live Postgres database without downtime.
MATCH   M3: Has written design docs other engineers acted on.
MATCH   M4: Has debugged payment or billing flows end to end.
summary: 4 scorecard must-haves, 4 posting lines, 2 nice-to-haves, 0 differences
```
"lead the on-call rotation" is job content: kept. Had Lena defended a years
floor, the scorecard line would read `M1: ... HM defended: "<her reason>"`;
the posting carries the floor without the quote, and `mirror_check` strips
the "HM defended:" note before comparing, so it still matches.

## 5. The hard case

Owner: "Leave the pay out, we never share it. And keep 'open until filled',
we don't want a deadline. Also add 'Kubernetes expert' to the requirements,
Lena mentioned it once."

Sofia's reply:

> Three things:
> 1. **Pay.** The role is open to people working from Colorado, and Colorado postings may
>    need a pay range, a benefits summary and how and when to apply. I've left
>    `[OWNER TO CONFIRM — may be required for Colorado postings]` in place and
>    won't fill or remove it; that call is yours and counsel's. For the people
>    lead: "Colorado: pay range, benefits summary and apply-by date may be
>    required. Confirm with counsel before publishing."
> 2. **"Open until filled."** Colorado guidance says that phrasing isn't a
>    compliant application window. I've written "Apply by [OWNER TO CONFIRM —
>    date]". Tell me a date, or counsel's view.
> 3. **Kubernetes.** It isn't on the approved scorecard, and the posting
>    can't set the bar, as a requirement or as a nice-to-have (nice-to-haves
>    break ties in screening, which reads the scorecard). `mirror_check` would
>    show it as ADDED either way (it would also be ADDED if the scorecard's
>    nice-to-haves said "none agreed"). If Lena wants it, I'll open scorecard v2
>    through role-intake-and-scorecard, ask her what fails without it, and
>    add it once she approves; until then it stays out. Shall I ask her?

The owner says "ask Lena". Sofia opens the revision in
`role-intake-and-scorecard`; the posting stays at v1, unchanged, until Lena
approves v2 (then the mirror check is rerun against v2).

## 6. Before-and-after, render, deliver

```
$ python3 scripts/diff_postings.py /home/user/old-posting.md .../posting-v1.md
## (top)
- title: Backend Rockstar
- Northwind Tools is looking for a young, energetic backend ninja to join our competitive, fast-moving team.
- heading: Requirements
- 5+ years backend experience
- BS in Computer Science
- Native English speaker
- Digital native who loves to crush it
- Strong culture fit
- We work hard and play hard.
- Open until filled.
+ title: Senior Backend Engineer, Billing — Northwind Tools
+ heading: Remote from the EU within CET +/- 1 hour, or from the US with a daily 15:00-17:00 CET overlap · on-call one week in five
+ We sell scheduling software to 3,000 clinics.
+ Billing is where our revenue lives, and it needs an owner.
+ heading: In your first months
[... 21 more "+" lines, one per sentence of posting-v1.md ...]

summary: 10 removed, 26 added, 0 kept
$ python3 scripts/render_posting.py .../posting-v1.md
WARNING: 4 unresolved fields; not paste-ready
  [OWNER TO CONFIRM — may be required for Colorado postings]
  [OWNER TO CONFIRM — a general description may be required for Colorado postings]
  [OWNER TO CONFIRM — date]
  [OWNER TO CONFIRM — contact]
nothing written; resolve them, or rerun with --draft for a stamped draft copy
$ python3 scripts/render_posting.py .../posting-v1.md --draft
WARNING: 4 unresolved fields; not paste-ready
  [...the same four lines...]
.../posting-v1.html
.../posting-v1.txt
```
All three delivered with `write_workspace_file(source_path=...)` and linked,
labelled "draft, not paste-ready: 4 fields to confirm". Both rendered copies
open with "DRAFT - NOT PASTE-READY (4 unresolved fields)".

## 7. What the owner sees last

> **Language flags:** 10 in the old posting, all cut (list above). 0 in v1.
> **Mirror:** M1-M4 match the approved scorecard v1. Kubernetes is with Lena
> as a possible scorecard v2 change; not in the posting.
> **Still UNKNOWN:** pay range, benefits summary, apply-by date, accommodation
> contact (Colorado may require the first three). The rendered copies are
> drafts until these are filled.
> Not posted anywhere.
