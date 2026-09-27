# Attribution: statement-reconciliation

This package is an AutoGPT platform skill. One file in it is adapted from an
Apache-2.0 upstream skill; everything else is original to AutoGPT.

## Adapted file

- `references/bank-rec-layout.md` is adapted from the `reconciliation` skill in
  anthropics/knowledge-work-plugins, installed in this catalog as
  `account-reconciliation`.
  - Source: https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/finance/skills/reconciliation/SKILL.md
  - Pinned commit: `1c7187c4fc17feefa6cde39517f12dae1249e6c4`
  - Original author: Anthropic and upstream contributors
  - Licence: Apache-2.0; a copy is in `LICENSE` in this package. Existing
    copyright and notice terms remain applicable.
  - Changes: kept the statement-side / ledger-side layout and the reconciling
    item classes; reworded for small-business bank and card accounts; made
    every ledger-side item a proposal for the accountant rather than an entry;
    added aging buckets labelled as defaults to confirm with the owner.

## Adapted for AutoGPT

- 2026-09-26: `bank-rec-layout.md` adapted as described above.
- 2026-09-27: added a prior-period tie line above the layout, the no-plugging
  rule under the unexplained difference, and a pointer to the scripts that fill
  the layout; pointed the attribution line at this file (the upstream package
  is not installed with this one). Added this ATTRIBUTION.md and the Apache-2.0
  `LICENSE` so the package carries its own notice when installed alone.

## Original files

`SKILL.md`, all other files in `references/`, and everything in `scripts/`,
`templates/`, `examples/` and `checklists/` are original AutoGPT work.
