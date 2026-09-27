# Posting-law fields by place (dated; confirm with counsel)

Checked 2026-09-27. This table tells you which fields **may be required** so
you can mark them `[OWNER TO CONFIRM — may be required for <place>]` and tell
the people lead. It is not legal advice, and you never say a field *is*
required. Never supply a figure.

| Place | Fields that may be required in the posting | Also | Source | Status in this package |
|---|---|---|---|---|
| California | Pay scale: a good-faith estimate of the salary or hourly range the employer reasonably expects to pay (employers with 15+ employees) | Never seek salary history; do not rely on it | [56] | Read from the statute |
| Colorado | Pay (a closed range), a general description of benefits, how and when to apply | "Open until filled" is not compliant | [57] | Read from state guidance (2024) |
| Other US states and cities with pay-transparency laws (e.g. New York, Washington, Illinois) | Pay range likely; other fields vary | Salary-history bans tracked in [75] | [75] | **Not verified here.** Flag "may apply; confirm with counsel" |
| NYC, Illinois, California, EU | If an AI tool assists screening: notice and audit duties may attach to the process, not the posting text | Route to the people lead | [52][69][72][71][53] | Flag only |
| EU / UK | Pay-transparency and equality rules are changing | — | — | **Not verified here.** Flag "confirm with counsel" |
| Anywhere | Accommodation route (always included, as good practice) | Physical demands "with or without reasonable accommodation" | [46] | Always |
| Anywhere | Candidate AI-use policy, if the owner has one | Per stage: application vs live interview | [104] | If `candidate_ai_policy` is set |
| Anywhere | Anti-scam line, owner's choice | Job scams impersonate recruiters and ask for payment | [82][9] | Optional |

## How to mark a field

```
Pay range: [OWNER TO CONFIRM — may be required for Colorado postings]
```
And one line in the chat output for the people lead:
"Colorado: pay range, benefits summary and apply-by date may be required in the
posting. Confirm with counsel before publishing."

## Line templates (owner edits the wording)

- **Accommodation:** "If you need an adjustment or accommodation at any stage,
  tell us at <contact> and we will arrange it."
- **AI use** (example policy shape from one employer [104]): "Draft your
  application yourself; refining it with AI is fine. Please do not use AI
  during live interviews unless we say so."
- **Anti-scam** [82]: "We will never ask you for payment, bank details, or to
  move to a messaging app."
- **Equal opportunity:** "We welcome applicants of every background."

Sources: [sources.md](sources.md).
