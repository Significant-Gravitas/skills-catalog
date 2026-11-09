---
name: hand-off-robot-and-sim-files
description: 'Use when geometry leaves CAD for a robot or a simulator: URDF structure, MoveIt planning semantics, and SDFormat worlds, each authored as source of truth and validated.'
version: '1'
---

# Hand off robot and sim files

Inputs: the assembly (links, joints, limits, meshes) and the consumer (MoveIt, Gazebo, or another simulator). Output: validated .urdf, .srdf, or .sdf files with the frame and inertial ledger behind them. Fallbacks: an unmeasured inertial is computed from geometry and material or flagged UNKNOWN — inertials are never freehanded to make a validator pass.

1. Keep the three files distinct: URDF is the robot's structure, SRDF is planning semantics layered on a valid URDF, SDF is the simulator's model and world description. None does another's job.
2. Author the XML directly as the source of truth; meshes exported from the CAD models plug in by reference, with frames following the ledger.
3. Derive planning groups, end effectors, group states, and disabled collisions from the URDF's actual link and joint names — copied, never typed from memory.
4. State units, frame conventions, and pose reference frames explicitly; simulator files default to SI with named reference frames on poses and axes.
5. Run the matching validator before handoff and report its output verbatim. A file that has not validated is a draft and is labeled one.
6. Close with what the consumer still owes: controller config, planning tuning, or world assets — geometry handoff is not a running robot.

<!-- Reuse: handoff workflows adapted from earthtojake/text-to-cad@4d42cb0 skills/urdf/SKILL.md, skills/srdf/SKILL.md, skills/sdf/SKILL.md (MIT) — structure/semantics/simulation separation rewritten for this package. -->
