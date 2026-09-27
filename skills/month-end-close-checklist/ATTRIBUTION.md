# Attribution: month-end-close-checklist

This package is an AutoGPT platform skill. One file in it is adapted from an
Apache-2.0 upstream skill; everything else is original to AutoGPT.

## Adapted file

- `references/close-dependency-map.md` is adapted from the `close-management`
  skill in anthropics/knowledge-work-plugins, installed in this catalog as
  `month-end-close-management`.
  - Source: https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/finance/skills/close-management/SKILL.md
  - Pinned commit: `1c7187c4fc17feefa6cde39517f12dae1249e6c4`
  - Original author: Anthropic and upstream contributors
  - Licence: Apache-2.0; a copy is in `LICENSE` in this package. Existing
    copyright and notice terms remain applicable.
  - Changes: kept the levelled dependency structure and the critical-path idea;
    rewrote the tasks for a small-business close where posting, adjusting and
    locking stay with the owner and the accountant.

## Adapted for AutoGPT

- 2026-09-26: `close-dependency-map.md` adapted as described above.
- 2026-09-27: added processor reports (Level 1), processor clearing and the
  Undeposited Funds / suspense / Opening Balance Equity review (Level 2),
  bills-not-yet-received (Level 3), and owner sign-off plus the recorded lock
  date (Level 5); tied each item to a control id in
  `templates/close-controls.csv`; pointed the attribution line at this file.
  Added this ATTRIBUTION.md and the Apache-2.0 `LICENSE` so the package carries
  its own notice when installed alone.

## Original files

`SKILL.md`, all other files in `references/`, and everything in `scripts/`,
`templates/`, `examples/` and `checklists/` are original AutoGPT work.
