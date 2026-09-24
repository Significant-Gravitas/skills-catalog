#!/usr/bin/env python3
"""Build a history-free tree containing only approved skill packages."""

import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "catalog.yml"
SKILLS_DIR = ROOT / "skills"

ROOT_FILES = ("README.md", "LICENSE.md", "catalog.yml")
ROOT_DIRECTORIES = ("tools", ".github")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python tools/export_public.py OUTPUT_DIRECTORY")
        return 2
    destination = Path(argv[0]).resolve()
    if destination.exists() and any(destination.iterdir()):
        raise RuntimeError(f"{destination} must be empty")
    destination.mkdir(parents=True, exist_ok=True)

    catalog = yaml.safe_load(CATALOG.read_text(encoding="utf-8")) or {}
    approved = [
        entry
        for entry in catalog.get("skills") or []
        if entry.get("distribution_status") == "approved"
    ]
    if not approved:
        raise RuntimeError("catalog has no approved skills")

    for name in ROOT_FILES:
        if name == "catalog.yml":
            continue
        shutil.copy2(ROOT / name, destination / name)
    for name in ROOT_DIRECTORIES:
        shutil.copytree(ROOT / name, destination / name)

    public_catalog = {
        "skills": approved,
    }
    (destination / "catalog.yml").write_text(
        "# Public distribution manifest. Every entry is approved.\n"
        + yaml.safe_dump(public_catalog, sort_keys=False),
        encoding="utf-8",
    )

    public_skills = destination / "skills"
    public_skills.mkdir()
    for entry in approved:
        slug = entry["slug"]
        shutil.copytree(SKILLS_DIR / slug, public_skills / slug)

    print(f"exported {len(approved)} approved skills to {destination}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
