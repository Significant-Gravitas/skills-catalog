#!/usr/bin/env python3
"""Validate a rubric before it goes to the owner for approval.

Usage:
  python3 scripts/validate_rubric.py <rubric-vN.md> [--requirements <requirements.csv>]
                                     [--write-back] [--json]

Input:  a rubric made from templates/rubric.md; optionally the requirements.csv
        written by role-intake-and-job-description.
Data:   references/disallowed-signals.csv (proxy and affect terms).
ERROR (must fix before approval):
  - the criteria table header differs from the template (the expected header is printed);
  - a criterion missing any anchor, the scorer, the confirm method, the evidence
    sources or the outcome it supports; duplicate ids or duplicate criteria;
  - identical anchors at two levels; anchor_1 written as "not assessed"
    (1 means the method was completed and found nothing);
  - comparative anchors ("better than", "top 10%", "best") [78];
  - a disallowed signal (prestige, gaps, fit, affect, polish, age, location,
    family, health, appearance, affinity) or a protected trait named outright
    (religion, sex or gender, race or ethnicity, national origin or
    citizenship, sexual orientation) in any text column of a row
    (criterion, outcome, evidence sources, anchors, not-assessed rule, confirm
    method, scorer), unless the exact word or phrase is listed in the
    allowed_terms header line with a reason. Allowed terms match whole words
    or phrases only, and may be scoped to one criterion:
    "allowed_terms: C2:billing health (the job's own metric)";
  - a communication criterion that names no work product;
  - with --requirements: a must-show requirement no criterion covers, a
    criterion citing a removed or unknown requirement.
WARN (show the owner): criteria outside the default four to seven; rating words
  in anchors ("excellent", "strong"); anchor_4 with no stated result; a scorer
  still OPEN; more than four loop methods without loop_reason [29]; a
  test-in-process requirement with no criterion; a criterion citing no requirement.
--write-back: when there are no errors, fill rubric_criterion_id in
  requirements.csv (ids joined with ';') so the JD approval item can be ticked.
Exit:   0 no errors, 1 errors (numbered fix list printed), 2 unreadable input.
Stdlib only, no network.
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rubric_io  # noqa: E402

SIGNALS = Path(__file__).resolve().parent.parent / "references" / "disallowed-signals.csv"
DEFAULT_MIN, DEFAULT_MAX = 4, 7   # default criteria count (confirm with the owner)
DEFAULT_MAX_METHODS = 4           # default loop size: four interviews reached 86% confidence [29]
COMPARATIVE = re.compile(r"\b(better than|best|top \d+%?|stronger than|compared (to|with) (other|the other)|than (most|other) candidates|rank(ed|s)?|percentile)\b", re.I)
RATING_WORDS = re.compile(r"\b(excellent|good|great|strong|poor|weak|outstanding|exceptional|solid|average|adequate|impressive)\b", re.I)
RESULT_WORDS = re.compile(r"(\d|%|\bresult|\breduc|\bincreas|\bcut\b|\bgrew|\bsaved|\bshipped|\badopted|\bused by|\bimproved|\bon time|\bfewer|\bwithout|\bremov|\bearlier|\bfaster)", re.I)
COMMS = re.compile(r"\bcommunicat", re.I)
WORK_PRODUCT = re.compile(r"\b(writ\w*|written|document\w*|runbook|policy|report\w*|email|spec\w*|present\w*|explain\w*|brief\w*|summar\w*|proposal|ticket|update|memo|slides|call|meeting)\b", re.I)
EMPTY = {"", "-", "tbd", "todo", "n/a", "?"}
# Every text column except ids and weight is scanned for disallowed signals:
# evidence_sources is passed on to resume-screening, so a proxy there would
# reach screening through an approved rubric.
SCANNED_COLUMNS = ("criterion", "outcome_supported", "evidence_sources", "anchor_1", "anchor_2",
                   "anchor_3", "anchor_4", "not_assessed_rule", "confirm_method", "scorer")


def load_signals() -> list[tuple[re.Pattern, str, str, str]]:
    with SIGNALS.open(encoding="utf-8", newline="") as fh:
        return [(re.compile(r["pattern"], re.I), r["category"], r["why"], r["source"]) for r in csv.DictReader(fh)]


def allowed(meta: dict) -> list[tuple[str | None, str, str]]:
    """Parse 'allowed_terms: [C2:]term (reason); ...' into (scope, term, reason)."""
    out = []
    for part in (meta.get("allowed_terms") or "").split(";"):
        m = re.match(r"\s*(?:(C\d+)\s*:\s*)?([^()]+?)\s*\((.+)\)\s*$", part)
        if m:
            out.append((m.group(1), m.group(2).lower(), m.group(3)))
    return out


def is_allowed(match: re.Match, text: str, cid: str, ok_terms) -> bool:
    """True when the signal match lies inside a whole-word occurrence of an allowed term for this row."""
    for scope, term, _ in ok_terms:
        if scope and scope != cid:
            continue
        for occ in re.finditer(r"\b" + re.escape(term) + r"\b", text, re.I):
            if occ.start() <= match.start() and match.end() <= occ.end():
                return True
    return False


def validate(text: str, requirements: list[dict] | None = None) -> dict:
    doc = rubric_io.parse(text)
    meta, rows = doc["meta"], doc["rows"]
    errors: list[str] = []
    warns: list[str] = []

    if doc["header"] is None:
        errors.append("no criteria table found; the header row must be: | " + " | ".join(rubric_io.HEADER) + " |")
        return {"errors": errors, "warnings": warns, "rows": [], "meta": meta}
    if doc["header"] != rubric_io.HEADER:
        errors.append("criteria table header differs from the template; expected: | " + " | ".join(rubric_io.HEADER) + " |")

    for key in ("role_slug", "version", "status"):
        if not meta.get(key) or meta[key].startswith("<"):
            errors.append(f"header line '{key}:' is missing or not filled")
    if meta.get("status") not in (None, "", "draft", "approved"):
        errors.append("status must be draft or approved")

    if not rows:
        errors.append("the criteria table has no rows")
    n = len(rows)
    if rows and not DEFAULT_MIN <= n <= DEFAULT_MAX:
        warns.append(f"{n} criteria; the default is {DEFAULT_MIN} to {DEFAULT_MAX} (fewer is fine for a narrow role; confirm with the owner)")

    signals = load_signals()
    ok_terms = allowed(meta)
    for scope, term, reason in ok_terms:
        where_ok = f" in {scope} only" if scope else " in every criterion"
        warns.append(f"allowed by the owner: '{term}'{where_ok} ({reason}); the approver sees this line")

    ids, names = set(), set()
    for r in rows:
        cid = r.get("criterion_id", "")
        where = f"line {r['_line']} ({cid or 'no id'})"
        if not re.fullmatch(r"C\d+", cid):
            errors.append(f"{where}: criterion_id must look like C1, C2 ...")
        if cid in ids:
            errors.append(f"{where}: duplicate criterion_id")
        ids.add(cid)
        key = re.sub(r"\W+", " ", r.get("criterion", "").lower()).strip()
        if key in names:
            errors.append(f"{where}: duplicate criterion text; merge them (criteria must be separately scorable)")
        names.add(key)
        for col in ("criterion", "outcome_supported", "evidence_sources", "anchor_1", "anchor_2",
                    "anchor_3", "anchor_4", "not_assessed_rule", "confirm_method", "scorer"):
            if r.get(col, "").strip().lower() in EMPTY or r.get(col, "").startswith("<"):
                errors.append(f"{where}: '{col}' is empty")
        anchors = [r.get(f"anchor_{k}", "").strip().lower() for k in range(1, 5)]
        if len({a for a in anchors if a}) < len([a for a in anchors if a]):
            errors.append(f"{where}: two anchors are identical; each level needs its own observable description")
        if re.search(r"not assessed|no evidence available|not tested", anchors[0]):
            errors.append(f"{where}: anchor_1 means 'method completed, no qualifying evidence'; 'not assessed' is separate, never a 1")
        for k in range(1, 5):
            a = r.get(f"anchor_{k}", "")
            if COMPARATIVE.search(a):
                errors.append(f"{where}: anchor_{k} compares candidates ('{COMPARATIVE.search(a).group(0)}'); anchors describe behaviour against a fixed standard [78]")
            if RATING_WORDS.search(a):
                warns.append(f"{where}: anchor_{k} uses a rating word ('{RATING_WORDS.search(a).group(0)}'); describe what the person did [78]")
        if r.get("anchor_4") and not RESULT_WORDS.search(r["anchor_4"]):
            warns.append(f"{where}: anchor_4 should name a stated result (level 4 = greater scope with a result)")
        for col in SCANNED_COLUMNS:
            scanned = r.get(col, "")
            for pat, cat, why, src in signals:
                for m in pat.finditer(scanned):
                    if is_allowed(m, scanned, cid, ok_terms):
                        continue
                    errors.append(f"{where}: disallowed signal '{m.group(0)}' in {col} [{cat}]: {why} {src}")
        if COMMS.search(r.get("criterion", "")) and not WORK_PRODUCT.search(r.get("criterion", "") + " " + r.get("anchor_3", "")):
            errors.append(f"{where}: a communication criterion must name the work product and the level the role needs")
        if r.get("scorer", "").strip().upper().startswith("OPEN"):
            warns.append(f"{where}: scorer is OPEN; name one person before approval")
        if requirements is not None and not rubric_io.req_ids(r.get("requirement_ids", "")):
            warns.append(f"{where}: cites no requirement; add one to requirements.csv (usually test-in-process) so the posting and the rubric agree [111]")
        w = r.get("weight", "").strip().lower()
        if meta.get("weighting", "equal").lower().startswith("equal") and w not in ("equal", ""):
            warns.append(f"{where}: weighting is 'equal' in the header but this row says '{r.get('weight')}'")

    if meta.get("weighting", "").lower().startswith("custom"):
        try:
            total = sum(float(r.get("weight") or 0) for r in rows)
            if abs(total - 100) > 0.01:
                warns.append(f"custom weights add up to {total:g}, not 100")
        except ValueError:
            errors.append("custom weighting needs a number in every weight cell")

    methods = [m for m in re.split(r"[;,]", meta.get("loop_methods", "")) if m.strip() and not m.strip().startswith("<")]
    if len(methods) > DEFAULT_MAX_METHODS and not meta.get("loop_reason"):
        warns.append(f"{len(methods)} loop methods; the default is {DEFAULT_MAX_METHODS} or fewer [29]; add loop_reason or cut one")

    coverage: dict[str, list[str]] = {}
    if requirements is not None:
        by_id = {q.get("req_id", "").strip(): q for q in requirements}
        for r in rows:
            for rid in rubric_io.req_ids(r.get("requirement_ids", "")):
                if rid not in by_id:
                    errors.append(f"{r.get('criterion_id')}: cites unknown requirement {rid}")
                elif by_id[rid].get("group", "").strip() == "removed":
                    errors.append(f"{r.get('criterion_id')}: cites removed requirement {rid} ('{by_id[rid].get('requirement')}'); the posting no longer asks for it, so it must not be scored [111]")
                else:
                    coverage.setdefault(rid, []).append(r.get("criterion_id", ""))
        for rid, q in by_id.items():
            g = q.get("group", "").strip()
            if g == "must-show" and rid not in coverage:
                errors.append(f"must-show requirement {rid} ('{q.get('requirement')}') has no criterion")
            if g == "test-in-process" and rid not in coverage:
                warns.append(f"test-in-process requirement {rid} ('{q.get('requirement')}') has no criterion")

    return {"errors": errors, "warnings": warns, "rows": rows, "meta": meta, "coverage": coverage}


def read_requirements(path: str) -> tuple[list[dict], list[str]]:
    with Path(path).expanduser().open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        return list(reader), list(reader.fieldnames or [])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("rubric")
    ap.add_argument("--requirements")
    ap.add_argument("--write-back", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        text = Path(args.rubric).expanduser().read_text(encoding="utf-8")
        reqs, fields = read_requirements(args.requirements) if args.requirements else (None, [])
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: cannot read input: {exc}", file=sys.stderr)
        return 2

    result = validate(text, reqs)
    wrote = False
    if args.write_back and args.requirements and not result["errors"]:
        if "rubric_criterion_id" not in fields:
            result["errors"].append("requirements.csv has no rubric_criterion_id column; recreate it from role-intake-and-job-description's template")
        else:
            for q in reqs:
                q["rubric_criterion_id"] = ";".join(result["coverage"].get(q.get("req_id", "").strip(), []))
            with Path(args.requirements).expanduser().open("w", encoding="utf-8", newline="") as fh:
                w = csv.DictWriter(fh, fieldnames=fields)
                w.writeheader()
                w.writerows(reqs)
            wrote = True

    if args.json:
        print(json.dumps({k: result[k] for k in ("errors", "warnings", "coverage") if k in result} | {"wrote_back": wrote}, indent=2))
    else:
        for i, e in enumerate(result["errors"], 1):
            print(f"ERROR {i}. {e}")
        for w in result["warnings"]:
            print(f"WARN  {w}")
        print(f"Criteria: {len(result['rows'])}; status: {result['meta'].get('status', '?')}; version: {result['meta'].get('version', '?')}")
        if wrote:
            print(f"Wrote rubric_criterion_id back to {args.requirements}")
        print("OK" if not result["errors"] else f"{len(result['errors'])} error(s); fix them before asking for approval")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
