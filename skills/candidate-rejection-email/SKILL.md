---
name: "candidate-rejection-email"
description: "Draft a clear, kind rejection email from an approved human decision without inventing feedback or sending it. Use after the named decision-maker has confirmed the decision and the stage. Handles single drafts, call talking points for late-stage candidates, and batches of declines from a sheet (each row blocked until its decision is confirmed), lints every draft for comparative claims, AI or scoring reasons, keep-on-file promises and protected-trait language, and stops with no draft when a background check or other consumer report is part of the reason (FCRA pre-adverse action comes first)."
triggers: ["draft a rejection email", "write the decline email to this candidate", "tell the candidate we're not moving forward", "rejection note after the final interview", "decline emails for these applicants", "batch rejection emails after the screen", "talking points for a rejection call", "decline after a background check"]
version: "2"
---

# Candidate rejection email

Turns a confirmed human decision into an unsent, kind and specific decline
draft. Harper does not decide who is rejected, does not write the reason, and
never sends.

**Use when:** the named decision-maker has confirmed a rejection and the stage,
for one candidate or a batch.
**Do not use for:** deciding or recommending the outcome (people decide;
candidate-interview-debrief records it), FCRA notices (the vendor's or
counsel's forms), or offers (candidate-offer-draft).

## Inputs and where they come from

| Input | Source |
|---|---|
| Decision, decision-maker, date, stage | The decision record (`~/workspace/hiring/<role-slug>/debriefs/<candidate-id>/decision-record.md`) or the owner in chat. Missing: `needs human confirmation`, and no draft. |
| Whether a background or other consumer report played any part | The owner. Ask every time it is not recorded; `unknown` blocks the draft. |
| Chosen name, role, company, approved sender and title | Hiring plan (`~/workspace/hiring/<role-slug>/hiring-plan.md`, or a legacy `hiring-plan-<role>.md` found with `run_capability(id="tool:list_workspace_files", input={"include_all_sessions": true})`), the application, or the owner. |
| Whether the company permits feedback, and any feedback approved verbatim | The decision-maker, word for word. Never derived from scorecards or notes. |
| Retention wording, and the expenses or work-sample contact and date | The owner's recorded policy. Otherwise left out. If memory is on, `memory_search(query="<company> hiring policy: candidate retention / rejection feedback")` may find it; use a hit only if it records who stated it and when, and show it to the owner as "stated by <name>, <date>" to confirm before use. |
| A batch | `templates/decline-batch.csv`, filled by the owner or from the decision records, saved to `~/workspace/hiring/<role-slug>/drafts/`. |

Collect missing items in one `ask_question` call, with options (yes / no /
not sure) for the consumer-report question.

## Tools and pre-flight

1. `bash_exec`: `mkdir -p ~/workspace/hiring/<role-slug>/drafts && test -w ~/workspace/hiring/<role-slug>/drafts && echo STATE_OK`.
   No `STATE_OK`: deliver with `write_workspace_file` only, and say that the drafts will not persist.
2. `bash_exec`: `python3 --version` (standard library only). Without Python, apply
   `references/decline-content-rules.md` by hand and label drafts "hand-checked, not lint-verified".

## Procedure

1. **Confirm the decision.** Get a named decision-maker, the date, the
   decision and the stage. If any is missing, return `needs human
   confirmation` for that candidate and draft nothing.
2. **Consumer-report check.** Ask whether a background check or other consumer
   report played any part, in whole or in part.
   - **Yes:** stop. Draft nothing, and give the one-paragraph routing from
     `references/fcra-adverse-action-routing.md` [48][76]. The only way
     forward: after the owner confirms in writing that the FCRA steps are
     complete and still wants a separate courtesy note, follow that
     reference's section "After the owner confirms the FCRA steps are
     complete" (a single draft only, never via the batch; the batch keeps
     blocking every `yes` row).
   - **Unknown:** ask, and hold that candidate.
   - **No:** continue.
3. **Gather content.** Use feedback only if the company permits it and the
   decision-maker approved it word for word. Take retention wording only from
   the recorded policy; without it, do not mention keeping details [100]. Add
   the expenses or work-sample line only for late stages, with the approved
   contact and date.
