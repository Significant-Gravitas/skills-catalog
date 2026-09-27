# Affect, AI and the kit

Rules for what the kit and packets never do, and what they must say about
AI. `[n]` numbers follow the recruiting dossier (section 8). Legal lines are
dated 2026-09 and say "may apply; confirm with counsel".

## 1. Never rate affect or demeanour

- Scorecards never rate confidence, enthusiasm, nerves, energy, honesty,
  "presence", eye contact, body language or "fit", whether from the live
  conversation, a recording, a transcript, or AI meeting notes.
- Why: the EU AI Act prohibits AI systems that infer emotions in the
  workplace, hiring included [73][53]; AI video tools have produced scores
  unrelated to what candidates said [106]; "culture fit" works as a class
  proxy and can encode evaluator demographics [79].
- Meeting notes (Granola or similar) are evidence only of what was said.

## 2. Packets quote, never paraphrase

LLM summaries of a candidate shift when demographic details are perturbed
[62]; disability-related credentials were penalised and the model
confabulated its reasons [61]. So the packet summary is at most five direct
quotes, each with its source, checked by `scripts/verify_quotes.py`. A gap is
written "not stated", never filled.

## 3. Do not score polish

LLM evaluators prefer resumes written by LLMs (67-82% self-preference) [63].
Strong-answer notes and anchors describe substance (what was done and what
changed), never writing or speaking polish.

## 4. The candidate AI-use statement

State, per stage, what AI use is allowed, so candidates and interviewers
work from the same rule. Example of a published employer policy: draft the
application yourself then refine with AI; no AI in live interviews unless
told [104]. The kit records the owner's policy in `candidate_ai_policy`;
if it is UNSET, the packet says "no policy set" and the hand-back asks the
owner once. Never invent a policy.

## 5. AI-assisted screening and interviewing laws (orientation)

When the role is in New York City, Illinois, California or the EU, add one
line for the owner: AI-assisted screening and interview notice or audit
rules may apply (NYC LL144 bias audit and notice [52][69]; Illinois HB 3773
and the AI Video Interview Act [72][55]; California ADS rules [71]; EU AI
Act high-risk obligations, application date moved to 2 Dec 2027 by
Regulation (EU) 2026/1744 [119]). Confirm with counsel; do not advise.

## Sources

| # | Source | URL |
| --- | --- | --- |
| 52 | NYC AEDT rules (6 RCNY 5-300) | https://euro.ecom.cmu.edu//program/law/08-732/Regulatory/NY5-300.pdf |
| 53 | EU AI Act Annex III, Art. 5 (AI Act Explorer) | https://artificialintelligenceact.eu/annex/3/ |
| 55 | Illinois AI Video Interview Act | https://www.ilga.gov/Legislation/ILCS/Articles?ActID=4015&ChapterID=68&Print=True |
| 61 | UW News, ChatGPT bias against disability credentials | https://www.washington.edu/news/2024/06/21/chatgpt-ai-bias-ableism-disability-resume-cv/ |
| 62 | Seshadri et al. 2025, Small Changes, Large Consequences | https://arxiv.org/abs/2501.04316 |
| 63 | Xu, Li & Jiang 2025, AI self-preferencing | https://arxiv.org/abs/2509.00462 |
| 69 | NYC DCWP, Automated Employment Decision Tools | https://www.nyc.gov/site/dca/about/automated-employment-decision-tools.page |
| 71 | Mayer Brown, California employment AI regulations | https://www.mayerbrown.com/en/insights/publications/2025/08/california-adopts-new-employment-ai-regulations-effective-october-1-2025 |
| 72 | Morgan Lewis, Illinois HB 3773 | https://www.morganlewis.com/pubs/2024/09/illinois-passes-new-law-to-address-ai-in-the-workplace |
| 73 | Future of Privacy Forum, EU emotion-recognition prohibition | https://fpf.org/blog/red-lines-under-eu-ai-act-unpacking-the-prohibition-of-emotion-recognition-in-the-workplace-and-education-institutions/ |
| 79 | ScienceDaily, Rivera "Hiring as Cultural Matching" | https://www.sciencedaily.com/releases/2012/11/121129093008.htm |
| 104 | Anthropic, Guidance on Candidates' AI Usage | https://www.anthropic.com/candidate-ai-guidance |
| 106 | LARB, review of Schellmann's The Algorithm | https://lareviewofbooks.org/article/keeping-humans-in-the-loop-on-hilke-schellmanns-the-algorithm/ |
| 119 | Regulation (EU) 2026/1744, Digital Omnibus on AI | https://eur-lex.europa.eu/eli/reg/2026/1744/oj/eng |
