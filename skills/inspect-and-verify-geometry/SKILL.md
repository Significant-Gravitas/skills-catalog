---
name: inspect-and-verify-geometry
description: 'Use when a dimension, fit, clearance, mass, or reference must be proven: check scripts that measure the built model, reference resolution, and the gates a design must pass before export.'
version: '1'
---

# Inspect and verify geometry

Inputs: the model id or file, and the numbers in question. Output: measured values with the script or command that produced them, each labeled FACT, INFERENCE, or UNKNOWN. Fallbacks: a check that fails or cannot decide has shown nothing — say so and name what would decide it, instead of softening the result.

1. Measure the model, not the picture. A check script calls the model and measures its shape: bounds, distances between parts in world coordinates, volumes, and mass where materials are assigned.
2. Assert person-given dimensions inside the model body where they belong; use a separate check script for derived numbers the person asks about after the fact.
3. Resolve named references before editing: a reference returns the element, its measured facts, and the code that made it. Edit that code; never patch around it.
4. Apply the gates in order: seating parts touch, no unintended interference, given dimensions match measurements, then process checks (manufacturability, printability) before any export is offered.
5. For assemblies, weigh the whole: part volumes times material densities, naming any part with no material assigned instead of assuming one.
6. Never shrink a specified feature — a fillet, a radius, a wall — to make a build pass. A reduced feature is a different design and is reported as one.
7. Report compactly: claim, measured value, method. Anything not measured is listed as unverified, with the check that would close it.

<!-- Reuse: inspection method adapted from earthtojake/text-to-cad@4d42cb0 skills/cad/references/inspection-and-validation.md and snapshot-review.md (MIT) — measure-the-shape gates rewritten for this package. -->
