# Retain the skills introduced by PR 2

The user decided on September 25, 2026 that PR 4's blanket replacement/removal
scope applies only to skills already present before PR 2. Newly added PR 2
skills must survive. Exact-name and purpose-overlap choices remain open.

The boundary is the catalog at
`00d9cfbf2c9c01a13dc5626a50e8f4b9c4d2d35d` (171 entries), before PR 2 merged as
`c0237abc5a3503b1bb62d3422704132176305847`.

## Applied protection

- PR 2 added 167 skills. PR 4 now carries forward 166 noncolliding packages and
  their exact catalog entries, without rewriting their contents or assigning
  new licences/authorship to them.
- The remaining addition, `product-experiment-design`, has an unresolved
  exact-name clash. The existing PR 4 proposal remains unchanged; retaining that
  proposal in this draft does not choose it over Nick's version. The original
  PR 2 entry and file hashes are recorded alongside the unresolved decision.
- The 74 proposed imported packages remain intact. The current draft therefore
  has 240 catalog entries and 498 package files: 74 proposed imported packages
  plus 166 retained PR 2 packages. This is not a final approved selection.
- `provenance/pr2-carryforward.json` pins all 167 additions and binds each
  retained file's bytes, Git blob, mode and catalog metadata. The checker rejects
  missing or changed retained packages. This protection is separate from the
  existing source-integrity checks for the 74 imported proposals.

`resume-screening` was present before PR 2. Nick modified it; he did not add it.
It therefore stays inside PR 4's original replacement/removal scope under the
user's historical-boundary rule. Its modify/delete Git conflict is a mechanical
merge-resolution item, not a separate pending content choice. This repository
scope decision does not delete any production database record or installed user
copy.

## Exact-name choice still required

Both versions use `product-experiment-design`, but they perform different work:

| Option | What it does |
|---|---|
| Nick's skill from PR 2 | Designs and reads out statistical experiments, with sample sizing, guardrails and precommitted scale/extend/kill bands. |
| The replacement proposed in PR 4 | Pawel Huryn's `brainstorm-experiments-existing` from `phuryn/pm-skills`, packaged under the shared name. It proposes low-effort tests of assumptions, including prototypes, fake doors and technical spikes. |
| Keep both | Requires distinct installed names and updated catalog/provenance references. No rename has been chosen. |

[Nick's exact source](https://github.com/Significant-Gravitas/skills-catalog/blob/c0237abc5a3503b1bb62d3422704132176305847/skills/product-experiment-design/SKILL.md)
and [the exact PR 4 proposal reviewed](https://github.com/Significant-Gravitas/skills-catalog/blob/bde80d2ac60042b847c8277f1575552a622696f6/skills/product-experiment-design/SKILL.md).

Purpose-overlap decisions likewise remain open. No retained PR 2 skill has been
removed, renamed or rewritten to resolve an overlap. The earlier expert
coverage ledger describes the proposed imported alternatives; it is not an
instruction to delete the retained PR 2 skills.

## Merge and production boundary

PR 4 remains a draft. Its manifest and exact-name conflict must be reconciled
with main after the remaining decisions. Do not resolve the manifest by taking
one side wholesale. Check the protected inventory again after resolving.

This change does not seed production, retire database listings, change expert
assignments or update installed user copies. Those operations remain separate
from repository retention. The combined rollout still needs the approved
per-expert mapping and the documented importer/runtime prerequisites.
