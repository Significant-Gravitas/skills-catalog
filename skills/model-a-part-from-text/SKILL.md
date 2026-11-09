---
name: model-a-part-from-text
description: 'Use when a person describes a part in words, a sketch, or a spec and wants parametric geometry: a build123d model on the text-to-cad server, checked numerically and shown live.'
version: '1'
---

# Model a part from text

Inputs: the brief (text, sketch, or spec), target process, and material if known. Output: a model script plus its live viewer page, the measured bounds and fits, and a snapshot of the result. Fallbacks: a missing or conflicting dimension that changes the result is surfaced as an assumption for the person to settle — never invented, never scale-fit from an unscaled image.

1. Transcribe the brief into a dimension ledger first: function, envelope in mm, interfaces and datums, hole patterns, material, process, and what must stay parametric. Flag gaps before modeling.
2. Write the model as code: dimensions live in a plain helper function; one @model per configuration returns a labelled build123d shape; millimetres, +Z up. Assemblies are a separate skill — a single part stays a single model.
3. Build with cad run and read the run line (parts, bounds, joints). A contradiction with the ledger is fixed before anything else is discussed.
4. Assert person-given dimensions inside the model body, then hand the person the viewer page once and name the model id every later command will use.
5. Take one snapshot from the angle that shows the defining features. The snapshot proves arrangement, never size — sizes come from the run line and measured checks.
6. Iterate by reference: when the person names a face or feature, resolve it, edit the code that made it, and rebuild. Never edit an exported file to fake a model change.
7. End with the verification log: ledger vs measured values, assumptions still open, and the exact export list to request when files are wanted. No order, release, or production-ready claim without their yes.

<!-- Reuse: cad core workflow adapted from earthtojake/text-to-cad@4d42cb0 skills/cad/SKILL.md (MIT, Thompson Labs LLC) — model-as-code, cad run/inspect/snapshot verbs, ledger-first intake rewritten for this package. -->
