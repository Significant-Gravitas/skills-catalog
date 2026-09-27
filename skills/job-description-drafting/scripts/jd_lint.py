#!/usr/bin/env python3
"""Lint a job posting for age, proxy, gender-coded and label wording.

Usage (cd ~/skills/job-description-drafting first):
    python3 scripts/jd_lint.py <posting.md|.txt> [--terms references/lint-terms.csv] [--json]

Input:  a posting as text or markdown.
Output: one line per hit:
          L<line>:<col> <FLAG|CHECK|info> "<matched text>" [<category>] -> <swap> (<source>)
        then counts per category. FLAG = change unless the owner defends it;
        CHECK = context-dependent (e.g. "lead" in a job title is fine);
        info = feminine-coded words, reported for balance only.
        --json prints the same as a JSON list.
Exit:   0 no FLAG hits; 1 at least one FLAG hit; 2 unreadable input or lexicon.

Stdlib only, no network. The lexicon is references/lint-terms.csv:
term,match(word|stem|phrase|regex),category,severity(flag|context|info),suggested_swap,source_ref.
word/phrase also match a plural (-s/-es), and a space or hyphen in the term
matches either in the text ("recent graduate" catches "recent graduates",
"able-bodied" catches "able bodied"). regex rows are case-insensitive and
bounded so they never match inside a longer word.
The lint is a backstop, not the review: it cannot see every proxy. Read every
line against references/protected-traits-and-proxies.md as well.
The script flags; the owner decides. Never rewrite silently.
"""

import csv
import json
import re
import sys
from pathlib import Path

DEFAULT_TERMS = Path(__file__).resolve().parent.parent / "references" / "lint-terms.csv"
LABEL = {"flag": "FLAG", "context": "CHECK", "info": "info"}
# Internal note lines in a draft (same list render_posting.py leaves out) are not linted.
INTERNAL = ("cut for language:", "still unknown:", "internal:", "not posted anywhere")


def load_terms(path: Path):
    try:
        with path.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
    except OSError as exc:
        print(f"error: cannot read lexicon {path}: {exc}", file=sys.stderr)
        sys.exit(2)
    compiled = []
    for r in rows:
        kind = r["match"].strip()
        if kind == "regex":
            try:
                rx = re.compile(r"(?<![\w-])(?:" + r["term"].strip() + r")(?![\w-])", re.I)
            except re.error as exc:
                print(f"error: bad regex in lexicon {path}: {r['term']!r}: {exc}", file=sys.stderr)
                sys.exit(2)
            compiled.append((rx, r))
            continue
        term = r["term"].strip().lower()
        # A space or hyphen in the term matches either (or both) in the text.
        esc = re.sub(r"(\\ |\\-)", lambda _m: r"[\s-]+", re.escape(term))
        if kind == "stem":
            rx = re.compile(r"(?<![\w-])" + esc + r"[\w-]*", re.I)
        else:  # word or phrase; a plural (-s/-es) matches too
            rx = re.compile(r"(?<![\w-])" + esc + r"(?:s|es)?(?![\w-])", re.I)
        compiled.append((rx, r))
    return compiled


def lint(text: str, terms):
    hits = []
    in_comment = False
    for n, line in enumerate(text.splitlines(), start=1):
        # Skip HTML comments (template notes) so they are not linted.
        if "<!--" in line:
            in_comment = "-->" not in line
            continue
        if in_comment:
            in_comment = "-->" not in line
            continue
        if line.strip().lstrip(">").strip().lower().startswith(INTERNAL):
            continue
        taken = []
        for rx, r in terms:
            for m in rx.finditer(line):
                span = (m.start(), m.end())
                if any(s < span[1] and span[0] < e for s, e in taken):
                    continue  # a longer phrase already matched here
                taken.append(span)
                hits.append({
                    "line": n, "col": m.start() + 1, "text": m.group(0),
                    "category": r["category"], "severity": r["severity"].strip(),
                    "swap": r["suggested_swap"], "source": r["source_ref"],
                })
    order = {"flag": 0, "context": 1, "info": 2}
    hits.sort(key=lambda h: (order.get(h["severity"], 3), h["line"], h["col"]))
    return hits


def main(argv):
    args = argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__, file=sys.stderr)
        return 2
    path = Path(args[0]).expanduser()
    terms_path = DEFAULT_TERMS
    as_json = "--json" in args
    if "--terms" in args:
        i = args.index("--terms")
        if i + 1 >= len(args):
            print("error: --terms needs a path", file=sys.stderr)
            return 2
        terms_path = Path(args[i + 1]).expanduser()
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: cannot read {path}: {exc}. Save the posting as UTF-8 text first.", file=sys.stderr)
        return 2
    hits = lint(text, load_terms(terms_path))
    if as_json:
        print(json.dumps(hits, indent=1, ensure_ascii=False))
    else:
        for h in hits:
            print(f'L{h["line"]}:{h["col"]} {LABEL.get(h["severity"], h["severity"])} "{h["text"]}" '
                  f'[{h["category"]}] -> {h["swap"]} ({h["source"]})')
        counts = {}
        for h in hits:
            counts[h["category"]] = counts.get(h["category"], 0) + 1
        summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "no hits"
        flags = sum(1 for h in hits if h["severity"] == "flag")
        print(f"summary: {flags} FLAG, {len(hits) - flags} other; {summary}")
    return 1 if any(h["severity"] == "flag" for h in hits) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
