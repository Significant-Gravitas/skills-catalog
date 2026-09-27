# Run and share checklist

## Before any number
- [ ] Files re-read fresh from ~/workspace/hiring/ (tracker outranks chat).
- [ ] An ATS export went through `normalize_export.py`; dropped protected columns told to the owner in one line.
- [ ] Vendor traps printed by `--vendor` are carried into the report where they touch a number.
- [ ] Ambiguous dates resolved with the owner (`--date-order`), not guessed.
- [ ] Unmapped stages mapped with the owner (`--stage-map`), not guessed.

## The numbers
- [ ] Every number in the reply comes from report.json / report.md, with its label.
- [ ] The first banner (cohort vs all-rows view) is stated.
- [ ] SMALL SAMPLE banner repeated in the reply when present.
- [ ] Clocks: which clock, from which date; evergreen and zero-day caveats kept.
- [ ] Cost per hire only with owner cost lines, formula and variant.
- [ ] No rate by any protected group; no inferred demographics.
- [ ] Every INFERENCE line shows its arithmetic and assumptions.

## Output
- [ ] Chat read under 300 words (templates/funnel-read.md) unless the full table was asked for.
- [ ] Snapshot saved (`snapshot_and_chart.py`), diff used for rollup lines.
- [ ] Files delivered with `write_workspace_file(source_path=…)` and `workspace://` links.

## Before anything leaves the chat
- [ ] The owner asked for this specific send (channel or email).
- [ ] `share_safe.py` built the copy being sent from report.json, exit 0; every `--allow` was checked by eye.
- [ ] Share copy has role-level numbers and counts only: no per-candidate lines (no stage-and-days, waiting-on or reply status per person), no names, links, emails, phones.
- [ ] Channel confirmed with `list_chat_platform_channels`; the post call is left to the gate.
- [ ] Email: a Gmail draft, never a send.
