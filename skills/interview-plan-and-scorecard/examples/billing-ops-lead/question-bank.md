# Question bank: Billing Operations Lead (rubric v1)

Filled from `templates/question-bank.md` after the lint changes in the
walkthrough (step 3). `questions.md` beside it is the one-line lint fixture for
the same bank. Each block maps to exactly one criterion in `rubric.csv`, and
the ids match `questions_ref` in `loop.csv`.

---

### Q1: C1, Runs a recurring finance process end to end
- **Slot / interviewer:** 1, Maya Chen
- **Type:** past-behaviour
- **Question (read as written):** "Walk me through the last month-end close you ran, from the first task to sign-off."
- **Set follow-ups:**
  - "Which steps were yours, and which were someone else's?"
  - "Tell me about a time a step ran late or had an error. What did you do?"
  - "What would you change about that process now?"
- **Good evidence looks like:** names the steps they owned end to end, and how they handled a missed deadline or an error (anchor 3); a measured improvement they made is a 4.
- **Weak evidence looks like:** describes the team's process in general terms, or names steps but not what they did when one went wrong (anchors 1-2).
- **Do not score:** employer prestige, polish, confidence, shared interests, anything off-criterion.
- **Minutes:** 25

---

### WS1: C2, Writes reporting queries
- **Slot / interviewer:** 2, Tom Reyes
- **Type:** work sample
- **Task (read as written):** "Here are two sample tables, invoices and payments, with 40 rows each. Write a query that reconciles paid and unpaid invoices for March and returns the unpaid total. Talk me through it as you go. You have 30 minutes, and you can use the SQL reference sheet."
- **Set follow-ups:**
  - "How would you check that the total is right?"
  - "What in this data could make the total wrong?"
- **Pass evidence:** the query runs and returns the correct unpaid total for the sample, with one check for the duplicate payment rows planted in the data (anchor 3); explaining a check for a second data issue unprompted is a 4.
- **Weak evidence looks like:** the query does not run or returns the wrong total (1), or runs but misses the duplicates (2).
- **Do not score:** typing speed, SQL dialect, formatting style. C1 is a secondary for this slot: note C1 evidence only if it comes up, and do not probe for it.
- **Minutes:** 45 (30 task, 15 follow-ups)

---

### Q2: C3, Writes policy others follow
- **Slot / interviewer:** 3, Priya Nair
- **Type:** past-behaviour
- **Question (read as written):** "Tell me about a procedure you wrote that other people used. How did you keep it current?"
- **Set follow-ups:**
  - "Who used it, and how do you know they did?"
  - "What changed after it was adopted?"
  - "What would you write differently now?"
- **Good evidence looks like:** a written procedure a team used, and how they kept it current (anchor 3); a measurable change after adoption is a 4.
- **Weak evidence looks like:** cannot point to a written procedure others used (1), or cannot say how it was used or kept current (2).
- **Do not score:** writing polish in the answer itself, employer prestige, shared interests.
- **Minutes:** 40

---

### Ability requirements (only if the role has them)
Asked of every candidate in the same words at the start of slot 1 by Maya, and
mapped to no criterion. It is Maya's stated requirement for this role, recorded
in the plan with her name.
- AR1: "Month-end close runs to 19:00 on the last two working days of each month. Can you meet that schedule, with or without reasonable accommodation?" [35][46]
