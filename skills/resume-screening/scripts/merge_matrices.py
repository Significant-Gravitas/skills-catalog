#!/usr/bin/env python3
"""Collect per-candidate screening records into one matrix, in candidate-id order.

Usage:
  python3 scripts/merge_matrices.py <records_dir> --criteria <criteria.json> --out-dir <batch_dir>

Input:  <records_dir>/<id>.json, one per candidate, each written by a separate
        screening pass (templates/screen-subtask-prompt.md defines the shape):
          {"id": "A-001", "rubric_version": 1,
           "rows": [{"criterion_id": "C1", "result": "EVIDENCE FOUND",
                     "quote": "...", "location": "role 1, bullet 2", "note": ""}],
           "interview_questions": ["..."], "needs_a_look": false, "needs_a_look_reason": ""}
        criteria.json from find_rubric.py --emit-criteria.
Checks: every criterion has exactly one row; result is one of EVIDENCE FOUND,
        EVIDENCE MISSING, CONFIRM IN INTERVIEW; every EVIDENCE FOUND row has a
        quote and a location; no unknown criterion ids; no score, rank or
        recommendation fields. Problems are printed per id and the record goes
        on the needs-a-look list instead of into the matrix.
Run verify_quotes.py on <records_dir> first; an EVIDENCE FOUND row without a
        quote_check is listed as unverified.
Output: <batch_dir>/matrix.csv   candidate_id,criterion_id,criterion,must,result,
                                 sofia_label,quote,location,note,quote_check
        <batch_dir>/matrices.md  one table per candidate plus its interview
                                 questions, in id order (never sorted by result)
        <batch_dir>/merge_problems.csv  id,problem (if any)
Exit:   0 merged (problems listed), 2 bad input.
Stdlib only, no network.
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import screenio  # noqa: E402

FORBIDDEN_KEYS = {"score", "rank", "ranking", "recommendation", "decision", "advance", "reject", "overall", "fit"}


def check(rec: dict, crit_ids: list[str]) -> list[str]:
    problems = []
    bad_keys = FORBIDDEN_KEYS & {k.lower() for k in rec}
    if bad_keys:
        problems.append(f"record carries forbidden field(s) {sorted(bad_keys)}; the screen never scores, ranks or recommends")
    rows = rec.get("rows") or []
    seen = {}
    for r in rows:
        cid = r.get("criterion_id", "")
        if cid not in crit_ids:
            problems.append(f"unknown criterion '{cid}'")
            continue
        if cid in seen:
            problems.append(f"criterion {cid} appears twice")
        seen[cid] = r
        if r.get("result") not in screenio.RESULTS:
            problems.append(f"{cid}: result must be one of {list(screenio.RESULTS)}, got '{r.get('result')}'")
        if r.get("result") == "EVIDENCE FOUND" and (not (r.get("quote") or "").strip() or not (r.get("location") or "").strip()):
            problems.append(f"{cid}: EVIDENCE FOUND needs a quote and its location")
        if FORBIDDEN_KEYS & {k.lower() for k in r}:
            problems.append(f"{cid}: row carries a score, rank or recommendation field")
    for cid in crit_ids:
        if cid not in seen:
            problems.append(f"criterion {cid} has no row")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("records_dir")
    ap.add_argument("--criteria", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    try:
        crit = screenio.load_criteria(args.criteria)["criteria"]
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    crit_ids = [c["id"] for c in crit]
    by_id = {c["id"]: c for c in crit}
    rec_dir = Path(args.records_dir).expanduser()
    files = sorted(rec_dir.glob("*.json"), key=lambda p: screenio.id_key(p.stem))
    if not files:
        print(f"error: no record files in {rec_dir}", file=sys.stderr)
        return 2

    matrix, problems, md, unverified = [], [], [], []
    for f in files:
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            problems.append({"id": f.stem, "problem": f"not valid JSON: {exc}"})
            continue
        cid = rec.get("id") or f.stem
        if rec.get("needs_a_look"):
            problems.append({"id": cid, "problem": "needs a look: " + (rec.get("needs_a_look_reason") or "screener could not read it")})
            continue
        errs = check(rec, crit_ids)
        if errs:
            problems.extend({"id": cid, "problem": e} for e in errs)
            continue
        rows = {r["criterion_id"]: r for r in rec["rows"]}
        md.append(f"### {cid}\n\n| Criterion | Result | Evidence |\n|---|---|---|")
        for c in crit_ids:
            r = rows[c]
            out = {"candidate_id": cid, "criterion_id": c, "criterion": by_id[c]["text"],
                   "must": "yes" if by_id[c].get("must") else "no", "result": r["result"],
                   "sofia_label": screenio.SOFIA_LABEL[r["result"]], "quote": (r.get("quote") or "").strip(),
                   "location": (r.get("location") or "").strip(), "note": (r.get("note") or "").strip(),
                   "quote_check": r.get("quote_check", "")}
            if out["result"] == "EVIDENCE FOUND" and not out["quote_check"]:
                unverified.append(f"{cid} {c}")
            matrix.append(out)
            ev = f"\"{out['quote']}\" ({out['location']})" if out["quote"] else (out["note"] or "not stated")
            if out["quote"] and out["note"]:
                ev += f"; {out['note']}"
            if out["quote_check"].startswith("approximate"):
                ev += " [approximate match: read the source line]"
            md.append(f"| {c} {by_id[c]['text']} | `{r['result']}` | {ev.replace('|', '/')} |")
        qs = rec.get("interview_questions") or []
        md.append("\nQuestions for interview: " + (" ".join(qs) if qs else "none") + "\n")

    out_dir = Path(args.out_dir).expanduser()
    screenio.write_csv(out_dir / "matrix.csv", matrix, screenio.MATRIX_FIELDS)
    (out_dir / "matrices.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    if problems:
        screenio.write_csv(out_dir / "merge_problems.csv", problems, ["id", "problem"])
    merged = len({m["candidate_id"] for m in matrix})
    print(f"merged {merged} record(s) into matrix.csv and matrices.md (id order)")
    for p in problems:
        print(f"PROBLEM {p['id']}: {p['problem']}")
    if unverified:
        print("UNVERIFIED quotes (run verify_quotes.py on the records, then merge again): " + ", ".join(unverified))
    return 0


if __name__ == "__main__":
    sys.exit(main())
