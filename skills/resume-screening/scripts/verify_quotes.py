#!/usr/bin/env python3
"""Check every quote (EVIDENCE FOUND and CONFIRM IN INTERVIEW rows) against the redacted resume. Run before merging.

Usage:
  python3 scripts/verify_quotes.py <records_dir> <red_dir>

Input:  <records_dir>/<id>.json (one per candidate, from the screening passes)
        and <red_dir>/<id>.txt from redact.py (the same text the screener read).
Rule:   after normalising case, whitespace, quote marks, dashes and bullets:
          exact substring               -> quote_check "exact"
          best fuzzy match >= 0.98      -> "exact" (formatting-only difference)
          best fuzzy match 0.92 to 0.98 -> "approximate (<ratio>)": kept, and
                                           shown with a marker for the human
          below 0.92, or empty          -> the row becomes CONFIRM IN INTERVIEW,
                                           note "quote not found in source;
                                           screener paraphrase (not in resume):
                                           <text>", and the quote is blanked,
                                           so no unverified text is ever shown
                                           in quote marks
        Thresholds are defaults: confirm with the owner.
        A quote is never "repaired"; a quote that is not in the resume is an
        invented fact about a person.
Output: each record file updated in place (quote_check added per row; the
        original record is kept as <id>.json.orig the first time); one line
        per downgraded or approximate row, by candidate id and criterion.
Exit:   0 done, 2 bad input.
Stdlib only (difflib), no network.
"""

import difflib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import screenio  # noqa: E402

EXACT_RATIO = 0.98   # default (confirm with the owner)
MIN_RATIO = 0.92     # default (confirm with the owner)


def best_ratio(quote: str, source: str) -> float:
    q, s = screenio.norm_text(quote), screenio.norm_text(source)
    if not q:
        return 0.0
    if q in s:
        return 1.0
    words = s.split(" ")
    qlen = len(q.split(" "))
    best = 0.0
    for size in {max(1, qlen - 2), qlen, qlen + 2}:
        for i in range(0, max(1, len(words) - size + 1)):
            sm = difflib.SequenceMatcher(a=q, b=" ".join(words[i:i + size]), autojunk=False)
            if sm.real_quick_ratio() <= best or sm.quick_ratio() <= best:
                continue
            best = max(best, sm.ratio())
    return best


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    rec_dir, red_dir = Path(sys.argv[1]).expanduser(), Path(sys.argv[2]).expanduser()
    files = sorted(rec_dir.glob("*.json"), key=lambda p: screenio.id_key(p.stem))
    if not files:
        print(f"error: no record files in {rec_dir}", file=sys.stderr)
        return 2
    exact, approx, changed = 0, [], []
    for f in files:
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            print(f"skip {f.name}: not valid JSON ({exc}); merge_matrices.py will list it", file=sys.stderr)
            continue
        cid = rec.get("id") or f.stem
        src = red_dir / f"{cid}.txt"
        source = src.read_text(encoding="utf-8") if src.is_file() else ""
        orig = f.with_name(f.name + ".orig")
        if not orig.exists():
            shutil.copyfile(f, orig)
        for r in rec.get("rows") or []:
            if r.get("quote_check", "").startswith(("exact", "approximate", "not found")):
                continue
            if r.get("result") == "CONFIRM IN INTERVIEW" and not r.get("quote", "").strip():
                continue  # nothing quoted; nothing to check
            if r.get("result") not in ("EVIDENCE FOUND", "CONFIRM IN INTERVIEW"):
                continue
            ratio = best_ratio(r.get("quote", ""), source)
            if ratio >= EXACT_RATIO:
                r["quote_check"] = "exact"
                exact += 1
            elif ratio >= MIN_RATIO:
                r["quote_check"] = f"approximate ({ratio:.2f})"
                approx.append(f"{cid} {r.get('criterion_id')}")
            else:
                r["result"] = "CONFIRM IN INTERVIEW"
                said = r.get("quote", "").strip()
                parts = ["quote not found in source"]
                if said:
                    parts.append(f"screener paraphrase (not in resume): {said}")
                if r.get("note"):
                    parts.append(r["note"])
                r["note"] = "; ".join(parts)
                r["quote"] = ""
                r["quote_check"] = f"not found ({ratio:.2f})"
                changed.append(f"{cid} {r.get('criterion_id')}")
        f.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"checked {exact + len(approx) + len(changed)} quote(s): {exact} exact, {len(approx)} approximate, {len(changed)} not found")
    for c in approx:
        print(f"APPROXIMATE {c}: kept with a marker; the human should read the source line")
    for c in changed:
        print(f"DOWNGRADED {c}: quote not found in source -> CONFIRM IN INTERVIEW")
    return 0


if __name__ == "__main__":
    sys.exit(main())
