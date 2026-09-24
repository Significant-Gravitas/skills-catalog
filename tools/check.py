#!/usr/bin/env python3
"""Validate schema-v2 provenance and unchanged source bytes, offline.

This is an archival integrity contract, not a platform-import compatibility
check. Upstream names, frontmatter, body sizes and relative links are preserved.
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
REGISTRY_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
REPO_PART = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.-]*$")


class ValidationError(ValueError):
    pass


class UniqueLoader(yaml.SafeLoader):
    """Reject duplicate YAML keys instead of silently discarding information."""


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
    """Require an unambiguous relative POSIX path on Windows and Unix."""
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValidationError(f"unsafe relative path: {value!r}")
    if any(ord(c) < 32 for c in value):
        raise ValidationError(f"control character in path: {value!r}")
    parts = value.split("/")
    if any(p in {"", ".", ".."} or p.endswith((" ", ".")) for p in parts):
        raise ValidationError(f"path must be normalized and confined: {value!r}")
    return value


def _is_link(path: Path) -> bool:
    if path.is_symlink():
        return True
    try:
        # Includes Windows junctions, which may not be reported as symlinks.
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
    path = record["path"]
    if len(content) != record["size"]:
        raise ValidationError(f"{path}: size differs from immutable manifest")
    if hashlib.sha256(content).hexdigest() != record["sha256"]:
        raise ValidationError(f"{path}: SHA-256 differs from immutable manifest")
    if git_blob_sha1(content) != record["source"]["blob_sha1"]:
        raise ValidationError(f"{path}: Git blob SHA-1 differs from immutable manifest")


@dataclass
class Result:
    root: Path
    entries: list[dict] = field(default_factory=list)
    records: dict[str, dict] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    provenance: dict[str, dict] = field(default_factory=dict)

    def require_valid(self) -> None:
        if self.errors:
            raise ValidationError("\n".join(self.errors))


def _read_document(root: Path, relative: str, *, as_yaml: bool = False) -> Any:
    text = confined_path(root, relative).read_text(encoding="utf-8-sig")
    if as_yaml:
        return yaml.load(text, Loader=UniqueLoader)
    return json.loads(text, object_pairs_hook=_json_pairs)


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


def _load_plan(root: Path) -> Result:
    result = Result(root)
    try:
        catalog = _read_document(root, "catalog.yml", as_yaml=True)
        manifest = _read_document(root, "provenance/files.json")
        evidence = _read_document(root, "provenance/evidence.json")
        if not isinstance(catalog, dict) or catalog.get("schema_version") != 2:
            raise ValidationError("catalog.yml: schema_version must be 2")
        if not isinstance(manifest, dict) or manifest.get("schema_version") != 2:
            raise ValidationError("provenance/files.json: schema_version must be 2")
        if not isinstance(catalog.get("skills"), list) or not catalog["skills"]:
            raise ValidationError("catalog.yml: skills must be a nonempty list")
        if not isinstance(manifest.get("files"), list) or not manifest["files"]:
            raise ValidationError("provenance/files.json: files must be a nonempty list")
        if not isinstance(evidence, dict) or evidence.get("schema_version") != 2 or not isinstance(evidence.get("observations"), list):
            raise ValidationError("provenance/evidence.json: schema-v2 observations list required")
        evidence_ids = set()
        for observation in evidence["observations"]:
            if not isinstance(observation, dict) or not isinstance(observation.get("id"), str) or not observation["id"]:
                raise ValidationError("evidence observation requires an ID")
            if observation["id"] in evidence_ids:
                raise ValidationError(f"duplicate evidence ID: {observation['id']}")
            evidence_ids.add(observation["id"])
    except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
        result.errors.append(str(exc))
        return result
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    pins: dict[str, str] = {}
    for index, entry in enumerate(catalog["skills"]):
        try:
            if not isinstance(entry, dict):
                raise ValidationError("entry must be a mapping")
            slug = entry.get("slug")
            if not isinstance(slug, str) or not REGISTRY_ID.fullmatch(slug):
                raise ValidationError("slug must be a lowercase registry ID")
            if slug in seen_ids:
                raise ValidationError(f"duplicate registry ID: {slug}")
            seen_ids.add(slug)
            name = entry.get("name")
            if not isinstance(name, str) or not name:
                raise ValidationError(f"{slug}: original name is required")
            repo, upstream_path = _source(entry.get("source"))
            pin = entry.get("upstream_commit")
            if not isinstance(pin, str) or not SHA1.fullmatch(pin):
                raise ValidationError(f"{slug}: upstream_commit must be a full immutable SHA")
            if repo in pins and pins[repo] != pin:
                raise ValidationError(f"{slug}: multiple commits share package_root for {repo}")
            pins[repo] = pin
            if entry.get("package_root") != f"skills/{repo}":
                raise ValidationError(f"{slug}: package_root must match skills/owner/repo")
            path = relative_path(entry.get("path"))
            confined_path(root, path)
            if path != f"skills/{repo}/{upstream_path}":
                raise ValidationError(f"{slug}: path must preserve original source layout")
            if path.casefold() in seen_paths:
                raise ValidationError(f"{slug}: duplicate/case-colliding skill path: {path}")
            seen_paths.add(path.casefold())
            categories = _strings(entry.get("categories"), f"{slug} categories", nonempty=True)
            if set(categories) - CATEGORIES:
                raise ValidationError(f"{slug}: unknown categories: {sorted(set(categories) - CATEGORIES)}")
            _strings(entry.get("required_providers"), f"{slug} required_providers")
            _strings(entry.get("experts"), f"{slug} experts")
            if entry.get("status") not in {"core", "conditional"}:
                raise ValidationError(f"{slug}: status must be core or conditional")
            if not isinstance(entry.get("license"), str) or not entry["license"].strip():
                raise ValidationError(f"{slug}: license identifier is required")
            if entry.get("provenance") != f"provenance/skills/{slug}.json":
                raise ValidationError(f"{slug}: provenance path must match registry ID")
            proof = _read_document(root, entry["provenance"])
            expected_source = {"repo": repo, "commit": pin, "path": upstream_path}
            if not isinstance(proof, dict) or proof.get("slug") != slug or proof.get("name") != name:
                raise ValidationError(f"{slug}: per-skill provenance identity differs")
            if not isinstance(proof.get("source"), dict) or any(proof["source"].get(k) != v for k, v in expected_source.items()):
                raise ValidationError(f"{slug}: per-skill provenance source differs")
            if not isinstance(proof.get("author"), str) or not proof["author"].strip():
                raise ValidationError(f"{slug}: upstream author attribution is required")
            if proof.get("status") != entry["status"]:
                raise ValidationError(f"{slug}: provenance status differs from catalog")
            license_meta = proof.get("license")
            if not isinstance(license_meta, dict) or license_meta.get("spdx") != entry["license"] or license_meta.get("file") != path + "/LICENSE":
                raise ValidationError(f"{slug}: per-skill license identity differs from catalog/path")
            refs = _strings(proof.get("evidence_ids"), f"{slug} evidence_ids", nonempty=True)
            if set(refs) - evidence_ids:
                raise ValidationError(f"{slug}: unresolved evidence IDs: {sorted(set(refs) - evidence_ids)}")
            result.provenance[slug] = proof
            result.entries.append(entry)
        except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
            result.errors.append(f"catalog entry {index + 1}: {exc}")
    file_paths: set[str] = set()
    for index, record in enumerate(manifest["files"]):
        try:
            if not isinstance(record, dict):
                raise ValidationError("file record must be a mapping")
            path = relative_path(record.get("path"))
            confined_path(root, path)
            if not path.startswith("skills/"):
                raise ValidationError(f"{path}: manifest covers only skills/")
            if path.casefold() in file_paths:
                raise ValidationError(f"duplicate/case-colliding manifest path: {path}")
            file_paths.add(path.casefold())
            source = record.get("source")
            if not isinstance(source, dict):
                raise ValidationError(f"{path}: source mapping is required")
            repo = source.get("repo")
            source_path = relative_path(source.get("path"))
            if not isinstance(repo, str) or repo not in pins:
                raise ValidationError(f"{path}: source repo is not in catalog")
            if source.get("commit") != pins[repo]:
                raise ValidationError(f"{path}: source commit does not match catalog pin")
            if not isinstance(source.get("blob_sha1"), str) or not SHA1.fullmatch(source["blob_sha1"]):
                raise ValidationError(f"{path}: full source Git blob SHA-1 is required")
            if record.get("role") == "upstream":
                if path != f"skills/{repo}/{source_path}":
                    raise ValidationError(f"{path}: upstream path was relocated")
            elif record.get("role") == "license-copy":
                owners = [e for e in result.entries if path == e["path"] + "/LICENSE"]
                if not owners or owners[0]["package_root"] != f"skills/{repo}":
                    raise ValidationError(f"{path}: license-copy must be in its owning skill folder")
            else:
                raise ValidationError(f"{path}: role must be upstream or license-copy")
            if not isinstance(record.get("sha256"), str) or not SHA256.fullmatch(record["sha256"]):
                raise ValidationError(f"{path}: SHA-256 is required")
            if type(record.get("size")) is not int or record["size"] < 0:
                raise ValidationError(f"{path}: nonnegative byte size is required")
            if record.get("mode") not in {"100644", "100755"}:
                raise ValidationError(f"{path}: unsupported source mode (symlinks are forbidden)")
            result.records[path] = record
        except (OSError, ValueError, TypeError) as exc:
            result.errors.append(f"manifest entry {index + 1}: {exc}")
    return result


def _inventory(root: Path, errors: list[str]) -> set[str]:
    try:
        directory = confined_path(root, "skills")
        if not directory.exists():
            return set()
        if not directory.is_dir():
            raise ValidationError("skills must be a directory")
        found = set()
        for parent, directories, files in os.walk(directory, followlinks=False, onerror=lambda exc: errors.append(str(exc))):
            for name in list(directories):
                child = Path(parent) / name
                if _is_link(child):
                    errors.append(f"symlink/reparse directory is not allowed: {child.relative_to(root).as_posix()}")
                    directories.remove(name)
            for name in files:
                child = Path(parent) / name
                relative = child.relative_to(root).as_posix()
                if _is_link(child) or not stat.S_ISREG(child.lstat().st_mode):
                    errors.append(f"nonregular source file is not allowed: {relative}")
                else:
                    found.add(relative)
        return found
    except (OSError, ValidationError) as exc:
        errors.append(str(exc))
        return set()


def _original_name(content: bytes, label: str) -> str:
    lines = content.decode("utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValidationError(f"{label}: SKILL.md must start with YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValidationError(f"{label}: frontmatter closing delimiter missing") from exc
    metadata = yaml.load("\n".join(lines[1:end]), Loader=UniqueLoader)
    if not isinstance(metadata, dict) or not isinstance(metadata.get("name"), str):
        raise ValidationError(f"{label}: frontmatter name must be a string")
    return metadata["name"]


def validate(root: Path = ROOT, *, expected_count: int | None = None, allow_missing: bool = False, supplied: dict[str, bytes] | None = None, strict_modes: bool = False) -> Result:
    """supplied overlays downloads for complete preflight without source writes."""
    root = root.resolve()
    result = _load_plan(root)
    if result.errors:
        return result
    supplied = supplied or {}
    if set(supplied) - set(result.records):
        result.errors.append(f"supplied files not declared: {sorted(set(supplied) - set(result.records))}")
    if expected_count is not None and len(result.entries) != expected_count:
        result.errors.append(f"expected {expected_count} skills, catalog declares {len(result.entries)}")
    actual = _inventory(root, result.errors)
    effective = actual | set(supplied)
    for path in sorted(actual - set(result.records)):
        result.errors.append(f"{path}: source file is not tracked by provenance/files.json")
    if not allow_missing:
        for path in sorted(set(result.records) - effective):
            result.errors.append(f"{path}: manifest file is missing")
    declared_skills = {e["path"] + "/SKILL.md" for e in result.entries}
    manifest_skills = {p for p in result.records if p.endswith("/SKILL.md")}
    if declared_skills != manifest_skills:
        result.errors.append("SKILL.md completeness differs: " + f"undeclared={sorted(manifest_skills - declared_skills)}, untracked={sorted(declared_skills - manifest_skills)}")
    for path in sorted(effective & set(result.records)):
        try:
            content = supplied[path] if path in supplied else confined_path(root, path).read_bytes()
            verify_bytes(result.records[path], content)
            if strict_modes and os.name != "nt" and path not in supplied:
                executable = bool(confined_path(root, path).stat().st_mode & 0o111)
                if executable != (result.records[path]["mode"] == "100755"):
                    result.errors.append(f"{path}: executable mode differs from manifest")
        except (OSError, ValueError) as exc:
            result.errors.append(str(exc))
    for entry in result.entries:
        skill_path = entry["path"] + "/SKILL.md"
        license_path = entry["path"] + "/LICENSE"
        for required in (skill_path, license_path):
            if required not in result.records:
                result.errors.append(f"{entry['slug']}: required manifest file absent: {required}")
        if license_path in result.records and result.records[license_path]["size"] == 0:
            result.errors.append(f"{entry['slug']}: controlling LICENSE is empty")
        proof = result.provenance[entry["slug"]]
        if skill_path in result.records and proof.get("primary_sha256") != result.records[skill_path]["sha256"]:
            result.errors.append(f"{entry['slug']}: primary_sha256 differs from SKILL.md manifest")
        if license_path in result.records:
            src = result.records[license_path]["source"]
            expected_urls = {
                f"https://github.com/{src['repo']}/blob/{src['commit']}/{src['path']}",
                f"https://raw.githubusercontent.com/{src['repo']}/{src['commit']}/{src['path']}",
            }
            license_url = proof["license"].get("source_url")
            normalized_url = urllib.parse.unquote(license_url.split("#", 1)[0]) if isinstance(license_url, str) else None
            if normalized_url not in expected_urls:
                result.errors.append(f"{entry['slug']}: license source URL differs from exact copied source")
        if skill_path not in effective:
            continue
        try:
            content = supplied[skill_path] if skill_path in supplied else confined_path(root, skill_path).read_bytes()
            if _original_name(content, entry["slug"]) != entry["name"]:
                result.errors.append(f"{entry['slug']}: original frontmatter name differs from catalog name")
            record = result.records.get(skill_path)
            if record and record["role"] != "upstream":
                result.errors.append(f"{entry['slug']}: SKILL.md must have upstream provenance")
        except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
            result.errors.append(str(exc))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--expected-count", type=int)
    parser.add_argument("--strict-modes", action="store_true", help="also compare POSIX executable bits (Windows uses Git index validation)")
    args = parser.parse_args(argv)
    result = validate(args.root, expected_count=args.expected_count, strict_modes=args.strict_modes)
    for error in result.errors:
        print(f"error: {error}", file=sys.stderr)
    print(f"{len(result.entries)} skills, {len(result.records)} source files, {len(result.errors)} errors")
    return int(bool(result.errors))


if __name__ == "__main__":
    sys.exit(main())
