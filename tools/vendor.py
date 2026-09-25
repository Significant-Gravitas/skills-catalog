#!/usr/bin/env python3
"""Restore reviewed package outputs from verified local original archives.

Default / --check: offline verification only.
--restore: recreate only missing package members by replaying the exact recorded
adaptations. Existing edits, undeclared files and symlinks are errors. Original
archives are required and never changed. No network, cleanup or skill execution.
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

from check import ROOT, ValidationError, confined_path, validate


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


def restore_missing(root: Path = ROOT, *, expected_count: int | None = None) -> int:
    root = root.resolve()
    initial = validate(root, allow_missing=True, expected_count=expected_count)
    initial.require_valid()  # All originals and rendered outputs pass before writing.
    supplied: dict[str, bytes] = {}
    for relative, record in sorted(initial.records.items()):
        if confined_path(root, relative).exists():
            continue
        supplied[relative] = initial.rendered[relative]
    final = validate(root, supplied=supplied, expected_count=expected_count)
    final.require_valid()
    if (final.records != initial.records or final.provenance != initial.provenance
            or final.entries != initial.entries or final.carryforward != initial.carryforward
            or final.unresolved != initial.unresolved):
        raise ValidationError("catalog/provenance changed during restoration preflight")
    # Final preflight also catches changes to existing sources during preparation.
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
    modes.add_argument("--restore", action="store_true", help="restore missing package files from local original archives")
    modes.add_argument("--fetch", action="store_true", help="deprecated alias for --restore; no network requests")
    parser.add_argument("--expected-count", type=int)
    args = parser.parse_args(argv)
    try:
        if args.restore or args.fetch:
            if args.fetch:
                print("--fetch is deprecated; using offline --restore (no downloads).", file=sys.stderr)
            count = restore_missing(args.root, expected_count=args.expected_count)
            print(f"Restored {count} missing package files from verified originals and recorded adaptations.")
        else:
            result = validate(args.root, expected_count=args.expected_count)
            result.require_valid()
            print(f"Verified {len(result.entries)} skills and {len(result.records) + len(result.carryforward_files)} files offline.")
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
