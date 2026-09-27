---
name: "job-description-drafting"
description: "The posting step after role-intake-and-scorecard: turn an approved role scorecard into a public job posting, rewrite an old posting against it, or check a posting's language before it goes live."
triggers: ["write a job description", "rewrite this job posting", "check this JD for bias", "job post for the new role", "make this posting inclusive", "draft the req posting", "is this job ad any good"]
version: "2"
---

# Job description drafting

This is the step after role intake and scorecard: the approved scorecard is
the bar, and the posting is how that bar is shown to the public. The posting
never sets the bar on its own.

**Use it for:** a scored role that needs its posting; an old posting (paste,
URL or file) to rewrite against the scorecard; "check this JD for bias" or
"is this job ad any good" on any posting.
**Do not use it for:** deciding what the role requires (run
`role-intake-and-scorecard` first), pay figures (never invented), or
publishing (drafts only).

## Inputs and where they come from

| Input | Where from | If missing |
|---|---|---|
| Approved role scorecard (M1..Mn, N1..) | `~/workspace/hiring/roles/<role-slug>/scorecard.md` (status `approved`) | See Decisions: no scorecard |
| HM notes on the team and the work, day-in-the-life lines | The intake conversation / scorecard quotes | Ask one question |
| Facts that must appear: title, level, location and work setup, pay range, benefits, how and by when to apply | Owner, as stated | Written `[OWNER TO CONFIRM]`, never guessed |
| `hiring_jurisdictions`, `candidate_ai_policy` | `cat ~/workspace/hiring/preferences.md` | Ask once; else leave the AI-use line out |
| An old posting | Paste; URL via `web_fetch`; upload via `read_workspace_file(..., save_to_path=...)` | — |

## Procedure

Mirror the steps in `TodoWrite`. Pre-flight once: `python3 --version`.

1. **Load the bar.** `cat ~/workspace/hiring/roles/<role-slug>/scorecard.md`.
   Check the header says `status: approved`. If it says anything else
   (`draft`, `draft-pending-calibration`), stop: nothing reaches a posting
   until the HM approves the scorecard. Route to `role-intake-and-scorecard`
   for the approval. Only if the owner insists on a posting now, draft it with
   "Draft pending calibration" as the first line of the posting and say the
   bar is not approved (the fallback in Decisions below).
2. **Bring in an old posting if there is one.** URL: `web_fetch(url,
   extract_text=true)`; if a JavaScript job board returns under 500
   characters, `run_capability(id="tool:browser_navigate", input={"url": ...})`
   and read the snapshot (read-only). Extract only this role's section and
   confirm with the owner it is the right posting. Save it as
   `/home/user/old-posting.md`. `web_fetch` caps at 100 KB; say so if the page
   was cut off.
3. **Draft from [templates/posting.md](templates/posting.md)**, always in this
   order:
   - The mission in two sentences.
   - What this person owns in the first months (the scorecard's year-one
     outcomes, trimmed), with day-in-the-life lines pulled verbatim from the
     intake conversation, and the baseline in plain words: who should apply
     and what success looks like.
   - Work terms: location as work terms (on-site days, hours, travel), never a
     postcode or "local candidates only".
   - The scorecard's must-haves, word for word as checkable outcomes; the
     posting never adds or loosens one.
   - The labelled nice-to-haves.
   - What the team offers: scope, growth, pay range and benefits as stated.
   - How and by when to apply.
   - An accommodation line (always; contact `[OWNER TO CONFIRM]` if unknown).
   - The candidate AI-use line, only if `candidate_ai_policy` is set [104].
   - The anti-scam line, only if the owner wants it [82].
   - A short equal-opportunity close.
   Requirements are outcomes, not pedigree: "has shipped a service handling
   production traffic" beats "5+ years experience". Degree demands and
   years-floors appear only if the scorecard records "HM defended: ...", and
   the posting carries the floor, never the HM's defence note (internal).
   Nice-to-haves come only from the scorecard's `## Nice-to-haves` (N-lines);
   if it has none agreed, the posting has no nice-to-have section. A new one
   goes through a scorecard revision like a must-have.
