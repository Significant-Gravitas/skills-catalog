---
name: slice-and-ship-to-print
description: 'Use when a model becomes a print or an outsourced cut: slicing with the user''s own presets, preflight for cutting services, and handoff to the printer app — the agent never runs the machine.'
version: '1'
---

# Slice and ship to print

Inputs: the model or mesh, the target printer or cutting service, and the user's profiles where they exist. Output: sliced G-code or a preflight report, plus the handoff the person completes. Fallbacks: no user preset means the missing profile is requested by name — a guessed preset is never sliced silently, and missing order data yields a needs-information report, not a pass.

1. Slice headless with complete presets resolved from the user's own profiles first; the output names the printer, material, and preset it was built for.
2. For outsourced flat or machined parts, preflight the actual exported file against the service's live catalog and specs: material, thickness, and service availability joined on the exact SKU, checked in the file that will be uploaded.
3. A preflight with missing or inapplicable data reports needs-information. It never rounds up to ready-to-order.
4. Hand printing to the printer's own app: the sliced file opens there, and the person picks the printer and starts the print. The agent never contacts, controls, or unlocks a printer.
5. Every handoff states the file, its tolerance basis, and the one action left for the person. Ordering or submitting needs their yes.

<!-- Reuse: slicing and preflight adapted from earthtojake/text-to-cad@4d42cb0 skills/gcode/SKILL.md (orca_presets.py), skills/sendcutsend/SKILL.md (live catalog/specs, report template), skills/bambu-labs/SKILL.md (MIT) — agent-never-prints boundary rewritten for this package. -->
