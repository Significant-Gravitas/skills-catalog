# Evidence matrix, one candidate (shape rendered by merge_matrices.py)

```markdown
### A-003

| Criterion | Result | Evidence |
|---|---|---|
| C1 <criterion> | `EVIDENCE FOUND` | "<exact words>" (<location>) |
| C2 <criterion> | `EVIDENCE MISSING` | not stated<; tested by ...> |
| C3 <criterion> | `CONFIRM IN INTERVIEW` | "<exact words>" (<location>); <what is unclear> |

Questions for interview: C2: <question about the work>. C3: <question>.
```

Rules:
- One row per rubric criterion, in rubric order.
- `EVIDENCE FOUND` always has the exact words and a location, verified by
  `verify_quotes.py`; an approximate match carries "[approximate match: read
  the source line]".
- No names, contact details, photos, locations, school names, graduation
  years, gap commentary, scores, ranks, or overall views.
- Sofia's reading of the same rows: FACT / UNKNOWN (not stated) / UNKNOWN
  (confirm in interview); the `sofia_label` column in `matrix.csv`.
