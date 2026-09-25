#!/usr/bin/env python3
"""Bind the complete catalogue and the expert roster to one release.

Check without changing files: ``python tools/release.py check``.
After an intentional content edit: ``python tools/release.py refresh``.
Neither command accesses an environment or publishes anything.
"""

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
HEX256 = re.compile(r"^[a-f0-9]{64}$")
SCHEMA_VERSION = 2
TOP_LEVEL_KEYS = (
    "schema_version", "release_key", "provenance", "catalog_sha256", "packages",
    "experts", "retirements", "retired_experts", "system_packages",
)
PATH_SEGMENT = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9._-]*$")


class ReleaseError(ValueError):
    """The candidate release is incomplete, inconsistent or unsafe."""


def canonical_json(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReleaseError(message)


def _keys(value: object, expected: set[str], label: str) -> dict:
    _require(isinstance(value, dict), f"{label} must be an object")
    _require(set(value) == expected, f"{label} must have exactly {sorted(expected)}")
    return value


def _name(value: object, label: str) -> str:
    _require(isinstance(value, str) and bool(NAME.fullmatch(value)), f"invalid {label}")
    return value


def _hash(value: object, label: str) -> str:
    _require(isinstance(value, str) and bool(HEX256.fullmatch(value)), f"invalid {label}")
    return value


def tracked_modes(root: Path) -> dict[str, str]:
    """Use Git modes on Windows, where filesystem executable bits are unavailable."""
    try:
        output = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--stage", "-z"],
            check=True, capture_output=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ReleaseError("release tooling requires a Git checkout") from exc
    result = {}
    for record in output.split(b"\0"):
        if not record:
            continue
        metadata, raw_path = record.split(b"\t", 1)
        mode, _, stage = metadata.decode("ascii").split()
        _require(stage == "0", "resolve Git conflicts before checking a release")
        result[raw_path.decode("utf-8")] = mode
    return result


def inventory(root: Path) -> tuple[str, list[dict]]:
    catalog_path = root / "catalog.yml"
    _require(not catalog_path.is_symlink(), "catalog.yml must not be a symlink")
    catalog_bytes = catalog_path.read_bytes()
    catalog = yaml.safe_load(catalog_bytes)
    _require(isinstance(catalog, dict), "catalog.yml must contain an object")
    entries = catalog.get("skills")
    _require(isinstance(entries, list) and bool(entries), "catalog.yml needs skills")
    slugs = [_name(e.get("slug"), "catalogue slug") for e in entries if isinstance(e, dict)]
    _require(len(slugs) == len(entries), "catalogue entries must be objects")
    _require(len(slugs) == len(set(slugs)), "duplicate catalogue slug")
    skills = root / "skills"
    _require(not skills.is_symlink(), "skills must not be a symlink")
    directories = {p.name for p in skills.iterdir() if p.is_dir()}
    _require(directories == set(slugs), "skills directories must equal catalogue slugs")
    modes = tracked_modes(root)
    packages = []
    for slug in sorted(slugs):
        folder = skills / slug
        _require(not folder.is_symlink(), f"{slug}: symlink package is forbidden")
        files = []
        for path in sorted(folder.rglob("*")):
            _require(not path.is_symlink(), f"{slug}: symlink is forbidden: {path.name}")
            if path.is_dir():
                continue
            _require(path.is_file(), f"{slug}: only regular files are allowed")
            relative = path.relative_to(folder).as_posix()
            _require(all(PATH_SEGMENT.fullmatch(p) for p in relative.split("/")), f"{slug}: invalid path {relative}")
            repo_path = path.relative_to(root).as_posix()
            mode = modes.get(repo_path)
            _require(mode in ("100644", "100755"), f"{repo_path}: stage regular files before release hashing")
            files.append({"path": relative, "sha256": sha256(path.read_bytes()), "executable": mode == "100755"})
        files.sort(key=lambda item: item["path"])
        _require(any(f["path"] == "SKILL.md" for f in files), f"{slug}: missing SKILL.md")
        packages.append({"slug": slug, "tree_sha256": sha256(canonical_json(files)), "files": files})
    return sha256(catalog_bytes), packages


def expert_inventory(root: Path, active: set[str]) -> list[dict]:
    """One entry per experts/<key>.yml: its key, exact-byte hash and bundled skills."""
    directory = root / "experts"
    _require(not directory.is_symlink(), "experts must not be a symlink")
    _require(directory.is_dir(), "experts/ directory is missing")
    experts = []
    for path in sorted(directory.iterdir()):
        _require(not path.is_symlink(), f"experts/{path.name}: symlink is forbidden")
        _require(path.is_file() and path.suffix == ".yml", f"experts/{path.name}: only <key>.yml files are allowed")
        key = _name(path.stem, f"expert file name experts/{path.name}")
        data = path.read_bytes()
        try:
            document = yaml.safe_load(data)
        except yaml.YAMLError as exc:
            raise ReleaseError(f"experts/{path.name}: not valid YAML: {exc}") from exc
        _require(isinstance(document, dict), f"experts/{path.name} must contain an object")
        _require(document.get("key") == key, f"experts/{path.name}: key must equal the file name")
        skills = document.get("skills")
        _require(isinstance(skills, list), f"{key}: skills must be an array")
        for slug in skills:
            _name(slug, f"{key} bundled skill")
        _require(len(skills) == len(set(skills)), f"{key}: duplicate bundled skill")
        missing = [slug for slug in skills if slug not in active]
        _require(not missing, f"{key}: bundled skill is not an active package: {', '.join(missing)}")
        experts.append({"key": key, "sha256": sha256(data), "skills": list(skills)})
    return experts


def validate_manifest(manifest: object) -> None:
    """Validate references before any publisher considers database writes."""
    value = _keys(manifest, set(TOP_LEVEL_KEYS), "release")
    _require(type(value["schema_version"]) is int and value["schema_version"] == SCHEMA_VERSION, "unsupported schema_version")
    _name(value["release_key"], "release_key")
    _require(isinstance(value["provenance"], dict) and bool(value["provenance"]), "provenance must be a nonempty object")
    _hash(value["catalog_sha256"], "catalog_sha256")
    _require(value["system_packages"] == [], "system packages require a supported schema extension")
    packages = value["packages"]
    _require(isinstance(packages, list) and bool(packages), "packages must be a nonempty array")
    active = set()
    for package in packages:
        package = _keys(package, {"slug", "tree_sha256", "files"}, "package")
        slug = _name(package["slug"], "package slug")
        _require(slug not in active, f"duplicate package: {slug}")
        active.add(slug)
        files = package["files"]
        _require(isinstance(files, list) and bool(files), f"{slug}: files must be nonempty")
        paths = set()
        for item in files:
            item = _keys(item, {"path", "sha256", "executable"}, f"{slug} file")
            path = item["path"]
            _require(isinstance(path, str) and bool(path) and all(PATH_SEGMENT.fullmatch(p) for p in path.split("/")), f"{slug}: invalid file path")
            _require(path not in paths, f"{slug}: duplicate file path {path}")
            paths.add(path)
            _hash(item["sha256"], f"{slug}/{path} hash")
            _require(type(item["executable"]) is bool, f"{slug}/{path}: executable must be boolean")
        _require("SKILL.md" in paths, f"{slug}: missing SKILL.md")
        _require(files == sorted(files, key=lambda f: f["path"]), f"{slug}: files must be sorted by path")
        _hash(package["tree_sha256"], f"{slug} tree hash")
        _require(package["tree_sha256"] == sha256(canonical_json(files)), f"{slug}: tree hash mismatch")
    _require(packages == sorted(packages, key=lambda p: p["slug"]), "packages must be sorted by slug")
    experts = value["experts"]
    _require(isinstance(experts, list), "experts must be an array")
    keys = set()
    for expert in experts:
        expert = _keys(expert, {"key", "sha256", "skills"}, "expert")
        key = _name(expert["key"], "expert key")
        _require(key not in keys, f"duplicate expert key: {key}")
        keys.add(key)
        _hash(expert["sha256"], f"{key} expert hash")
        assignments = expert["skills"]
        _require(isinstance(assignments, list), f"{key}: skills must be an array")
        for slug in assignments:
            _name(slug, f"{key} assigned skill")
        _require(len(assignments) == len(set(assignments)), f"{key}: duplicate skill assignment")
        _require(set(assignments) <= active, f"{key}: assigned skill missing from release")
    _require(experts == sorted(experts, key=lambda e: e["key"]), "experts must be sorted by key")
    retirements = value["retirements"]
    _require(isinstance(retirements, list), "retirements must be an array of slugs")
    for slug in retirements:
        _name(slug, "retired slug")
    _require(len(retirements) == len(set(retirements)), "duplicate retirement")
    _require(not (set(retirements) & active), "an active package cannot be retired")
    _require(retirements == sorted(retirements), "retirements must be sorted")
    retired_experts = value["retired_experts"]
    _require(isinstance(retired_experts, list), "retired_experts must be an array of expert keys")
    for key in retired_experts:
        _name(key, "retired expert key")
    _require(len(retired_experts) == len(set(retired_experts)), "duplicate retired expert")
    _require(not (set(retired_experts) & keys), "an active expert cannot be retired")
    _require(retired_experts == sorted(retired_experts), "retired_experts must be sorted")


def check(root: Path, manifest: dict) -> None:
    validate_manifest(manifest)
    catalog_hash, packages = inventory(root)
    _require(manifest["catalog_sha256"] == catalog_hash, "catalog.yml hash mismatch; review changes and refresh the release")
    _require(manifest["packages"] == packages, "package bytes, paths or modes differ from release.json")
    experts = expert_inventory(root, {p["slug"] for p in packages})
    listed = {e["key"] for e in manifest["experts"]}
    found = {e["key"] for e in experts}
    _require(not (found - listed), f"expert files not listed in release.json: {', '.join(sorted(found - listed))}")
    _require(not (listed - found), f"experts listed in release.json have no file: {', '.join(sorted(listed - found))}")
    for entry, actual in zip(manifest["experts"], experts):
        _require(entry["skills"] == actual["skills"], f"{entry['key']}: skills differ from experts/{entry['key']}.yml")
        _require(entry["sha256"] == actual["sha256"], f"{entry['key']}: expert file bytes differ from release.json; review changes and refresh the release")


def refreshed(root: Path, manifest: dict) -> dict:
    """Regenerate every derived field; keep the authored ones as they are."""
    catalog_hash, packages = inventory(root)
    derived = {
        "schema_version": SCHEMA_VERSION,
        "catalog_sha256": catalog_hash,
        "packages": packages,
        "experts": expert_inventory(root, {p["slug"] for p in packages}),
    }
    authored = {"retired_experts": [], **manifest}
    return {key: derived[key] if key in derived else authored.get(key) for key in TOP_LEVEL_KEYS}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "refresh"))
    args = parser.parse_args()
    try:
        path = ROOT / "release.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        if args.command == "refresh":
            manifest = refreshed(ROOT, manifest)
            validate_manifest(manifest)
            path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        check(ROOT, manifest)
        assignments = sum(len(e["skills"]) for e in manifest["experts"])
        print(
            f"{manifest['release_key']} (schema {manifest['schema_version']}): "
            f"{len(manifest['packages'])} packages, {len(manifest['experts'])} expert files, "
            f"{assignments} ordered skills, {len(manifest['retirements'])} retired packages, "
            f"{len(manifest['retired_experts'])} retired experts verified"
        )
        return 0
    except (ReleaseError, OSError, ValueError, yaml.YAMLError) as exc:
        print(f"error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
