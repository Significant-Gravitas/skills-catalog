---
name: "role-intake-and-job-description"
description: "Turn a hiring need into an intake brief and a plain job description based on outcomes, job-related evidence, and approved terms. Use before publishing or revising a role, and before any rubric or screening. Also rewrites an existing posting (pasted, uploaded, or a careers-page link) with a line-by-line change log and a language check for age, proxy and gender-coded wording."
triggers: ["write a job description", "role intake for a new hire", "turn this hiring need into a JD", "rewrite this job posting", "which requirements does this role need", "draft the posting for this role", "check this job ad for biased wording"]
version: "2"
---

# Role intake and job description

Use this before publishing or revising a role. The approved requirements feed
hiring-rubric-design; nothing here is published or posted.

**Use when:** a role needs a JD; an old posting needs rewriting; the owner asks
which requirements the role really needs; a posting needs a wording check.
**Do not use for:** the first session on a role with no owners recorded (start
with recruiting-getting-started), the rubric (hiring-rubric-design), or legal
questions (the people lead or counsel).

## Inputs and where they come from

| Input | Where it comes from |
| --- | --- |
| Owners, terms, policies, hiring jurisdictions | `~/workspace/hiring/<role-slug>/hiring-plan.md`. If missing, look for an older `hiring-plan-<role>.md` (`references/hiring-state.md`); if none, record owners as `OPEN`. |
| The hiring need | The manager in chat, or `ask_question` for gaps. |
| An old posting | A paste; an upload (`read_workspace_file(file_id=..., save_to_path="/home/user/in/old-posting.<ext>")`); or a URL (`web_fetch(url, extract_text=true)`; if it returns under about 500 characters from a script-heavy job board, `run_capability(id="tool:browser_navigate", input={"url": ...})` and read the snapshot). `web_fetch` stops at 100 KB: say so if the page was cut. |
| Previous version | `requirements.csv` and `jd-v<N>.md` in the role folder. |

## Tools and pre-flight

1. `bash_exec`: `python3 --version || echo "python3 missing"`. Without Python,
   run the checks in steps 5 and 6 by hand from `references/` and label them
   "hand-checked, not script-verified".
2. `mkdir -p ~/workspace/hiring/<role-slug>`; if it is not writable, deliver every
   file with `write_workspace_file` and say state will not carry over.
3. For a rewrite: `python3 ~/skills/role-intake-and-job-description/scripts/extract_text.py /home/user/in/old-posting.<ext> > /home/user/old.md`
   (PDF needs `pip install --user pypdf`). Exit 2 means scanned or unreadable:
   ask for a paste.
4. Mirror `checklists/review-checks.md` in `TodoWrite`.

## Procedure

1. **Intake.** Get the reason for the hire, outcomes due in the first months
   (default checkpoints: 30, 60 and 90 days; use the manager's own if
   different), recurring work, decisions the role owns, manager, team,
   location and work terms, hours, travel, approved level, approved pay range,
   and required legal text. Ask only what the plan and the paste do not
   answer, in one `ask_question` call. Fill `templates/intake-brief.md`.
2. **Sort every requirement.** For each, ask what work would fail without it,
   then put it in one group (`references/requirement-tests.md`):
   - must show before hire;
   - can be tested in the process;
   - can be learned after hire;
   - removed: a preference with no clear link to the work, unless the hiring
     manager gives a job-related reason.
   Every must-show requirement must be objective, non-comparative and
   job-relevant. Write the sort to `~/workspace/hiring/<role-slug>/requirements.csv`
   from `templates/requirements.csv`; leave `rubric_criterion_id` blank.
3. **Check the sort.**
   `python3 ~/skills/role-intake-and-job-description/scripts/req_check.py ~/workspace/hiring/<role-slug>/requirements.csv`
   Fix every `ERROR`. Each `WARN` (degree, years, "native", location, "fit")
   needs a job-related reason in `what_fails_without_it`, or the row moves to
   `removed`.
4. **Draft** from `templates/job-description.md`: outcome first, then the
   main duties (default: five to eight), required evidence (must-show rows word
   for word), useful experience, reporting line, work terms, process (with the
   accommodation line and the candidate AI-use line from the plan), and
   approved pay or benefits. Use plain verbs. No inflated titles, personality
   labels, coded language, or a long tool list where a skill would do.
   Location is work terms, never a postcode or commute radius. Save as
   `~/workspace/hiring/<role-slug>/jd-v<N>.md`.
