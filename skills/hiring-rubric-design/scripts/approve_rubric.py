#!/usr/bin/env python3
"""Stamp an owner's approval on a rubric, freeze it, or start the next version.

Usage:
  python3 scripts/approve_rubric.py <rubric-vN.md> --approver "<name>" --quote "<owner's words>"
                                   [--date YYYY-MM-DD] [--requirements <requirements.csv>]
  python3 scripts/approve_rubric.py <rubric-vN.md> --verify
  python3 scripts/approve_rubric.py <rubric-vN.md> --new-version

Approve: runs the validator (with --requirements if given) and refuses on any
  error; refuses if the file is already approved; sets status: approved,
  approved_by, approved_on (today, UTC, unless --date) and approval_quote,
  rewrites the body line "Approved by: ..." in the Approval section to match; then
  writes <rubric-vN.md>.sha256 in sha256sum format. Run it only after the
  owner has said yes in this chat; the quote is their sentence.
Verify: exit 0 if the approved file still matches its .sha256; exit 4 if it
  was edited after approval (screening must stop); exit 3 if it is not
  approved or has no .sha256.
New version: copies an approved rubric-vN.md to rubric-v<N+1>.md as a draft
  (version bumped, approval cleared) and prints the new path. Refuses if the
  target exists. Edit and approve the new file; vN stays frozen.
Exit:   0 ok, 1 validation failed, 2 bad input, 3 not approved, 4 changed after approval.
Stdlib only, no network.
"""

import argparse
import datetime as dt
import hashlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rubric_io  # noqa: E402
from validate_rubric import read_requirements, validate  # noqa: E402


APPROVAL_LINE = re.compile(r"^Approved by:.*$", re.M)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def set_approval_line(text: str, line: str) -> str:
    """Rewrite the body's 'Approved by:' line so the frozen record agrees with the header."""
    if APPROVAL_LINE.search(text):
        return APPROVAL_LINE.sub(lambda _: line, text, count=1)
    return text.rstrip("\n") + "\n\n## Approval\n\n" + line + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rubric")
    ap.add_argument("--approver")
    ap.add_argument("--quote")
    ap.add_argument("--date")
    ap.add_argument("--requirements")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--new-version", action="store_true")
    args = ap.parse_args()

    path = Path(args.rubric).expanduser()
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        return 2
    meta = rubric_io.parse(text)["meta"]
    sha_file = path.with_name(path.name + ".sha256")

    if args.verify:
        if meta.get("status") != "approved" or not sha_file.is_file():
            print(f"NOT APPROVED: {path.name} (status '{meta.get('status')}', checksum file {'present' if sha_file.is_file() else 'missing'})")
            return 3
        expected = sha_file.read_text(encoding="utf-8").split()[0]
        if sha(path) != expected:
            print(f"CHANGED AFTER APPROVAL: {path.name} no longer matches {sha_file.name}; stop and ask the owner to re-approve or create a new version")
            return 4
        print(f"APPROVED and unchanged: {path.name} v{meta.get('version')} by {meta.get('approved_by')} on {meta.get('approved_on')}")
        return 0

    if args.new_version:
        if meta.get("status") != "approved":
            print(f"error: {path.name} is still a draft; edit it directly instead of creating a new version", file=sys.stderr)
            return 3
        try:
            n = int(meta.get("version", ""))
        except ValueError:
            print("error: header 'version:' is not a whole number", file=sys.stderr)
            return 2
        m = re.search(r"-v(\d+)\.md$", path.name)
        target = path.with_name(re.sub(r"-v\d+\.md$", f"-v{n + 1}.md", path.name) if m else path.stem + f"-v{n + 1}.md")
        if target.exists():
            print(f"error: {target} already exists; open it instead", file=sys.stderr)
            return 2
        new = text
        for key, value in (("version", str(n + 1)), ("status", "draft"), ("approved_by", ""),
                           ("approved_on", ""), ("approval_quote", "")):
            new = rubric_io.set_meta(new, key, value)
        new = set_approval_line(new, "Approved by: pending.")
        target.write_bytes(new.encode("utf-8"))  # LF only: the checksum binds exact bytes
        print(f"created {target} (draft v{n + 1}); v{n} stays frozen. Candidates already screened on v{n} must be listed for the owner.")
        return 0

    if not args.approver or not args.quote:
        print("error: --approver and --quote are required; record the owner's own approval sentence", file=sys.stderr)
        return 2
    if meta.get("status") == "approved":
        print(f"error: {path.name} is already approved; use --new-version to change it", file=sys.stderr)
        return 3
    reqs = None
    if args.requirements:
        try:
            reqs, _ = read_requirements(args.requirements)
        except (OSError, UnicodeDecodeError) as exc:
            print(f"error: cannot read {args.requirements}: {exc}", file=sys.stderr)
            return 2
    result = validate(text, reqs)
    if result["errors"]:
        for i, e in enumerate(result["errors"], 1):
            print(f"ERROR {i}. {e}")
        print("refused: fix the errors, show the owner the fixed rubric, then approve again")
        return 1
    date = args.date or dt.datetime.now(dt.timezone.utc).date().isoformat()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        print("error: --date must be YYYY-MM-DD", file=sys.stderr)
        return 2
    quote = args.quote.replace("\n", " ").strip()
    for key, value in (("status", "approved"), ("approved_by", args.approver.strip()),
                       ("approved_on", date), ("approval_quote", f'"{quote}"')):
        text = rubric_io.set_meta(text, key, value)
    end = "" if quote[-1:] in ".!?" else "."  # no double full stop after a quote that ends a sentence
    text = set_approval_line(text, f'Approved by: {args.approver.strip()}, {date}, "{quote}"{end}')
    path.write_bytes(text.encode("utf-8"))  # LF only: the checksum binds exact bytes
    digest = sha(path)
    sha_file.write_bytes(f"{digest}  {path.name}\n".encode("utf-8"))
    print(f"approved: {path.name} v{meta.get('version')} by {args.approver} on {date}")
    print(f"checksum: {digest} -> {sha_file.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