4. **Mark posting-law fields.** Look up each place in `hiring_jurisdictions`
   and the posting location in
   [references/posting-law-fields.md](references/posting-law-fields.md). For
   every field it lists that the owner has not given (pay range, benefits,
   apply-by date), write `[OWNER TO CONFIRM — may be required for <place>]`
   and add one line for the people lead. Never say a field is legally
   required; say it may be, and confirm with counsel. Never supply a figure.
5. **Save and screen the language.** Save the draft as
   `~/workspace/hiring/roles/<role-slug>/posting-v<N>.md` (next N; never
   overwrite a version). Run
   `cd ~/skills/job-description-drafting && python3 scripts/jd_lint.py ~/workspace/hiring/roles/<role-slug>/posting-v<N>.md`.
   Every `FLAG` gets a swap or a one-line owner defence; `CHECK` hits are read
   in context (a job title with "Lead" is fine); `info` hits are balance only.
   What the lint means: [references/inclusive-language-lint.md](references/inclusive-language-lint.md).
   The lint is a backstop, not the review: also read every line against
   [references/protected-traits-and-proxies.md](references/protected-traits-and-proxies.md)
   and report, with line numbers, any proxy the lint missed (an age or
   graduation-year cut-off, a citizenship or language-origin demand, a
   pronoun for the hire, family, religion, appearance, salary history).
   Also cut, by reading: laundry lists of nice-to-haves posing as
   requirements, and jargon a strong outsider would not know. When you cut a
   line, say what you cut and why in one line.
6. **Check the mirror.** Run
   `cd ~/skills/job-description-drafting && python3 scripts/mirror_check.py ~/workspace/hiring/roles/<role-slug>/scorecard.md ~/workspace/hiring/roles/<role-slug>/posting-v<N>.md`.
   Anything `CHANGED`, `MISSING` or `ADDED` (including a posting
   nice-to-have that is not on the scorecard's `## Nice-to-haves`; with none
   agreed there, every posting nice-to-have is `ADDED`; "Bonus points", "Preferred qualifications" and "Even better if" headings count as nice-to-have sections) is fixed in the posting, or goes back through
   `role-intake-and-scorecard` to change the bar first. Exit 0 before the
   clean block. A requirements heading the script does not recognise: pass
   `--heading "<heading text>"`.
7. **Show it; take one round of edits.** Show the posting in chat, then the
   lint result, the cut list, and anything still UNKNOWN. After edits, save
   `posting-v<N+1>.md` and rerun steps 5 and 6.
8. **Before-and-after for a rewrite.**
   `cd ~/skills/job-description-drafting && python3 scripts/diff_postings.py /home/user/old-posting.md ~/workspace/hiring/roles/<role-slug>/posting-v<N>.md`
   and show the changed lines.
9. **Render and deliver.**
   `cd ~/skills/job-description-drafting && python3 scripts/render_posting.py ~/workspace/hiring/roles/<role-slug>/posting-v<N>.md`
   writes `.html` (paste into rich-text ATS fields) and `.txt` (plain fields);
   internal notes are left out. If any `[OWNER TO CONFIRM]`, `<...>` or
   "draft pending calibration" is left, it prints `WARNING: <n> unresolved
   fields; not paste-ready`, writes nothing and exits 1. Resolve them, or
   rerun with `--draft` for copies stamped "DRAFT - NOT PASTE-READY" and
   deliver them labelled as drafts. Deliver all three with
   `write_workspace_file(filename=..., source_path=...)` and link them as
   `workspace://<file_id>#<mime>`.

## Decisions inside the procedure

- **Scorecard not approved?** Route to `role-intake-and-scorecard` for the
  HM's approval first. Only if the owner insists on a posting now: draft it
  with "Draft pending calibration" at the top, and it is not paste-ready.
