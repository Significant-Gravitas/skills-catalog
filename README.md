# AutoGPT skills catalog

43 selected upstream skills, preserved exactly as authored, with supporting files,
original attribution, pinned commits and licences. This replaces the previous
171-entry catalog. AutoGPT curates the collection; the skill authors remain the
upstream authors.

**Catalog schema v2 is not compatible with the current AutoGPT platform importer.
Do not run a production seed against this revision.** See
[import compatibility](docs/IMPORT_COMPATIBILITY.md) for required platform changes,
including original names/paths, metadata, attribution and retirement of previous
listings. Repository checks do not establish runtime or importer compatibility.

## Selections

[SELECTIONS.md](SELECTIONS.md) lists every skill, its function, author, licence and
proposed expert assignments. There are 36 core selections (45 expert assignments)
and seven conditional sources. Conditional sources need the recorded native
service, runtime or specialist context. Max and Frankie had no original skills;
their proposed assignments are optional additions.

Research captured 24 September 2026. Every candidate has individual installation
evidence. Counts are telemetry, not unique users or proven outcomes. Three niche
choices have smaller adoption: amendment-history (566), board-deck-builder (603)
and nda-review (643). seo-report (368) is only the required companion to the
conditional OpenSEO audit. No skill was executed or benchmarked during curation.

## Layout

```
catalog.yml                         unique registry IDs, original names and paths
skills/<owner>/<repo>/...            unchanged upstream tree-relative files
skills/.../<skill>/SKILL.md          original instructions, never rewritten
skills/.../<skill>/LICENSE           exact controlling licence copy
provenance/files.json                source commit, path, hashes and mode per file
provenance/skills/<slug>.json         attribution, evidence, licence and review
provenance/evidence.json             dated observations and source-response hashes
provenance/replaced-catalog.json     previous registry entries for migration
```

Only the 43 selected SKILL.md files are included. Shared support is stored once,
with original relative paths. Upstream README/plugin metadata may mention skills
that are not selected or supplied. These trees are not complete plugin installs;
do not automatically register every command or metadata file.

`slug` is a unique catalog identity; `name` is the unchanged upstream name. Corey
and Anthropic both use customer-research, so their registration IDs differ while
both retain their original names. `path` points to the original skill folder.
`package_root` identifies its upstream tree, not a request to bundle every shared
file into every skill. The platform needs shared-source/dependency support.

## Provenance and licensing

Every original file records its repository, full commit, original path, Git blob
SHA-1, SHA-256 and executable mode. Adjacent licence copies identify their actual
upstream source path. Source bytes are preserved with Git newline conversion off.
Per-skill sidecars contain authorship, licence scope/obligations, adoption/activity
evidence, review limitations and native prerequisites, without changing skill text.

Evidence records preserve factual observations, source URLs, capture dates and
hashes of original responses. They do not republish whole third-party web pages
or claim certified timestamps. The checksum of the separate complete local
research archive is recorded; that archive retains the full source responses.

Preserve MIT/Apache licence and applicable notices. The two Trail of Bits skills
retain CC-BY-SA-4.0 attribution and recipients' licence rights; do not impose
proprietary-only restrictions on that material. Services, third-party linked
content and trademarks have separate terms. No endorsement or human-only
upstream authorship is claimed.

Seven selections inherit an Anthropic root Apache licence with unexplained
appended text: the three human-resources skills, invoice-chase, vendor-review,
risk-assessment and status-report. The exact text is preserved; research found no
additional commercial restriction. Resolve that anomaly before commercial release.
Other plugin-local licences are retained separately.

## Verify and restore

Use Python 3.12 and PyYAML:

```sh
python -m pip install pyyaml
python tools/check.py --expected-count 43
python -m unittest discover -s tools -p 'test_*.py'
python tools/vendor.py --check
python tools/vendor.py --fetch
```

The checker validates catalog/provenance consistency and unchanged source bytes;
it does not claim parity with the old platform importer. The vendor tool restores
missing files from recorded immutable URLs, verifies responses before writing,
and refuses to overwrite mismatched existing content. It never fetches HEAD,
rewrites frontmatter, trims Markdown or strips sections. Revision/selection changes
require a new reviewed manifest and source update.

## Why vendored files rather than submodules?

Submodules pin whole repositories, not chosen skill folders. They require recursive
checkout and their content is absent from ordinary GitHub source tarballs, which
the existing platform seed downloads. Vendored immutable files keep the selected
source, licences and provenance visible in one PR and ordinary clone/tarball.
Commit pins and hashes provide traceability without following upstream updates.

## Publishing

This repository change does not remove database listings or update expert
assignments. Importer support, explicit listing retirement, expert reassignment
and end-to-end runtime checks remain separate prerequisites documented in
[import compatibility](docs/IMPORT_COMPATIBILITY.md).
