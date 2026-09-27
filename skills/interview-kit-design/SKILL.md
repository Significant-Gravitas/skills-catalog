---
name: "interview-kit-design"
description: "Designs a structured interview loop for a role: one owner per must-have, four to six job-related questions per slot with strong-answer notes and probes, a clock per slot, anchored 1-5 scorecards, and one-page prep packets for tomorrow's interviewers built from the tracker, with quoted and sourced candidate summaries. Lints questions for protected-trait drift and checks the kit before booking. Use when a role needs its interview loop planned, the panel needs question banks and anchored scorecards, or tomorrow's interviewers need prep packets."
triggers: ["design the interview loop", "build an interview question bank", "write interview scorecards", "prep packet for tomorrow's panel", "what should each interviewer ask", "structured interview kit", "which competency does each slot cover"]
version: "2"
---

# Interview kit design

A structured kit makes a loop fair and a debrief possible: every candidate
for the role meets the same competencies, core questions and anchored scale.
Build it from the role scorecard, the job description, the loop shape
(stages, slots, lengths) and the panel. Packets also use what the candidate
sent, their public professional work, and earlier rounds. Why structure
works, with sources: `references/structured-interview-science.md`.

**Use when:** a loop needs designing or changing; the panel needs questions or
scorecards; the owner pastes questions to check; packets are due (on request
or from the evening-interview-prep routine).
**Do not use for:** the role scorecard itself (role-intake-and-scorecard),
booking the loop (interview-coordination), running the debrief
(hiring-debrief-and-decision).

## Inputs and where they come from

| Input | Source |
| --- | --- |
| Role scorecard with must-haves M1..Mn | `~/workspace/hiring/roles/<role-slug>/scorecard.md` (role-intake-and-scorecard) or the owner |
| Job description | `~/workspace/hiring/roles/<role-slug>/` or pasted |
| Loop shape, panel, owner timezone, scorecard window, candidate AI policy, accommodation contact | `~/workspace/hiring/preferences.md` (`loop_shape.<role>`, `panel.<role>`, `timezone`, `scorecard_due_hours`, `candidate_ai_policy`, `hiring_jurisdictions`); else `memory_search("hiring preferences")`; else one `ask_question` |
| Loop log (who, when, which competency) | `~/workspace/hiring/tracker/loops.csv` (interview-coordination keeps it) |
| Candidate material | Files the owner supplied (pull uploads with `read_workspace_file(..., save_to_path=...)`) and the candidate's public professional work; earlier-round records in `~/workspace/hiring/debriefs/<role-slug>/` |
| Calendar (optional cross-check) | `find_capability("google calendar list events")` → `run_capability` (read-only) |

## Pre-flight

Every `python3 scripts/...` command in this skill runs as `cd ~/skills/interview-kit-design && python3 scripts/...`: `bash_exec` starts in `/home/user`, not the package folder.

`bash_exec`: `cd ~/skills/interview-kit-design && python3 --version && python3 -c "import zoneinfo; zoneinfo.ZoneInfo('Europe/Lisbon')" || python3 -m pip install --user tzdata`.
`mkdir -p ~/workspace/hiring/roles/<role-slug> ~/workspace/hiring/packets`.
No Python: do every check by hand with `checklists/kit-review.md` and label
the output "not script-checked". Mirror the checklist in `TodoWrite` for a
new kit.

## Procedure: the kit

1. **Map competencies to slots.** Every must-have gets exactly one owner, so
   nothing is asked twice or skipped. Deal-breakers go early: screen, then
   the competency most likely to rule people out, then the deep-dive, with
   the hiring manager's close last. Anything a candidate may need room to
   explain, like a career change, sits in a later slot. Default four slots
   or fewer (four interviews predicted the decision with 86% confidence
   [29]; default — confirm with the owner); a fifth needs a stated reason.
   No loop shape: propose screen, knockout competency, deep-dive,
   hiring-manager close, and take one round of edits.
2. **Write the questions** in `templates/kit.md`, one competency at a time,
   four to six per slot (patterns: `references/question-bank-patterns.md`).
   Under each: what a strong answer shows, and one probe that tests whether
   the candidate did the work: "Which part was yours?", "What number
   moved?", "What would you change?". Drop any question that checks
   recognition of a tool name rather than use; signals the wanted answer;
   bundles two questions; or could be answered by reading the posting back.
   Tighten and open up the owner's own questions before adding new ones.
