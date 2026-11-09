---
name: source-catalog-parts
description: 'Use when an assembly needs real purchasable hardware — screws, bearings, motors, servos, connectors, boards: find the actual part and its STEP file before drawing placeholder geometry.'
version: '1'
---

# Source catalog parts

Inputs: the part needed (name, standard, or key dimensions) and its interface constraints. Output: the matched catalog part, its canonical STEP file with verified checksum, and the model change that consumes it. Fallbacks: no credible match means a clearly-labeled placeholder with the search trail recorded — a placeholder is never presented as the real part.

1. Search the catalog before modeling anything: try the exact name, then aliases, family terms, and standards (a servo answers to more than one designation). Record what was tried.
2. Choose on interface truth: envelope, shaft or bore, mounting pattern, and rating against the assembly's ledger — not on the prettiest thumbnail.
3. Download the canonical file and verify its checksum before it enters the project. A failed checksum is a failed part.
4. Convert the STEP to xbf once and compose it into the model by reference, so assemblies rebuild fast and the vendor origin survives for inspection.
5. Measure the composed result (seating, clearance, mass roll-up) like any other part; catalog truth does not exempt a fit check.
6. Record the part's source, designation, and checksum in the deliverable notes so the next person can re-source the identical item.

<!-- Reuse: sourcing workflow adapted from earthtojake/text-to-cad@4d42cb0 skills/step-parts/SKILL.md, references/step-parts-api.md, scripts/download_step_part.py (MIT) — search-before-placeholder and checksum rules rewritten for this package. -->
