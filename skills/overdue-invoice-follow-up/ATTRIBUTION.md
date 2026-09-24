# Attribution: overdue-invoice-follow-up

Original skill: `invoice-chase`.
Original author: Anthropic and upstream contributors
Source: https://github.com/anthropics/knowledge-work-plugins/blob/1c7187c4fc17feefa6cde39517f12dae1249e6c4/small-business/skills/invoice-chase/SKILL.md
Pinned commit: `1c7187c4fc17feefa6cde39517f12dae1249e6c4`.
Licence: Apache-2.0; see LICENSE. Existing copyright and notice terms remain applicable.

AutoGPT adapted the packaging on 2026-09-25. AutoGPT did not author the original expert guidance. All original bytes, hashes and exact edits are retained in the catalog repository provenance records.

## Recorded changes

- `SKILL.md` from `anthropics/knowledge-work-plugins/small-business/skills/invoice-chase/SKILL.md`: Move direct shared-resource references into this package.; Use the clear installed name, standard licence and string-valued attribution metadata; preserve all other upstream fields and body. Normalize equivalent tool-list separators where required.; Identify adapted files while retaining upstream authorship and licence.
- `LICENSE` from `anthropics/knowledge-work-plugins/LICENSE`: Copied unchanged.
- `reference/examples/firm-reminder.md` from `anthropics/knowledge-work-plugins/small-business/skills/invoice-chase/reference/examples/firm-reminder.md`: Copied unchanged.
- `reference/examples/gentle-reminder.md` from `anthropics/knowledge-work-plugins/small-business/skills/invoice-chase/reference/examples/gentle-reminder.md`: Copied unchanged.
- `reference/gotchas.md` from `anthropics/knowledge-work-plugins/small-business/skills/invoice-chase/reference/gotchas.md`: Copied unchanged.
- `reference/tone-matching.md` from `anthropics/knowledge-work-plugins/small-business/skills/invoice-chase/reference/tone-matching.md`: Copied unchanged.
- `reference/v2_sources.md` from `anthropics/knowledge-work-plugins/small-business/skills/invoice-chase/reference/v2_sources.md`: Move the reference document’s shared-resource links inside this package.; Identify adapted files while retaining upstream authorship and licence.
- `shared/tenant-scope.md` from `anthropics/knowledge-work-plugins/small-business/shared/tenant-scope.md`: Copied unchanged.
- `shared/connector-neutrality.md` from `anthropics/knowledge-work-plugins/small-business/shared/connector-neutrality.md`: Correct a moved shared document’s sibling resource path.; Identify adapted files while retaining upstream authorship and licence.
- `shared/currency-and-locale.md` from `anthropics/knowledge-work-plugins/small-business/shared/currency-and-locale.md`: Optional full onboarding reference stays upstream; the required locale fields and missing-context fallback are already reproduced inline.; Identify adapted files while retaining upstream authorship and licence.
- `shared/untrusted-content.md` from `anthropics/knowledge-work-plugins/small-business/shared/untrusted-content.md`: Copied unchanged.
- `shared/connector-call-shapes.md` from `anthropics/knowledge-work-plugins/small-business/shared/connector-call-shapes.md`: Copied unchanged.
- `shared/voice-profile.md` from `anthropics/knowledge-work-plugins/small-business/shared/voice-profile.md`: Update documented SKILL.md-to-resource example for the flat package layout.; Identify adapted files while retaining upstream authorship and licence.
- `shared/artifact-style.md` from `anthropics/knowledge-work-plugins/small-business/shared/artifact-style.md`: Update documented SKILL.md-to-resource example for the flat package layout.; Correct a moved shared document’s sibling resource path.; Identify adapted files while retaining upstream authorship and licence.
- `shared/quickbooks-report-traps.md` from `anthropics/knowledge-work-plugins/small-business/shared/quickbooks-report-traps.md`: Copied unchanged.
- `shared/gmail-inbox-traps.md` from `anthropics/knowledge-work-plugins/small-business/shared/gmail-inbox-traps.md`: Copied unchanged.
- `shared/reference/artifact-example.html` from `anthropics/knowledge-work-plugins/small-business/shared/reference/artifact-example.html`: Correct the moved example’s locale-rule reference.; Identify adapted files while retaining upstream authorship and licence.

## Runtime requirements

- AR aging and payment history or original CSV upload/manual-send fallback.
- Optional supported ledger,processor,mail connectors and output artifact capability; context/voice/output preferences supplied normally.
- Upstream optional adjacent-skill offers (plan-payroll,cash-flow-snapshot,close-month,build-connector) are not part of this curated kit; those separate functions remain unavailable unless supplied unchanged and independently assessed.
- Native persistent business profile/shared state and artifact delivery; upstream owner approval applies to draft queues as well as actual sends.
- Persistent owner Business context and voice profile; updates must survive sessions and package re-materialization.
- Actual mail/ledger/payment connectors only for connected actions; owner approval for queued drafts and sends remains unchanged.
- The authored visual-artifact/publishing or user-selected output delivery capability.

Native frontmatter is retained. Preserving it does not establish platform enforcement:

```json
{
  "version": "0.3.0",
  "allowed-tools": "Read, WebFetch"
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
