# What a rejection draft says, and what it never says

Citations `[n]` are in `references/sources.md`.

Contents
1. Timing
2. Structure
3. Feedback
4. Things never said
5. Retention and "keep on file"
6. Stage differences
7. Batches
8. Putting drafts into the sender's mailbox

---

## 1. Timing

61% of job seekers report being ghosted after an interview, and
underrepresented candidates report it more often (66% against 59%) [80].
A kind, prompt "no" is better than silence. Harper cannot send, but it can
make the draft ready the same day the decision is recorded. The candidate
should hear by the date promised in the candidate information note. Without
one, the default is within 5 business days of the decision (default, confirm
with the owner).

## 2. Structure

1. Plain subject: "Your application for <role>". No outcome in the subject.
2. Greeting with the candidate's chosen name, never a legal name they did not use.
3. The decision in the first two sentences.
4. Specific thanks: the call, the work sample, the number of interviews.
5. Approved feedback, if any, verbatim.
6. Practicalities for late stages: expenses, and what happens to their work sample.
7. A short close. The approved sender's name.
8. Approval footer (not part of the email): decision-maker and date, whether
   feedback was approved, whether a consumer report was involved, sender,
   "DRAFT, not sent".

## 3. Feedback

- Only feedback the decision-maker approved word for word. Harper never
  derives a reason from scorecards, the debrief pack or the rubric, and never
  fills a gap with a generic claim ("not the right fit", "the bar was high").
- Job-related and no broader than the evidence: "In the work sample, the
  query did not account for duplicate invoices" rather than "your SQL isn't
  strong enough".
- If the owner asks Harper to write feedback, Harper offers wording drawn
  only from the recorded, job-related rationale in the decision record. The
  decision-maker must approve it word for word before it goes into a draft.

## 4. Things never said

| Never | Why |
|---|---|
| "Other candidates were stronger / more experienced", unless the decision-maker approved that exact statement | Comparative claims invite dispute and are rarely evidenced in the form stated |
| Any mention of AI, algorithms, automated screening, scores or rankings | Only 8% of job seekers call AI hiring fair [101]. Describing the method goes beyond the approved text, and in some places automated decisions carry notice duties [54][69] |
| How the decision was made beyond the approved text | Panel notes and scorecards stay internal |
| Protected traits or proxies: age, "overqualified", family, origin, health, religion, "fit" | [34][45][74][79] |
| Legal conclusions ("this decision was lawful", "we do not discriminate") | Legal statements belong to counsel |
| A background check, record or credit report | FCRA route instead; see `fcra-adverse-action-routing.md` [48] |
| A promise of future contact ("we'll keep you in mind", "we'll be in touch about future roles") | Unless the owner has a real process behind it, it is a promise nobody keeps |

## 5. Retention and "keep on file"

- Say that details are kept, or that the candidate is in a talent pool, only
  when the owner's recorded retention policy allows it. Use the policy's own
  wording, in `retention_line`.
- UK ICO: do not keep unsuccessful candidates' records longer than
  necessary (typically the period in which a claim could be brought), and
  tell candidates up front before keeping them for future vacancies [100].
- US employers generally must keep hiring records for at least 1 year [44].
  Harper never promises deletion or tells the owner to purge records;
  retention questions go to counsel.

## 6. Stage differences

| Stage | Length | Feedback | Call first? |
|---|---|---|---|
| Application | 3-4 sentences | Rare; only approved | No |
| After a screen | Short | Only approved | Owner's choice |
| After the loop | Short email, plus call talking points | Only approved | Often; the owner decides |

Word counts are defaults (lint warns over 180 words; default, confirm with the owner).

## 7. Batches

For more than one candidate, use `templates/decline-batch.csv` and
`scripts/merge_declines.py`. Each row needs its own decision-maker, decision
date and consumer-report answer. A missing value blocks that row only. The
blocked list is shown to the owner first.

## 8. Putting drafts into the sender's mailbox (optional)

Only when the owner asks, and only with a mail tool the owner connected:
- Resolve the tool with `find_capability(query="gmail create draft")`, then
  `describe_capability`. Use a tool only if its name or description says it
  creates a **draft**. Never use a send tool. If only a send tool exists, stop
  and hand over copyable drafts.
- Confirm that the connected account belongs to the named sender.
- Probe with `run_capability(..., validate_only=true)`, then make one call per
  draft. Creating a draft is a write, and the platform's approval gate may
  hold it (`approval_required`). Wait for it.
- Report "N drafts in <sender>'s mailbox, none sent" only for calls that
  returned success. List any failures.
