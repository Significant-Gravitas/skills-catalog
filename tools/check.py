#!/usr/bin/env python3
"""Validate the catalog and expert roster the way the platform seed will.

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
EXPERTS_DIR = ROOT / "experts"

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
MAX_DAY_ONE = 3
MAX_DAY_ONE_TITLE_CHARS = 80
MAX_DAY_ONE_DESCRIPTION_CHARS = 240
MAX_DAY_ONE_TIMING_CHARS = 40
SESSION_MODES = {"THREAD", "FRESH"}
EXPERT_FIELDS = {
    "key", "name", "role", "job_title", "tagline", "avatar_url", "categories",
    "bio", "identity", "voice_preferences", "voice_samples", "boundaries",
    "day_one", "preloads", "routines", "skills",
}
ROUTINE_FIELDS = {"key", "title", "prompt", "crons", "asks", "session_mode"}

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)
_SEGMENT_RE = re.compile(r"^[A-Za-z0-9_-][A-Za-z0-9._-]*$")
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
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
    experts = _check_experts(listed, errors)
    for error in errors:
        print(f"error: {error}")
    print(f"{len(entries)} skills and {experts} experts checked, {len(errors)} errors")
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


def _check_experts(slugs: set[str], errors: list[str]) -> int:
    """Validate every experts/<key>.yml against the release schema 2 roster."""
    if not EXPERTS_DIR.is_dir():
        errors.append("experts/: directory is missing")
        return 0
    names: dict[str, str] = {}
    count = 0
    for path in sorted(EXPERTS_DIR.iterdir()):
        label = f"experts/{path.name}"
        if not path.is_file() or path.suffix != ".yml":
            errors.append(f"{label}: only <key>.yml files belong in experts/")
            continue
        count += 1
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            errors.append(f"{label}: not valid YAML: {exc}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{label}: must be a mapping")
            continue
        _check_expert(label, path.stem, data, slugs, errors)
        name = data.get("name")
        if isinstance(name, str) and name.strip():
            folded = name.strip().casefold()
            if folded in names:
                errors.append(f"{label}: display name '{name}' is already used by {names[folded]}")
            else:
                names[folded] = label
    return count


def _check_expert(
    label: str, stem: str, data: dict, slugs: set[str], errors: list[str]
) -> None:
    missing = sorted(EXPERT_FIELDS - set(data))
    extra = sorted(str(k) for k in set(data) - EXPERT_FIELDS)
    if missing:
        errors.append(f"{label}: missing fields {missing}")
    if extra:
        errors.append(f"{label}: unknown fields {extra}")

    key = data.get("key")
    if not isinstance(key, str) or not _KEY_RE.match(key):
        errors.append(f"{label}: key must be lowercase kebab-case, ≤64")
    elif key != stem:
        errors.append(f"{label}: key '{key}' must match the file name")

    for field in ("name", "role", "job_title", "tagline", "bio", "identity"):
        if field in data and not _nonempty(data[field]):
            errors.append(f"{label}: {field} must be a non-empty string")
    for field in ("voice_preferences", "boundaries"):
        if field in data and not isinstance(data[field], str):
            errors.append(f"{label}: {field} must be a string")
    if "avatar_url" in data and not (
        data["avatar_url"] is None or isinstance(data["avatar_url"], str)
    ):
        errors.append(f"{label}: avatar_url must be a string or null")

    if "categories" in data:
        categories = data["categories"]
        if not isinstance(categories, list) or not categories or not all(
            isinstance(c, str) and c in CATEGORIES for c in categories
        ):
            errors.append(
                f"{label}: categories must be one or more of "
                f"{sorted(CATEGORIES)}, got {categories}"
            )

    if "voice_samples" in data:
        samples = data["voice_samples"]
        if not isinstance(samples, list):
            errors.append(f"{label}: voice_samples must be a list")
        else:
            for i, sample in enumerate(samples):
                if not _exact(sample, {"label", "text"}) or not all(
                    isinstance(sample[f], str) for f in ("label", "text")
                ):
                    errors.append(f"{label}: voice_samples[{i}] must be label and text strings")

    if "day_one" in data:
        _check_day_one(label, data["day_one"], errors)
    if "preloads" in data:
        _check_preloads(label, data["preloads"], errors)
    if "routines" in data:
        _check_routines(label, data["routines"], errors)

    if "skills" in data:
        skills = data["skills"]
        if not isinstance(skills, list) or not all(isinstance(s, str) for s in skills):
            errors.append(f"{label}: skills must be a list of catalog slugs")
        else:
            if len(skills) != len(set(skills)):
                errors.append(f"{label}: skills lists a slug twice")
            for slug in skills:
                if slug not in slugs:
                    errors.append(f"{label}: skill '{slug}' is not in catalog.yml")


def _check_day_one(label: str, rows: object, errors: list[str]) -> None:
    if not isinstance(rows, list):
        errors.append(f"{label}: day_one must be a list")
        return
    if len(rows) > MAX_DAY_ONE:
        errors.append(f"{label}: day_one has {len(rows)} items, limit {MAX_DAY_ONE}")
    for i, row in enumerate(rows):
        fields = ("title", "description", "timing")
        if not _exact(row, set(fields)) or not all(isinstance(row[f], str) for f in fields):
            errors.append(f"{label}: day_one[{i}] must be title, description and timing strings")
            continue
        if not 1 <= len(row["title"]) <= MAX_DAY_ONE_TITLE_CHARS:
            errors.append(f"{label}: day_one[{i}] title must be 1-{MAX_DAY_ONE_TITLE_CHARS} chars")
        if len(row["description"]) > MAX_DAY_ONE_DESCRIPTION_CHARS:
            errors.append(f"{label}: day_one[{i}] description is over {MAX_DAY_ONE_DESCRIPTION_CHARS} chars")
        if len(row["timing"]) > MAX_DAY_ONE_TIMING_CHARS:
            errors.append(f"{label}: day_one[{i}] timing is over {MAX_DAY_ONE_TIMING_CHARS} chars")


def _check_preloads(label: str, rows: object, errors: list[str]) -> None:
    if not isinstance(rows, list):
        errors.append(f"{label}: preloads must be a list")
        return
    seen: set[str] = set()
    for i, row in enumerate(rows):
        if (
            not _exact(row, {"slug", "cron"})
            or not _nonempty(row["slug"])
            or not (row["cron"] is None or isinstance(row["cron"], str))
        ):
            errors.append(f"{label}: preloads[{i}] must be a slug with a cron string or null")
            continue
        if row["slug"] in seen:
            errors.append(f"{label}: preload '{row['slug']}' is listed twice")
        seen.add(row["slug"])


def _check_routines(label: str, rows: object, errors: list[str]) -> None:
    if not isinstance(rows, list):
        errors.append(f"{label}: routines must be a list")
        return
    seen: set[str] = set()
    for i, row in enumerate(rows):
        where = f"{label}: routines[{i}]"
        if not _exact(row, ROUTINE_FIELDS):
            errors.append(f"{where} must have exactly {sorted(ROUTINE_FIELDS)}")
            continue
        key = row["key"]
        if not isinstance(key, str) or not _KEY_RE.match(key):
            errors.append(f"{where}: key must be lowercase kebab-case, ≤64")
        elif key in seen:
            errors.append(f"{where}: routine key '{key}' is used twice")
        else:
            seen.add(key)
        for field in ("title", "prompt"):
            if not _nonempty(row[field]):
                errors.append(f"{where}: {field} must be a non-empty string")
        for field in ("crons", "asks"):
            if not isinstance(row[field], list) or not all(isinstance(v, str) for v in row[field]):
                errors.append(f"{where}: {field} must be a list of strings")
        if row["session_mode"] not in SESSION_MODES:
            errors.append(f"{where}: session_mode must be one of {sorted(SESSION_MODES)}")


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _exact(value: object, fields: set[str]) -> bool:
    return isinstance(value, dict) and set(value) == fields


if __name__ == "__main__":
    sys.exit(main())
