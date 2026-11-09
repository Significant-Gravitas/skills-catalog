---
name: refactor-safely
description: Use when code needs restructuring, deduplication, or simplification without changing behavior.
version: '1'
---

# Refactor safely

Inputs: the target module, why it is being refactored, and the current test suite for it. Output: small behavior-preserving steps, each with green tests, plus a before/after note. Fallbacks: if behavior is untested, characterize it with tests first; if that is impossible, say so and shrink the refactor.

1. Characterize current behavior with tests before touching structure.
2. Work in small steps; tests green between every step. One cleanup per area, never a bundled rewrite.
3. Prefer deleting and reusing over adding: dead code, needless complexity, and abstractions with one caller go first.
4. No unrelated edits. Anything out of scope becomes a named follow-up.
5. Run the full relevant suite and the whole-project linter/formatter at the end; show output.
6. Deliver the four-part contract, calling out any behavior you could not prove preserved as UNKNOWN.

<!-- Reuse: the nightly audit finds cleanup candidates, but the safe-step refactor discipline itself is new writing for this bot. -->
