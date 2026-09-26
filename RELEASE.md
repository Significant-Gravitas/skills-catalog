# Catalogue release contract

`release.json` binds the complete catalogue and the whole expert roster to one
release. It is not a record that an environment has applied it. Every deploy of
the AutoGPT backend runs `publish-skills-catalog` right after database migrations,
which publishes this repository's `main`. Validation in this repository neither
connects to a database nor publishes a release.

## Schema version 2

`release.json` has exactly these top-level keys: `schema_version`, `release_key`,
`provenance`, `catalog_sha256`, `packages`, `experts`, `retirements`,
`retired_experts`, `system_packages`. Any other key is rejected.

- `schema_version`: integer `2`. The backend publisher accepts only this version
  and fails closed on schema 1.
- `release_key`: lowercase kebab-case identifier for this reviewed release.
- `provenance`: source and review information. It does not grant write authority.
- `catalog_sha256`: SHA-256 of the exact `catalog.yml` bytes. This binds listing
  metadata, attribution and licensing along with package contents.
- `packages`: sorted by slug. Each object contains `slug`, `tree_sha256`, and
  `files`. Every catalogue entry must appear exactly once, and no package folder
  may be omitted. Every regular file in each package is included, including
  `SKILL.md`, supporting documents, scripts and licences.
- `experts`: sorted by `key`. Each object has exactly
  `{"key": ..., "sha256": ..., "skills": [...]}`. `key` is the permanent expert
  key and the name of its file, `experts/<key>.yml`. `sha256` is the SHA-256 of
  the exact bytes of that file. `skills` is the ordered array of active package
  slugs the expert bundles; it duplicates the file's `skills` list for readable
  diffs and must equal it. Every file in `experts/` must be listed, and every
  listed key must have a file. The array order is the marketplace assignment
  order. A display-name change must not rename a key.
- `retirements`: sorted array of explicitly retired slugs. A retired slug cannot
  also be active or assigned. Absence from `packages` does not authorize deletion.
- `retired_experts`: sorted array of explicitly retired expert keys. A retired key
  cannot also be in `experts`. The publisher archives these templates in every
  environment. Absence from `experts` does not authorize archiving.
- `system_packages`: must be empty. Nonempty values are rejected until the
  system-package consumer and its schema extension are implemented together.

Each package file is an object with exactly these fields:

```json
{"path":"SKILL.md","sha256":"<64 lowercase hex characters>","executable":false}
```

`path` is relative to its package, uses `/`, and cannot be absolute, hidden or
traverse upward. Symlinks are rejected. `sha256` hashes exact file bytes without
newline conversion. `executable` represents Git mode `100755`; `100644` is false.
Other Git file modes are unsupported. New files and mode changes must be staged
before generating a release so Windows and Linux compute the same result.

To compute `tree_sha256`, sort the file objects by `path`, encode that array as
UTF-8 JSON with sorted object keys, separators `,` and `:`, and no ASCII escaping,
then SHA-256 those bytes. In Python:

```python
hashlib.sha256(json.dumps(
    sorted(files, key=lambda item: item["path"]),
    sort_keys=True, separators=(",", ":"), ensure_ascii=False,
).encode("utf-8")).hexdigest()
```

This digest covers paths, contents and executable modes. It has no timestamp,
environment identifier or dependency on the commit that contains the manifest.
Package listing metadata is separately bound by `catalog_sha256`; the backend
must include the relevant catalogue entry when choosing an immutable version.

## Expert files

Each expert is one YAML file, `experts/<key>.yml`, with all of these fields and
no others:

| Field | Type and limits |
| --- | --- |
| `key` | `^[a-z0-9][a-z0-9-]{0,63}$`; must equal the file name |
| `name` | display name, non-empty; unique across experts, case-insensitive |
| `role`, `job_title`, `tagline` | non-empty strings |
| `avatar_url` | string or null |
| `categories` | non-empty list from `marketing`, `sales`, `finance`, `support`, `operations`, `research`, `content`, `development` |
| `bio`, `identity` | non-empty strings |
| `voice_preferences` | string, may be empty |
| `voice_samples` | list of `{label, text}` |
| `boundaries` | string |
| `day_one` | at most 3 items of `{title, description, timing}`; title 1-80 chars, description at most 240, timing at most 40 |
| `preloads` | list of `{slug, cron}`; cron is a string or null; slugs unique |
| `routines` | list of `{key, title, prompt, crons, asks, session_mode}`; `key` uses the same pattern as expert keys and is unique; `crons` and `asks` are lists of strings; `session_mode` is `THREAD` or `FRESH` |
| `skills` | ordered list of unique catalogue package slugs |

`python tools/check.py` enforces this schema; `python tools/release.py check`
binds each file's bytes and `skills` into the manifest.

## Editing and checking

After deliberately editing packages, their metadata or expert files:

```sh
git add catalog.yml skills/ experts/
python tools/release.py refresh
python tools/check.py
python tools/release.py check
python -m unittest discover -s tools -p test_release.py
```

`refresh` regenerates `schema_version`, `catalog_sha256`, `packages` and `experts`
from the working tree. It preserves the authored provenance, release key and
retirement decisions (`retirements` and `retired_experts`), and fails if those
references become inconsistent. `check` fails when any package byte, expert file
byte or bundled skill list differs from the manifest. Review the manifest diff
alongside the content diff. A changed release should carry its own release key;
an applied key must never be repurposed for different content.

## Publishing

`publish-skills-catalog` runs on every backend deploy, right after database
migrations, and publishes `main`:

- New or changed packages become immutable, content-addressed marketplace
  versions.
- Expert templates are upserted by key. Keys in `retired_experts` are archived.
- Users' installed copies catch up lazily: unedited copies are replaced, and
  edited copies are three-way merged with the user's side winning conflicts.

The catalogue cannot prove that a database write is safe. The publisher must
reject unexpected state, constrain its writes to platform-authored records and
preserve customers' edits.

## Baseline provenance

The first release was `catalogue-baseline-2026-09-25` (schema 1):

| Scope | Preserved value |
| --- | --- |
| Source packages | Catalogue commit `c0237abc5a3503b1bb62d3422704132176305847` |
| Complete packages | 338 |
| Files | 435: 338 `SKILL.md` files and 97 companion files |
| Marketplace experts | 32 |
| Ordered skill assignments | 321 |
| Retirements | 0 |

All 435 package file SHA-256 values and modes and the `catalog.yml` SHA-256 were
checked against the recorded archive successfully imported into production on
25 September 2026. Expert assignments came from the read-only production snapshot
at 16:38:17.985323 UTC that day; its SHA-256 is recorded under `provenance` for audit.
No database row IDs, user data, credentials or customer skill files are included.

The schema 2 release, `catalogue-experts-2026-09-26`, keeps those 338 packages
and the same 321 ordered assignments byte for byte, and moves the full expert
definitions into `experts/<key>.yml`. They were generated from the AutoGPT
backend's Python roster. It retires the `blake` expert, whose template was folded
into Max, and retires no packages.
