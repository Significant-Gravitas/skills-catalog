---
name: "recruiting-getting-started"
description: "Run the first hiring session for an open role: learn the owners and constraints, save a hiring plan to the workspace, and finish with a real job description draft or rubric in the same session. Use when a team opens a role, says it needs to hire, or has no written hiring process; it records who decides, where the role is hired, and which policies apply before any screening."
triggers: ["help me start hiring for a role", "set up our hiring process", "we just opened a new role", "build a hiring plan for this role", "recruiting kickoff with Harper", "we need to hire someone", "first hiring session with Harper", "no written hiring process", "who decides on this hire"]
version: "2"
---

# Recruiting getting started

Use this when a team opens a role or has no written hiring process. The
session ends with a saved hiring plan and one real deliverable, not a plan to
make one later.

**Use when:** a new role opens; the owner says "we need to hire"; there is no
written process, owner list or decision-maker; a later Harper skill finds no
hiring plan for the role.
**Do not use for:** writing or rewriting a posting when a plan already exists
(role-intake-and-job-description), a rubric (hiring-rubric-design), screening
(resume-screening), or any employment-law question (the people lead or counsel).

## Inputs and where they come from

| Input | Where it comes from |
| --- | --- |
| Role, outcome, owners, terms, policies | The owner, by `ask_question` (step 2). Never inferred from a title. |
| Standing company facts (decision-maker, sender, retention policy) | `memory_search`; a hit is a proposal marked "from memory, confirm". |
| Existing plan for this role | `~/workspace/hiring/<role-slug>/hiring-plan.md`; older plans may exist as `hiring-plan-<role>.md` in the cloud workspace (`run_capability(id="tool:list_workspace_files", input={"include_all_sessions": true})`). |
| Old job description, scorecard, tracker | A paste or upload, or Drive if connected (step 1). |

Folder layout, which skill writes which file, and memory rules:
`references/hiring-state.md`.

## Tools and pre-flight

1. `bash_exec`: `python3 --version || echo "python3 missing"`. Without Python,
   do the checks in steps 5 and 6 by hand and say so in the output.
2. State: step 3 creates the role folder. If `~/workspace` is not writable, say
   once "the plan will not carry to the next chat" and deliver every file with
   `write_workspace_file` instead.
3. Mirror `checklists/kickoff-checklist.md` in `TodoWrite`.

## Procedure

1. **Look before asking.**
   - `memory_search(query="hiring decision rights policies")`.
   - `bash_exec`: `ls ~/workspace/hiring/ 2>/dev/null`. A folder for this role
     means a plan exists: open it and update it, do not start over.
   - If the owner mentions an old JD or scorecard in Drive:
     `find_capability(query="google drive search files")` →
     `describe_capability` → `run_capability(..., validate_only=true)` → the
     real call. A sign-in card means Drive is not connected: say so in one line
     and ask for a paste; never wait on it. Read only the file the owner
     confirms; Drive search can surface other roles' confidential papers.
2. **Ask once, with a card.** Send the questions in
   `templates/intake-questions.md` in one `ask_question` call, dropping any
   already answered by memory, the paste or an existing plan. Every question
   has a "Don't know yet" option; record that answer as `OPEN`. The card ends
   the turn: do not draft the JD in the same turn unless the owner already
   pasted enough to start.
3. **Create the role folder.**
   `bash ~/skills/recruiting-getting-started/scripts/init_role.sh <role-slug>`
   - exit 0: folder and blank `hiring-plan.md` created from `templates/hiring-plan.md`.
   - exit 2: the role already exists; open the plan and update it in place.
4. **Fill the plan** with `write_file` or `edit_file`, keeping every heading of
   the template (other skills parse them). Rules:
   - An owner nobody named stays `OPEN`; do not assume authority from a title.
   - A policy is recorded as the owner stated it, with who stated it and the
     date; never write one yourself.
   - Pay is `OPEN` until someone with authority approves a range; never supply a figure.
   - Location is written as work terms (country or state, hours, onsite days,
     travel), never a postcode or commute radius [72].
5. **Flag jurisdiction rules; do not advise.**
   `python3 ~/skills/recruiting-getting-started/scripts/policy_flags.py --locations "<hiring locations>" --ai-screening <yes|no|unknown> --background-check <yes|no|unknown> --talent-pool <yes|no|unknown> --video-interviews <yes|no|unknown> --federal-contractor <yes|no|unknown>`
   Take `--federal-contractor` from the plan's "US federal contractor" policy
   row (record the card's answer there in step 4, so a later session reads the
   same value); if the row is `OPEN` or missing, pass `unknown` and add "Is the
   company a US federal contractor?" to "Open questions" for the people lead. Copy each printed flag into "Jurisdiction flags" and add one line per flag
   to "Open questions" addressed to the people lead. Each flag says "may
   apply; confirm with counsel". A NOTE saying a location was not recognised,
   that a city name was not counted because of the state or country named
   with it, or that "New York" could be the city or the state, becomes an open question
   for the owner. Background: `references/policy-intake-checklist.md`.
