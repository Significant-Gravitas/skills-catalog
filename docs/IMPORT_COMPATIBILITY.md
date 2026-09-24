# Import compatibility and publication requirements

**This schema-version-2 catalogue is incompatible with the inspected AutoGPT importer. Keep this PR in draft and do not seed it into production until the platform follow-up supports this format and its migration has been reviewed.** Passing this repository's source-integrity checks establishes preservation of the upstream files; it does not establish that the current platform can import, install or run them unchanged.

The catalogue contains 43 selected upstream skills, with core and conditional status recorded separately. Sources retain their original names, frontmatter, instructions and supporting content under `skills/<owner>/<repo>/<upstream-path>`. Catalogue identity, source paths, licences and provenance are external metadata. No upstream instruction changes or corrective wrappers are part of this change. Conditional status does not mean a skill's service accounts, tools, native configuration or runtime have been provisioned.

## Importer blockers

| Concern | Inspected platform behavior | Follow-up requirement |
| --- | --- | --- |
| Schema and source paths | `load_catalog` reads only `slug`, `categories` and `required_providers`. `_load` requires `skills/<slug>/SKILL.md`; it does not read the new source-path or provenance fields. | Explicitly recognize schema version 2, resolve its primary source paths and reject unsupported schema versions before writes. |
| Identity and original names | `_load` requires the parsed upstream name to equal the catalogue slug. Workspace storage also uses the parsed name as the package identity. | Keep a unique catalogue/install identity separate from the original upstream name. Do not resolve collisions by editing SKILL.md. |
| Duplicate names | Corey Haines's marketing skill and Anthropic's customer-support skill both have the original name `customer-research`. | Retain both sources and define unambiguous listing, installation and runtime lookup behavior. A listing-only alias does not resolve a workspace collision by itself. |
| Attribution and licence fields | `_upsert_version` obtains `sourceRepo`, `sourceUrl` and `license` from parsed SKILL.md frontmatter. It does not consume the catalogue's scalar `license` or source/provenance records. Listings created by this seed have no upstream owning account assigned. | Populate upstream attribution, source revision and licence from the catalogue/provenance sidecars without adding them to or rewriting upstream SKILL.md. Verify how the UI represents publisher versus original author. |
| Original bytes and metadata | The skill parser carries only a limited set of extra frontmatter fields. Its renderer serializes YAML again and trims body whitespace. The seed stores parsed fields rather than the original complete SKILL.md. | Preserve original bytes and authored metadata across import, version storage, export and installation. Test the full round trip against the pinned hashes. |
| Relative support paths | Runtime activation materializes supplementary files inside a single `skills/<name>` package and directs relative paths there. It has no selected source-root/primary-path model. | Preserve the authored source hierarchy within an explicit package root, including shared resources and selected sibling dependencies. Validate containment after resolving relative paths. |
| Native plugin behavior | Copying plugin metadata does not provide plugin-root variables, namespaced command dispatch, service accounts or user configuration. | Verify native runtime support and prerequisites. Keep conditional options unavailable until their requirements are met; do not substitute instruction overrides. |

The metadata issue affects **19 of the 43 primary sources**: 13 have `argument-hint` and six have `user-invocable`. The six sources whose `user-invocable` setting must survive are `close-management`, `knowledge-synthesis`, `task-management`, `memory-management`, `data-visualization` and `nda-review`. An unchanged source snapshot alone does not establish that the runtime honors these fields.

The inspected parser carries `license`, `compatibility`, `allowed-tools`, `metadata`, `source` and `source_url`, in addition to its core fields. Preservation of a field is separate from implementing its behavior.

## Licences, provenance and package limits

A plain `LICENSE` file is already supported as an ordinary supplementary package file. The same is true of ordinary files such as `NOTICE`, `ATTRIBUTION.md` or `PROVENANCE.json` when their paths satisfy validation. Their presence does not automatically fill marketplace licence or attribution fields. They count toward the existing supplementary-file and byte limits.

