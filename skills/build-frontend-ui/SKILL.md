---
name: build-frontend-ui
description: Use when a screen, component, or flow needs building from a spec or design reference in the product's existing frontend stack.
version: '1'
---

# Build frontend UI

Inputs: the spec or design reference, the target app and component library, and acceptance criteria including loading, error, and empty states. Output: implemented, tested components wired to real data. Fallbacks: without a design, build from the spec and the nearest existing screen, and label visual guesses INFERENCE; never invent metrics or copy.

1. Map the design or spec to existing components and paths first; reuse the design system before creating new components.
2. Build states the design cannot show: loading, error, empty, focus, and keyboard behavior.
3. Wire real data with the repo's fetching pattern; handle races, retries, and stale responses.
4. Accessibility pass: labels, contrast, focus order, and screen-reader names — checked, not assumed.
5. Test: component tests for interactions and edge states; run the project's test and lint commands and show output.
6. Deliver the four-part contract with screenshots or test evidence where available.

<!-- Reuse: design-to-code mapping discipline from handoff-note methods, rewritten for direct building. -->
