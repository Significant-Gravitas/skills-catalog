# Prep packet: Priya Nair · Senior Backend Engineer · interview 2 of 3 that day · kit slot 3

**When:** Thu 29 Oct 11:10–11:55 Europe/Dublin / Thu 29 Oct 11:10–11:55 Europe/Lisbon
**Interviewer:** Ana Silva · **You own:** M2: Designs changes to a live data store without downtime, with a rollback path
**Scorecard due:** Fri 30 Oct 11:55 Europe/Lisbon (24 h after the slot)

## Candidate summary (max 5 lines; direct quotes only)

- "Led the migration of our 4TB invoices table from a single Postgres instance to a partitioned cluster with zero downtime" — source: screens/priya-nair-resume.txt
- "using a shadow-copy tool I wrote (pg-shadow-copy)" — source: screens/priya-nair-resume.txt
- "Primary on-call for the payments ledger service (Go), one week in four." — source: screens/priya-nair-resume.txt
- "cut unmatched items from 2.1% to 0.3%" — source: screens/priya-nair-resume.txt
- Rollback approach on that migration: not stated

## Sources on file

- debriefs/senior-backend-engineer/2026-10-21-priya-nair-screen.md
- screens/priya-nair-resume.txt

## Your questions (M2)

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

## Earlier rounds

- Covered: M1 by Sam Lee on 20 Oct
- Open question to close: Rollback thinking on a live migration was not covered in the screen (Ana's slot should close it) (2026-10-21-priya-nair-screen.md)
- Open question to close: On-call depth: said "one week in four"; confirm what she personally fixed during pages (2026-10-21-priya-nair-screen.md)

## Logistics

Google Meet (link in invite) · greeted by: not recorded · scorecard in the kit format, filed alone before any panel discussion.

## Reminders

- Same core questions for every candidate; follow-ups only to clarify.
- Rate evidence against the anchors; never affect, demeanour or 'fit'.
- Accommodation requests go to Rita Gomes, people@northwind.example; never ask for medical detail.
- Candidate AI use in this interview: Take-home: AI tools allowed, say which. Live interviews: no AI unless the interviewer offers it.
