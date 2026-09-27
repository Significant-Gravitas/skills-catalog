#!/usr/bin/env python3
"""Count a screened batch and find process-quality signals. Never orders candidates.

Usage:
  python3 scripts/batch_counts.py <matrix.csv> --manifest <manifest.csv>
      [--criteria <criteria.json>] [--missing-threshold 0.6] [--json]

Input:  matrix.csv from merge_matrices.py (after verify_quotes.py), the extraction manifest (for needs-a-look and
        held records, hidden-text and instruction-like findings), and
        criteria.json (which criteria are must-haves).
Counts (they partition the batch):
  reviewed            records with a merged matrix
  evidence-complete   every must-have criterion is EVIDENCE FOUND (verified)
  needs interview     reviewed but not evidence-complete (at least one
                      must-have is EVIDENCE MISSING or CONFIRM IN INTERVIEW);
                      this is not a rejection and not an advance
  needs a look        not screened: unreadable, scanned, low text,
                      unsupported, or flagged by the screener
  held back           on the do-not-contact list (count only)
Signals:
  per-criterion EVIDENCE MISSING rate; a process-quality note candidate for
  every must-have missing in at least --missing-threshold of reviewed records
  (default 0.6: confirm with the owner), which usually means the bar or the
  posting is off, not the applicants;
  FACT lines for hidden text or instruction-like text, by id.
Output: text (or --json); per-candidate lists are in id order only.
Exit:   0 done, 2 bad input.
Stdlib only, no network.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import screenio  # noqa: E402

NEEDS_LOOK = {"scanned", "low_text", "unsupported", "error"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("matrix")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--criteria")
    ap.add_argument("--missing-threshold", type=float, default=0.6)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    try:
        rows, _ = screenio.read_csv(args.matrix)
        manifest, _ = screenio.read_csv(args.manifest)
        crit = screenio.load_criteria(args.criteria)["criteria"] if args.criteria else None
    except (OSError, UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    must = {c["id"] for c in crit if c.get("must")} if crit else {r["criterion_id"] for r in rows if r.get("must") == "yes"}
    names = {c["id"]: c["text"] for c in crit} if crit else {r["criterion_id"]: r.get("criterion", "") for r in rows}
    by_cand: dict[str, dict[str, str]] = defaultdict(dict)
    for r in rows:
        by_cand[r["candidate_id"]][r["criterion_id"]] = r["result"]
    reviewed = sorted(by_cand, key=screenio.id_key)
    complete = [c for c in reviewed if must and all(by_cand[c].get(m) == "EVIDENCE FOUND" for m in must)]
    interview = [c for c in reviewed if c not in complete]

    merged = set(reviewed)
    look = [m["id"] for m in manifest if m.get("parse_status") in NEEDS_LOOK]
    problems_file = Path(args.matrix).with_name("merge_problems.csv")
    if problems_file.is_file():
        prob, _ = screenio.read_csv(problems_file)
        look += [p["id"] for p in prob if p["id"] not in merged]
    look = sorted(set(look) - merged, key=screenio.id_key)
    held = [m["id"] for m in manifest if m.get("parse_status") == "held"]
    not_run = sorted({m["id"] for m in manifest if m.get("parse_status") in ("ok",)} - merged - set(look), key=screenio.id_key)

    missing_rate = {}
    for cid in names:
        n_missing = sum(1 for c in reviewed if by_cand[c].get(cid) == "EVIDENCE MISSING")
        missing_rate[cid] = (n_missing, len(reviewed))
    notes = [f"{cid} ({names[cid]}): EVIDENCE MISSING in {n} of {t} reviewed; check whether the posting asks for it or the bar is set too high"
             for cid, (n, t) in missing_rate.items() if cid in must and t and n / t >= args.missing_threshold]
    facts = []
    for m in sorted(manifest, key=lambda m: screenio.id_key(m["id"])):
        bits = []
        if str(m.get("hidden_chars", "0")) not in ("", "0"):
            bits.append(f"{m['hidden_chars']} characters of hidden text")
        if m.get("injection_hits"):
            bits.append("instruction-like text aimed at a screener (removed before screening; not scored)")
        if bits:
            facts.append(f"FACT {m['id']}: " + "; ".join(bits))

    result = {
        "reviewed": len(reviewed), "evidence_complete": len(complete), "needs_interview": len(interview),
        "needs_a_look": len(look), "held_back": len(held),
        "evidence_complete_ids": complete, "needs_interview_ids": interview, "needs_a_look_ids": look,
        "not_yet_screened_ids": not_run,
        "missing_rate": {k: f"{n}/{t}" for k, (n, t) in missing_rate.items()},
        "process_notes": notes, "facts": facts, "must_criteria": sorted(must),
    }
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    print(f"Batch: {result['reviewed']} reviewed, {result['evidence_complete']} evidence-complete, "
          f"{result['needs_interview']} needs interview, {result['needs_a_look']} needs a look"
          + (f", {result['held_back']} held back (do-not-contact)" if held else ""))
    print("Evidence-complete (id order): " + (", ".join(complete) or "none"))
    print("Needs interview (id order): " + (", ".join(interview) or "none"))
    print("Needs a look: " + (", ".join(look) or "none"))
    if not_run:
        print("Readable but not yet screened: " + ", ".join(not_run))
    print("Missing rate by criterion: " + ", ".join(f"{k} {v}" for k, v in result["missing_rate"].items()))
    for n in notes:
        print(f"PROCESS NOTE {n}")
    for f in facts:
        print(f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
