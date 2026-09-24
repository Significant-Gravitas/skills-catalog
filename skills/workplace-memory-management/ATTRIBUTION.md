# Attribution: workplace-memory-management

Original skill: `memory-management`.
Original author: Anthropic and upstream contributors
Source: https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/productivity/skills/memory-management/SKILL.md
Pinned commit: `1c7187c4fc17feefa6cde39517f12dae1249e6c4`.
Licence: Apache-2.0; see LICENSE. Existing copyright and notice terms remain applicable.

AutoGPT adapted the packaging on 2026-09-25. AutoGPT did not author the original expert guidance. All original bytes, hashes and exact edits are retained in the catalog repository provenance records.

## Recorded changes

- `SKILL.md` from `anthropics/knowledge-work-plugins/productivity/skills/memory-management/SKILL.md`: Explicitly load original local companion/configuration guidance without assuming native plugin autoload or registering commands.; Use the clear installed name, standard licence and string-valued attribution metadata; preserve all other upstream fields and body. Normalize equivalent tool-list separators where required.; Identify adapted files while retaining upstream authorship and licence.
- `LICENSE` from `anthropics/knowledge-work-plugins/productivity/LICENSE`: Copied unchanged.
- `references/task-management.md` from `anthropics/knowledge-work-plugins/productivity/skills/task-management/SKILL.md`: Resolve the same dashboard file from the package directory rather than an unavailable native plugin-root variable.; Identify adapted files while retaining upstream authorship and licence.
- `references/start.md` from `anthropics/knowledge-work-plugins/productivity/skills/start/SKILL.md`: Relocate original connector-category reference inside this package.; Use the original task template bundled inside this package.; Resolve the same dashboard file from the package directory rather than an unavailable native plugin-root variable.; Identify adapted files while retaining upstream authorship and licence.
- `references/update.md` from `anthropics/knowledge-work-plugins/productivity/skills/update/SKILL.md`: Relocate original connector-category reference inside this package.; Identify adapted files while retaining upstream authorship and licence.
- `assets/dashboard.html` from `anthropics/knowledge-work-plugins/productivity/skills/dashboard.html`: Copied unchanged.
- `references/CONNECTORS.md` from `anthropics/knowledge-work-plugins/productivity/CONNECTORS.md`: The original native plugin configuration is optional upstream setup documentation, not an installed local manifest.; Identify adapted files while retaining upstream authorship and licence.

## Runtime requirements

- Writable persistent TASKS.md,CLAUDE.md,memory folder; user can open dashboard in a browser supporting File System Access APIs.
- Original optional connectors for tracker/chat/email/calendar/docs; normal provisioning only,no dispatch wrappers or instruction overrides.
- A stable shared working directory for TASKS.md, CLAUDE.md and memory/ that all four workflows use across sessions.
- Ability to deliver/open dashboard.html in a browser with File System Access APIs against those same persistent files.
- Use bundled sibling documents as instructions; no /productivity:* command handler is installed by this recipe.

## Unresolved native integration requirements

- The inspected platform drops user-invocable:false. Preserve this flag and require an explicit runtime/background-loading decision; packaging alone does not implement it.
- The dashboard/browser and agent must access the same persistent task/memory files. Source relocation cannot provide that filesystem/UI integration.

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
| anthropics/knowledge-work-plugins/customer-support/skills/customer-research | `customer-support-research` |
| anthropics/knowledge-work-plugins/customer-support/skills/draft-response | `customer-response-drafting` |
| anthropics/knowledge-work-plugins/customer-support/skills/customer-escalation | `customer-escalation` |
| anthropics/knowledge-work-plugins/finance/skills/reconciliation | `account-reconciliation` |
| anthropics/knowledge-work-plugins/finance/skills/close-management | `month-end-close-management` |
| anthropics/knowledge-work-plugins/finance/skills/financial-statements | `financial-statement-preparation` |
| anthropics/knowledge-work-plugins/small-business/skills/invoice-chase | `overdue-invoice-follow-up` |
| anthropics/knowledge-work-plugins/operations/skills/vendor-review | `vendor-evaluation` |
| anthropics/knowledge-work-plugins/legal/skills/vendor-check | `vendor-contract-status` |
| anthropics/knowledge-work-plugins/enterprise-search/skills/knowledge-synthesis | `multi-source-research-synthesis` |
| anthropics/knowledge-work-plugins/operations/skills/status-report | `project-status-report` |
| anthropics/knowledge-work-plugins/operations/skills/risk-assessment | `operational-risk-assessment` |
| anthropics/knowledge-work-plugins/legal/skills/meeting-briefing | `legal-meeting-briefing` |
| anthropics/knowledge-work-plugins/productivity/skills/task-management | `task-list-management` |
| anthropics/knowledge-work-plugins/productivity/skills/memory-management | `workplace-memory-management` |
| anthropics/knowledge-work-plugins/productivity/skills/start | `productivity-setup` |
| anthropics/knowledge-work-plugins/productivity/skills/update | `productivity-task-sync` |
| anthropics/knowledge-work-plugins/data/skills/explore-data | `dataset-exploration` |
| anthropics/knowledge-work-plugins/data/skills/data-visualization | `data-visualization` |
| anthropics/knowledge-work-plugins/sales/skills/pipeline-review | `sales-pipeline-review` |
| anthropics/knowledge-work-plugins/human-resources/skills/interview-prep | `candidate-interview-planning` |
| anthropics/knowledge-work-plugins/human-resources/skills/draft-offer | `employment-offer-drafting` |
| anthropics/knowledge-work-plugins/human-resources/skills/recruiting-pipeline | `recruiting-pipeline` |
| anthropics/knowledge-work-plugins/sales/skills/account-research | `sales-account-research` |
| anthropics/knowledge-work-plugins/sales/skills/draft-outreach | `sales-outreach-drafting` |
| anthropics/knowledge-work-plugins/sales/skills/call-prep | `sales-call-preparation` |

This package has not been executed or benchmarked. Static package validation does not provision accounts, tools, native dispatch or persistent storage.
