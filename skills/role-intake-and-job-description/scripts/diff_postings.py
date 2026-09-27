#!/usr/bin/env python3
"""Show what changed between an old posting and the new draft, sentence by sentence.

Usage:
  python3 scripts/diff_postings.py <old.md> <new.md> [--json]

Input:  two text or markdown files (use extract_text.py first for DOCX/PDF/HTML).
Output: section headings removed and added, then changes labelled with
        their section (old section for removals, new section otherwise):
          - old sentence      (removed)
          + new sentence      (added)
          ~ old  ->  new      (reworded; similarity at or above 0.6)
        and a count of unchanged sentences. Markdown emphasis is ignored.
Exit:   0 always when both files are readable, 2 otherwise.
Stdlib only (difflib), no network.
"""

import difflib
import json
import re
import sys
from pathlib import Path

REWORD_RATIO = 0.6  # default: sentences this similar are shown as a rewording, not remove + add


def sentences(text: str) -> list[tuple[str, str]]:
    """Return (heading, sentence) pairs."""
    out = []
    heading = "(top)"
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line) or re.match(r"^\*\*(.+?)\*\*:?$", line)
        if m:
            heading = m.groups()[-1].strip()
            continue
        line = re.sub(r"^[-*]\s+", "", line)
        line = re.sub(r"[*_`]", "", line)
        for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])", line):
            s = s.strip()
            if s:
                out.append((heading, s))
    return out


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        old = sentences(Path(args[0]).expanduser().read_text(encoding="utf-8"))
        new = sentences(Path(args[1]).expanduser().read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    a = [s for _, s in old]
    b = [s for _, s in new]
    old_heads = list(dict.fromkeys(h for h, _ in old))
    new_heads = list(dict.fromkeys(h for h, _ in new))
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    changes = []
    same = 0
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "equal":
            same += i2 - i1
            continue
        olds, news = a[i1:i2], b[j1:j2]
        used = set()
        for o in olds:
            best, score = None, 0.0
            for k, n in enumerate(news):
                if k in used:
                    continue
                r = difflib.SequenceMatcher(a=o.lower(), b=n.lower()).ratio()
                if r > score:
                    best, score = k, r
            if best is not None and score >= REWORD_RATIO:
                used.add(best)
                changes.append({"section": new[j1 + best][0], "kind": "~", "old": o, "new": news[best]})
            else:
                changes.append({"section": old[i1 + olds.index(o)][0], "kind": "-", "old": o, "new": ""})
        for k, n in enumerate(news):
            if k not in used:
                changes.append({"section": new[j1 + k][0], "kind": "+", "old": "", "new": n})

    if "--json" in sys.argv:
        print(json.dumps({"changes": changes, "unchanged": same,
                          "sections_removed": [h for h in old_heads if h not in new_heads],
                          "sections_added": [h for h in new_heads if h not in old_heads]}, indent=2))
        return 0
    gone = [h for h in old_heads if h not in new_heads]
    added = [h for h in new_heads if h not in old_heads]
    if gone or added:
        print("Sections removed: " + (", ".join(gone) or "none"))
        print("Sections added: " + (", ".join(added) or "none"))
    current = None
    for c in changes:
        if c["section"] != current:
            current = c["section"]
            print(f"\n[{current}]")
        if c["kind"] == "~":
            print(f"~ {c['old']}\n    -> {c['new']}")
        elif c["kind"] == "-":
            print(f"- {c['old']}")
        else:
            print(f"+ {c['new']}")
    print(f"\n{len(changes)} change(s); {same} sentence(s) unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
