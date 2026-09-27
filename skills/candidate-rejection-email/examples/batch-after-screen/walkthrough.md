# Worked example: a batch of six declines (fictional)

Input: `decline-batch.csv` beside this file. Maya Chen is the decision-maker
for the Billing Operations Lead role at Acme.

## Request

> Maya: "Decline emails for these applicants please. Same wording for
> everyone. Chris asked why, so tell him we went with people who had more
> multi-entity experience."

## Step 1. Gate check

Harper reads `~/workspace/hiring/billing-ops-lead/hiring-plan.md`. The
sender is Maya, and no retention policy is recorded, so every
`retention_line` stays empty. Harper also checks each row's decision:

- A-101, A-102, A-105: decision by Maya on 2026-10-05, no consumer report.
- A-103: no decision-maker or date recorded, so this row needs human confirmation.
- A-104: consumer report `unknown`, so Harper asks.
- B-003: consumer report `yes`, so this is an FCRA stop.

## Step 2. Merge

```
cd ~/skills/candidate-rejection-email && \
python3 scripts/merge_declines.py ~/workspace/hiring/billing-ops-lead/drafts/decline-batch.csv \
  --out ~/workspace/hiring/billing-ops-lead/drafts/2026-10-05
```

```
2 draft(s) written, 4 blocked
BLOCKED A-103: needs human confirmation: decision_maker and decision_date are required
BLOCKED A-104: ask the owner: did a background or consumer report play any part? ...
BLOCKED A-105: lint COMPARATIVE: 'went with candidates'; lint COMPARATIVE: 'more experience'
BLOCKED B-003: FCRA stop: a consumer report is involved; draft nothing ...
```

## Step 3. What Harper tells Maya (blocked rows first)

> 2 drafts are ready (A-101 application stage, A-102 after the screen). 4 are
> held:
> - **A-103 Lee:** no decision recorded. Who decided, and when?
> - **A-104 Ravi:** did a background or consumer report play any part? Yes or no.
> - **A-105 Chris:** the feedback compares him with other candidates. I can
>   include it only if you approve that exact comparison in writing
>   (`comparative_approved: yes`). A job-related alternative, if you want
>   one: "The role needs hands-on multi-entity close experience, which we
>   didn't see in your application." That needs your word-for-word approval
>   too.
> - **B-003 Priya:** the background report was part of the decision, so the
>   FCRA pre-adverse action process comes first
>   (`references/fcra-adverse-action-routing.md`). No draft from me until you
>   confirm those steps are done.
>
> Nothing has been sent.

## Step 4. Deliver

`drafts.md` and `drafts.csv` are delivered with `write_workspace_file` and
linked. If Maya asks to put them in her Gmail drafts, Harper follows
`references/decline-content-rules.md` section 8: a draft-only tool, her own
account, `validate_only` first, and a report of only the calls that
succeeded.

## A second batch: names that contain lint words

`decline-batch-names.csv` beside this file is a batch for a dental practice:
the role is "Medical Billing Specialist" and the company is "Brightside
Family Dental". Those words would trip the PROTECTED rule if they were a
reason, but here they are the owner's own role and company names. The merge
passes each row's chosen_name, role, company, sender and sender_title to the
lint as `--allow` names, so both rows are drafted, not blocked:

```
2 draft(s) written, 0 blocked
```

Each draft carries a `NAME` warning ("Medical (in 'Medical Billing
Specialist')"; "Family (in 'Brightside Family Dental')"). Harper reads it,
confirms that the name is the real role or company and not a reason, and
says so to the owner. The same word anywhere else in the draft, for example
"family commitments" in the feedback, is still an error.
