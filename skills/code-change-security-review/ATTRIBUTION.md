# Attribution: code-change-security-review

Original skill: `differential-review`.
Original author: Omar Inuwa; published by Trail of Bits
Source: https://github.com/trailofbits/skills/blob/32e34f8173796e3566a51aee877dc96bc5191f64/plugins/differential-review/skills/differential-review/SKILL.md
Pinned commit: `32e34f8173796e3566a51aee877dc96bc5191f64`.
Licence: CC-BY-SA-4.0; see LICENSE. Existing copyright and notice terms remain applicable.

AutoGPT adapted the packaging on 2026-09-25. AutoGPT did not author the original expert guidance. All original bytes, hashes and exact edits are retained in the catalog repository provenance records.

## Recorded changes

- `SKILL.md` from `trailofbits/skills/plugins/differential-review/skills/differential-review/SKILL.md`: Use the clear installed name, standard licence and string-valued attribution metadata; preserve all other upstream fields and body. Normalize equivalent tool-list separators where required.; Identify adapted files while retaining upstream authorship and licence.
- `LICENSE` from `trailofbits/skills/LICENSE`: Copied unchanged.
- `methodology.md` from `trailofbits/skills/plugins/differential-review/skills/differential-review/methodology.md`: Copied unchanged.
- `adversarial.md` from `trailofbits/skills/plugins/differential-review/skills/differential-review/adversarial.md`: Copied unchanged.
- `reporting.md` from `trailofbits/skills/plugins/differential-review/skills/differential-review/reporting.md`: Copied unchanged.
- `patterns.md` from `trailofbits/skills/plugins/differential-review/skills/differential-review/patterns.md`: Copied unchanged.

## Runtime requirements

- A local Git repository with accessible base/head refs, file reading/search, Bash/POSIX shell commands and file writing; gh only for PR metadata.
- audit-context-building optional; source documents manual line-by-line fallback.
- Namespaced adversarial-modeler agent optional; source offers direct adversarial.md route.
- issue-writer is an optional follow-on, not verified or supplied as a required executable.
- AutoGPT compatibility with the skill loader and tool interface has not been tested.

Native frontmatter is retained. Preserving it does not establish platform enforcement:

```json
{
  "allowed-tools": "Read Write Grep Glob Bash"
}
```

## Installed names

References to original skill names can be resolved using this table. Native API/command identifiers and persistent project-state filenames remain unchanged.

| Original source and name | Installed name |
| --- | --- |
| trailofbits/skills/plugins/supply-chain-risk-auditor/skills/supply-chain-risk-auditor | `supply-chain-risk-auditor` |
| trailofbits/skills/plugins/differential-review/skills/differential-review | `code-change-security-review` |

This package has not been executed or benchmarked. Static package validation does not provision accounts, tools, native dispatch or persistent storage.
