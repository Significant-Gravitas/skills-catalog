---
name: review-code
description: Use when a PR, diff, or branch needs a full correctness, edge-case, security, and test-coverage review. For a security/performance-only check without a full diff review, use Secure and speed pass instead.
version: '1'
---

# Review code

Inputs: the diff or PR, its description and linked ticket, and CI status. Output: findings ranked blocker, should-fix, question, nit — each with file and line, trigger, and a concrete fix. Fallbacks: if you cannot see CI, tests, or callers, say exactly what is unseen and never claim safe or passed.

1. Read the diff in the context of its callers and tests, not in isolation.
2. Check correctness first, then edge and error paths, security, performance, and accessibility for UI changes.
3. Verify the tests actually cover the changed behavior; untested behavior changes are a blocker.
4. Separate what a linter should catch from what needs human judgment; do not spend review on formatting.
5. For high-risk changes (auth, money, data deletion, migrations), add an adversarial pass: how would this break, and what is the blast radius in caller count?
6. End with a clear verdict: approve, approve with fixes, or request changes — and what evidence would change it. Approving is the owner's call on their own PRs; never merge without their yes.

<!-- Reuse: structured review taxonomy and differential risk pass, rewritten in own words. -->
