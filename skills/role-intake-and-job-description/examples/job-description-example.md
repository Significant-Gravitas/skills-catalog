# Example intake brief and job description

Fictional role, for shape only. The hiring plan came from
recruiting-getting-started (see that skill's kickoff example).

## Intake brief — Billing Operations Lead

- Reason: billing issues are handled ad hoc by engineers and support; month-end close slips each quarter.
- Outcomes (manager's checkpoints): 30 days — owns the failed-payment queue; 60 days — runs month-end close with finance; 90 days — written billing runbook in use.
- Decisions owned: refund exceptions up to the approved limit; billing-policy wording (with finance sign-off).
- Manager: Maya Chen. Team: Finance Operations (4). Remote, UK hours, no travel.
- Level: L4 (APPROVED — Luis Ortega). Pay range: `[OWNER TO CONFIRM]`. Legal text: `[OWNER TO CONFIRM]`.

| Requirement | Group | Reason |
|---|---|---|
| Has run a recurring billing or finance process end to end | must show before hire | month-end close fails without it |
| Can write reporting queries in SQL | can be tested in the process | needed for reconciliation from month 2 |
| Knows our billing tool | can be learned after hire | vendor training exists |
| Degree in finance | removed | no work need given |
| "Rockstar self-starter" | removed | personality label, not evidence |

## requirements.csv (saved to `~/workspace/hiring/billing-ops-lead/`)

```csv
req_id,requirement,group,what_fails_without_it,objective,non_comparative,job_relevant,evidence_method,change_reason,approved_by,approved_on,rubric_criterion_id
R1,has run a recurring billing or finance process end to end,must-show,month-end close slips without an owner who has done it,yes,yes,yes,resume and interview,,,,
R2,can write reporting queries in SQL,test-in-process,reconciliation from month 2 needs queries,yes,yes,yes,work sample,,,,
R3,knows our billing tool,learn-after-hire,day-to-day billing work,yes,yes,yes,,,,,
R4,degree in finance,removed,,,,,,no work need given by Maya; screening on it would contradict the posting,,,
R5,rockstar self-starter,removed,,,,,,personality label; no observable behaviour behind it,,,
```

```
$ python3 ~/skills/role-intake-and-job-description/scripts/req_check.py ~/workspace/hiring/billing-ops-lead/requirements.csv --jd ~/workspace/hiring/billing-ops-lead/jd-v1.md
Counts: must-show 1, test-in-process 1, learn-after-hire 1, removed 2
OK
```

## Job description draft

**Billing Operations Lead** (remote, UK hours)

You will make our billing run without engineering help: failed payments followed up, month-end closed on time, and a billing runbook the whole team uses.

What you will do:
- Own the failed-payment queue and its follow-up.
- Run month-end billing close with the finance team.
- Write and keep the billing runbook and refund policy.
- Decide refund exceptions within the approved limit.
- Work with support and product on billing changes.
- Report billing health to the finance lead each month.

What we need to see:
- Has run a recurring billing or finance process end to end.

Useful: can write reporting queries in SQL (we will test this in the process, and can support you to build it). Our billing tool: we will train you.
Reporting to: Maya Chen, Finance Operations Manager.
Process: 30-minute call, work sample, two interviews. Tell us about any adjustments you need at any stage: people@acme.example.
Using AI tools: you may use AI to polish your written application; please do not use AI in live interviews.
Pay: `[OWNER TO CONFIRM]`. Legal text: `[OWNER TO CONFIRM]`.

## Language flags

```
$ python3 ~/skills/role-intake-and-job-description/scripts/jd_lint.py ~/workspace/hiring/billing-ops-lead/jd-v1.md
L1:22 "Lead" [masculine-coded/suggest] -> keep in a job title or when the role leads people; otherwise 'guide' or 'own' ([31])
L11:40 "lead" [masculine-coded/suggest] -> keep in a job title or when the role leads people; otherwise 'guide' or 'own' ([31])
Summary: feminine-coded 2, masculine-coded 2
Gender-coded balance: masculine 2, feminine 2 (balanced) [31]
```

Shown to Maya as: no flags that need a decision. "Lead" appears in the job
title and in "finance lead" (a person's title); both are known benign cases.

## Posting fields

Hiring jurisdiction: UK. `references/posting-law-fields.md` lists no UK pay
field; nothing added. The UK note (no health questions before an offer) is
carried to the interview plan.

## Approval checklist

- [ ] Outcomes and duties — Maya Chen
- [ ] Pay range — Luis Ortega
- [ ] Legal text — people lead
- [ ] Removed requirements (R4, R5) — Maya Chen
- [ ] Every must-show requirement maps to a rubric criterion (hiring-rubric-design fills `rubric_criterion_id`) — Maya Chen