- **No scorecard?** Run `role-intake-and-scorecard` first. If the user insists
  on a posting now, ask the four intake questions (year-one delivery, the two
  things that rule a candidate out, whether anyone's work sets the bar, when
  the seat must be filled), save the answers as a draft scorecard through that
  skill, and mark the posting a draft pending calibration.
- **Only an old posting?** Rewrite in place against the scorecard and show the
  before-and-after on the lines you changed (step 8).
- **"Check this JD for bias" on a posting with no scorecard?** Run the lint
  (step 5) and the posting-law lookup (step 4) on it as-is; report the lint's
  hits and the proxies you found by reading, with line numbers; skip the
  mirror check and say why. Zero FLAGs alone is never "no bias found".
- **Owner wants pay left out in a place listed in posting-law-fields?** Keep
  `[OWNER TO CONFIRM — may be required for <place>]`, add the people-lead
  line, and do not remove the flag. The decision is theirs and counsel's.
- **Owner wants to add a requirement or a nice-to-have** the scorecard does
  not have? It goes through a scorecard revision in
  `role-intake-and-scorecard` (its `scorecard_check.py --revise`) and the HM's
  approval first, or it stays out. The posting never sets the bar.
- **Owner defends a flagged word** (e.g. "lead" in "Lead Engineer")? Keep it
  and record the defence in the internal notes.

## Output contract

1. The posting in chat, in the template order.
2. `Language flags`: each lint FLAG with line and swap, and what the owner
   chose; the cut list, one line per cut.
3. `Mirror`: "M1-M<n> match the approved scorecard v<k>" (or what differs).
4. `Still UNKNOWN`: every `[OWNER TO CONFIRM]` field, with the place that may
   require it.
5. For a rewrite, the before-and-after.
6. Files: `posting-v<N>.md`, `.html`, `.txt` in
   `~/workspace/hiring/roles/<role-slug>/`, delivered and linked; if
   `render_posting.py` warned, the count of unresolved fields and "draft, not
   paste-ready".
7. A last line: "Not posted anywhere."

## Guardrails

- Drafts only. Never post a job, publish a req, or send a posting anywhere
  without the owner's explicit yes for that specific action.
- Never invent the numbers: pay, title, level and start date go in only as the
  user stated them. Do not guess a salary range or derive one from the
  company's size, stage or funding. Unconfirmed means `[OWNER TO CONFIRM]` /
  UNKNOWN.
- The posting never adds, loosens or rewords a must-have; changes go through
  the scorecard.
- No protected-trait wording or proxy, no photo request, no postcode or
  commute filter, no health question ("with or without reasonable
  accommodation" for physical demands).
- Legal questions about posting law go to the people lead or attorney with a
  one-line brief; you flag, you do not advise.

## Quality self-check

- [ ] Scorecard status `approved`; otherwise routed for approval, or (owner insisted) the posting opens with "Draft pending calibration".
- [ ] `jd_lint.py`: zero unhandled FLAGs, and every line read against protected-traits-and-proxies.md (misses reported).
- [ ] `mirror_check.py`: exit 0.
- [ ] Every posting-law field for the location is filled as stated or `[OWNER TO CONFIRM]`.
- [ ] Accommodation line present; AI-use line only if the policy is set.
- [ ] No number that the owner did not state.
- [ ] HTML/TXT rendered (no unresolved-field warning, or delivered as a stamped draft), versions saved, copies delivered.

Pre-publish checklist: [checklists/pre-publish.md](checklists/pre-publish.md).
Worked example with a hard case: [examples/senior-backend-posting.md](examples/senior-backend-posting.md).
Citations: [references/sources.md](references/sources.md).

## Siblings

Before: `role-intake-and-scorecard` (the bar; rescopes go there). After:
`candidate-sourcing-strategy` (names), `resume-screening` (inbound against the
same M-ids). First chat: `sofia-getting-started`.