The inspected platform limits are:

| Limit | Value |
| --- | --- |
| Supplementary files per skill | 100, excluding only the primary root SKILL.md |
| Bytes per supplementary file | 2 MiB |
| Total package bytes | 20 MiB, including the primary SKILL.md |
| Path depth | 8 segments |
| Skill name | 64 characters |
| Description | 1,024 characters |
| Instruction body | 50,000 characters |
| Triggers | 10, each at most 64 characters |

Hidden path segments, symlinks and paths that escape the package are rejected. Plugin files such as `.mcp.json` and `.claude-plugin/plugin.json` therefore cannot be included unchanged in a package accepted by the current validator. The 43 inspected primary SKILL.md files are each at most 20,386 bytes, so their instruction bodies are below the body cap. This is not a blanket claim that every complete supporting package satisfies the other limits.

Preserve the exact applicable upstream licence and any required notices. An intermediate plugin licence may be the applicable source; searching only the skill directory and repository root is insufficient. Trail of Bits sources retain their CC-BY-SA-4.0 attribution and applicable share-alike terms. Catalogue metadata and the presence of a licence file do not change the upstream grant.

Keep provenance durable in this repository: record the original repository/path, full immutable commit, source URL, applicable licence source, authorship and source checksums outside the original instructions. Preserve file bytes and executable modes when committing. Git line-ending conversion must not silently change vendored source; check committed blobs against the pinned source hashes as well as checking working-tree files.

## Supporting-source layout

Retain the original hierarchy beneath each `skills/<owner>/<repo>/` root. The source-path metadata identifies the selected primary files. This repository contains exactly the 43 selected SKILL.md files; upstream README and plugin metadata may mention other skills that are omitted. Only the explicit catalogue entries are selected for registration.

| Source group | Layout and runtime requirements |
| --- | --- |
| Corey Haines marketing | Retain each selected `skills/<name>/` directory and repository-level `tools/` paths. For example, `emails` uses `../../tools/`. The inspected complete `tools/` directory has 164 files before counting skill files and licences, exceeding the existing per-skill supplementary-file cap. Keep shared source once; define how a future importer materializes the needed original paths. |
| Anthropic standard plugins | Retain `plugin/skills/<name>/`, plugin-local `CONNECTORS.md` and the applicable plugin licence. References to `../../CONNECTORS.md` depend on this hierarchy. |
| Invoice chase | Retain the complete `small-business/skills/invoice-chase/` directory and original `small-business/shared/` tree. The inspected shared tree has 15 files. Its native voice/business state, output delivery and optional connectors are runtime prerequisites. |
| Operations status reporting | Keep `status-report` and the selected `risk-assessment` sibling available, together with `operations/CONNECTORS.md`. |
| Productivity | Retain the complete original plugin, all four selected skills and `skills/dashboard.html`. Native `CLAUDE_PLUGIN_ROOT`, command dispatch, persistent files and browser support remain required. The original plugin has hidden metadata paths rejected by the current package validator. |
| Commercial legal | Retain `commercial-legal/CLAUDE.md` and original plugin support. User-specific practice configuration requires setup before substantive work. The native `/commercial-legal:review` dispatcher is an unselected skill and is **not supplied**; `nda-review` remains background/reference guidance. The pinned parent instructions describe plugin-root references, while the repository stores templates at repository-root `references/`; that upstream/runtime ambiguity remains unchanged. The consumer must resolve native loading/configuration without rewriting source or inventing a corrective wrapper. |
| Supply-chain risk auditor | Keep all original scripts beside SKILL.md. Its commands depend on native `{baseDir}/scripts/...` resolution, `uv`, Python 3.11+ and the documented external data sources. |
| Differential review | Preserve the plugin hierarchy, its methodology/reporting/pattern references and optional agents. The source's manual fallback is already authored behavior; no substitute wrapper is needed or proposed. |
| OpenSEO | Preserve both selected skills and the original plugin/MCP metadata. OpenSEO account, service and tool availability remain independent prerequisites. |
| Board deck builder | Keep original references and templates beside SKILL.md. A rendering tool is separate from the authored content workflow. |

