#!/usr/bin/env python3
"""Check the requirement sort, and that the job description matches it.

Usage:
  python3 scripts/req_check.py <requirements.csv> [--jd <jd.md>] [--require-mapping] [--json]

Input:  requirements.csv made from templates/requirements.csv:
        req_id,requirement,group,what_fails_without_it,objective,non_comparative,
        job_relevant,evidence_method,change_reason,approved_by,approved_on,rubric_criterion_id
        group is must-show | test-in-process | learn-after-hire | removed.
Checks (ERROR):
  - header differs from the template; duplicate or malformed req_id (R1, R2 ...);
  - unknown group; a kept requirement with no "what fails without it";
  - a must-show row that is not objective, non-comparative and job-relevant
    (all three "yes"), or has no evidence_method;
  - a must-show row using comparative words (best, top, stronger than ...);
  - a removed row with no change_reason;
  - with --jd: a must-show requirement not quoted word for word in the JD,
    or a removed requirement still present in the JD;
  - with --require-mapping: a must-show row with no rubric_criterion_id.
Checks (WARN): degree, years-of-experience, "native", location or "fit" terms
  in a kept requirement (they need a job-related reason in what_fails_without_it);
  a test-in-process row with no evidence_method.
Output: ERROR/WARN lines, then counts per group.
Exit:   0 clean (warnings allowed), 1 errors, 2 unreadable input.
Stdlib only, no network.
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

HEADER = ["req_id", "requirement", "group", "what_fails_without_it", "objective",
          "non_comparative", "job_relevant", "evidence_method", "change_reason",
          "approved_by", "approved_on", "rubric_criterion_id"]
GROUPS = {"must-show", "test-in-process", "learn-after-hire", "removed"}
COMPARATIVE = re.compile(r"\b(best|top|strongest|stronger than|better than|most \w+|among the|than other)\b", re.I)
WATCH = re.compile(r"\b(degree|bachelor|master'?s|mba|phd|\d+\+?\s*years?|native|local|fit|young|graduate)\b", re.I)


def norm(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[*_`]", "", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("requirements")
    ap.add_argument("--jd")
    ap.add_argument("--require-mapping", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        with Path(args.requirements).expanduser().open(encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            header = reader.fieldnames or []
            rows = list(reader)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: cannot read {args.requirements}: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []
    warns: list[str] = []
    if header != HEADER:
        missing = [c for c in HEADER if c not in header]
        extra = [c for c in header if c not in HEADER]
        errors.append(f"header must be exactly: {','.join(HEADER)} (missing {missing}, extra {extra})")

    seen = set()
    for i, r in enumerate(rows, 2):
        rid = (r.get("req_id") or "").strip()
        where = f"row {i} ({rid or 'no id'})"
        if not re.fullmatch(r"R\d+", rid):
            errors.append(f"{where}: req_id must look like R1, R2 ...")
        elif rid in seen:
            errors.append(f"{where}: duplicate req_id")
        seen.add(rid)
        group = (r.get("group") or "").strip()
        text = (r.get("requirement") or "").strip()
        if not text:
            errors.append(f"{where}: requirement text is empty")
        if group not in GROUPS:
            errors.append(f"{where}: group must be one of {sorted(GROUPS)}, got '{group}'")
            continue
        fails = (r.get("what_fails_without_it") or "").strip()
        if group != "removed" and not fails:
            errors.append(f"{where}: say what work fails without it, or move it to 'removed'")
        if group == "must-show":
            bad = [k for k in ("objective", "non_comparative", "job_relevant") if (r.get(k) or "").strip().lower() != "yes"]
            if bad:
                errors.append(f"{where}: must-show fails the three-part test on {bad}; rewrite it or move it to test-in-process")
            if COMPARATIVE.search(text):
                errors.append(f"{where}: must-show uses comparative wording ('{COMPARATIVE.search(text).group(0)}'); a must-have is met or not met on its own")
            if not (r.get("evidence_method") or "").strip():
                errors.append(f"{where}: must-show needs an evidence_method (resume, work sample, interview ...)")
            if args.require_mapping and not (r.get("rubric_criterion_id") or "").strip():
                errors.append(f"{where}: must-show has no rubric criterion (run hiring-rubric-design's validator with --write-back)")
        if group == "test-in-process" and not (r.get("evidence_method") or "").strip():
            warns.append(f"{where}: say how the process will test it (evidence_method)")
        if group == "removed" and not (r.get("change_reason") or "").strip():
            errors.append(f"{where}: removed requirement needs a change_reason the owner can read")
        if group != "removed" and WATCH.search(text):
            warns.append(f"{where}: '{WATCH.search(text).group(0)}' needs a job-related reason in what_fails_without_it, or remove it [36][111]")

    if args.jd:
        try:
            jd = norm(Path(args.jd).expanduser().read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as exc:
            print(f"error: cannot read {args.jd}: {exc}", file=sys.stderr)
            return 2
        for r in rows:
            text = norm(r.get("requirement") or "")
            if not text:
                continue
            group = (r.get("group") or "").strip()
            if group == "must-show" and text not in jd:
                errors.append(f"{r.get('req_id')}: must-show requirement is not quoted word for word in the JD: \"{r.get('requirement')}\"")
            if group == "removed" and text in jd:
                errors.append(f"{r.get('req_id')}: removed requirement still appears in the JD: \"{r.get('requirement')}\"")

    counts = Counter((r.get("group") or "").strip() for r in rows)
    if args.json:
        print(json.dumps({"errors": errors, "warnings": warns, "counts": counts}, indent=2))
    else:
        for e in errors:
            print(f"ERROR {e}")
        for w in warns:
            print(f"WARN  {w}")
        print("Counts: " + ", ".join(f"{g} {counts.get(g, 0)}" for g in ["must-show", "test-in-process", "learn-after-hire", "removed"]))
        print("OK" if not errors else f"{len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
