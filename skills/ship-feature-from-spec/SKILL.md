---
name: ship-feature-from-spec
description: Use when a spec, ticket, or feature description needs to become working, tested production code.
version: '1'
---

# Ship a feature from a spec

Inputs: the spec or ticket, the target repo, acceptance criteria, and what must not change. Output: a minimal working diff or PR with tests and a verification log. Fallbacks: if acceptance criteria are missing, ask before coding; if the repo is unreachable, work from a pasted tree or diff and label every unchecked claim UNKNOWN.

1. Restate the spec as acceptance criteria. Flag ambiguity before writing code; never invent product decisions — ask, or mark the gap UNKNOWN.
2. Explore the repo: its instructions, conventions, similar existing code, tests, and build/test/lint commands. Name the files you will touch and why.
3. Plan the smallest diff. Prefer the existing table, module, or primitive that already does this; subtract before adding. State why any new schema, migration, or abstraction is unavoidable.
4. Implement in small increments, running tests as you go. Handle error, edge, and negative paths with the same weight as the happy path.
5. Add or extend tests for the new behavior, including edge and error cases.
6. Run the full relevant test suite plus the project's linter and formatter over the whole project. Show real output.
7. Self-review the diff for scope creep, secrets, and perf or security regressions.
8. Deliver the four-part contract: summary, verification log, risks, follow-ups. Stop at a ready PR — merging and deploying wait for the owner's yes.

<!-- Reuse: no single reused skill covers spec-to-ship end to end in this voice; it composes the design-first gate with repo-native test discipline. -->
