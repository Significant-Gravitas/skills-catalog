# Interview kit: Senior Backend Engineer, Billing

role_slug: senior-backend-engineer
scale: 1-5
loop_length_note: 30-minute screen, then three slots on one day
accommodation_contact: Rita Gomes, people@northwind.example
candidate_ai_policy: Take-home: AI tools allowed, say which. Live interviews: no AI unless the interviewer offers it.
status: approved by Lena Ortiz 2026-10-14

## Must-haves

- M1: Has run a production service in Go or a similar typed language for at least a year, including on-call
- M2: Designs changes to a live data store without downtime, with a rollback path
- M3: Debugs payment or billing flows end to end
- M4: Explains a technical trade-off to a non-engineer so they can decide

## Slot 1: Screen

length: 30
interviewer: Sam Lee
owns: M1
clock: 5 context, 20 main, 5 candidate questions

### Questions

1. "Tell me about the production service you've owned most recently."
   - Strong answer: names the service, its load or users, and the parts they wrote or ran themselves
   - Probe: Which part was yours?
2. "Walk me through the last incident you were paged for."
   - Strong answer: the alert, what they checked first, the fix, what changed afterwards
   - Probe: What would you change?
3. "How did you know the service was healthy on a normal day?"
   - Strong answer: specific metrics or alerts they relied on and why
   - Probe: What number did you watch?
4. "Tell me about a bug that reached production through code you reviewed."
   - Strong answer: owns the miss, names the review gap and the change they made
   - Probe: What did you change in how you review?

### Anchors M1

- 1: cannot describe a service they ran in production
- 2: worked on a service but never carried its on-call or health
- 3: ran one service in production with on-call, and can describe an incident end to end
- 4: also improved the service's reliability measurably (alerts, runbooks, SLOs)
- 5: did that across several services and taught others to run them
- not assessed: the slot did not cover it

## Slot 2: Billing debugging

length: 60
interviewer: Dev Rao
owns: M3
clock: 5 context, 40 main problem, 15 candidate questions

### Questions

1. "Walk me through a billing or payment bug you traced to its root."
   - Strong answer: names the symptom, the data they pulled, the wrong assumption
   - Probe: Which part was yours?
2. "A customer was charged twice. Where do you look first, and why?"
   - Strong answer: idempotency keys, webhook retries, the reconciliation job
   - Probe: What would you log so you'd know next time?
3. "How did you confirm the fix worked in production?"
   - Strong answer: a metric or reconciliation that moved
   - Probe: What number moved?
4. "Tell me about a time finance and engineering disagreed about what the numbers said."
   - Strong answer: how they found the source of truth and settled it with evidence
   - Probe: Who disagreed, and what did you do?

### Anchors M3

- 1: cannot describe a billing failure they worked on
- 2: fixed symptoms, could not say the cause
- 3: traced one real bug to root cause and verified the fix
- 4: also changed the system so the class of bug stopped
- 5: did that across teams and can show the result
- not assessed: the slot did not cover it

## Slot 3: Live data changes

length: 45
interviewer: Ana Silva
owns: M2
clock: 5 context, 30 main problem, 10 candidate questions

### Questions

1. "Tell me about the riskiest schema or data migration you've shipped on a live system."
   - Strong answer: the plan, the steps, how they kept it online
   - Probe: Which part was yours?
2. "If step 3 of that plan had failed halfway, how would you have rolled back?"
   - Strong answer: a concrete rollback with the data state at each step
   - Probe: What would the customer have seen?
3. "We need to split a 2TB invoices table by region with no downtime. Sketch your first plan."
   - Strong answer: dual writes or shadow copy, backfill, verification, cut-over, rollback
   - Probe: What would you verify before cut-over?
4. "What did you measure to know the migration was safe to finish?"
   - Strong answer: named checks (row counts, checksums, error rates) and thresholds
   - Probe: What number moved?

### Anchors M2

- 1: has not changed a live data store
- 2: ran migrations with downtime or without a rollback path
- 3: shipped one zero-downtime change with a tested rollback
- 4: designed the approach for others and verified it with checks they defined
- 5: built tooling or practice that made such changes routine for the team
- not assessed: the slot did not cover it

## Slot 4: Hiring manager close

length: 45
interviewer: Lena Ortiz
owns: M4
clock: 5 context, 25 main, 15 candidate questions

### Questions

1. "Tell me about a technical trade-off you had to explain to someone outside engineering."
   - Strong answer: the options, what they said, the decision the other person made
   - Probe: What did they decide, and why?
2. "Explain to me, as our finance lead, why we might delay a billing release by a week."
   - Strong answer: plain language, the risk in money or customers, a clear choice
   - Probe: What would you need from me to decide?
3. "When did a non-engineer change your mind about a technical plan?"
   - Strong answer: a real instance and what they changed
   - Probe: What would you change?
4. "What's the accomplishment you're proudest of that's most like owning our billing service?"
   - Strong answer: specific task, result with a number, their actions, time frame
   - Probe: What number moved?

### Anchors M4

- 1: cannot give an example of explaining a trade-off outside engineering
- 2: explained, but the listener could not decide from it
- 3: explained one real trade-off so a non-engineer made the call
- 4: does this routinely and adapts to the listener
- 5: shaped how the company makes such decisions
- not assessed: the slot did not cover it

## Dropped or rewritten questions

| Original | Why | Replacement |
| --- | --- | --- |
| "You're comfortable with Stripe, right?" | Leading and tool-name recognition (drop rules) | Slot 2, question 2 |
| "Where are you originally from? We have a lot of Irish folks." | National origin [34] | Dropped |
| "Any health stuff we should know about for on-call?" | Health question before an offer [35][46] | Screen: "The role is on call one week in five, including nights; can you do that, with or without reasonable accommodation?" (owner chose to state this in the screen's context segment) |
| "Where do you see yourself in five years?" | Fortune-teller hypothetical [23] | Slot 4, question 4 (Most Significant Accomplishment) |

## Open items

- none
