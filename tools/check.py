#!/usr/bin/env python3
"""Validate flat skill packages, original evidence, and recorded adaptations offline.

Package limits follow AutoGPT's inspected skills.py (2026-09-25). This does not
execute skills or certify their runtime dependencies or semantic correctness.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import urllib.parse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
CATEGORIES = {"marketing", "sales", "finance", "support", "operations", "research", "content", "development"}
SHA1 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
REGISTRY_ID = re.compile(r"^[a-z0-9](?:[a-z0-9_-]{0,62}[a-z0-9])?$")
REPO_PART = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*$")
PACKAGE_SEGMENT = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9._-]*$")
MAX_PACKAGE_FILES = 100  # Siblings only; the root SKILL.md is separate.
MAX_PACKAGE_FILE_BYTES = 2 * 1024 * 1024
MAX_PACKAGE_BYTES = 20 * 1024 * 1024  # Includes root SKILL.md.
MAX_PACKAGE_PATH_DEPTH = 8
PR2_SOURCE = {
    "repo": "Significant-Gravitas/skills-catalog",
    "base_commit": "00d9cfbf2c9c01a13dc5626a50e8f4b9c4d2d35d",
    "commit": "c0237abc5a3503b1bb62d3422704132176305847",
    "pull_request": 2,
}
PR2_PENDING_SLUG = "product-experiment-design"


class ValidationError(ValueError):
    pass


class UniqueLoader(yaml.SafeLoader):
    """Reject duplicate keys rather than discarding evidence."""


def _mapping(loader: UniqueLoader, node: Any, deep: bool = False) -> dict:
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValidationError(f"duplicate YAML key: {key!r}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def _json_pairs(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def relative_path(value: Any) -> str:
    """An unambiguous confined relative path on Windows and Unix."""
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValidationError(f"unsafe relative path: {value!r}")
    if any(ord(c) < 32 for c in value):
        raise ValidationError(f"control character in path: {value!r}")
    if any(p in {"", ".", ".."} or p != p.strip() or p.endswith(".") for p in value.split("/")):
        raise ValidationError(f"path must be normalized and confined: {value!r}")
    return value


def _is_link(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        return bool(getattr(path.lstat(), "st_file_attributes", 0) & 0x400)
    except FileNotFoundError:
        return False


def confined_path(root: Path, relative: Any) -> Path:
    relative = relative_path(relative)
    current = root
    for segment in relative.split("/"):
        current = current / segment
        if _is_link(current):
            raise ValidationError(f"symlink/reparse point is not allowed: {relative}")
    if not current.resolve().is_relative_to(root.resolve()):
        raise ValidationError(f"path escapes repository: {relative}")
    return current


def git_blob_sha1(content: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(content)).encode("ascii") + b"\0" + content).hexdigest()


def verify_bytes(record: dict, content: bytes) -> None:
    """Verify output metadata; original blob identity is checked separately."""
    label = record.get("path", record.get("archive", "content"))
    if len(content) != record["size"]:
        raise ValidationError(f"{label}: size differs from manifest")
    if hashlib.sha256(content).hexdigest() != record["sha256"]:
        raise ValidationError(f"{label}: SHA-256 differs from manifest")


def verify_original(source: dict, content: bytes) -> None:
    verify_bytes(source, content)
    if git_blob_sha1(content) != source["blob_sha1"]:
        raise ValidationError(f"{source['path']}: original Git blob SHA-1 differs")


@dataclass
class Result:
    root: Path
    entries: list[dict] = field(default_factory=list)
    records: dict[str, dict] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    provenance: dict[str, dict] = field(default_factory=dict)
    rendered: dict[str, bytes] = field(default_factory=dict)
    # Carried platform packages retain their existing bytes/metadata; they do
    # not acquire the upstream licence or adaptation evidence of the 74 imports.
    carryforward: dict[str, dict] = field(default_factory=dict)
    carryforward_files: dict[str, dict] = field(default_factory=dict)
    unresolved: set[str] = field(default_factory=set)

    def require_valid(self) -> None:
        if self.errors:
            raise ValidationError("\n".join(self.errors))


def _read_document(root: Path, relative: str, *, as_yaml: bool = False) -> Any:
    text = confined_path(root, relative).read_text(encoding="utf-8-sig")
    return yaml.load(text, Loader=UniqueLoader) if as_yaml else json.loads(text, object_pairs_hook=_json_pairs)


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{label}: nonempty string required")
    return value


def _strings(value: Any, label: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(x, str) or not x for x in value):
        raise ValidationError(f"{label}: expected a list of nonempty strings")
    if nonempty and not value:
        raise ValidationError(f"{label}: at least one value is required")
    if len(set(value)) != len(value):
        raise ValidationError(f"{label}: duplicate values")
    return value


def _source(value: Any) -> tuple[str, str]:
    parts = relative_path(value).split("/")
    if len(parts) < 3 or any(not REPO_PART.fullmatch(p) for p in parts[:2]):
        raise ValidationError("source must be owner/repo/path")
    return "/".join(parts[:2]), "/".join(parts[2:])


def _digest_fields(value: dict, label: str) -> None:
    if not isinstance(value.get("sha256"), str) or not SHA256.fullmatch(value["sha256"]):
        raise ValidationError(f"{label}: SHA-256 is required")
    if type(value.get("size")) is not int or value["size"] < 0:
        raise ValidationError(f"{label}: nonnegative byte size is required")


def _pinned_url(url: Any, source: dict) -> bool:
    normalized = urllib.parse.unquote(url.split("#", 1)[0]) if isinstance(url, str) else None
    return normalized in {
        f"https://github.com/{source['repo']}/blob/{source['commit']}/{source['path']}",
        f"https://raw.githubusercontent.com/{source['repo']}/{source['commit']}/{source['path']}",
    }


def _transforms(record: dict) -> None:
    transforms = record.get("transformations")
    if not isinstance(transforms, list):
        raise ValidationError(f"{record['path']}: transformations must be a list")
    for transform in transforms:
        if not isinstance(transform, dict):
            raise ValidationError("transformation must be a mapping")
        _text(transform.get("reason"), "transformation reason")
        kind = transform.get("kind")
        if kind == "replace":
            _text(transform.get("old"), "replacement old text")
            if not isinstance(transform.get("new"), str) or type(transform.get("expected_count")) is not int or transform["expected_count"] < 1:
                raise ValidationError("replacement requires new text and a positive exact occurrence count")
        elif kind == "frontmatter":
            if record["role"] != "skill" or not isinstance(transform.get("updates"), dict) or not transform["updates"]:
                raise ValidationError("frontmatter updates require a primary skill and nonempty mapping")
            if set(transform["updates"]) - {"name", "license", "metadata", "allowed-tools"}:
                raise ValidationError("frontmatter changes may only update name, license, metadata or tool formatting")
        elif kind == "notice":
            _text(transform.get("text"), "notice text")
        else:
            raise ValidationError(f"unknown transformation kind: {kind}")
    if record["role"] == "license" and transforms:
        raise ValidationError("controlling license bytes may not be transformed")


def _load_carryforward(result: Result) -> None:
    """Load the explicitly pinned PR 2 preservation policy, when present.

    The sole unresolved same-name proposal remains in ordinary import provenance.
    This manifest is evidence of carry-forward, not a new licence assessment.
    """
    relative = "provenance/pr2-carryforward.json"
    if not confined_path(result.root, relative).exists():
        return
    manifest = _read_document(result.root, relative)
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1:
        raise ValidationError(f"{relative}: schema_version must be 1")
    if manifest.get("source") != PR2_SOURCE:
        raise ValidationError(f"{relative}: immutable PR 2 source identity differs")
    added = _strings(manifest.get("added_slugs"), "PR 2 added_slugs", nonempty=True)
    if len(added) != 167:
        raise ValidationError("PR 2 protection must account for all 167 added slugs")
    seen, paths = set(), set()
    for category, expected in (("retained", 166), ("unresolved", 1)):
        rows = manifest.get(category)
        if not isinstance(rows, list) or len(rows) != expected:
            raise ValidationError(f"PR 2 {category}: exactly {expected} records required")
        for row in rows:
            if not isinstance(row, dict):
                raise ValidationError(f"PR 2 {category}: record must be a mapping")
            slug = row.get("slug")
            if not isinstance(slug, str) or not REGISTRY_ID.fullmatch(slug) or slug in seen:
                raise ValidationError("PR 2 record has an invalid or duplicate slug")
            seen.add(slug)
            entry = row.get("catalog_entry")
            if not isinstance(entry, dict) or entry.get("slug") != slug or entry.get("source") != "platform":
                raise ValidationError(f"{slug}: original platform catalog entry required")
            if category == "unresolved":
                if slug != PR2_PENDING_SLUG:
                    raise ValidationError("only product-experiment-design is an unresolved PR 2 name decision")
                _text(row.get("reason"), f"{slug} unresolved decision reason")
                result.unresolved.add(slug)
            else:
                if slug == PR2_PENDING_SLUG:
                    raise ValidationError("product-experiment-design must retain its unresolved decision")
                result.carryforward[slug] = row
            files = row.get("files")
            if not isinstance(files, list) or not files:
                raise ValidationError(f"{slug}: original PR 2 file inventory required")
            members = set()
            for record in files:
                if not isinstance(record, dict):
                    raise ValidationError(f"{slug}: file record must be a mapping")
                path = relative_path(record.get("path"))
                confined_path(result.root, path)
                prefix = f"skills/{slug}/"
                if not path.startswith(prefix):
                    raise ValidationError(f"{path}: PR 2 file must belong to its declared package")
                segments = path[len(prefix):].split("/")
                if len(segments) > MAX_PACKAGE_PATH_DEPTH or any(not PACKAGE_SEGMENT.fullmatch(p) for p in segments):
                    raise ValidationError(f"{path}: unsafe package segment or depth")
                if path.casefold() in paths:
                    raise ValidationError(f"{path}: duplicate/case-colliding PR 2 path")
                paths.add(path.casefold())
                members.add(path)
                _digest_fields(record, path)
                if record.get("mode") not in {"100644", "100755"}:
                    raise ValidationError(f"{path}: unsupported PR 2 file mode")
                if not isinstance(record.get("blob_sha1"), str) or not SHA1.fullmatch(record["blob_sha1"]):
                    raise ValidationError(f"{path}: original PR 2 Git blob SHA-1 required")
                if category == "retained":
                    result.carryforward_files[path] = record
            if f"skills/{slug}/SKILL.md" not in members:
                raise ValidationError(f"{slug}: PR 2 primary SKILL.md missing from inventory")
    if set(added) != seen:
        raise ValidationError("PR 2 added_slugs must equal retained plus unresolved slugs")


def _load_plan(root: Path) -> Result:
    result = Result(root)
    try:
        catalog = _read_document(root, "catalog.yml", as_yaml=True)
        manifest = _read_document(root, "provenance/files.json")
        evidence = _read_document(root, "provenance/evidence.json")
        if not isinstance(catalog, dict) or not isinstance(catalog.get("skills"), list) or not catalog["skills"]:
            raise ValidationError("catalog.yml: nonempty skills list required")
        if catalog.get("schema_version", 1) != 1:
            raise ValidationError("catalog.yml: standard v1 layout required")
        if not isinstance(manifest, dict) or manifest.get("schema_version") != 3 or not isinstance(manifest.get("files"), list) or not manifest["files"]:
            raise ValidationError("provenance/files.json: schema-v3 nonempty files list required")
        if not isinstance(evidence, dict) or evidence.get("schema_version") not in {2, 3} or not isinstance(evidence.get("observations"), list):
            raise ValidationError("provenance/evidence.json: observations list required")
        _load_carryforward(result)
        evidence_ids = set()
        for observation in evidence["observations"]:
            identity = _text(observation.get("id"), "evidence ID")
            if identity in evidence_ids:
                raise ValidationError(f"duplicate evidence ID: {identity}")
            evidence_ids.add(identity)
    except (OSError, ValueError, TypeError, AttributeError, yaml.YAMLError) as exc:
        result.errors.append(str(exc))
        return result
    seen_ids = set()
    for index, entry in enumerate(catalog["skills"]):
        try:
            if not isinstance(entry, dict):
                raise ValidationError("entry must be a mapping")
            slug = entry.get("slug")
            if not isinstance(slug, str) or not REGISTRY_ID.fullmatch(slug) or slug == "agent_building_guide":
                raise ValidationError("slug must be a non-reserved platform name of 1–64 characters")
            if slug in seen_ids:
                raise ValidationError(f"duplicate registry ID: {slug}")
            seen_ids.add(slug)
            if any(key in entry for key in ("path", "package_root", "upstream_commit", "name", "provenance")):
                raise ValidationError(f"{slug}: obsolete nested-layout catalog fields")
            categories = _strings(entry.get("categories"), f"{slug} categories", nonempty=True)
            if set(categories) - CATEGORIES:
                raise ValidationError(f"{slug}: unknown category")
            _strings(entry.get("required_providers"), f"{slug} required_providers")
            if slug in result.carryforward:
                if entry != result.carryforward[slug]["catalog_entry"]:
                    raise ValidationError(f"{slug}: catalog metadata differs from protected PR 2 entry")
                result.entries.append(entry)
                continue
            repo, upstream = _source(entry.get("source"))
            _text(entry.get("license"), f"{slug} license identifier")
            proof = _read_document(root, f"provenance/skills/{slug}.json")
            if not isinstance(proof, dict) or proof.get("schema_version") != 3 or proof.get("slug") != slug or proof.get("name") != slug:
                raise ValidationError(f"{slug}: per-skill provenance identity differs")
            src = proof.get("source")
            if not isinstance(src, dict) or src.get("repo") != repo or src.get("path") != upstream or not isinstance(src.get("commit"), str) or not SHA1.fullmatch(src["commit"]):
                raise ValidationError(f"{slug}: per-skill provenance source differs")
            _text(proof.get("author"), f"{slug} upstream author attribution")
            _text(proof.get("original_name"), f"{slug} original_name")
            if proof.get("status") not in {"core", "conditional"}:
                raise ValidationError(f"{slug}: provenance status must be core or conditional")
            license_meta = proof.get("license")
            if not isinstance(license_meta, dict) or license_meta.get("spdx") != entry["license"] or license_meta.get("file") != f"skills/{slug}/LICENSE":
                raise ValidationError(f"{slug}: per-skill license identity differs")
            refs = _strings(proof.get("evidence_ids"), f"{slug} evidence_ids", nonempty=True)
            if set(refs) - evidence_ids:
                raise ValidationError(f"{slug}: unresolved evidence IDs")
            if not isinstance(proof.get("packaging"), dict):
                raise ValidationError(f"{slug}: packaging record required")
            result.entries.append(entry)
            result.provenance[slug] = proof
        except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
            result.errors.append(f"catalog entry {index + 1}: {exc}")
    missing = (set(result.carryforward) | result.unresolved) - seen_ids
    if missing:
        result.errors.append("protected PR 2 catalog entries are missing: " + ", ".join(sorted(missing)))
    if result.unresolved - set(result.provenance):
        result.errors.append("unresolved PR 2 name must retain its separately reviewed import proposal")
    paths = set()
    for index, record in enumerate(manifest["files"]):
        try:
            if not isinstance(record, dict):
                raise ValidationError("file record must be a mapping")
            path = relative_path(record.get("path"))
            confined_path(root, path)
            parts = path.split("/")
            if len(parts) < 3 or parts[0] != "skills" or parts[1] not in result.provenance:
                raise ValidationError(f"{path}: output must belong to a declared skills/<slug>/ package")
            if path.casefold() in paths:
                raise ValidationError(f"duplicate/case-colliding manifest path: {path}")
            paths.add(path.casefold())
            relative = "/".join(parts[2:])
            if len(parts[2:]) > MAX_PACKAGE_PATH_DEPTH or any(not PACKAGE_SEGMENT.fullmatch(p) for p in parts[2:]):
                raise ValidationError(f"{path}: unsafe package segment or path depth exceeds 8")
            role = record.get("role")
            if role not in {"skill", "support", "license", "attribution"}:
                raise ValidationError(f"{path}: unsupported file role")
            if (relative == "SKILL.md") != (role == "skill") or (relative == "LICENSE") != (role == "license"):
                raise ValidationError(f"{path}: primary/controlling-license role differs from path")
            if relative != "SKILL.md" and parts[-1] == "SKILL.md":
                raise ValidationError(f"{path}: additional SKILL.md is not a selected package")
            _digest_fields(record, path)
            if record.get("mode") not in {"100644", "100755"}:
                raise ValidationError(f"{path}: unsupported mode (symlinks are forbidden)")
            _text(record.get("reason"), f"{path} inclusion reason")
            _transforms(record)
            src = record.get("source")
            if src is None:
                if role != "attribution" or not isinstance(record.get("content"), str) or record["transformations"]:
                    raise ValidationError(f"{path}: generated content is allowed only for untransformed attribution")
            else:
                if not isinstance(src, dict) or "content" in record:
                    raise ValidationError(f"{path}: sourced output cannot contain generated content")
                proof_source = result.provenance[parts[1]]["source"]
                if src.get("repo") != proof_source["repo"] or src.get("commit") != proof_source["commit"]:
                    raise ValidationError(f"{path}: source commit/repo does not match skill provenance")
                relative_path(src.get("path"))
                _digest_fields(src, path + " original")
                if not isinstance(src.get("blob_sha1"), str) or not SHA1.fullmatch(src["blob_sha1"]):
                    raise ValidationError(f"{path}: original Git blob SHA-1 required")
                if src.get("archive") != "provenance/originals/" + src["sha256"]:
                    raise ValidationError(f"{path}: archive path must match original SHA-256")
                confined_path(root, src["archive"])
            result.records[path] = record
        except (OSError, ValueError, TypeError) as exc:
            result.errors.append(f"manifest entry {index + 1}: {exc}")
    return result


def _inventory(root: Path, relative: str, errors: list[str]) -> set[str]:
    try:
        directory = confined_path(root, relative)
        if not directory.exists():
            return set()
        if not directory.is_dir():
            raise ValidationError(f"{relative} must be a directory")
        found = set()
        for parent, directories, files in os.walk(directory, followlinks=False, onerror=lambda exc: errors.append(str(exc))):
            for name in list(directories):
                child = Path(parent) / name
                if _is_link(child):
                    errors.append(f"symlink/reparse directory is not allowed: {child.relative_to(root).as_posix()}")
                    directories.remove(name)
            for name in files:
                child = Path(parent) / name
                path = child.relative_to(root).as_posix()
                if _is_link(child) or not stat.S_ISREG(child.lstat().st_mode):
                    errors.append(f"nonregular file is not allowed: {path}")
                else:
                    found.add(path)
        return found
    except (OSError, ValidationError) as exc:
        errors.append(str(exc))
        return set()


def frontmatter(content: bytes, label: str) -> tuple[dict, str]:
    # Path.read_text in the actual seed normalizes CRLF before parsing.
    text = content.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    match = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.DOTALL)
    if not match:
        raise ValidationError(f"{label}: canonical YAML frontmatter required")
    metadata = yaml.load(match.group(1), Loader=UniqueLoader)
    if not isinstance(metadata, dict) or not isinstance(metadata.get("name"), str):
        raise ValidationError(f"{label}: frontmatter name must be a string")
    return metadata, match.group(2).lstrip("\n")


def _skill_shape(content: bytes, slug: str) -> dict:
    metadata, body = frontmatter(content, slug)
    if metadata["name"] != slug:
        raise ValidationError(f"{slug}: frontmatter name differs from folder/catalog slug")
    description = metadata.get("description")
    if not isinstance(description, str) or not description.strip() or len(description.strip()) > 1024:
        raise ValidationError(f"{slug}: description must contain 1–1024 characters")
    if not body or len(body) > 50_000:
        raise ValidationError(f"{slug}: body must contain 1–50000 characters")
    triggers = metadata.get("triggers") or []
    if isinstance(triggers, str):
        triggers = [s.strip() for s in triggers.split(",") if s.strip()]
    elif not isinstance(triggers, list):
        raise ValidationError(f"{slug}: triggers must be a list or comma-delimited string")
    triggers = [str(t).strip() for t in triggers if str(t).strip()]
    if len(triggers) > 10 or any(len(t) > 64 for t in triggers):
        raise ValidationError(f"{slug}: triggers exceed 10 entries or 64 characters")
    return metadata


def _skill_content(content: bytes, entry: dict, proof: dict) -> None:
    slug = entry["slug"]
    metadata = _skill_shape(content, slug)
    if metadata.get("license") != entry["license"]:
        raise ValidationError(f"{slug}: frontmatter license differs")
    attribution = metadata.get("metadata")
    if not isinstance(attribution, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in attribution.items()):
        raise ValidationError(f"{slug}: metadata must map string keys to string values")
    for key, expected in {"author": proof["author"], "source": entry["source"], "source_url": proof.get("source_url")}.items():
        if attribution.get(key) != expected:
            raise ValidationError(f"{slug}: metadata {key} differs from provenance")


def validate(root: Path = ROOT, *, expected_count: int | None = None, allow_missing: bool = False, supplied: dict[str, bytes] | None = None, strict_modes: bool = False) -> Result:
    """Verify original archives, deterministic replay and installable package shape."""
    root = root.resolve()
    result = _load_plan(root)
    if result.errors:
        return result
    supplied = supplied or {}
    if set(supplied) - set(result.records):
        result.errors.append("supplied output files are not declared")
    if expected_count is not None and len(result.entries) != expected_count:
        result.errors.append(f"expected {expected_count} skills, catalog declares {len(result.entries)}")
    actual = _inventory(root, "skills", result.errors)
    declared = set(result.records) | set(result.carryforward_files)
    for path in sorted(actual - declared):
        result.errors.append(f"{path}: output file is not tracked by provenance/files.json or PR 2 carry-forward")
    effective = actual | set(supplied)
    if not allow_missing:
        for path in sorted(set(result.records) - effective):
            result.errors.append(f"{path}: manifest file is missing")
    expected_proofs = {f"provenance/skills/{slug}.json" for slug in result.provenance}
    if _inventory(root, "provenance/skills", result.errors) != expected_proofs:
        result.errors.append("per-skill provenance inventory differs from catalog")
    originals = {r["source"]["archive"] for r in result.records.values() if r.get("source")}
    if _inventory(root, "provenance/originals", result.errors) != originals:
        result.errors.append("original archive inventory differs: missing or unreferenced archive")
    for path, record in result.carryforward_files.items():
        try:
            # These files have no replay archive and must remain present even in
            # --restore mode. They are never regenerated from imported sources.
            content = confined_path(root, path).read_bytes()
            verify_original(record, content)
            if strict_modes and os.name != "nt":
                executable = bool(confined_path(root, path).stat().st_mode & 0o111)
                if executable != (record["mode"] == "100755"):
                    raise ValidationError(f"{path}: executable mode differs from protected PR 2 file")
        except (OSError, ValueError, TypeError, KeyError) as exc:
            result.errors.append(f"{path}: protected PR 2 file: {exc}")
    for slug, row in result.carryforward.items():
        members = row["files"]
        if len(members) - 1 > MAX_PACKAGE_FILES:
            result.errors.append(f"{slug}: package exceeds 100 sibling files")
        if any(r["size"] > MAX_PACKAGE_FILE_BYTES for r in members if r["path"] != f"skills/{slug}/SKILL.md"):
            result.errors.append(f"{slug}: package file exceeds 2 MiB")
        if sum(r["size"] for r in members) > MAX_PACKAGE_BYTES:
            result.errors.append(f"{slug}: package exceeds 20 MiB")
        try:
            _skill_shape(confined_path(root, f"skills/{slug}/SKILL.md").read_bytes(), slug)
        except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError) as exc:
            result.errors.append(f"{slug}: {exc}")
    from package import render_file  # Renderer owns only the declared mechanical changes.
    for path, record in result.records.items():
        try:
            if record.get("source"):
                src = record["source"]
                verify_original(src, confined_path(root, src["archive"]).read_bytes())
            rendered = render_file(record, root)
            verify_bytes(record, rendered)
            result.rendered[path] = rendered
            if path in effective:
                content = supplied[path] if path in supplied else confined_path(root, path).read_bytes()
                verify_bytes(record, content)
                if content != rendered:
                    raise ValidationError(f"{path}: output differs from recorded adaptation replay")
                if strict_modes and os.name != "nt" and path not in supplied:
                    executable = bool(confined_path(root, path).stat().st_mode & 0o111)
                    if executable != (record["mode"] == "100755"):
                        raise ValidationError(f"{path}: executable mode differs from manifest")
        except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError) as exc:
            result.errors.append(f"{path}: {exc}")
    for entry in result.entries:
        slug = entry["slug"]
        if slug in result.carryforward:
            continue
        prefix = f"skills/{slug}/"
        members = {p: r for p, r in result.records.items() if p.startswith(prefix)}
        primary = members.get(prefix + "SKILL.md")
        license_record = members.get(prefix + "LICENSE")
        if primary is None or license_record is None:
            result.errors.append(f"{slug}: required manifest file absent: SKILL.md or LICENSE")
            continue
        if not any(r["role"] == "attribution" for r in members.values()):
            result.errors.append(f"{slug}: attribution file required")
        if len(members) - 1 > MAX_PACKAGE_FILES:
            result.errors.append(f"{slug}: package exceeds 100 sibling files")
        if any(r["size"] > MAX_PACKAGE_FILE_BYTES for r in members.values() if r["role"] != "skill"):
            result.errors.append(f"{slug}: package file exceeds 2 MiB")
        if sum(r["size"] for r in members.values()) > MAX_PACKAGE_BYTES:
            result.errors.append(f"{slug}: package exceeds 20 MiB")
        proof = result.provenance[slug]
        try:
            src = primary["source"]
            if src["path"] != proof["source"]["path"] + "/SKILL.md":
                raise ValidationError("primary source path differs from skill provenance")
            if proof.get("primary_sha256") != src["sha256"] or proof.get("packaged_sha256") != primary["sha256"]:
                raise ValidationError("primary_sha256 or packaged_sha256 differs from manifest")
            if not _pinned_url(proof.get("source_url"), src):
                raise ValidationError("primary source URL differs")
            if not _pinned_url(proof["license"].get("source_url"), license_record["source"]):
                raise ValidationError("license source URL differs from exact copied source")
            if license_record["size"] == 0:
                raise ValidationError("controlling LICENSE is empty")
            if proof.get("source_modified") != any(r.get("source") and r["sha256"] != r["source"]["sha256"] for r in members.values()):
                raise ValidationError("source_modified differs from actual adapted bytes")
            original = confined_path(root, src["archive"]).read_bytes()
            original_meta = frontmatter(original, slug + " original")[0]
            if original_meta["name"] != proof["original_name"]:
                raise ValidationError("original_name differs from archived upstream frontmatter")
            if prefix + "SKILL.md" in result.rendered:
                packaged = result.rendered[prefix + "SKILL.md"]
                packaged_meta = frontmatter(packaged, slug)[0]
                permitted = {"name", "license", "metadata", "allowed-tools"}
                preserved_keys = (set(original_meta) | set(packaged_meta)) - permitted
                if any(original_meta.get(k) != packaged_meta.get(k) for k in preserved_keys):
                    raise ValidationError("original frontmatter fields changed outside permitted metadata adaptation")
                if original_meta.get("allowed-tools") != packaged_meta.get("allowed-tools"):
                    def tool_tokens(value: Any) -> list[str]:
                        if not isinstance(value, str):
                            raise ValidationError("allowed-tools may change only its string separator formatting")
                        return value.replace(",", " ").split()
                    if tool_tokens(original_meta.get("allowed-tools")) != tool_tokens(packaged_meta.get("allowed-tools")):
                        raise ValidationError("allowed-tools names changed beyond separator formatting")
                _skill_content(packaged, entry, proof)
        except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError) as exc:
            result.errors.append(f"{slug}: {exc}")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--expected-count", type=int)
    parser.add_argument("--strict-modes", action="store_true", help="verify executable bits on POSIX; Windows requires a Git-index check")
    args = parser.parse_args(argv)
    result = validate(args.root, expected_count=args.expected_count, strict_modes=args.strict_modes)
    for error in result.errors:
        print(f"error: {error}", file=sys.stderr)
    print(f"Checked {len(result.entries)} skills ({len(result.provenance)} reviewed imports, "
          f"{len(result.carryforward)} unchanged PR 2 packages), "
          f"{len(result.records) + len(result.carryforward_files)} packaged files: {len(result.errors)} error(s).")
    return 1 if result.errors else 0


if __name__ == "__main__":
    sys.exit(main())
