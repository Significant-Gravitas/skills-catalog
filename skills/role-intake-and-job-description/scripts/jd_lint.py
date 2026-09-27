#!/usr/bin/env python3
"""Lint a job description for age, proxy, label and gender-coded wording.

Usage:
  python3 scripts/jd_lint.py <jd.md> [--terms references/lint-terms.csv] [--json]

Input:  a job description as text or markdown.
Data:   references/lint-terms.csv with columns
        term,match,category,level,suggested_swap,source
        match is word | stem | phrase | regex; level is
          flag   likely to screen people out without a work reason: raise it
          check  keep only if the requirement sort gives a work reason
          suggest gender-coded wording; offer the swap, the owner decides
          info   counted for balance only
Output: one line per hit: L<line>:<col> "<text>" [<category>/<level>] -> <swap> (<source>)
        then a summary by category, and the masculine/feminine-coded balance.
        Lines inside <!-- --> comments are skipped.
Exit:   0 no flag/check hits, 1 at least one flag or check hit, 2 unreadable input.

The lint suggests; the owner accepts or rejects each hit. It never rewrites.
Known benign cases (for example "Lead" in a job title, "competitive pay")
are listed in references/inclusive-language-lint.md. Stdlib only, no network.
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

DEFAULT_TERMS = Path(__file__).resolve().parent.parent / "references" / "lint-terms.csv"


def compile_term(row: dict) -> re.Pattern:
    term, kind = row["term"], row["match"]
    if kind == "regex":
        return re.compile(term, re.I)
    if kind == "word":
        return re.compile(r"\b" + re.escape(term) + r"\b", re.I)
    if kind == "stem":
        return re.compile(r"\b" + re.escape(term) + r"[\w-]*", re.I)
    if kind == "phrase":
        words = [re.escape(w) for w in term.split()]
        return re.compile(r"\b" + r"[\s-]+".join(words) + r"\b", re.I)
    raise ValueError(f"unknown match type '{kind}' for term '{term}'")


def load_terms(path: Path) -> list[tuple[dict, re.Pattern]]:
    try:
        with path.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
    except OSError as exc:
        sys.exit(f"error: cannot read terms file {path}: {exc}")
    out = []
    for row in rows:
        try:
            out.append((row, compile_term(row)))
        except (re.error, ValueError) as exc:
            sys.exit(f"error: bad row in {path.name} for term '{row.get('term')}': {exc}")
    return out


def lint(text: str, terms) -> list[dict]:
    hits = []
    in_comment = False
    for n, line in enumerate(text.splitlines(), 1):
        if "<!--" in line:
            in_comment = True
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue
        taken: list[tuple[int, int]] = []
        for row, pat in terms:
            for m in pat.finditer(line):
                span = (m.start(), m.end())
                if any(s < span[1] and span[0] < e for s, e in taken):
                    continue  # an earlier, more specific row already covered this text
                taken.append(span)
                hits.append({
                    "line": n, "col": m.start() + 1, "text": m.group(0),
                    "category": row["category"], "level": row["level"],
                    "swap": row["suggested_swap"], "source": row["source"],
                })
    hits.sort(key=lambda h: (h["line"], h["col"]))
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("jd")
    ap.add_argument("--terms", default=str(DEFAULT_TERMS))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        text = Path(args.jd).expanduser().read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: cannot read {args.jd}: {exc}. Save the draft as UTF-8 text first.", file=sys.stderr)
        return 2

    hits = lint(text, load_terms(Path(args.terms).expanduser()))
    by_cat = Counter(h["category"] for h in hits)
    masc = by_cat.get("masculine-coded", 0)
    fem = by_cat.get("feminine-coded", 0)
    blocking = [h for h in hits if h["level"] in ("flag", "check")]

    if args.json:
        print(json.dumps({"hits": hits, "by_category": by_cat, "masculine_coded": masc,
                          "feminine_coded": fem, "flag_or_check": len(blocking)}, indent=2))
    else:
        for h in hits:
            if h["level"] == "info":
                continue
            print(f'L{h["line"]}:{h["col"]} "{h["text"]}" [{h["category"]}/{h["level"]}] -> {h["swap"]} ({h["source"]})')
        print("Summary: " + (", ".join(f"{k} {v}" for k, v in sorted(by_cat.items())) or "no hits"))
        lean = "masculine-leaning" if masc > fem else "feminine-leaning" if fem > masc else "balanced"
        print(f"Gender-coded balance: masculine {masc}, feminine {fem} ({lean}) [31]")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
