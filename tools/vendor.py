#!/usr/bin/env python3
"""Vendor skills listed in catalog.yml from their public GitHub repos.

    python tools/vendor.py            # every entry with a GitHub source
    python tools/vendor.py cold-email # one slug

For each approved entry whose ``source`` is ``owner/repo/path`` the script
downloads the skill folder at its pinned ``source_commit``, drops upstream eval
fixtures and hidden files, copies the repo licence in beside the skill, and
rewrites the SKILL.md frontmatter so the listing carries where it came from.

Only the stdlib plus PyYAML. Set GITHUB_TOKEN to lift the anonymous API rate
limit.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog.yml"
SKILLS_DIR = ROOT / "skills"

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"

SKIPPED_DIRS = {"evals", "eval", "tests", "__tests__"}
LICENSE_NAMES = ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "LICENCE.md")

# The platform stores the SKILL.md body in the listing; this mirrors its cap.
MAX_BODY_CHARS = 50_000

# Upstream sections that only make sense inside the upstream repo: sponsored
# tool tables and links into sibling folders the vendored copy does not carry.
DROPPED_SECTIONS = ("## Tool Integrations",)
DROPPED_LINE_RE = re.compile(r"(\.\./)+tools/")

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?(.*)$", re.DOTALL)


def _get(url: str) -> bytes:
    headers = {"User-Agent": "skills-catalog-vendor"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as r:
        return r.read()


def _api(path: str) -> dict:
    return json.loads(_get(f"{API}{path}"))


def _split_source(source: str) -> tuple[str, str, str]:
    owner, repo, *rest = source.split("/")
    return owner, repo, "/".join(rest)


def _tree(owner: str, repo: str, commit: str) -> tuple[str, list[dict]]:
    sha = _api(f"/repos/{owner}/{repo}/commits/{commit}")["sha"]
    if sha != commit:
        raise RuntimeError(f"{owner}/{repo}: source_commit did not resolve exactly")
    tree = _api(f"/repos/{owner}/{repo}/git/trees/{sha}?recursive=1")
    if tree.get("truncated"):
        raise RuntimeError(f"{owner}/{repo} tree is truncated; vendor by hand")
    return sha, [b for b in tree["tree"] if b["type"] == "blob"]


def _wanted(relative: str) -> bool:
    segments = relative.split("/")
    if any(s.startswith(".") for s in segments):
        return False
    return not any(s in SKIPPED_DIRS for s in segments[:-1])


def _find_license(blobs: list[dict], skill_path: str) -> str | None:
    candidates = [f"{skill_path}/{n}" for n in LICENSE_NAMES] + list(LICENSE_NAMES)
    paths = {b["path"] for b in blobs}
    return next((c for c in candidates if c in paths), None)


def _clean_markdown(text: str, label: str, *, drop_sections: bool) -> str:
    kept: list[str] = []
    dropping = False
    for line in text.split("\n"):
        if drop_sections and line.startswith("## "):
            dropping = line.strip() in DROPPED_SECTIONS
        if dropping or DROPPED_LINE_RE.search(line):
            continue
        kept.append(line)
    cleaned = "\n".join(kept).rstrip() + "\n"
    for match in re.finditer(r"\]\((\.\./[^)]+)\)", cleaned):
        print(f"  warning: {label} still links outside its folder: {match.group(1)}")
    return cleaned


def _clean_body(body: str, slug: str) -> str:
    cleaned = _clean_markdown(body, slug, drop_sections=True)
    if len(cleaned) > MAX_BODY_CHARS:
        print(f"  warning: {slug} body is {len(cleaned)} chars, over {MAX_BODY_CHARS}")
    return cleaned


def _rewrite_skill_md(
    text: str, entry: dict, owner: str, repo: str, path: str, sha: str
) -> str:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(f"{entry['slug']}: upstream SKILL.md has no frontmatter")
    meta = yaml.safe_load(match.group(1)) or {}
    if meta.get("name") != entry["slug"]:
        raise ValueError(
            f"{entry['slug']}: upstream name is '{meta.get('name')}'; the "
            "catalog slug must match the SKILL.md name"
        )
    meta["license"] = entry.get("license") or meta.get("license") or "unknown"
    metadata = dict(meta.get("metadata") or {})
    metadata.update(
        {
            "source": f"{owner}/{repo}",
            "source_url": entry["source_url"],
            "upstream_commit": sha,
        }
    )
    meta["metadata"] = metadata
    frontmatter = yaml.safe_dump(
        meta, sort_keys=False, allow_unicode=True, width=100_000
    ).strip()
    body = _clean_body(match.group(2).lstrip("\n"), entry["slug"])
    return f"---\n{frontmatter}\n---\n\n{body}"


def vendor(entry: dict) -> None:
    slug = entry["slug"]
    owner, repo, path = _split_source(entry["source"])
    print(f"{slug} <- {owner}/{repo}/{path}")
    commit = str(entry.get("source_commit") or "")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError(f"{slug}: source_commit must be a full Git SHA")
    sha, blobs = _tree(owner, repo, commit)
    prefix = f"{path}/"
    members = [b for b in blobs if b["path"].startswith(prefix)]
    if not members:
        raise RuntimeError(f"{slug}: nothing under {path} in {owner}/{repo}")

    target = SKILLS_DIR / slug
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)

    for blob in members:
        relative = blob["path"][len(prefix) :]
        if not _wanted(relative):
            continue
        content = _get(f"{RAW}/{owner}/{repo}/{sha}/{blob['path']}")
        if relative == "SKILL.md":
            content = _rewrite_skill_md(
                content.decode("utf-8"), entry, owner, repo, path, sha
            ).encode("utf-8")
        elif relative.endswith(".md"):
            content = _clean_markdown(
                content.decode("utf-8"), f"{slug}/{relative}", drop_sections=False
            ).encode("utf-8")
        out = target / relative
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(content)
        if blob.get("mode") == "100755":
            out.chmod(0o755)

    license_path = _find_license(blobs, path)
    if license_path:
        (target / "LICENSE").write_bytes(
            _get(f"{RAW}/{owner}/{repo}/{sha}/{license_path}")
        )
    else:
        raise RuntimeError(f"{slug}: no LICENSE file found in {owner}/{repo}")

    notice = (
        f"{slug}\n\n"
        f"Source: {entry['source_url']}\n"
        f"Upstream commit: {sha}\n"
        f"License: {entry['license']} (see LICENSE)\n\n"
        "Significant Gravitas vendors this package for the AutoGPT Skills "
        "catalog. The vendoring step rewrites package metadata and may remove "
        "upstream-only links, tests, hidden files, and sponsored tool tables.\n"
    )
    (target / "NOTICE").write_text(notice, encoding="utf-8")

    count = sum(1 for p in target.rglob("*") if p.is_file())
    print(f"  {count} files at {sha[:12]}")


def main(argv: list[str]) -> int:
    catalog = yaml.safe_load(CATALOG.read_text(encoding="utf-8"))
    only = set(argv)
    for entry in catalog["skills"]:
        if entry.get("distribution_status") != "approved":
            continue
        if entry["source"] == "platform":
            continue
        if only and entry["slug"] not in only:
            continue
        vendor(entry)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
