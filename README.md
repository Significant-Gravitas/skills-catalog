# skills-catalog

The complete skill packages the AutoGPT Platform publishes as platform-authored
marketplace listings. `catalog.yml` describes each package; `release.json` binds
their exact contents to the ordered skill assignments for marketplace experts.
The database is the serving copy of a published release.

## Layout

```
catalog.yml            what gets published, with categories and provenance
release.json           exact package hashes, ordered expert skills and retirements
skills/<slug>/SKILL.md the skill itself: frontmatter + instructions
skills/<slug>/...      supporting docs the instructions reference
skills/<slug>/LICENSE  upstream licence, for vendored skills
tools/vendor.py        pulls a skill from a public GitHub repo into skills/
tools/release.py       checks or refreshes a release's content hashes
```

A skill's folder name, its `catalog.yml` slug and the `name` in its frontmatter must
all match. The SKILL.md format is the one the platform uses everywhere: YAML
frontmatter with `name`, `description` and optional `triggers`, then markdown.

## Adding a skill we wrote

1. Create `skills/<slug>/SKILL.md`.
2. Add an entry to `catalog.yml` with `source: platform`.
3. Add the skill to the appropriate expert in `release.json`, if applicable.
4. Stage the new package files, run `python tools/release.py refresh`, and open a PR.

## Adding a skill from an open-source repo

1. Check the upstream licence allows redistribution. MIT and Apache-2.0 do.
2. Add an entry to `catalog.yml` with `source: owner/repo/path/to/skill` and `license`.
3. Run `GITHUB_TOKEN=$(gh auth token) python tools/vendor.py <slug>`.
4. Read the result. The script drops upstream eval fixtures, hidden files, sponsored
   tool tables and links into folders it did not copy, and records the source repo,
   URL and commit in the frontmatter. Anything else that does not fit our product
   gets edited by hand.
5. Add any intended expert assignment in `release.json`, stage the package files,
   run `python tools/release.py refresh`, and open a PR.

Re-running the script on a slug refreshes it from upstream HEAD and overwrites any
hand edits, so keep those minimal or upstream them.

## Checks

`python tools/check.py` validates the catalog the way the platform seed will:
slugs match folder and frontmatter names, categories are canonical, package files
stay within the platform's caps, nothing is hidden, and no markdown links out of
its skill folder. The `Check catalog` workflow runs it on every PR and push to `main`.

`python tools/release.py check` also checks every package byte, file path and Git
executable mode, catalogue metadata, unique expert keys and ordered skill references.
`python -m unittest discover -s tools -p test_release.py` tests rejection of modified
packages, unsafe paths, inconsistent assignments and unintended retirements.

The release hash binds exact bytes. Text files are checked out with LF endings;
do not build an upload by converting line endings. Stage new files and executable
mode changes before refreshing the hashes.

## Publishing

Merging this baseline does not publish by itself. The new AutoGPT publisher is a
separate coordinated change: it validates a pinned catalogue revision, previews
only the adopted marketplace records, and activates the same reviewed release in
development and then production. The previous in-place seed command is not this
release process.

This first manifest preserves all 338 existing packages and all 321 ordered
assignments across 32 marketplace experts. It retires nothing. It contains no user
or organisation IDs and no personal skill data. Database ownership checks and
environment-specific record adoption belong to the publisher, not this catalogue.

See [the release contract](RELEASE.md) for the exact format, baseline provenance
and the remaining integration boundary.
