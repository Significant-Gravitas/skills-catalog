#!/usr/bin/env python3
"""Replay immutable manifest bytes, without transforming or overwriting sources.

Default / --check: offline verification only.
--fetch: restore missing files from commit-pinned raw URLs. Existing edits,
undeclared files and symlinks are errors. Verify every download and the complete
proposed tree before writing. No HEAD lookup, cleanup or partial-slug operation.
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable

from check import ROOT, confined_path, validate, verify_bytes


def raw_url(record: dict) -> str:
    source = record["source"]
    path = urllib.parse.quote(source["path"], safe="/")
    return f"https://raw.githubusercontent.com/{source['repo']}/{source['commit']}/{path}"


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "skills-catalog-immutable-replay"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def _publish_missing(root: Path, relative: str, content: bytes, mode: str) -> None:
    target = confined_path(root, relative)
    target.parent.mkdir(parents=True, exist_ok=True)
    confined_path(root, relative)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".vendor-", dir=target.parent, delete=False) as handle:
            temporary = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o755 if mode == "100755" else 0o644)
        confined_path(root, relative)
        # Atomic create-if-absent; never overwrite a concurrent user's file.
        # Both files share a filesystem. Unsupported hard links fail safely.
        os.link(temporary, target)
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def fetch_missing(root: Path = ROOT, *, fetcher: Callable[[str], bytes] = download, expected_count: int | None = None) -> int:
    root = root.resolve()
    initial = validate(root, allow_missing=True, expected_count=expected_count)
    initial.require_valid()  # Fail dirty/unknown files before network access.
    supplied: dict[str, bytes] = {}
    cache: dict[str, bytes] = {}
    for relative, record in sorted(initial.records.items()):
        if confined_path(root, relative).exists():
            continue
        url = raw_url(record)
        if url not in cache:
            cache[url] = fetcher(url)
        content = cache[url]
        verify_bytes(record, content)
        supplied[relative] = content
    validate(root, supplied=supplied, expected_count=expected_count).require_valid()
    # Final preflight also catches changes to existing sources during download.
    # Publication is per-file atomic, not a filesystem-wide transaction.
    for relative, content in supplied.items():
        _publish_missing(root, relative, content, initial.records[relative]["mode"])
    validate(root, expected_count=expected_count).require_valid()
    return len(supplied)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true", help="offline verification (default)")
    modes.add_argument("--fetch", action="store_true", help="restore missing files from immutable URLs")
    parser.add_argument("--expected-count", type=int)
    args = parser.parse_args(argv)
    try:
        if args.fetch:
            count = fetch_missing(args.root, expected_count=args.expected_count)
            print(f"Restored {count} missing files; all manifest bytes verified unchanged.")
        else:
            result = validate(args.root, expected_count=args.expected_count)
            result.require_valid()
            print(f"Verified {len(result.entries)} skills and {len(result.records)} files offline.")
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
