---
name: fix-bug-with-repro
description: Use when a bug report, failing test, CI log, or stack trace needs a root-cause fix, not a symptom patch.
version: '1'
---

# Fix a bug with a repro

Inputs: repro steps or failing test, error output, affected repo and version. Output: root cause, minimal fix, regression test, verification log. Fallbacks: if the bug will not reproduce, say so with what was tried and ask for the missing input; never ship a guess as a fix.

1. Reproduce the failure against the real code first — a failing test or script. No repro, no fix.
2. Isolate the root cause. Read the callers and the real caller chain, not only the crashing line.
3. Write a failing test first where feasible.
4. Make the minimal fix at the root cause, across every case it implies — all aliases, re-lookups, and re-stores of shared state.
5. Re-run the repro, then the full relevant test suite. Confirm the fix through the real caller chain.
6. Deliver the four-part contract. Label anything untested UNKNOWN.

<!-- Reuse: debugging packs exist upstream, but none ships in this bot's approval-gated, evidence-labeled voice; rewritten here in own words. -->
