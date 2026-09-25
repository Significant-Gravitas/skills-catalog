# AutoGPT skills catalog

74 reviewed community skill packages in the established Agent Skills format. This replaces all 171 previous catalog entries. The full seeded roster is accounted for: 32 experts and 321 original assignments. The initial live production inventory contained 15 experts; the larger number describes the code seed.

The exact current importer accepts all 74 packages in isolation. **This remains a draft: runtime integration, expert reassignment and production migration have not been performed.**

- [Every selected skill, function, author, source and licence](SELECTIONS.md)
- [Every expert and all 321 original assignments, including gaps](docs/EXPERT_COVERAGE.md)
- [40 deferred sources and reasons](docs/DEFERRED_SKILLS.md)
- [Import acceptance and remaining runtime work](docs/IMPORT_COMPATIBILITY.md)

## Standard packages

```
skills/<clear-unique-name>/
  SKILL.md          standard YAML and original instructions
  LICENSE           exact controlling upstream licence
  ATTRIBUTION.md    original author and packaging changes
  references/       required supporting guidance, when used
  scripts/          unchanged original executable files, when used
catalog.yml         existing AutoGPT loader format
provenance/         originals, evidence, hashes and recorded adaptations
```

The collection has 64 core and 10 conditional packages; 67 names were clarified. Folders match their declared names. Standard `license` and `metadata` fields carry attribution; the source metadata keys are AutoGPT conventions within the standard extension map. No new skill format, submodule fetch or shared package root is required.

Each package contains its own required local support files. Only dependencies used by selected workflows are included. Scripts, licences and unchanged supporting material retain exact original bytes and executable modes. Counted name/metadata/path adaptations preserve authored advice, gates, commands and body formatting.
There are 332 installed files. The largest package by file count is `lifecycle-email-marketing`, with 11 supplementary files. Every installed package stays within the inspected platform limits.

## Permanent provenance

`provenance/files.json` binds every installed file to its original repository/path/commit, Git blob, checksums, mode and counted transformations. Exact originals live under `provenance/originals/<sha256>`. `tools/vendor.py --restore` can recreate missing packages offline without executing upstream code.

Dated usage/activity captures are now stored inside this repository under `provenance/evidence-files/<sha256>`, not only in a local ZIP. Evidence is explicitly linked from each selection. Stars are repository-wide and installs are telemetry; neither proves successful outcomes. No skill was executed or benchmarked during curation.

The original authors remain the authors; AutoGPT curates and adapts packaging. Each package carries its full licence and attribution. MIT/Apache notices are retained; Trail of Bits CC-BY-SA-4.0 adaptations retain attribution and share-alike terms. Six selections now use verified clean historical source revisions. Invoice chase remains excluded until its licence is clarified. Authorship does not establish human-only authorship, and no upstream endorsement is claimed.

Deferred sources live under separate content-addressed archives, with exact reasons and licences. They are not discoverable packages. The advertising suite exceeds current limits; prospecting has an unresolved source safety finding. Public-relations, referrals and marketing-plan have contradictory authored guidance; the ideas library is held with its parent. No workflow is rewritten or weakened to pass review.

## Contributing and checking

Read [AGENTS.md](AGENTS.md).

```
python -m pip install pyyaml
python -m unittest discover -s tools -p 'test_*.py' -v
python tools/check.py --expected-count 74
python tools/check_research.py
python tools/audit_dependencies.py --check
python tools/vendor.py --check
```

Use `--strict-modes` with the package checker on POSIX. Source integrity, complete roster accounting, captured evidence and deferred-source retention are tested independently of import acceptance. See the documented exact importer probe for its source revision and limits.

Merging this catalog does not remove production listings or change expert assignments. A separate migration must preserve users’ installed copies, avoid the starter fallback, retire intended placeholders and assign only the supported kits. Coverage gaps and conditional sources remain explicit.
