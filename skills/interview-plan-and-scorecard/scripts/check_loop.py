#!/usr/bin/env python3
"""Check an interview loop against the approved rubric before anyone is invited.

Usage:
  cd ~/skills/interview-plan-and-scorecard && \
  python3 scripts/check_loop.py <rubric.csv|rubric.md> <loop.csv> \
      [--loop-minutes N] [--max-interviews 4] [--reference-policy yes|no|unknown] [--json]

Inputs
  rubric   columns: criterion_id, criterion (anchor columns are not needed here)
  loop     columns: slot, interviewer, criterion_ids, method, minutes,
           questions_ref, secondary_ids (optional), reason (optional)
           See templates/loop.csv. criterion_ids are the criteria that slot
           SCORES (primary). secondary_ids may be probed but never scored there.

Errors (exit 1, with a fix list):
  - a criterion_id that appears more than once in the rubric;
  - a rubric criterion with no primary slot, or with more than one;
  - an unknown criterion id in the loop;
  - a method outside question | work-sample | portfolio | reference;
  - a slot with no interviewer or no minutes;
  - slot minutes that do not add up to --loop-minutes (when given);
  - more slots than --max-interviews without a `reason` filled on the extra slots.
Warnings (exit 0):
  - a reference-check slot while --reference-policy is not "yes";
  - one interviewer holding every slot (no independent second view);
  - a slot that scores more than 3 criteria (default, confirm with the owner:
    each extra criterion shortens the evidence time for the others).

--max-interviews defaults to 4: Google's analysis found four interviews
predicted the hire decision with 86% confidence (Bock, Knowledge at Wharton
2015, dossier [29]). It is a default; the owner can set another number.

Output: a plain report on stdout (or JSON with --json). Exit 0 = no errors,
1 = errors found, 2 = bad input.
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tables import read_table, split_ids, fail  # noqa: E402

METHODS = {"question", "work-sample", "portfolio", "reference"}
MAX_CRITERIA_PER_SLOT = 3  # default, confirm with the owner


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("rubric")
    ap.add_argument("loop")
    ap.add_argument("--loop-minutes", type=int)
    ap.add_argument("--max-interviews", type=int, default=4)
    ap.add_argument("--reference-policy", choices=["yes", "no", "unknown"], default="unknown")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    rubric = read_table(a.rubric)
    if not rubric or "criterion_id" not in rubric[0]:
        fail("rubric needs a criterion_id column (see templates/rubric.csv)")
    loop = read_table(a.loop)
    if not loop:
        fail("loop has no rows (see templates/loop.csv)")
    for col in ("slot", "interviewer", "criterion_ids", "method", "minutes"):
        if col not in loop[0]:
            fail(f"loop is missing the '{col}' column (see templates/loop.csv)")

    ids = [r["criterion_id"] for r in rubric if r.get("criterion_id")]
    names = {r["criterion_id"]: r.get("criterion", "") for r in rubric}
    errors, warnings = [], []
    owners = defaultdict(list)
    total = 0
    dup_ids = sorted({cid for cid in ids if ids.count(cid) > 1})
    for cid in dup_ids:
        errors.append(f"criterion {cid} appears {ids.count(cid)} times in the rubric. Keep one row per "
                      "criterion (ask the rubric owner which anchors are approved).")
    ids = list(dict.fromkeys(ids))

    for n, row in enumerate(loop, start=1):
        slot = row.get("slot") or f"row {n}"
        who = row.get("interviewer", "")
        method = row.get("method", "").lower()
        prim = split_ids(row.get("criterion_ids", ""))
        sec = split_ids(row.get("secondary_ids", ""))
        if not who:
            errors.append(f"slot {slot}: no interviewer named. Add one or mark the slot as a missing owner.")
        if method not in METHODS:
            errors.append(f"slot {slot}: method '{method}' is not one of {sorted(METHODS)}.")
        if method == "reference" and a.reference_policy != "yes":
            warnings.append(f"slot {slot}: reference check planned but company policy on references is '{a.reference_policy}'. Confirm with the owner.")
        try:
            minutes = int(row.get("minutes", ""))
            total += minutes
        except ValueError:
            errors.append(f"slot {slot}: minutes '{row.get('minutes', '')}' is not a whole number.")
        if not prim:
            errors.append(f"slot {slot}: scores no criterion. Give it one or drop the slot.")
        if len(prim) > MAX_CRITERIA_PER_SLOT:
            warnings.append(f"slot {slot}: scores {len(prim)} criteria (default limit {MAX_CRITERIA_PER_SLOT}, confirm with the owner).")
        for cid in prim + sec:
            if cid not in names:
                errors.append(f"slot {slot}: criterion '{cid}' is not in the rubric. The loop may not add criteria.")
        for cid in prim:
            owners[cid].append(f"{slot} ({who or 'no interviewer'})")

    for cid in ids:
        if not owners.get(cid):
            errors.append(f"criterion {cid} ({names[cid]}): no slot scores it. Assign one primary owner and method.")
        elif len(owners[cid]) > 1:
            errors.append(f"criterion {cid} ({names[cid]}): scored in {len(owners[cid])} slots {owners[cid]}. Keep one primary; move the others to secondary_ids.")

    if a.loop_minutes is not None and total != a.loop_minutes:
        errors.append(f"slot minutes add up to {total}, stated loop length is {a.loop_minutes}.")

    if len(loop) > a.max_interviews:
        extra = loop[a.max_interviews:]
        missing = [r.get("slot", "?") for r in extra if not r.get("reason")]
        if missing:
            errors.append(
                f"{len(loop)} slots is over the default of {a.max_interviews} "
                f"(Bock [29]); fill `reason` for slots {missing} or cut them."
            )

    people = {r.get("interviewer", "") for r in loop if r.get("interviewer")}
    if len(loop) > 1 and len(people) == 1:
        warnings.append("one interviewer holds every slot, so no criterion gets an independent second view.")

    result = {
        "criteria": len(ids),
        "slots": len(loop),
        "total_minutes": total,
        "owners": {cid: owners.get(cid, []) for cid in ids},
        "errors": errors,
        "warnings": warnings,
    }
    if a.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Loop check: {len(loop)} slots, {total} minutes, {len(ids)} criteria")
        for cid in ids:
            print(f"  {cid}: {', '.join(owners.get(cid, [])) or 'UNCOVERED'}")
        for e in errors:
            print(f"ERROR   {e}")
        for w in warnings:
            print(f"WARNING {w}")
        print("OK: every criterion has exactly one primary owner." if not errors else f"{len(errors)} error(s): fix before output.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
