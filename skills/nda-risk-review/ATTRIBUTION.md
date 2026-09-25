# Attribution: nda-risk-review

Original skill: `nda-review`.
Original author: Anthropic and upstream contributors
Source: https://github.com/anthropics/claude-for-legal/blob/4a6c651889c97cc9140580363c73e0eb17379c2b/commercial-legal/skills/nda-review/SKILL.md
Pinned commit: `4a6c651889c97cc9140580363c73e0eb17379c2b`.
Licence: Apache-2.0; see LICENSE. Existing copyright and notice terms remain applicable.

AutoGPT adapted the packaging on 2026-09-25. AutoGPT did not author the original expert guidance. All original bytes, hashes and exact edits are retained in the catalog repository provenance records.

## Recorded changes

- `SKILL.md` from `anthropics/claude-for-legal/commercial-legal/skills/nda-review/SKILL.md`: Explicitly load original local companion/configuration guidance without assuming native plugin autoload or registering commands.; Use the clear installed name, standard licence and string-valued attribution metadata; preserve all other upstream fields and body. Normalize equivalent tool-list separators where required.; Identify adapted files while retaining upstream authorship and licence.
- `LICENSE` from `anthropics/claude-for-legal/LICENSE`: Copied unchanged.
- `references/practice-profile-template.md` from `anthropics/claude-for-legal/commercial-legal/CLAUDE.md`: Resolve the relocated practice guide’s sibling dashboard template.; Identify adapted files while retaining upstream authorship and licence.
- `references/company-profile-template.md` from `anthropics/claude-for-legal/references/company-profile-template.md`: Copied unchanged.
- `references/dashboard-template.md` from `anthropics/claude-for-legal/references/dashboard-template.md`: Copied unchanged.

## Runtime requirements

- An attorney-reviewed side-specific NDA playbook and configured legal approvers; uploaded contract text/files
- Runtime must support loading a native reference skill; upstream /commercial-legal:review is its usual dispatcher
- Optional CLM for native record-creation offers; no CLM required for document triage

## Unresolved native integration requirements

- The inspected platform drops user-invocable:false. Preserve this flag and require an explicit runtime/background-loading decision; packaging alone does not implement it.
- Requires a populated persistent practice/company profile with the original setup and attorney-review gates. Packaging cannot invent legal positions or configured approvers.
- Preserve matter isolation and native setup/dispatch expectations; no hidden config source file is installed by this flat package.

Native frontmatter is retained. Preserving it does not establish platform enforcement:

```json
{
  "user-invocable": false
}
```

## Installed names

References to original skill names can be resolved using this table. Native API/command identifiers and persistent project-state filenames remain unchanged.

| Original source and name | Installed name |
| --- | --- |
| anthropics/claude-for-legal/commercial-legal/skills/nda-review | `nda-risk-review` |
| anthropics/claude-for-legal/commercial-legal/skills/amendment-history | `contract-amendment-history` |

This package has not been executed or benchmarked. Static package validation does not provision accounts, tools, native dispatch or persistent storage.