The legacy catalogue validator is not an exact model of the platform: it rejects every Markdown link beginning with `../`, even if the resolved target would remain inside a larger original package. It also excludes every nested file named SKILL.md from its package accounting; the platform excludes only the package's primary root file. Schema-version-2 validation must distinguish source preservation from current importer compatibility and count all registered package members accurately.

The legacy `tools/vendor.py` workflow is also unsuitable for this catalogue: it downloads HEAD, rewrites frontmatter and Markdown, removes selected sections and relative tool references, skips hidden/test/evaluation files, and searches only limited licence locations. The replacement workflow must use the recorded immutable revisions and copy exact source bytes.

## Production replacement needs a separate migration

Replacing this repository's entries does not by itself replace the production marketplace or experts' installed skills.

The inspected normal seed run appends checked-in `STARTER_SKILLS` whose slugs are missing from the catalogue. Passing an explicit `catalog_dir` to the Python function avoids that fallback, but still does not retire other omitted listings. The seed only delists its explicit `RETIRED_STARTER_SLUGS` list, which contained `blake-getting-started` when inspected. Previously installed copies also remain separate from catalogue changes.

The platform follow-up must therefore define and review:

1. Schema-version-2 import, identity, attribution and exact-byte storage/install behavior.
2. Original support-path materialization and native runtime prerequisites, including conditional availability.
3. An explicit mapping/migration for the intended expert assignments and retirement of superseded catalogue listings.
4. Treatment of existing user installations, which this catalogue PR does not delete or rewrite.
5. Validation in a non-production environment before any production seed or migration.

These platform changes and production migration are **outside this catalogue PR**. Do not treat a successful catalogue check or merge as authorization or evidence that production publication has occurred.

## Inspection record

Captured on **2026-09-24**. These are Git **blob** identifiers returned for the inspected files, not repository commit identifiers. The URLs below identify their paths on the branch read; use the recorded blob hashes to distinguish this review from later file revisions.

| File | Inspected identity | Relevant locations |
| --- | --- | --- |
| [AutoGPT skill seed](https://github.com/Significant-Gravitas/AutoGPT/blob/master/autogpt_platform/backend/backend/api/features/store/skill_seed.py) | Blob `05014f04317b1a820a0df6db89c4de515d80f68f` | Fallback/retirement: lines 1265–1352; catalogue fields: 1355–1403; attribution/version storage: 1446–1501; source loading/package files: 1504–1566. |
| [AutoGPT skill parser, validator and runtime](https://github.com/Significant-Gravitas/AutoGPT/blob/master/autogpt_platform/backend/backend/copilot/tools/skills.py) | Blob `0425ccea6aeea1e805d9874e0e3f2c08f41a5497` | Carried fields and rendering: lines 214–306; content validation: 309–348; package rules: 463–575; workspace writes: 931–998; activation/materialization: 2139–2178 and 2484 onward. |
| [Legacy catalogue check](https://github.com/Significant-Gravitas/skills-catalog/blob/00d9cfbf2c9c01a13dc5626a50e8f4b9c4d2d35d/tools/check.py) | Catalogue commit `00d9cfbf2c9c01a13dc5626a50e8f4b9c4d2d35d` | Flat layout/name checks, link rejection and supplementary-file accounting. |
| [Legacy vendor workflow](https://github.com/Significant-Gravitas/skills-catalog/blob/00d9cfbf2c9c01a13dc5626a50e8f4b9c4d2d35d/tools/vendor.py) | Catalogue commit `00d9cfbf2c9c01a13dc5626a50e8f4b9c4d2d35d` | HEAD fetching, source rewriting, file exclusions and licence discovery. |

This was a static code and source-layout review. No platform seed, installation, upstream skill execution or production change was performed as part of it.