3. **Give each slot a clock** (default for a 45-minute slot: about 5 on
   context, 30 on the main problem, 10 for the candidate's questions; adjust
   to the owner's loop shape). Warn that the main problem overruns and eats
   the candidate's time. Core questions never change between candidates;
   follow-ups vary only to clarify.
4. **Anchor the scorecard** (`templates/scorecard-1to5.md`): 1
   unsatisfactory, 2 below bar, 3 meets bar, 4 above bar, 5 exceptional, each
   described in one line of this role's real work, plus "not assessed".
   Each rating cites something the candidate said or did. The card closes
   with hire or no hire and a one-sentence reason, **filled only after every
   competency rating**. Interviewers file alone, before talking to the rest
   of the panel, inside the scorecard window (default 24 hours — confirm with
   the owner). One scorecard per role.
5. **Lint and check.** Save to `~/workspace/hiring/roles/<role-slug>/kit.md`, then
   `cd ~/skills/interview-kit-design && python3 scripts/question_lint.py <kit.md>` (also on any
   list the owner pasted) and
   `python3 scripts/check_kit.py <kit.md> --scorecard <scorecard.md>`.
   Fix every ERROR; show each rewrite in the kit's "Dropped or rewritten"
   table (`references/unlawful-question-rewrites.md`). Explain WARNs you keep.
   Technical phrases ("race condition", "health checks", "medical-claims
   billing") are already exempt. If the lexicon still misreads a job-related
   term, mark that line `<!-- lint-ok: <reason> -->`: the hit prints as
   OVERRIDDEN, and each one goes in the "Dropped or rewritten" table for the
   owner to see. Never override a question about the person: the script
   honours an override only for one ambiguous technical word (condition,
   race, temple, health, citizen as in "citizen developer" ...) on a line that
   is not about the person (no "Are you / Do you" opener, no you/your within
   two words of the hit, no person-directed phrase), and never for criminal-record, salary-history,
   genetic or sex-orientation hits.
6. **Hand back** the kit (output contract). For the debrief, point the panel
   to the running order and challenge line in hiring-debrief-and-decision.

## Procedure: prep packets

1. `python3 scripts/build_packets.py --date tomorrow --tz <owner tz>` (or a date).
   "no interviews on <date>" → stop; in a routine run, post nothing.
2. Cross-check the calendar if connected (read-only); report mismatches, do
   not edit the tracker from here.
3. Fill only the summary: at most five lines, each a **direct quote** with
   its source, using only what the owner supplied and the candidate's public
   professional work; "not stated" for a gap. For a URL, `web_fetch` it, save
   the text, and pass `--source-map`.
4. `python3 scripts/verify_quotes.py <packet.md>`. Every summary line must
   end OK (an exact quote, or "not stated"); any changed word or number is a
   FAIL, so copy the words from the source or drop the line. Every quote on
   a line is checked; words outside the quotes (other than a short
   `<topic>:` label) FAIL as paraphrase, and so does a quote that cuts off a
   "not" or "never" just before it in the source. Mark SKIP lines
   UNVERIFIED in the packet.
5. Report every FLAG (no interviewer, no competency, no material, no zone).
6. Deliver each packet with `write_workspace_file(source_path=...)` and link it.

## Output contract

- **Kit:** question banks, anchored scorecards and slot timings in chat and at
  `~/workspace/hiring/roles/<role-slug>/kit.md` (one file per role), delivered
  as a `workspace://` link; the lint and check results (or "not script-checked");
  one line naming any slot missing an interviewer or a competency.
- **Packets:** one page per interview in slot order, top line with the time
  in the candidate's zone and the owner's, the interviewer and the
  competency they own; the quoted summary; that competency's questions;
  what earlier rounds covered and the open question this slot should close;
  one logistics line (room or video link, greeter, scorecard deadline).
  Saved as `~/workspace/hiring/packets/<date>-<role>-<candidate>-<time>-slot<n>.md`.

## Guardrails

- Every question is job-related. Nothing may touch race, colour, sex, age or
  graduation year, pregnancy or family plans, health or disability, religion,
  national origin, marital status, or the language someone speaks at home.
  Test a language only when the work happens in it. Work authorisation comes
  up only if the process needs it, as a yes or no. Ability questions use
  "with or without reasonable accommodation" [35][46]. Name who handles
  accommodation requests; never ask for medical detail.
- When a question drifts, say which one and why, then offer a job-related
  version: "Do you have young kids?" becomes "The role travels one week a
  month; does that work for you?"
- Never rate or ask about affect: confidence, enthusiasm, nerves, honesty,
  "fit", from a call, recording, transcript or notes [73]. Never score polish.
- Packets quote, never paraphrase [62]; no ranking or comparing candidates;
  nothing about age, family, health, religion or background.
- State the candidate AI-use policy per stage if the owner has one; never
  invent one [104]. If the role is in NYC, Illinois, California or the EU,
  add one line that AI-assisted interview rules may apply; confirm with
  counsel (`references/ai-affect-and-candidate-ai.md`).
- Kits and packets are drafts. Nothing reaches the panel or a candidate until
  the owner approves that particular send. On a yes: a Gmail draft per
  interviewer (`find_capability("gmail create draft")` → `describe_capability`
  → `run_capability(..., validate_only=true)` → the call; use only a draft
  tool) or a Slack DM with
  `run_capability(id="tool:post_to_chat_platform", input={...})` after
  confirming with `run_capability(id="tool:list_chat_platform_channels", input={...})`
  that the target is a DM. Never a group channel. The gate may ask again
  (`approval_required`): wait, and continue independent work. In an
  unattended routine run, make no external write (no Gmail, Calendar, Slack,
  Sheets or ATS change); saving packets to `~/workspace` and attaching them
  with `write_workspace_file` is allowed and expected.

## Quality self-check

- [ ] `check_kit.py` and `question_lint.py` exit 0, or the output says "not script-checked".
- [ ] Every must-have has one owner; every clock adds up and leaves candidate time.
- [ ] Hire / no-hire sits after the ratings; no affect or fit anywhere.
- [ ] Every packet summary line is a verified quote or "not stated".
- [ ] Every time carries its zone; unknown zones are flagged, never guessed.
- [ ] Nothing was sent; missing interviewers or competencies are named in one line.

## Fallbacks

Nothing from or about the candidate: base the packet on the role scorecard and
posting, and flag the summary as thin. No loop shape: propose the four-slot
default and take one round of edits. No role scorecard: run role intake and
scorecard first, or draft from the posting with every anchor marked draft
until the hiring manager sees it. No loop log: build packets by hand from the
owner's list and say the tracker is missing.

## Related skills

Load with `run_capability(id="skill:<slug>", input={})`:
role-intake-and-scorecard (must-haves), interview-coordination (books the
loop, keeps loops.csv), hiring-debrief-and-decision (reads the scorecards,
flags loose anchors back here), resume-screening (evidence for packets).

## Package files

- `scripts/question_lint.py`, `check_kit.py`, `build_packets.py`,
  `verify_quotes.py` (shared parser `kitparse.py`); each has `--selftest`
- `references/structured-interview-science.md`, `question-bank-patterns.md`,
  `unlawful-question-rewrites.md`, `ai-affect-and-candidate-ai.md`
- `templates/kit.md`, `scorecard-1to5.md`, `prep-packet.md`
- `checklists/kit-review.md`
- `examples/senior-backend/` (kit, lint, check, packets and verified summary,
  end to end), `examples/hard-case/` (drifting owner questions, a five-slot
  ask, a request to put age in a packet)

## Example

> **Example (fictional: Senior Backend Engineer, slot 2, billing debugging,
> 60 min, interviewer Dev Rao).**
>
> Competency: must-have M3, debugs payment or billing flows end to end.
> Clock: 5 context, 40 main problem, 15 candidate questions.
>
> 1. "Walk me through a billing or payment bug you traced to its root."
>    Strong answer: names the symptom, the data they pulled, the wrong
>    assumption. Probe: "Which part was yours?"
> 2. "A customer was charged twice. Where do you look first, and why?"
>    Strong: idempotency keys, webhook retries, reconciliation job.
>    Probe: "What would you log so you'd know next time?"
> 3. "How did you confirm the fix worked in production?"
>    Strong: a metric or reconciliation that moved. Probe: "What number moved?"
> 4. "Tell me about a billing change you shipped that went wrong. What did
>    you do in the first hour?"
>    Strong: rollback or containment first, then who they told and what data
>    they checked. Probe: "What would you change?"
>
> Dropped: "You're comfortable with Stripe, right?" (signals the answer,
> checks a tool name). Replaced by question 2.
>
> **Scorecard anchors (this competency):**
> 1 cannot describe a billing failure they worked on · 2 fixed symptoms,
> could not say the cause · 3 traced one real bug to root cause and verified
> the fix · 4 also changed the system so the class of bug stopped · 5 did
> that across teams and can show the result · not assessed.
>
> `check_kit.py`: ok. `question_lint.py`: clean.