5. **Review checks.**
   - Language: `python3 ~/skills/role-intake-and-job-description/scripts/jd_lint.py ~/workspace/hiring/<role-slug>/jd-v<N>.md`.
     List every flag and check hit with its swap under "Language flags"
     (`references/inclusive-language-lint.md` lists benign cases). The owner
     accepts or rejects each; do not silently rewrite.
   - Consistency: `python3 ~/skills/role-intake-and-job-description/scripts/req_check.py ~/workspace/hiring/<role-slug>/requirements.csv --jd ~/workspace/hiring/<role-slug>/jd-v<N>.md`.
     Every must-show requirement is quoted in the JD; no removed one remains.
   - Posting fields: look up each hiring location in
     `references/posting-law-fields.md`. For each field listed, keep
     `[OWNER TO CONFIRM]` and add "may be required for <location>; confirm" to
     the approval checklist for the people lead. Never supply a figure.
   - Mark every fact APPROVED (with who approved it) or `[OWNER TO CONFIRM]`.
     Pay and legal text are never filled in without approval.
6. **Rewrite only: show the change.**
   `python3 ~/skills/role-intake-and-job-description/scripts/diff_postings.py /home/user/old.md ~/workspace/hiring/<role-slug>/jd-v<N>.md`
   and put the output under "What changed".
7. **Save and deliver.** Save `intake-brief.md`; build a review copy with
   `python3 ~/skills/role-intake-and-job-description/scripts/to_docx.py ~/workspace/hiring/<role-slug>/jd-v<N>.md /home/user/out/jd-<role-slug>-v<N>.docx`
   (open items highlighted); deliver the markdown and the DOCX with
   `write_workspace_file(source_path=...)` and link them. Update the plan's
   Stages and Open approvals lines.

## Output contract

1. Intake brief.
2. Job-description draft (`jd-v<N>.md` and a DOCX link).
3. Removed or changed requirements, each with its reason.
4. Language flags (script output or "hand-checked").
5. Posting-field lines for the people lead, if any location matched.
6. For a rewrite, "What changed" from `diff_postings.py`.
7. Approval checklist from `templates/approval-checklist.md`, including
   "every must-show requirement maps to a rubric criterion".

## Guardrails

- Do not publish, post, or send the JD anywhere. The owner publishes.
- Pay, benefits and legal text only as approved; otherwise `[OWNER TO CONFIRM]`.
  Never estimate a band. Never ask for or mention salary history [56][75].
- Flag requirements that may screen people out without a stated work need,
  but do not give employment-law advice. Route policy or legal questions to
  the company's people lead or counsel.
- No protected trait or proxy in any requirement: age terms, graduation year,
  "digital native", "native speaker", postcode or commute, photo, family
  status, health, "culture fit" [45][34][72][74][79].
- Physical requirements only if essential, with "with or without reasonable
  accommodation" [35][46].
- Lint hits are suggestions; the owner decides each one.

## Quality self-check

- [ ] Every fact is APPROVED (by whom) or `[OWNER TO CONFIRM]`.
- [ ] `req_check.py --jd` is clean; every removed requirement has a reason.
- [ ] Language flags listed with swaps; nothing silently rewritten.
- [ ] Posting-location lines added for the people lead where they apply.
- [ ] Outcomes lead the JD; duties use plain verbs.
- [ ] Nothing was posted or sent.

## Related skills

recruiting-getting-started (plan and owners), hiring-rubric-design (next:
turns must-show rows into scored criteria), resume-screening,
interview-plan-and-scorecard. Load with `run_capability(id="skill:<slug>", input={})`.

## Package files

- `scripts/jd_lint.py`, `req_check.py`, `extract_text.py`, `diff_postings.py`, `to_docx.py`
- `references/requirement-tests.md`, `inclusive-language-lint.md`,
  `lint-terms.csv` (lint data), `posting-law-fields.md`, `hiring-state.md`, `sources.md`
- `templates/intake-brief.md`, `job-description.md`, `requirements.csv`, `approval-checklist.md`
- `checklists/review-checks.md`
- `examples/job-description-example.md` (new JD, end to end),
  `examples/jd-rewrite-with-lint.md` (hard case: rewriting a legacy Denver posting)

See [examples/job-description-example.md](examples/job-description-example.md)
for a finished draft and [examples/jd-rewrite-with-lint.md](examples/jd-rewrite-with-lint.md)
for a rewrite.
