---
name: export-files-on-request
description: 'Use when a person asks for files: STEP for CAD exchange, STL/3MF for print, GLB for review, xbf to share without code — written from the server-held document, only when asked.'
version: '1'
---

# Export files on request

Inputs: the model id, the format list, and the destination. Output: the written files with paths, plus what each file froze (the document state at write time). Fallbacks: an unbuilt or stale model is rebuilt first and the person told; a format the document cannot produce is refused in one line with the alternative.

1. Treat every file as an action on the held document, never as part of the model. No code change, no silent rebuild: the file holds what the document held when written, and a later edit reaches the file only when it is written again.
2. Export exactly the list asked for — STEP, STL, 3MF, GLB, or xbf — and nothing extra. A posed file comes from a posed model, not from rotating an export.
3. For print meshes on fitted parts, set the mesh tolerance to about a tenth of the smallest clearance and say which clearance drove it.
4. Standing deliverables live in an exports script that imports the models and rewrites every file in one run; run it after model changes instead of hand-exporting piecemeal.
5. Share without code only via xbf, and only with the owner's yes — it is the one export that leaves the parametric source behind.
6. Vendor STEP is converted to xbf once and reused; a mesh never becomes B-rep, and nobody is told it did.
7. Close by naming each file, its path, and the model state it froze. External release of any file needs the owner's yes.

<!-- Reuse: export discipline adapted from earthtojake/text-to-cad@4d42cb0 skills/cad/references/exports.md and project-layout.md (MIT) — files-as-actions and standing-deliverables rules rewritten for this package. -->
