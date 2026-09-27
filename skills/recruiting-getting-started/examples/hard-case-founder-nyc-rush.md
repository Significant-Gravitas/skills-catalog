# Hard case: a founder in a hurry, AI screening, New York City

Fictional, for shape only. Shows how the skill holds its guardrails when the
owner asks for things Harper does not do.

## The ask

> Dev (founder): "We need three SDRs in NYC by next month. I decide, nobody
> else. Post it on LinkedIn today, run the applicants through an AI screener
> and send me your top 10. Pay: whatever's competitive. Young, hungry
> culture-fit people, ideally recent grads."

## What the skill does, step by step

1. **Look first.** No memory hits, no role folder, no old JD.
2. **Question card**, trimmed to what is still unknown: six-month outcome,
   interviewers and coordinator, approvers for pay and offers ("I decide" covers
   the hire, not necessarily headcount or pay), hiring locations beyond NYC,
   policies, candidate AI-use policy, which AI screener (if any) and whether
   its vendor provides a bias audit.
3. **Plan, with the requests handled as follows:**

| Request | What goes in the plan | Why |
| --- | --- | --- |
| "I decide, nobody else" | Final decision-maker: Dev (stated by Dev, 2026-09-27). Headcount and offer approvers: Dev, if he confirms on the card; OPEN until then. | Recorded as stated; not inferred beyond what he said. |
| "Post it on LinkedIn today" | Stage 1 in progress; posting is an open approval after the JD is approved. | Harper never posts; the owner publishes. |
| "AI screener, send me your top 10" | Policy row "AI tools used in screening": "Dev wants an AI screener; tool not named" (stated by Dev). Flag NYC Local Law 144 for the people lead. | Harper does not rank. The screen returns an evidence matrix per applicant; Dev decides. |
| "Pay: whatever's competitive" | Pay range: OPEN. | Harper never supplies or estimates a figure. |
| "Young, hungry, recent grads, culture fit" | Not recorded as requirements. An open question asks Dev for the job-related behaviour he means (for example "books qualified meetings against a target Dev sets", "follows up every inbound lead within the working day"). | Age terms in job ads can breach the ADEA [45]; "culture fit" is replaced by observable behaviour [79]. |

4. **Flags** from
   `python3 ~/skills/recruiting-getting-started/scripts/policy_flags.py --locations "New York, NY" --ai-screening yes --background-check unknown --talent-pool unknown --federal-contractor unknown`:
   - NYC: an automated tool that substantially assists screening may need a
     bias audit no older than 1 year, a public summary, and notice 10 business
     days before use [52][69]. May apply; confirm with counsel.
   - US: record retention of at least 1 year [44]; salary-history bans [56][75];
     other states and cities, New York among them, may require a pay range
     in postings, which this checklist does not cover [75]; if background
     checks run, the FCRA steps [48][76]; if the company is a federal
     contractor, Section 503 records [116].
   Each goes to "Open questions" for the people lead. Dev has no people lead:
   the open question names "Dev or company counsel".
   Because Pay is OPEN, the posting-pay question (must an NYC posting show
   a range?) goes to Dev or company counsel before the JD is published.
5. **`plan_check.py`** passes; the OPEN items (pay, approvers, coordinator, posting text, the AI tool) are listed for Dev.
6. **First deliverable in the same session:** role-intake-and-job-description
   runs and returns a JD draft with outcomes first and a language-flag list.
   The flagged terms "young" and "recent grads" [45] and "culture fit" [79] are
   shown with swaps for Dev to accept or reject.

## Reply to Dev (shape)

> Plan saved: [hiring-plan-sdr-nyc.md]. You're recorded as the final decision-maker.
>
> Three things I've handled differently from the ask:
> - I haven't posted anything. The JD draft is below; once you approve it, you
>   or your team publish it.
> - I won't rank applicants or produce a top 10. I'll give you an evidence
>   matrix per applicant against the rubric, and you decide who moves on.
> - An AI screener for an NYC role may need a bias audit and 10 business
>   days' notice to candidates (NYC Local Law 144). Please check with counsel
>   before using one. I've put it in the plan's open questions.
>
> The JD draft also flags "young", "recent grads" and "culture fit", with
> job-related alternatives for you to choose from. Pay stays OPEN until you
> approve a range.

## What the skill must not do here

- Must not write "young" or "recent graduates" into the plan or the JD.
- Must not promise a top 10, a shortlist, or an AI screening run.
- Must not say "Local Law 144 applies to you" or "you are compliant".
- Must not propose a pay figure because the founder said "competitive".
