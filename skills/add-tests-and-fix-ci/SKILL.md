---
name: add-tests-and-fix-ci
description: Use when coverage is thin, tests are flaky, or CI is red and needs to be green for the right reason.
version: '1'
---

# Add tests and fix CI

Inputs: the module or failure, test command, and CI logs. Output: new or repaired tests, flaky-test diagnosis, and a green, honestly-reported CI run. Fallbacks: if CI cannot run locally, reproduce the failing job's exact commands; never silence, skip, or weaken a test to get green.

1. Read the failing output first. Classify: real failure, flake, or environment. Reproduce locally before changing anything.
2. For flaky tests, find the nondeterminism (time, order, network, shared state) and fix the cause; quarantine only with a filed follow-up and the owner's yes.
3. Plan tests by risk: failure modes first — bad input, empty, large, permissions, concurrency, timezones, retries, old data. Pick the level per case: unit, integration, end-to-end, or manual with a named acceptor.
4. Write the smallest tests that would have caught the bug or cover the behavior. Run them red, then green.
5. Run the whole relevant suite and the whole-project linter/formatter. Report real counts; label anything unrun UNKNOWN.
6. Deliver the four-part contract, including explicit uncovered gaps and who accepts them.

<!-- Reuse: reuse reports found test-planning methods but no shipped tests-plus-CI skill in this voice; composed here in own words. -->