4. **Draft.**
   - One candidate: use the stage block in `templates/decline-by-stage.md`.
     For late-stage candidates, also offer the call talking points (owner's choice).
   - Several: fill `templates/decline-batch.csv` and run
     `cd ~/skills/candidate-rejection-email && python3 scripts/merge_declines.py ~/workspace/hiring/<role-slug>/drafts/decline-batch.csv --out ~/workspace/hiring/<role-slug>/drafts/<YYYY-MM-DD>`.
     Blocked rows are listed first, each with its reason.
5. **Lint every single draft:**
   `cd ~/skills/candidate-rejection-email && python3 scripts/lint_decline.py <draft.txt> --allow "<company>" --allow "<role title>"`
   (the merge lints batch rows itself and passes each row's name, role,
   company and sender the same way). `--allow` only turns a PROTECTED or
   LEGAL hit inside that exact owner-supplied name ("Brightside Family
   Dental", "Medical Billing Specialist") into a `NAME` warning; confirm the
   name is real, not a reason. Fix every error. If the owner
   asked for text that trips the lint (a comparison, an AI reason, "keep on
   file"), leave it out and say why. A comparison is included only on the
   decision-maker's written approval of that exact statement (`comparative_approved: yes`).
6. **Return and save.** Return the draft or drafts, each with its approval
   footer, plus the blocked list. Save to `~/workspace/hiring/<role-slug>/drafts/`
   and deliver with `write_workspace_file(source_path=...)` as `workspace://` links.
7. **Optional, only when the owner asks:** place the drafts in the sender's
   own mailbox as unsent drafts, following `references/decline-content-rules.md`
   section 8 (a draft-only tool, the sender's account confirmed,
   `validate_only` first, and a count of only the calls that succeeded).

## Output contract

- Per candidate: subject, body, and the approval footer
  (`Decision confirmed by: <name>, <date>. Feedback approved verbatim: yes/none included. Consumer report involved: no (owner). Sender: <name>. Status: DRAFT, not sent.`).
- For late stages, optional call talking points.
- A blocked list: the candidate, the reason (`needs human confirmation`, FCRA
  stop, ask about consumer report, a duplicate row, a lint error) and the one question that
  unblocks it.
- Links to `drafts.md` / `drafts.csv`, and the statement that nothing was sent.

## Guardrails

- Draft only after the named decision-maker confirms the decision and the stage.
- The decision appears in the first two sentences. The thanks are specific.
  The subject stays plain.
- Never derive a reason from scorecards, and never fill a blank with a generic
  claim. Feedback is used only verbatim as approved, stated in job-related
  terms, and no broader than the evidence supports.
- Never say another candidate was better unless the decision-maker approved
  that exact statement.
- Never mention AI, automated scoring or ranking, or describe how the
  decision was made beyond the approved text [101].
- Never say "we'll keep your details on file" unless the recorded retention
  policy allows it. Never promise future contact.
- A consumer report in any part of the decision means no draft; route to
  FCRA [48][76].
- Never expose panel notes, protected information, legal conclusions or
  unapproved feedback.
- Never send, schedule, or change the candidate's stage in any system. A
  mailbox draft is created only on the owner's request, with a draft-only
  tool.

## Quality self-check

- [ ] Every draft has a named decision-maker and date, and the consumer-report answer is "no".
- [ ] `lint_decline.py` (or the merge) is clean, or the draft is labelled hand-checked.
- [ ] Feedback text matches the approved text character for character.
- [ ] Blocked rows are shown first, each with the question that unblocks it.
- [ ] No sentence was written that the owner asked for but a rule forbids; each omission is explained.
- [ ] Any timing default (5 business days) is labelled as a default when mentioned.
- [ ] Nothing was sent. Any mailbox-draft count covers only calls that succeeded.

## Files

- `scripts/merge_declines.py` (batch), `scripts/lint_decline.py` (content lint)
- `templates/decline-by-stage.md` (application, screen, loop, call talking points), `templates/decline-batch.csv`
- `references/fcra-adverse-action-routing.md`, `references/decline-content-rules.md`, `references/sources.md`
- `examples/declines-by-stage.md` (each stage, the FCRA stop, and a partly refused request); `examples/batch-after-screen/` (a six-row batch with four blocked rows)

## Related skills

- candidate-interview-debrief: the decision record, with the decision-maker, rationale and FCRA line.
- interview-plan-and-scorecard: the candidate note that sets the promised decision timing.
- candidate-offer-draft: for the candidate who is hired.
