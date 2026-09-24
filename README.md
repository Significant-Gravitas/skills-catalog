# AutoGPT skills catalog

43 selected community skills in ordinary, self-contained Agent Skills packages.
This replaces all 171 previous catalog entries. The original authors retain
authorship; AutoGPT curates and adapts packaging, names and attribution metadata.

The existing AutoGPT loader accepts all 43 packages in an isolated check using
the inspected parser and package validators. **This is still a draft collection:
runtime integration and production migration have not been performed.** See
[import and runtime status](docs/IMPORT_COMPATIBILITY.md).

## Skills and format

[SELECTIONS.md](SELECTIONS.md) lists every skill, essential function, source,
licence and proposed expert assignment. The collection contains 36 core and seven
conditional selections: 45 core and seven conditional expert assignments.

The package format follows [Agent Skills](https://agentskills.io/specification):

```
skills/<clear-unique-name>/
  SKILL.md                 name, description, licence, metadata and instructions
  LICENSE                  exact controlling upstream licence
  ATTRIBUTION.md           original author, source, adaptations and requirements
  references/              required local guidance, when used
  scripts/                 required executable code, when used
  assets/                  required templates/resources, when used
catalog.yml                existing AutoGPT catalog format
provenance/                 source archives, hashes, changes and research evidence
```

`name` matches the individual folder. Thirty-seven names have been clarified,
including the two different upstream `customer-research` skills, now
`customer-insight-research` and `customer-support-research`. The full mapping is
in [provenance/name-mapping.json](provenance/name-mapping.json).

Standard `license` and `metadata` fields carry the original licence and
attribution. `metadata.source` and `metadata.source_url` are conventions understood
by AutoGPT inside the standard extension map. Upstream native extension fields
remain present; their runtime behavior is a separate compatibility requirement.
There is no new platform import schema or shared-package-root requirement.

## Dependency packaging

Only selected skills and the supporting files their workflows use are installed.
Each package carries its own required local references. References have been
updated when files moved. Optional upstream discovery links point to immutable
source revisions; project-state files and external API identifiers keep their
authored names.

The marketing packages need ten shared tool guides, not the complete 164-file
tool collection. Unused development fixtures and unrelated tools are excluded.
The full collection has 221 installed files, including 43 licences and 43
attribution files; the largest package has 17 supplementary files and is under
180 KiB. No complete upstream repository or hidden plugin install is bundled.

Automated checks verify definite local Markdown links and report literal paths,
Python imports and dynamic/native references for review. Prose and optional
provider branches are ambiguous: a scan alone cannot determine every dependency.
The reviewed inclusion/exclusion decisions and unresolved runtime needs are
recorded in `provenance/dependency-review.json` and each skill's provenance.

## Provenance, authorship and changes

`provenance/files.json` records each installed file's upstream repository, path,
immutable commit, Git blob, original SHA-256, packaged SHA-256 and executable
mode. Exact original bytes are stored under `provenance/originals/<sha256>`;
these archives are outside the install tree and are not additional skills.
Identical source bytes are stored once. Recorded, counted transformations can
recreate every adapted package offline; modified files identify the adaptation.

Instructions and approval gates are retained. Adaptations cover clear names,
accurate metadata, required local paths and explicit references to original
plugin guidance. YAML headers are normalized; authored body formatting is not
globally reformatted. Licences and unchanged support files retain exact bytes.

Research evidence was captured on 2026-09-24. Per-skill provenance retains
adoption/activity observations, source URLs and response hashes. Counts are
installation telemetry, not unique users or evidence of successful outcomes.
The complete local research archive's checksum is recorded in the evidence file.
No source has been executed or benchmarked during curation/packaging.

Retain MIT/Apache copyright/licence notices. The Trail of Bits adaptations retain
CC-BY-SA-4.0 attribution and share-alike terms. Seven selections inherit an
Anthropic Apache licence with unexplained appended text; preserve the exact
licence and resolve that recorded ambiguity before commercial release. See the
individual provenance records. Original authorship does not establish human-only
authorship, and no upstream endorsement is claimed.

## Contributing and checking

Read [AGENTS.md](AGENTS.md) for mandatory naming, dependency, formatting,
attribution and publication rules.

```
python -m pip install pyyaml
python -m unittest discover -s tools -p 'test_*.py' -v
python tools/check.py --expected-count 43
python tools/audit_dependencies.py --check
python tools/vendor.py --check
```

On POSIX use `--strict-modes` with the checker. `tools/vendor.py --restore`
recreates missing package files from the local source archives and recorded
transformations. It does not fetch upstream HEAD, overwrite edited files or
execute third-party code. The exact source-specific importer probe and its
limitations are documented in [IMPORT_COMPATIBILITY.md](docs/IMPORT_COMPATIBILITY.md).

Merging this repository does not retire production listings or reassign experts.
Publication requires the documented runtime decisions, migration and end-to-end
verification; it is not implied by passing the packaging checks.
