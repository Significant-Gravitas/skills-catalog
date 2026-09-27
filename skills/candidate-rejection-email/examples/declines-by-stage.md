# Examples: declines by stage, and the FCRA stop (fictional)

Everything is fictional: Acme, Maya Chen (hiring manager and decision-maker),
Jo Patel (people team).

---

## 1. Application stage: short, no feedback

> **Subject:** Your application for Billing Operations Lead
>
> Hi Jordan,
>
> Thank you for applying for the Billing Operations Lead role at Acme. We have decided not to move forward with your application.
>
> Thank you again for your interest in Acme, and best wishes with your search.
>
> Maya Chen
> Head of Finance Operations
>
> ---
> Decision confirmed by: Maya Chen, 2026-10-05. Feedback approved verbatim: none included. Consumer report involved: no (owner). Sender: Maya Chen. Status: DRAFT, not sent.

---

## 2. After the loop: email with approved feedback and expenses

Maya approved one feedback sentence word for word in the decision record,
and the expenses line from the plan.

> **Subject:** Your application for Billing Operations Lead
>
> Hi Jordan,
>
> Thank you for interviewing for the Billing Operations Lead role and for the time you put into the SQL work sample. The team has decided not to move forward with your application.
>
> Maya asked me to share one point: in the work sample, the query did not account for duplicate invoices, which is a core part of this role's month-end work.
>
> If you submitted travel expenses, please send receipts to people@acme.example by 10 October and we will reimburse them.
>
> Thank you again for the time and care you put into the process, and best wishes.
>
> Maya Chen
> Head of Finance Operations
>
> ---
> Decision confirmed by: Maya Chen, 2026-09-25. Feedback approved verbatim: yes. Consumer report involved: no (owner). Sender: Maya Chen. Status: DRAFT, not sent.

`lint_decline.py` on this draft: clean.

## 3. After the loop: call talking points (for Maya, not the candidate)

1. "Hi Jordan, it's Maya from Acme. I'm calling about the Billing Operations Lead role. I'm sorry to say we've decided not to move forward."
2. "Thank you for the three conversations and for the SQL work sample. I know that took real time."
3. Approved feedback, read as approved: "One point I can share: in the work sample, the query didn't account for duplicate invoices, which is a core part of month-end here."
4. If Jordan asks how others did, or for the scores: "I'm not able to go into the panel's discussion, but I wanted you to hear it from me."
5. "If you had travel costs, send receipts to people@acme.example by 10 October."
6. "Thank you again. I'll follow up with a short email today."

## 4. The FCRA stop: no draft (hard case)

> Maya: "Draft the decline for Priya (B-003). The background check flagged a
> county record, but just say we went another way."

Harper's whole reply:

> I haven't drafted a rejection for Priya. The background report played a
> part in the decision, so the FCRA pre-adverse action process comes first: a
> notice with a copy of the report and the summary of rights, then a waiting
> period, then the adverse action notice. Your screening vendor or Jo Patel
> usually runs this. Tell me when those steps are done, and whether a
> separate note from the hiring team is still wanted. I also can't write "we
> went another way" as the reason, because it isn't the recorded reason.

Nothing is drafted, and nothing about the record is summarised. The decision
record gets `consumer_report_involved: yes (Maya, 2026-10-05)`.

## 5. A request that must be refused in part (hard case)

> Maya: "Tell the screen rejects the AI screener scored them below 60%, and
> that we'll keep their CVs for future roles."

Harper drafts the declines without either sentence and explains: the method
of the decision is not described beyond approved text, and AI scores are
never given as the reason [101]. "Keep on file" is included only if the
recorded retention policy allows it; the hiring plan has no policy, so it is
`[OWNER TO CONFIRM]` with Jo Patel [100]. Harper asks Maya whether the AI
screener was covered by the notices her jurisdiction may require. For
example, NYC's AEDT rules call for notice and a bias audit, so that
question goes to the people lead or counsel [69].
