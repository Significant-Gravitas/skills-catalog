#!/usr/bin/env python3
"""Validate the catalog the way the platform seed will.

    python tools/check.py

Fails on anything the seed would refuse, so a broken skill is caught on the
PR here rather than during a seed run against an environment. The rules
mirror backend/copilot/tools/skills.py in the platform repo; keep them in sync.
"""

import posixpath
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog.yml"
SKILLS_DIR = ROOT / "skills"

CATEGORIES = {
    "marketing",
    "sales",
    "finance",
    "support",
    "operations",
    "research",
    "content",
    "development",
}

MAX_NAME_CHARS = 64
MAX_DESCRIPTION_CHARS = 1024
MAX_BODY_CHARS = 50_000
MAX_TRIGGERS = 10
MAX_TRIGGER_CHARS = 64
MAX_PACKAGE_FILES = 100
MAX_PACKAGE_FILE_BYTES = 2 * 1024 * 1024
MAX_PACKAGE_BYTES = 20 * 1024 * 1024
MAX_PACKAGE_PATH_DEPTH = 8

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)
_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9._-]*$")
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_OUTSIDE_LINK_RE = re.compile(r"\]\((\.\./[^)]+)\)")


def main() -> int:
    errors: list[str] = []
    entries = _load_catalog(errors)
    listed = {e["slug"] for e in entries}
    for entry in entries:
        _check_skill(entry, errors)
    for directory in sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir()):
        if directory.name not in listed:
            errors.append(f"skills/{directory.name}: not listed in catalog.yml")
    for error in errors:
        print(f"error: {error}")
    print(f"{len(entries)} skills checked, {len(errors)} errors")
    return 1 if errors else 0


def _load_catalog(errors: list[str]) -> list[dict]:
    try:
        raw = yaml.safe_load(CATALOG.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        errors.append(f"catalog.yml: not valid YAML: {exc}")
        return []
    entries = raw.get("skills") or []
    seen: set[str] = set()
    valid: list[dict] = []
    for item in entries:
        slug = str(item.get("slug") or "").strip()
        if not slug:
            errors.append("catalog.yml: an entry has no slug")
            continue
        if slug in seen:
            errors.append(f"catalog.yml: '{slug}' is listed twice")
            continue
        seen.add(slug)
        categories = [str(c) for c in item.get("categories") or []]
        unknown = sorted(set(categories) - CATEGORIES)
        if not categories or unknown:
            errors.append(
                f"{slug}: categories must be one or more of "
                f"{sorted(CATEGORIES)}, got {categories}"
            )
        source = str(item.get("source") or "")
        if source != "platform" and len(source.split("/")) < 3:
            errors.append(f"{slug}: source must be 'platform' or owner/repo/path")
        if source != "platform" and not item.get("license"):
            errors.append(f"{slug}: a vendored skill needs its upstream license")
        valid.append(item)
    if not valid and not errors:
        errors.append("catalog.yml lists no skills")
    return valid


def _check_skill(entry: dict, errors: list[str]) -> None:
    slug = entry["slug"]
    directory = SKILLS_DIR / slug
    skill_md = directory / "SKILL.md"
    if not skill_md.is_file():
        errors.append(f"{slug}: skills/{slug}/SKILL.md is missing")
        return
    text = skill_md.read_text(encoding="utf-8")
    _check_skill_md(slug, text, errors)
    _check_package(slug, directory, len(text.encode("utf-8")), errors)
    for path in sorted(directory.rglob("*.md")):
        for match in _OUTSIDE_LINK_RE.finditer(path.read_text(encoding="utf-8")):
            rel = path.relative_to(directory).as_posix()
            errors.append(f"{slug}: {rel} links outside the skill: {match.group(1)}")


def _check_skill_md(slug: str, text: str, errors: list[str]) -> None:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        errors.append(f"{slug}: SKILL.md has no YAML frontmatter")
        return
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        errors.append(f"{slug}: frontmatter is not valid YAML: {exc}")
        return
    if not isinstance(meta, dict):
        errors.append(f"{slug}: frontmatter must be a mapping")
        return
    name = str(meta.get("name") or "").strip()
    description = str(meta.get("description") or "").strip()
    if name != slug:
        errors.append(f"{slug}: frontmatter name is '{name}', must match the slug")
    if not _NAME_RE.match(name) or len(name) > MAX_NAME_CHARS:
        errors.append(f"{slug}: name must be lowercase kebab-case, ≤{MAX_NAME_CHARS}")
    if not description:
        errors.append(f"{slug}: description is required")
    elif len(description) > MAX_DESCRIPTION_CHARS:
        errors.append(f"{slug}: description is over {MAX_DESCRIPTION_CHARS} chars")
    triggers = meta.get("triggers") or []
    if isinstance(triggers, str):
        triggers = [t.strip() for t in triggers.split(",") if t.strip()]
    if len(triggers) > MAX_TRIGGERS:
        errors.append(f"{slug}: more than {MAX_TRIGGERS} triggers")
    for trigger in triggers:
        if len(str(trigger)) > MAX_TRIGGER_CHARS:
            errors.append(f"{slug}: trigger '{trigger}' is over {MAX_TRIGGER_CHARS}")
    body = match.group(2).lstrip("\n")
    if len(body) > MAX_BODY_CHARS:
        errors.append(f"{slug}: body is {len(body)} chars, over {MAX_BODY_CHARS}")


def _check_package(
    slug: str, directory: Path, skill_md_bytes: int, errors: list[str]
) -> None:
    files = [p for p in directory.rglob("*") if p.is_file() and p.name != "SKILL.md"]
    if len(files) > MAX_PACKAGE_FILES:
        errors.append(f"{slug}: {len(files)} package files, limit {MAX_PACKAGE_FILES}")
    total = skill_md_bytes
    for path in files:
        rel = path.relative_to(directory).as_posix()
        size = path.stat().st_size
        total += size
        if size > MAX_PACKAGE_FILE_BYTES:
            errors.append(f"{slug}: {rel} is {size} bytes, over the per-file cap")
        problem = _path_error(rel)
        if problem:
            errors.append(f"{slug}: {rel}: {problem}")
    if total > MAX_PACKAGE_BYTES:
        errors.append(f"{slug}: package is {total} bytes, over {MAX_PACKAGE_BYTES}")


def _path_error(path: str) -> str | None:
    if posixpath.normpath(path) != path:
        return "path is not normalised"
    segments = path.split("/")
    if len(segments) > MAX_PACKAGE_PATH_DEPTH:
        return f"{len(segments)} segments deep, limit {MAX_PACKAGE_PATH_DEPTH}"
    for segment in segments:
        if not _SEGMENT_RE.match(segment):
            return f"segment '{segment}' must be letters, digits, '.', '_' or '-' and not hidden"
    return None


if __name__ == "__main__":
    sys.exit(main())
