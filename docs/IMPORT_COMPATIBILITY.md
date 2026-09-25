# Import compatibility and remaining runtime work

The catalog uses the existing `catalog.yml` structure and
`skills/<slug>/SKILL.md` paths. Each declared name matches its folder and slug.
All 74 packages pass the inspected platform's exact file-loading, content and
package validators in the isolated probe. The earlier custom version-two import
layout has been removed. No platform support for that custom layout is needed.

## What packaging now solves

| Concern | Current catalog behavior |
| --- | --- |
| Paths and names | Flat, unique, descriptive skill directories match the existing importer. |
| Shared supporting files | Required references, scripts and templates are bundled inside each individual package; local paths are updated. |
| Source and licence labels | Standard frontmatter contains `license`, `metadata.source` and `metadata.source_url`, which the existing seed reads. Original authors are identified in metadata and ATTRIBUTION.md. |
| Licence files | Every package carries its exact controlling LICENSE. This is already supported as an ordinary supplementary file. |
| Package limits | All 74 fit the inspected limits; the largest contains 11 supplementary files. Hidden plugin config files are not packaged as if the runtime could load them. |
| Source preservation | Original bytes remain in the provenance archive. Installed files are explicitly labelled adaptations and reproducible from recorded edits. Exact original formatting is not a runtime requirement. |

## What packaging cannot provide

**Keep this PR in draft until the required runtime decisions and publication
checks are complete. Import acceptance is not execution or deployment.**

- The seed stores selected parsed fields, not every original field. The exact parser/renderer drops `argument-hint` in 28 packages and `user-invocable` in 6. Native fields remain in this repo. The seed also omits some extra parsed fields, including tool restrictions; parser rendering is not a database persistence test.
- Packages with `user-invocable: false` are `data-visualization`, `month-end-close-management`, `multi-source-research-synthesis`, `nda-risk-review`, `task-list-management`, `workplace-memory-management`. Their background/reference behavior needs a platform decision; do not silently make them user-invocable.
- OpenSEO needs its actual service connection, credits, live research tools and
  report persistence. Both selected workflows/guidance are packaged, but files
  cannot create an authenticated service. Its API identifiers remain unchanged.
- Productivity needs shared persistent task/memory state and a browser that can
  read/write the dashboard's files. Guidance and dashboard assets are local;
  namespaced native commands have not been registered by copying these files.
- Legal workflows require the real populated practice/company profiles and
  original setup/approver gates. The original guardrail template is explicitly
  referenced; it is not a configured profile. Native setup/review/matter dispatch
  remains an integration requirement. No default legal positions are invented.
- The supply-chain auditor needs actual Python/uv execution, target manifests
  and network access to its documented data sources. Other skills may need
  connected CRM, email, accounting or document sources as recorded individually.
- Original author metadata is present, but the seed still creates platform-owned
  listings. Verify the marketplace's publisher-versus-original-author display.

These are concrete requirements, not a proposal for a new catalog architecture.
Full per-package prerequisites and dependency review decisions are preserved in
`provenance/skills/` and `provenance/dependency-review.json`.

## Production replacement

Removing old repo entries does not remove existing database listings. The normal
seed appends missing checked-in `STARTER_SKILLS`, and omission from the catalog
does not retire a listing. An explicit `catalog_dir` avoids the fallback but
still does not retire old listings. A separate migration must replace/retire
the intended placeholder listings and update expert assignments. Existing users'
installed copies must not be deleted as a side effect. The original 171-entry
catalog is recorded in `provenance/replaced-catalog.json` for that migration.

## Verification record and reproducibility

The fresh source inspection on 2026-09-25 found the same Git blobs as the prior
review:

| Source | Git blob |
| --- | --- |
| [skill_seed.py](https://github.com/Significant-Gravitas/AutoGPT/blob/master/autogpt_platform/backend/backend/api/features/store/skill_seed.py) | `05014f04317b1a820a0df6db89c4de515d80f68f` |
| [skills.py](https://github.com/Significant-Gravitas/AutoGPT/blob/master/autogpt_platform/backend/backend/copilot/tools/skills.py) | `0425ccea6aeea1e805d9874e0e3f2c08f41a5497` |

These are file/blob identities, not repository commits. Retrieve those exact
blobs with the GitHub Git Blobs API (or use saved copies); the probe refuses a
different source revision before executing its selected definitions:

```
python -m pip install pyyaml pydantic
python tools/probe_importer.py --seed-source /path/to/skill_seed.py --skills-source /path/to/skills.py --output docs/current-importer-probe.json
```

The probe executes only AST-selected loader/parser/validator/attribution helpers
and their data models/constants. Category validation uses the documented eight
canonical categories; the builtin lookup supplies `agent_building_guide`.
It never imports platform services, writes a database, installs a skill or
executes upstream skill scripts. [current-importer-probe.json](current-importer-probe.json)
records the 74 acceptances, source hashes and the fields lost by parser rendering.
The repository checker separately validates original and adapted file hashes,
transformation replay, evidence binding, licence files and package limits.

The dependency audit checks literal Markdown links, reports candidate file
references/imports, and records unresolved dynamic/native cases. It cannot prove
all dependencies in natural-language instructions, conditional branches or APIs.
Those decisions require documented source review; it must never silently prune
a required dependency just because a scanner did not find it.

## Expanded roster and deferred sources

The pinned seed defines 32 experts and 321 assignments. The initial live capture had 15 experts; Max had no installed skills there but has 37 seed-only skills. The [complete coverage ledger](EXPERT_COVERAGE.md) distinguishes reviewed coverage, partial matches, gaps, onboarding and initial broader role kits. A listed research match is not automatically an enabled production capability.

The 34-skill advertising suite exceeds the supplementary-file cap before its full native validation dependencies are included. Prospecting awaits a fix for its unchanged CSV exporter. Invoice chase awaits licence clarification. All 40 remain outside the installable catalog with their originals and evidence retained. Six other packages now use complete clean historical pins; no old licence is attached to later source files.

The incident-response workflow includes a crisis-escalation guardrail template. Triage, competitor research and other conditional workflows retain their actual service, configuration and data-source requirements. Packaging the template does not configure or authorize production incident actions.

Public-relations, referrals and marketing-plan are also deferred because their required references contain contradictory scoring or unresolved numerical assumptions. Marketing-ideas remains with its deferred parent; parent-level usage does not qualify it independently. These originals and all applicable third-party notices are retained without corrective edits.
