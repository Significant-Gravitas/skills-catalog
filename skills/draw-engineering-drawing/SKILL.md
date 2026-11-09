---
name: draw-engineering-drawing
description: 'Use when a part needs a shop drawing: a dimensioned PDF with projected views, hidden lines, hole callouts, notes, and a title block that follows the model.'
version: '1'
---

# Draw an engineering drawing

Inputs: the built part model, drawing standard (ISO or ASME), and sheet size. Output: a single PDF drawing whose dimensions sit on the projected geometry. Fallbacks: a dimension the geometry cannot support is left off and listed — a hand-typed number never appears on the sheet to fill a gap.

1. Project, never redraw: orthographic views with hidden lines and centre marks come from the part's geometry, so the drawing follows the model on every rebuild.
2. Attach dimensions to points on the geometry itself. If the model changes, the dimension moves with it; a detached number is a defect.
3. Call out holes, threads, and patterns from the features that made them, with datums matching how the part will be inspected.
4. Put material, finish, tolerance basis, and revision in the title block and notes — a drawing without its tolerance basis is unfinished.
5. Check the sheet visually once (views not overlapping, callouts legible) and numerically once (every ledger-critical dimension present on the sheet).
6. Deliver the PDF with the model id it was projected from. Regenerating the drawing after a model edit is one run, and the old PDF is named stale until then.

<!-- Reuse: drawing workflow adapted from earthtojake/text-to-cad@4d42cb0 skills/engineering-drawing/SKILL.md and references/sheet-api.md (MIT) — dimensions-on-geometry rule rewritten for this package. -->