6. **Check the plan.**
   `python3 ~/skills/recruiting-getting-started/scripts/plan_check.py ~/workspace/hiring/<role-slug>/hiring-plan.md`
   Fix every `ERROR` (missing heading or field). `OPEN` items are listed, not
   errors; each needs an owner in "Open approvals" or "Open questions".
7. **Deliver.** `write_workspace_file(filename="hiring-plan-<role-slug>.md", source_path="/home/user/workspace/hiring/<role-slug>/hiring-plan.md")`
   and link it as `workspace://<file_id>#text/markdown`. The `~/workspace`
   copy is the record; the delivered copy is for reading. Correct the record
   whenever the owner says so, then re-deliver.
8. **Remember company facts only.** If memory tools exist, store each
   company-level fact (decision-maker, default sender, retention policy,
   accommodation route) with
   `run_capability(id="tool:memory_store", input={"content": "<fact>", "scope": "project:hiring", "kind": "fact"})`.
   Never store candidate data. If memory is off, the plan file is enough.
9. **Show the stages** in `TodoWrite`: role intake and job description →
   rubric → interview plan and scorecard → screening → independent scores →
   debrief → human decision → candidate messages. Stage 1 in progress.
10. **Deliver one real piece of work now.** No approved JD: load
    role-intake-and-job-description with
    `run_capability(id="skill:role-intake-and-job-description", input={})`
    and return the draft. An approved JD exists: load hiring-rubric-design and
    return the rubric. Either way it is a draft for the owner's approval.

## Output contract

1. The saved plan (link) with owners, terms, policies (who stated each),
   stages, jurisdiction flags, open approvals and open questions.
2. One line naming what is still `OPEN` and who must settle it.
3. The first deliverable (JD draft or rubric), marked draft for approval.
4. The paths written under `~/workspace/hiring/<role-slug>/`.

## Guardrails

- No stage may use or infer a protected trait, or a proxy such as a name,
  photo, address or postcode, commute, graduation year, employment gap,
  accent, school prestige, family status, or writing style. Replace
  "culture fit" with job-related behaviour that can be observed and scored.
- Harper prepares the process and evidence. A named human makes every
  advance, reject, hire, pay and offer decision. Do not post the role,
  contact anyone, or send anything.
- Never state a legal conclusion. Jurisdiction flags say "may apply; confirm
  with counsel" and go to the people lead.
- If the owner plans AI-assisted screening or ranking, record it as a policy
  and flag it (step 5); Harper itself never ranks candidates.
- Memory holds company facts only, never candidate data.
- Never advise deleting hiring records; retention questions go to counsel [44].

## Quality self-check

- [ ] Every owner is a named person or `OPEN`; none was inferred from a title.
- [ ] Every policy line has "stated by" and a date; none was invented.
- [ ] Pay is an approved range with approver, or `OPEN`.
- [ ] `plan_check.py` shows no `ERROR` (or the hand check is labelled).
- [ ] Jurisdiction flags are copied and addressed to the people lead.
- [ ] A first deliverable exists in this session.
- [ ] Nothing was posted, sent or stored about a candidate.

## Related skills

role-intake-and-job-description (JD and requirements), hiring-rubric-design
(rubric), interview-plan-and-scorecard (loop and scorecards), resume-screening
(evidence matrix), candidate-interview-debrief, candidate-rejection-email,
candidate-offer-draft. Load with `run_capability(id="skill:<slug>", input={})`.

## Package files

- `scripts/init_role.sh`, `scripts/policy_flags.py`, `scripts/plan_check.py`
- `references/hiring-state.md`, `references/policy-intake-checklist.md`,
  `references/jurisdiction-triggers.csv` (data for `policy_flags.py`),
  `references/sources.md`
- `templates/hiring-plan.md`, `templates/intake-questions.md`
- `checklists/kickoff-checklist.md`
- `examples/billing-ops-lead-kickoff.md` (end to end),
  `examples/hard-case-founder-nyc-rush.md` (hard case)
- `evals/scenarios.md` (location strings `policy_flags.py` must read correctly)

## Example

Fictional hiring plan, for shape only (full run in `examples/billing-ops-lead-kickoff.md`).

```markdown
# Hiring plan: Billing Operations Lead (saved 2026-09-26)
Outcome: month-end close runs without engineering help; failed-payment
  follow-up has one owner.
Hiring manager / final decision: Maya Chen. Headcount + offer approval: Luis
  Ortega (Finance). Coordinator: OPEN.
Interviewers: Maya, Priya (Support lead), Tom (Engineering).
Start: by January 2027. Location: remote, UK hours. Level: L4. Pay: OPEN
  (range not yet approved).
Policies (stated by Maya, 2026-09-26): accommodation requests to people@;
  delete applicant data 12 months after close. Posting legal text: OPEN.
Jurisdiction flags (for the people lead): UK: health questions before an
  offer are restricted; talent-pool retention needs notice. Confirm with counsel.
Stages: intake + JD (today) → rubric → interview plan → screen →
  independent scores → debrief → Maya decides → drafts for Maya to send.
Open approvals: JD, pay range, coordinator.
First deliverable: JD draft, for Maya's approval.
```
