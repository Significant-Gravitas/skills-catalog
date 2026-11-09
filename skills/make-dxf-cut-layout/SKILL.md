---
name: make-dxf-cut-layout
description: 'Use for 2D deliverables: profiles, gaskets, panels, templates, and flat patterns for laser, plasma, or waterjet — planar geometry modeled, checked, and exported as DXF.'
version: '1'
---

# Make a DXF cut layout

Inputs: the profile or the 3D part it derives from, material and thickness, and the cutting process. Output: a DXF file plus the checks run on the planar geometry. Fallbacks: a part whose flat pattern depends on bend parameters the person has not chosen gets the bend question first — flat geometry is never guessed from a formed part.

1. Keep the 2D path distinct from the 3D part: the drawing is its own planar model, built and checked like any model, exported only after checks pass.
2. Derive outlines from the part geometry where a part exists, so the layout follows the model instead of a hand-traced copy.
3. For sheet-metal patterns, state the bend assumptions (radius, K-factor basis) in the deliverable; a supplier's own bend data overrides defaults and is recorded when provided.
4. Check the layout before export: closed profiles, no stray construction geometry, features sized for the process (minimum webs and hole-to-edge distances the shop states).
5. Export the DXF on request and name its material, thickness, and units alongside the file — a bare DXF without those three facts is not a deliverable.
6. If the file is headed to an outsourced cutter, hand off to the manufacturability check for a preflight instead of declaring it order-ready here.

<!-- Reuse: 2D workflow adapted from earthtojake/text-to-cad@4d42cb0 skills/dxf/SKILL.md and references/generator-templates.md (MIT) — planar-model discipline rewritten for this package. -->
