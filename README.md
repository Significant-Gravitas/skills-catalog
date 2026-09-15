# skills-catalog

The skills the AutoGPT Platform ships in its Skills marketplace as platform-authored
listings. The backend seed reads this repo and upserts one listing per entry in
`catalog.yml`, so publishing a skill is a merge here plus a seed run.

## Layout

```
catalog.yml            what gets published, with categories and provenance
skills/<slug>/SKILL.md the skill itself: frontmatter + instructions
skills/<slug>/...      supporting docs the instructions reference
skills/<slug>/LICENSE  upstream licence, for vendored skills
tools/vendor.py        pulls a skill from a public GitHub repo into skills/
```

A skill's folder name, its `catalog.yml` slug and the `name` in its frontmatter must
all match. The SKILL.md format is the one the platform uses everywhere: YAML
frontmatter with `name`, `description` and optional `triggers`, then markdown.

## Adding a skill we wrote

1. Create `skills/<slug>/SKILL.md`.
2. Add an entry to `catalog.yml` with `source: platform`.
3. Open a PR.

## Adding a skill from an open-source repo

1. Check the upstream licence allows redistribution. MIT and Apache-2.0 do.
2. Add an entry to `catalog.yml` with `source: owner/repo/path/to/skill` and `license`.
3. Run `GITHUB_TOKEN=$(gh auth token) python tools/vendor.py <slug>`.
4. Read the result. The script drops upstream eval fixtures, hidden files, sponsored
   tool tables and links into folders it did not copy, and records the source repo,
   URL and commit in the frontmatter. Anything else that does not fit our product
   gets edited by hand.
5. Open a PR.

Re-running the script on a slug refreshes it from upstream HEAD and overwrites any
hand edits, so keep those minimal or upstream them.

## Publishing

Merging to `main` does not publish by itself. The platform seed pulls this repo and
writes the listings to the database:

```
poetry run python -m backend.api.features.store.skill_seed
```

Run it against the environment you want updated. It is idempotent and rewrites each
listing's live version in place.
