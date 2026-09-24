# Skill catalog contribution rules

## Packages and names

- Use the established Agent Skills format: `skills/<name>/SKILL.md` with YAML
  `name` and `description`, followed by Markdown instructions. The folder and
  declared name must match. Keep names unique, lowercase and hyphenated, at most
  64 characters, and specific about the task. Prefer `sales-call-preparation`
  over `call-prep`; distinguish customer insight research from support research.
- Keep `catalog.yml` compatible with the existing AutoGPT importer. Do not add a
  new import schema or require source-root/path indirection to install a package.
  Build/provenance records are separate from the platform's catalog contract.
- A package must contain all of its required local, read-only supporting files.
  Put scripts, references, templates and assets inside that individual skill's
  folder. Do not depend on a sibling package or an upstream repository root
  being present. A sibling skill used as reference material may be included as
  an ordinary, attributed reference file; it is not another registered skill.
- When moving files, update every affected local reference, including references
  inside supporting files. Keep script imports and relative resources working.
  Do not rename project-state files, external tool/API identifiers, API argument
  values or native commands just because the installed skill name changes.
  Record original and installed names, including ambiguous cross-skill names.

## Import only dependencies that are used

- Inspect the selected skill and recursively follow its required local file
  references, script imports, templates and conditional workflow dependencies.
  Record a reason for each included support file. Do not vendor entire upstream
  repositories or complete shared tool collections by default.
- Exclude unused development tests, evaluation fixtures, unrelated plugins and
  repository maintenance tools. A test/fixture that the skill actually runs or
  needs is a dependency and must be kept.
- Optional discovery links may point to the exact pinned upstream revision;
  do not turn a required local runtime dependency into a remote link merely to
  make the package smaller. Preserve useful authored guidance and approvals.
- Automated scans can verify literal paths, links, imports and package limits.
  They cannot prove complete usage in prose, dynamic imports, templated paths,
  provider-specific branches or external services. Review those cases manually,
  record the decision and prerequisites, and leave unresolved requirements
  explicit. Do not call a package runtime-verified on the basis of a link scan.
- Run `python tools/audit_dependencies.py --check` after changing dependencies.
  Resolve definite local broken links; document genuine external/project-state
  dependencies instead of creating empty or invented files.

## Authorship, licences and provenance

- Upstream authors remain the authors. AutoGPT is the curator and packaging
  adapter. Never claim that our packaging work created the original skill.
- Use the standard top-level `license` field and bundle the full controlling
  licence as `LICENSE`. Keep additional applicable licence/copyright/NOTICE
  material. Store author and source details under the standard `metadata` map;
  use string values. `metadata.source` and `metadata.source_url` populate the
  existing AutoGPT importer's attribution fields. They are project conventions
  inside the standard extension map, not universal Agent Skills field names.
- Preserve immutable source repository, path, commit, Git blob, checksum and
  original bytes in `provenance/`. Retain discovery/adoption evidence and its
  capture date. Every installed file must be explained by the file manifest,
  including generated attribution files, and must have a recorded output hash.
- Adaptations must be reproducible from archived originals. Record exact
  replacements with expected occurrence counts and reasons. Fail if upstream
  text no longer matches; never silently apply a broad search-and-replace.
- Include `ATTRIBUTION.md` with each package. Mark modified source files with a
  packaging notice, retain the source licence and identify the modifications.
  Preserve applicable share-alike terms for CC-BY-SA adaptations. Never edit a
  licence to resolve ambiguity; keep the uncertainty documented for review.

## Formatting and permitted adaptations

- Changes are limited to clear names, accurate licence/source metadata, necessary
  packaging/path adaptations and formatting that preserves meaning. Do not
  rewrite expert advice, remove approval gates, invent legal positions, weaken
  tool restrictions or remove a workflow to pass validation.
- Normalize YAML headers to UTF-8/LF when generating compatible packages; retain
  all original metadata, including product-specific extensions. Converting
  metadata scalars to equivalent strings is allowed by the standard metadata
  contract. Preserve the original header in the source archive.
- Do not run a blanket Markdown formatter. Preserve authored body whitespace,
  indentation, code fences and examples except for recorded path/name edits and
  modification notices. Copy unchanged scripts, binaries, licences and other
  support files byte-for-byte, retaining executable modes. Disable Git newline
  conversion for packaged and archived source files.
- Renaming a tool permission or moving a behavior flag is not cosmetic.
  Preserve native flags such as `user-invocable` and record any platform behavior
  they require. Retaining a field in this repository does not mean AutoGPT's
  database or runtime currently honors it.

## Verification and publication

- Run the unit tests, `python tools/check.py --expected-count 43`, and the
  dependency audit. On POSIX also use `--strict-modes`. Update the expected count
  intentionally when changing the reviewed selection. Verify that the archived
  originals and every generated package match their manifests.
- Keep packages within the inspected AutoGPT limits: 100 supplementary files,
  2 MiB per supplementary file, 20 MiB total, eight path segments, no hidden path
  segments, symlinks or escaping paths. The primary `SKILL.md` is the only file
  excluded from the supplementary-file count.
- Use the exact importer probe with the documented upstream source revision to
  distinguish import acceptance from source-integrity checks. Do not execute
  third-party scripts merely to inspect/package them.
- Static import acceptance is not a successful end-to-end installation or run.
  Keep missing accounts, services, native dispatch, persistent state and metadata
  behavior explicit. Do not publish an unusable conditional package silently.
- A repo update does not retire production listings, remove starter fallback
  skills or reassign experts. Those changes require a separate explicit migration;
  never delete users' installed copies as an incidental packaging operation.

References: https://agentskills.io/specification and
https://github.com/vercel-labs/skills .
