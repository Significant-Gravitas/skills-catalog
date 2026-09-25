# Attribution: customer-response-drafting

Original skill: `draft-response`.
Original author: Anthropic / upstream contributors; retain Apache-2.0 and applicable notices.
Source: https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/customer-support/skills/draft-response/SKILL.md
Pinned commit: `1c7187c4fc17feefa6cde39517f12dae1249e6c4`.
Licence: Apache-2.0; see LICENSE. Existing copyright and notice terms remain applicable.

AutoGPT adapted the packaging on 2026-09-25. AutoGPT did not author the original expert guidance. All original bytes, hashes and exact edits are retained in the catalog repository provenance records.

## Recorded changes

- `SKILL.md` from `anthropics/knowledge-work-plugins/customer-support/skills/draft-response/SKILL.md`: Relocate original connector-category reference inside this package.; Use the clear installed name, standard licence and string-valued attribution metadata; preserve all other upstream fields and body. Normalize equivalent tool-list separators where required.; Identify adapted files while retaining upstream authorship and licence.
- `LICENSE` from `anthropics/knowledge-work-plugins/customer-support/LICENSE`: Copied unchanged.
- `references/CONNECTORS.md` from `anthropics/knowledge-work-plugins/customer-support/CONNECTORS.md`: The original native plugin configuration is optional upstream setup documentation, not an installed local manifest.; Identify adapted files while retaining upstream authorship and licence.

## Runtime requirements

- Use the author-defined tool categories for connected CRM/support/knowledge/email/chat sources; supply accessible records and actual account context. No placeholder text replacement is required.

Native frontmatter is retained. Preserving it does not establish platform enforcement:

```json
{
  "argument-hint": "<situation description>"
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
