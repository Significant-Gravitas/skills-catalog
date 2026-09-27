# Worked example: kickoff for a Billing Operations Lead

Fictional company and people, for shape only. Shows every step of the
procedure, including tool calls and script output.

## The ask

> Maya (Head of Finance Ops): "We need to hire someone to own billing. Engineers
> keep getting pulled into failed payments and month-end slips. Can you get us
> started?"

## Step 1: look before asking

- `memory_search(query="hiring decision rights policies")` returns one fact:
  "Accommodation requests go to people@acme.example (stated by Maya, 2026-08-02)".
  Shown to Maya as "from memory, confirm".
- `ls ~/workspace/hiring/` shows only `support-lead/`. No folder for this role.
- Maya mentions no old JD; Drive is not searched.

## Step 2: one question card

`ask_question` with 9 of the 10 template questions (the accommodation question
is pre-filled from memory and shown for confirmation instead). The turn ends.

Answers next turn (summarised):

| Question | Answer |
| --- | --- |
| Role and six-month outcome | Billing Operations Lead; month-end close runs without engineering help; failed-payment follow-up has one owner |
| Hiring manager / final decision | Maya Chen, both |
| Approvers | Headcount and offers: Luis Ortega (Finance). JD and rubric: Maya |
| Interviewers / coordinator | Maya, Priya (Support lead), Tom (Engineering); coordinator: Don't know yet |
| Start and pattern | January 2027; Remote |
| Where posted and hired | UK only |
| Level and pay | Level L4 approved by Luis; pay: Not yet approved |
| Policies | Delete applicant data 12 months after close (Maya); posting legal text: Ask our people lead; background checks: none |
| AI use | Candidates may use AI to polish written applications, not in live interviews; we use no AI screening tool |
| Existing material | Nothing yet |

## Step 3: role folder

```
$ bash ~/skills/recruiting-getting-started/scripts/init_role.sh billing-ops-lead
created: /home/user/workspace/hiring/billing-ops-lead/hiring-plan.md
roles already set up under /home/user/workspace/hiring:
billing-ops-lead
support-lead
```

## Step 5: jurisdiction flags

```
$ python3 ~/skills/recruiting-getting-started/scripts/policy_flags.py --locations "Remote (UK)" --ai-screening no --background-check no --talent-pool unknown --video-interviews no --federal-contractor no
Regions matched: UK
- [UK] UK: no health or disability questions before an offer, except in narrow cases (Equality Act 2010 s.60). May apply; confirm with counsel. Sources: [58]. Checked 2026-09-27.
- [UK] If unsuccessful candidates are kept in a talent pool: UK: keep recruitment records no longer than needed and tell candidates before keeping them in a talent pool (ICO guidance). May apply; confirm with counsel. Sources: [100]. Checked 2026-09-27.
- NOTE 'Remote (UK)': remote roles follow where candidates live and work; name the countries or states you will hire in.
```

## Step 4 and 6: the filled plan, checked

```markdown
# Hiring plan: Billing Operations Lead
role_slug: billing-ops-lead
plan_version: 1
saved_on: 2026-09-26

## Role
- Title: Billing Operations Lead
- Outcome (what is different six months after the start): month-end close runs without engineering help; failed-payment follow-up has one owner
- Work the person must deliver: failed-payment queue, month-end billing close with finance, billing runbook
- Reason for the hire: billing issues handled ad hoc by engineers and support; close slips each quarter

## Owners and decision rights
- Hiring manager: Maya Chen
- Final decision-maker: Maya Chen
- Headcount approver: Luis Ortega
- JD approver: Maya Chen
- Rubric approver: Maya Chen
- Candidate-message approver: Maya Chen
- Default sender: Maya Chen
- Offer approver: Luis Ortega
- Coordinator: OPEN
- Interviewers: Maya Chen, Priya Shah (Support lead), Tom Reid (Engineering)

## Terms
- Start window: by January 2027
- Location and work terms: remote, UK hours, no travel
- Hiring jurisdictions: UK
- Level: L4 (APPROVED by Luis Ortega, 2026-09-26)
- Pay range: OPEN

## Policies
| Policy | Text as stated | Stated by | Date |
| --- | --- | --- | --- |
| Accommodation route | requests to people@acme.example | Maya Chen | 2026-08-02 (memory, confirmed 2026-09-26) |
| Data retention and talent pool | delete applicant data 12 months after close; talent pool not decided | Maya Chen | 2026-09-26 |
| Required posting text | OPEN | | |
| Candidates' AI use | AI may polish written applications; no AI in live interviews | Maya Chen | 2026-09-26 |
| Background checks | none planned | Maya Chen | 2026-09-26 |
| AI tools used in screening or interviews | none | Maya Chen | 2026-09-26 |
| US federal contractor | no | Maya Chen | 2026-09-26 |

## Existing materials
- Job description: none
- Scorecard or rubric: none
- Applicant tracking system: none (applications by email)

## Stages
1. Role intake and job description: in progress (2026-09-26)
2. Rubric: not started
3. Interview plan and scorecard: not started
4. Screening: not started
5. Independent scores: not started
6. Debrief: not started
7. Human decision: not started
8. Candidate messages (drafts only): not started

## Jurisdiction flags (for the people lead; not legal advice)
- UK: no health or disability questions before an offer, except in narrow cases (s.60) [58]. May apply; confirm with counsel.
- If a talent pool is kept: records no longer than needed, and notice before keeping candidates in a pool [100]. May apply; confirm with counsel.

## Open approvals
- JD draft: Maya Chen
- Pay range: Luis Ortega

## Open questions
- Coordinator: Maya to name, or Maya coordinates herself
- Required posting text: people lead
- Talent pool yes or no, and the notice wording: Maya with the people lead
- UK flags above: people lead to confirm

## Change log
- 2026-09-26: plan created (recruiting-getting-started)
```

```
$ python3 ~/skills/recruiting-getting-started/scripts/plan_check.py ~/workspace/hiring/billing-ops-lead/hiring-plan.md
OPEN  3 item(s): Coordinator; Pay range; policy: Required posting text
OK
```

## Steps 7 to 10

- Delivered with `write_workspace_file(filename="hiring-plan-billing-ops-lead.md", source_path="/home/user/workspace/hiring/billing-ops-lead/hiring-plan.md")`, linked as `workspace://<file_id>#text/markdown`.
- Memory: three company facts stored (Maya is the default decision-maker for Finance Ops roles; 12-month retention; candidate AI-use policy). Nothing about any candidate.
- `TodoWrite`: eight stages, stage 1 in progress.
- `run_capability(id="skill:role-intake-and-job-description", input={})`, then the JD draft is returned in the same session (see that skill's example).

## Reply to Maya (shape)

> Plan saved: [hiring-plan-billing-ops-lead.md]. Three things are still open:
> coordinator (you), pay range (Luis) and posting legal text (people lead).
> Two UK points for the people lead are in the plan; I have not treated them
> as legal advice. Your JD draft is below, marked for your approval. Nothing
> has been posted or sent.
