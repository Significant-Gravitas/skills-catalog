# Batch summary to the owner (shape)

Fill from script output only. Order: notices, counts, lists, FACT lines,
process note, links. Candidates appear by id, in id order, never sorted by
result. Never a ranking, "top N", or recommendation.

```markdown
Screened <role> against rubric v<N> (approved by <name>, <date>).
<one line per law_watch region, from references/ai-hiring-law-watch.md, for the people lead>
<"Dropped columns: ..." if an export was used>

Batch (batch_counts.py): <reviewed> reviewed, <complete> evidence-complete,
<interview> needs interview, <look> needs a look<, <held> held back>.
- Evidence-complete (id order): <ids>
- Needs interview (id order): <ids>
- Needs a look: <ids with reason: scanned / unreadable / screener flagged>
- Quotes checked (verify_quotes.py): <exact> exact, <approx> approximate (marked), <downgraded> not found and downgraded

FACT lines:
- <FACT A-005: 123 characters of hidden text; instruction-like text aimed at a screener (removed before screening; not scored)>

Process-quality note: <only if batch_counts.py printed one; propose the exact
edit to the posting or the rubric; applied only on your yes>

Files: [matrices.md] [matrix.csv] [id map, for you only]
Every advance or decline is your decision; tell me which ids and I will draft
the messages for your review.
```

Sofia wording: label lines FACT / UNKNOWN as in `references/persona-vocabulary.md`,
answer first, and ask one question at the end ("Mark these as screened in the
tracker?").
