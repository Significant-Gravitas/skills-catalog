# skills-catalog

The source and review repository for the AutoGPT Platform Skills marketplace.
Every skill stays in the private review catalog, but only entries marked
`distribution_status: approved` may be published or exported. A public export
contains only approved entries and their files.

## Layout

```
catalog.yml            all skills, review status, categories and provenance
skills/<slug>/SKILL.md the skill itself: frontmatter + instructions
skills/<slug>/...      supporting docs the instructions reference
skills/<slug>/LICENSE  the package licence for every approved skill
skills/<slug>/NOTICE   source, pinned commit and attribution
tools/vendor.py        pulls an approved skill from its pinned source commit
tools/export_public.py builds a clean tree containing only approved skills
```

A skill's folder name, its `catalog.yml` slug and the `name` in its frontmatter must
all match. The SKILL.md format is the one the platform uses everywhere: YAML
frontmatter with `name`, `description` and optional `triggers`, then markdown.

## Distribution status

Every catalog entry has one status:

- `approved` — source and redistribution rights are verified;
- `provenance_review` — the original source or rights are not yet verified;
- `legal_review` — the source license is known, but another copyright or
  trademark question remains.

Review states preserve the skill while blocking public distribution. Never infer
approval from an MIT label alone: the source must have the right to license all
material in the package.

## Approving a vendored skill

1. Record `source: owner/repo/path`, `provenance: vendored`, a full
   `source_commit`, its pinned `source_url`, and `license`.
2. Check that the source has the right to license the whole package, including
   text based on books, courses, standards, or commercial methods.
3. Set `distribution_status: approved`.
4. Run `GITHUB_TOKEN=$(gh auth token) python tools/vendor.py <slug>`.
5. Check the generated `LICENSE`, `NOTICE`, frontmatter and package contents.
6. Open a PR with the rights evidence.

Re-running the script refreshes from the pinned commit and overwrites hand edits.
Change `source_commit` in review before taking a newer upstream version.

## Approving an original skill

An original skill needs `provenance: original`, a package license, a notice that
names the rights holder, and a review of employee, contractor, source-material
and model-output rights. Do not use `source: platform` as proof of authorship.

## Checks

`python tools/check.py` validates statuses, approved provenance, pinned commits,
license and notice files, frontmatter attribution, names, categories, package
limits and local links. The `Check catalog` workflow runs it on every PR and
push to `main`.

## Publishing

Merging to `main` does not publish by itself. The platform seed must read this
repo, skip every entry not marked `approved`, and write the approved listings:

```
poetry run python -m backend.api.features.store.skill_seed
```

Run it against the environment you want updated. It is idempotent and rewrites each
listing's live version in place.

Removing approval does not withdraw a listing that is already live. Mark the live
listing unavailable as a separate release step.

For a public GitHub release, follow [PUBLICATION.md](PUBLICATION.md). Never make
this private review repository public because its history contains held skills.
