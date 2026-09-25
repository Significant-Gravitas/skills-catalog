# skills-catalog

The complete skill packages and the whole marketplace expert roster the AutoGPT
Platform publishes as platform-authored listings. `catalog.yml` describes each
package; `experts/<key>.yml` defines each expert (persona, voice, day-one rows,
preloads, routines and the ordered skills it bundles); `release.json` binds the
exact bytes of both. The database is the serving copy of a published release.

## Layout

```
catalog.yml            what gets published, with categories and provenance
experts/<key>.yml      one marketplace expert: persona, voice, routines, bundled skills
release.json           exact package and expert-file hashes, ordered skills, retirements
skills/<slug>/SKILL.md the skill itself: frontmatter + instructions
skills/<slug>/...      supporting docs the instructions reference
skills/<slug>/LICENSE  upstream licence, for vendored skills
tools/vendor.py        pulls a skill from a public GitHub repo into skills/
tools/release.py       checks or refreshes a release's content hashes
tools/check.py         validates skills and expert files the way the platform will
```

A skill's folder name, its `catalog.yml` slug and the `name` in its frontmatter must
all match. The SKILL.md format is the one the platform uses everywhere: YAML
frontmatter with `name`, `description` and optional `triggers`, then markdown.

## Adding a skill we wrote

1. Create `skills/<slug>/SKILL.md`.
2. Add an entry to `catalog.yml` with `source: platform`.
3. Add the slug to the `skills` list of the appropriate `experts/<key>.yml`, if applicable.
4. Stage the new files, run `python tools/release.py refresh`, and open a PR.

## Adding a skill from an open-source repo

1. Check the upstream licence allows redistribution. MIT and Apache-2.0 do.
2. Add an entry to `catalog.yml` with `source: owner/repo/path/to/skill` and `license`.
3. Run `GITHUB_TOKEN=$(gh auth token) python tools/vendor.py <slug>`.
4. Read the result. The script drops upstream eval fixtures, hidden files, sponsored
   tool tables and links into folders it did not copy, and records the source repo,
   URL and commit in the frontmatter. Anything else that does not fit our product
   gets edited by hand.
5. Add any intended expert assignment to `experts/<key>.yml`, stage the files,
   run `python tools/release.py refresh`, and open a PR.

Re-running the script on a slug refreshes it from upstream HEAD and overwrites any
hand edits, so keep those minimal or upstream them.

## Editing an expert

Each marketplace expert is one file, `experts/<key>.yml`. The file name is the
permanent key; the `key` field inside must match it, and a display-name change
never renames the key. The file holds every field the platform shows or runs:
`key`, `name`, `role`, `job_title`, `tagline`, `avatar_url`, `categories`, `bio`,
`identity`, `voice_preferences`, `voice_samples`, `boundaries`, `day_one`,
`preloads`, `routines` and the ordered `skills` it bundles. See
[the release contract](RELEASE.md) for the exact schema. Edit the file, stage it,
run `python tools/release.py refresh`, and open a PR. To retire an expert, delete
its file and add its key to `retired_experts` in `release.json`.

## Checks

`python tools/check.py` validates the catalog the way the platform will:
slugs match folder and frontmatter names, categories are canonical, package files
stay within the platform's caps, nothing is hidden, and no markdown links out of
its skill folder. It also validates every `experts/<key>.yml`: required fields and
types, day-one limits, unique routine keys and preload slugs, canonical categories,
bundled skills that exist in the catalog, the key matching the file name, and no
two experts sharing a display name. The `Check catalog` workflow runs it on every PR and push to `main`.

`python tools/release.py check` also checks every package byte, file path and Git
executable mode, catalogue metadata, every expert file's bytes, that every expert
file is listed and every listed expert has a file, and ordered skill references.
`python -m unittest discover -s tools -p test_release.py` tests rejection of modified
packages and expert files, unsafe paths, inconsistent assignments and unintended
retirements.

The release hash binds exact bytes. Text files are checked out with LF endings;
do not build an upload by converting line endings. Stage new files and executable
mode changes before refreshing the hashes.

## Publishing

Every deploy of the AutoGPT backend runs its `publish-skills-catalog` command right
after database migrations, and that command publishes this repository's `main`.
Merging to `main` is therefore how a change ships; the next deploy of each
environment picks it up.

- New or changed packages become immutable, content-addressed marketplace
  versions. An unchanged package is a no-op.
- Expert templates are upserted by key from `experts/<key>.yml`. Keys listed in
  `retired_experts` are archived.
- Users' installed copies catch up lazily. An unedited copy is replaced with the
  new version; an edited copy is three-way merged against the version it was
  installed from, with the user's side winning conflicts.

The publisher only accepts release schema 2 and fails closed on anything it does
not recognise. `release.json` contains no user or organisation IDs and no personal
skill data.

See [the release contract](RELEASE.md) for the exact format and baseline provenance.
