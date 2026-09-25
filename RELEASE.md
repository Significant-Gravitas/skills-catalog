# Catalogue release contract

`release.json` is a candidate release, not a record that an environment has applied
it. An AutoGPT publisher consumes a specific reviewed Git commit. Validation in
this repository neither connects to a database nor publishes a release.

## Schema version 1

- `schema_version`: integer `1`.
- `release_key`: lowercase kebab-case identifier for this reviewed release.
- `provenance`: source and review information. It does not grant write authority.
- `catalog_sha256`: SHA-256 of the exact `catalog.yml` bytes. This binds listing
  metadata, attribution and licensing along with package contents.
- `packages`: sorted by slug. Each object contains `slug`, `tree_sha256`, and
  `files`. Every catalogue entry must appear exactly once, and no package folder
  may be omitted. Every regular file in each package is included, including
  `SKILL.md`, supporting documents, scripts and licences.
- `experts`: sorted by stable `key`. `skills` is an ordered array of active package
  slugs. The array order is the marketplace assignment order. Keys are permanent
  catalogue identifiers, initially the lowercase marketplace names; a display-name
  change must not implicitly rename a key. The publisher maps keys to explicitly
  adopted platform template IDs separately for each environment. This file does
  not choose database records by name or contain environment-specific IDs.
- `retirements`: sorted array of explicitly retired slugs. A retired slug cannot
  also be active or assigned. Absence from `packages` does not authorize deletion.
  The baseline array is empty.
- `system_packages`: empty in this version. Nonempty values are rejected until
  the system-package consumer and its schema extension are implemented together.

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
The publisher binds the entire release to its pinned source revision and manifest
digest rather than trusting the human-readable `release_key` alone.

## Editing and checking

After deliberately editing packages or their metadata:

```sh
git add catalog.yml skills/
python tools/release.py refresh
python tools/check.py
python tools/release.py check
python -m unittest discover -s tools -p test_release.py
```

`refresh` updates only `catalog_sha256` and `packages`; it preserves the authored
expert assignments, provenance, release key and retirement decisions. It fails if
those references become inconsistent. Review the manifest diff alongside the
content diff. A changed release needs its own reviewed release key before
publication; an applied key must never be repurposed for different content.

## Preserved migration baseline

The first release is `catalogue-baseline-2026-09-25`:

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
Only stable expert keys and their ordered slugs were copied into the manifest.
No database row IDs, user data, credentials or customer skill files are included.

This additive baseline preserves [Nick's merged PR2](https://github.com/Significant-Gravitas/skills-catalog/pull/2)
and the earlier catalogue. It does not apply the later replacements from
[PR4](https://github.com/Significant-Gravitas/skills-catalog/pull/4). Their publication
is a separate release after the backend's ownership protections, immutable
versions, previews, rollback and coherent installations have been deployed and
tested. Application-specific expert text changes remain a separate backend
contribution; adding this manifest does not apply them.

The catalogue cannot prove that a database write is safe. The publisher must
reject unknown expert keys, ownership collisions and unexpected state; constrain
all writes to the explicitly adopted platform records; preserve existing customer
copies; and record the actual applied release per environment.
