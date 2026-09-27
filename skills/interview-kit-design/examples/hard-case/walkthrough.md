# Hard case: the owner's favourite questions, a five-slot ask, a career changer

Fictional. Lena Ortiz (hiring manager, Platform Engineer role) pastes her
questions (`owner-questions.md`) and asks: "Use these as the kit. Make it
five interviews so everyone gets a look. And for Kofi, put in the packet
that he's older and switching careers, so the panel goes easy."

## 1. Lint the owner's questions

```
$ python3 scripts/question_lint.py examples/hard-case/owner-questions.md
ERROR line 3  origin          'Where are you originally from'
ERROR line 5  family          'kids'
ERROR line 7  salary-history  'current salary'
ERROR line 10 affect          'passionate'
WARN  line 4  leading         ', right?'
WARN  line 6  tool-recognition 'Have you used'
WARN  line 8  double-barrelled 'and how did you fix it?'
WARN  line 9  brainteaser     'How many golf balls fit in'
exit=1
```

## 2. What goes back to Lena (one table, her intent kept)

| Her question | Why | Rewrite |
| --- | --- | --- |
| Where are you originally from? | National origin [34] | Dropped |
| You're comfortable being on call, right? | Leading | "The role is on call one week in five, nights included; tell me about the last on-call rotation you carried." |
| Do you have young kids? The on-call is rough. | Children and childcare questions [74] | "The role is on call one week in five, nights included; does that work for you?" |
| Have you used Kubernetes? | Tool-name recognition | "Walk me through the last cluster change you shipped. Which part was yours?" |
| What's your current salary? | Salary-history bans [56][75] | Removed from the loop; pay expectations are asked at offer stage by job-offer-and-close-plan |
| Tell me about the last outage you led. What went wrong and how did you fix it? | Two questions in one | "Tell me about the last outage you led." Probe: "What would you change?" |
| How many golf balls fit in a 747? | Brainteaser [23] | Dropped; replaced by a capacity-planning problem from the team's real backlog |
| How passionate are you about infrastructure? | Affect [73][79] | "Tell me about infrastructure work you chose to take on when nobody asked." |
| Tell me about a time you cut cloud costs. | Clean | Kept as written |

## 3. The five-slot ask

`check_kit.py` warns on a fifth slot (four interviews predicted the
decision with 86% confidence [29]; default — confirm with the owner). The
reply: "Four slots cover all five must-haves with one owner each. If you
want a fifth, tell me which must-have it adds evidence for and I'll add it
with that reason written in the kit." "So everyone gets a look" is not a
competency, so the kit stays at four until Lena names one.

## 4. The packet request about Kofi

Refused in one line, with the job-related alternative:

> I won't put age or anything like it in a packet. His career change is
> already in the loop's shape: the deep-dive slot (slot 3) is where he has
> room to explain it, and the packet quotes his own words: "Moved from
> network operations to platform engineering in 2025" — source: his resume.

"Go easy" is not added either: every candidate gets the same core
questions and the same anchors.

## 5. Other hard parts

- Kofi's resume shows a two-year gap. Nothing in the packet mentions it;
  gaps are not asked about or scored (gap-related claims in AI screening
  litigation [108]; practitioner judgement for interviews).
- No candidate material for a second candidate: the packet is built from
  the role scorecard and posting, and the summary says "not stated" with a
  flag that it is thin.
- The loop row for one slot has no timezone: `build_packets.py` refuses
  that row ("times are never assumed"), and the hand-back asks
  coordination to fix the tracker.
