#!/usr/bin/env python3
"""Sentence-level before/after between an old posting and the rewrite.

Usage (cd ~/skills/job-description-drafting first):
    python3 scripts/diff_postings.py <old.md|.txt> <new.md|.txt>

Output: for each changed stretch, a block labelled "## <section>" (the
        section heading it falls under, "(top)" before the first heading) of
        "- old" / "+ new" lines; unchanged sentences are not printed. The title
        ("# ...") and section headings ("## ...", or a whole **bold** line) are
        compared too, as "title: ..." and "heading: ..." lines, so a retitled
        role shows up. Ends with counts of removed, added and kept lines.
Exit:   0 always when both files are readable; 2 otherwise.
Stdlib only (difflib), no network.
"""

import difflib
import re
import sys
from pathlib import Path


INTERNAL = ("cut for language:", "still unknown:", "internal:", "not posted anywhere")


def read(p):
    try:
        return Path(p).expanduser().read_text(encoding="utf-8").replace("\r\n", "\n")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: cannot read {p}: {exc}", file=sys.stderr)
        sys.exit(2)


def sentences(text):
    out, heading = [], "(top)"
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    for line in text.splitlines():
        s = line.strip().lstrip(">").strip()
        if not s or s.lower().startswith(INTERNAL):
            continue
        if s.startswith("#") or (s.startswith("**") and s.endswith("**")):
            label = s.strip("#* ").strip()
            kind = "title" if re.match(r"^#(?!#)", s) else "heading"
            out.append((heading, f"{kind}: {label}"))
            heading = label
            continue
        s = re.sub(r"^[-*]\s+", "", s)
        for part in re.split(r"(?<=[.!?])\s+", s):
            part = part.strip()
            if part:
                out.append((heading, part))
    return out


def main(argv):
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    old = sentences(read(argv[1]))
    new = sentences(read(argv[2]))
    a = [s for _, s in old]
    b = [s for _, s in new]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    removed = added = kept = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            kept += i2 - i1
            continue
        head = new[j1][0] if j1 < len(new) else (new[-1][0] if new else "(end)")
        print(f"## {head}")
        for s in a[i1:i2]:
            print(f"- {s}")
            removed += 1
        for s in b[j1:j2]:
            print(f"+ {s}")
            added += 1
        print()
    print(f"summary: {removed} removed, {added} added, {kept} kept")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
