# Attribution: supply-chain-risk-auditor

Original skill: `supply-chain-risk-auditor`.
Original author: Eric Quintero; published by Trail of Bits
Source: https://github.com/trailofbits/skills/blob/32e34f8173796e3566a51aee877dc96bc5191f64/plugins/supply-chain-risk-auditor/skills/supply-chain-risk-auditor/SKILL.md
Pinned commit: `32e34f8173796e3566a51aee877dc96bc5191f64`.
Licence: CC-BY-SA-4.0; see LICENSE. Existing copyright and notice terms remain applicable.

AutoGPT adapted the packaging on 2026-09-25. AutoGPT did not author the original expert guidance. All original bytes, hashes and exact edits are retained in the catalog repository provenance records.

## Recorded changes

- `SKILL.md` from `trailofbits/skills/plugins/supply-chain-risk-auditor/skills/supply-chain-risk-auditor/SKILL.md`: Run unchanged collector/render scripts from this skill package directory. Make the package working directory explicit and preserve absolute target/output paths after script relocation.; Use the clear installed name, standard licence and string-valued attribution metadata; preserve all other upstream fields and body. Normalize equivalent tool-list separators where required.; Identify adapted files while retaining upstream authorship and licence.
- `LICENSE` from `trailofbits/skills/LICENSE`: Copied unchanged.
- `scripts/collect.py` from `trailofbits/skills/plugins/supply-chain-risk-auditor/skills/supply-chain-risk-auditor/scripts/collect.py`: Copied unchanged.
- `scripts/render.py` from `trailofbits/skills/plugins/supply-chain-risk-auditor/skills/supply-chain-risk-auditor/scripts/render.py`: Copied unchanged.
- `scripts/model.py` from `trailofbits/skills/plugins/supply-chain-risk-auditor/skills/supply-chain-risk-auditor/scripts/model.py`: Copied unchanged.
- `scripts/sources.py` from `trailofbits/skills/plugins/supply-chain-risk-auditor/skills/supply-chain-risk-auditor/scripts/sources.py`: Copied unchanged.

## Runtime requirements

- Python >=3.11 and uv; bundled scripts are stdlib-only
- Authenticated gh strongly recommended for GitHub rate limits; collector can return unassessable without it
- Network to OSV, npm/PyPI registries, Go module proxy, deps.dev, OpenSSF Scorecard and GitHub
- Optional pip-audit integration detected by source; no project/package installation by collector
- Run documented uv commands from the skill package directory; Python >=3.11 is declared by the scripts’ inline PEP 723 metadata.

## Unresolved native integration requirements

- Requires an actual script execution environment, uv/Python3.11+, target manifests and network API access. Never replace script measurements with model estimates.

Native frontmatter is retained. Preserving it does not establish platform enforcement:

```json
{
  "allowed-tools": "Read Write Bash Glob Grep"
}
```

## Installed names

References to original skill names can be resolved using this table. Native API/command identifiers and persistent project-state filenames remain unchanged.

| Original source and name | Installed name |
| --- | --- |
| trailofbits/skills/plugins/supply-chain-risk-auditor/skills/supply-chain-risk-auditor | `supply-chain-risk-auditor` |
| trailofbits/skills/plugins/differential-review/skills/differential-review | `code-change-security-review` |

This package has not been executed or benchmarked. Static package validation does not provision accounts, tools, native dispatch or persistent storage.
