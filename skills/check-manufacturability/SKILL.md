---
name: check-manufacturability
description: 'Use when a part must survive a real process: sheet-metal bending, CNC machining, injection molding, or additive printing — measured findings with the rule behind each one.'
version: '1'
---

# Check manufacturability

Inputs: the part model or mesh, the target process, and the shop or printer if known. Output: findings ranked by severity, each with the measured value, the limit it was compared against, and the source of that limit. Fallbacks: a process limit no source states is reported as UNKNOWN with the supplier question that would settle it — textbook defaults never masquerade as a shop's capability.

1. Name the process first; the checks differ completely. Sheet metal: bend radii, reliefs, flat-pattern sanity. Machining: internal corner radii against real cutters, tool access, setups. Molding: draft, undercuts, projected area. Additive: wall thickness, overhang angle, support burden, build orientation.
2. Measure, do not eyeball: walls, angles, and radii come from the geometry or the mesh measurement tool, per process limits table where one applies.
3. Cite the rule behind every finding (process table, shop spec, or stated default) so the person can argue with the limit, not with the messenger.
4. For additive meshes, measure the exported mesh, not the B-rep — and say which mesh tolerance produced it, since the measurement inherits it.
5. Suggest the smallest geometry change that clears each finding, and name what it costs (a fillet grown, a wall thickened). Never silently apply the change.
6. Close with a verdict per process: ready, ready with listed changes, or blocked on a supplier answer. No certification or safety claim is ever made here.

<!-- Reuse: process reviews adapted from earthtojake/text-to-cad@4d42cb0 skills/dfm/SKILL.md (sheet-metal/CNC/molding references, mold_tool.py) and skills/dfam-check/SKILL.md (process-limits, dfam_tool.py) (MIT) — evidence-first verdicts rewritten for this package. -->
