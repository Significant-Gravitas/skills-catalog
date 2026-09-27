# Kickoff questions (one `ask_question` call)

Drop any question already answered by memory, a paste, or an existing plan.
Keep "Don't know yet" on every question; that answer is recorded as `OPEN`.
`ask_question` takes at most 10 questions, each with at most 25 options of at
most 200 characters (platform limits).

```json
{
  "questions": [
    {
      "question": "What is the role, and what should be different six months after this person starts?",
      "options": ["I'll type it", "Don't know yet"]
    },
    {
      "question": "Who is the hiring manager, and who makes the final hire decision?",
      "options": ["Same person (I'll name them)", "Different people (I'll name them)", "Don't know yet"]
    },
    {
      "question": "Who approves headcount, the job description, pay, and offer terms?",
      "options": ["I'll name them", "Don't know yet"]
    },
    {
      "question": "Who interviews, and who coordinates scheduling?",
      "options": ["I'll list them", "No coordinator yet", "Don't know yet"]
    },
    {
      "question": "Target start window and working pattern?",
      "options": ["Remote", "Hybrid", "Onsite", "Don't know yet"]
    },
    {
      "question": "Where will the role be posted and hired? Name the countries, states or cities (this decides which posting and AI-screening rules may apply).",
      "options": ["I'll list them", "Don't know yet"]
    },
    {
      "question": "Is the level and pay range approved? If so, by whom?",
      "options": ["Approved (I'll give range and approver)", "Level only", "Not yet approved", "Don't know yet"]
    },
    {
      "question": "Which policies apply: accommodation route, data retention and talent-pool notice, required posting text, background checks? Is the company a US federal contractor?",
      "options": ["I'll paste or describe them", "Ask our people lead", "Don't know yet"]
    },
    {
      "question": "What is your policy on candidates using AI, and do you use any AI tool to screen or interview?",
      "options": ["I'll describe it", "No policy yet", "Don't know yet"]
    },
    {
      "question": "Is there an existing job description, scorecard, or applicant tracking system?",
      "options": ["I'll paste or upload it", "It's in Drive", "In our ATS (I'll export)", "Nothing yet", "Don't know yet"]
    }
  ]
}
```

After the answers arrive: every "Don't know yet" becomes `OPEN` in the plan,
with a line in "Open questions" naming who is likely to know (ask the owner
if unsure; never guess a person).
