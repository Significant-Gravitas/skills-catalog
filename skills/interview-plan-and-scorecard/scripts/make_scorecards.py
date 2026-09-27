#!/usr/bin/env python3
"""Generate one blank scorecard per interviewer, holding only that person's criteria.

Usage:
  cd ~/skills/interview-plan-and-scorecard && \
  python3 scripts/make_scorecards.py <rubric.csv|rubric.md> <loop.csv> <out_dir> \
      --candidate <candidate-id> [--role "<role title>"] [--scale 4]
  python3 scripts/make_scorecards.py --selftest   (file-name uniqueness check)

Inputs
  rubric   columns: criterion_id, criterion, anchor_1 .. anchor_N
           (headers "1".."N" or "score_1".."score_N" also work).
           Anchors are copied verbatim; a missing anchor is written as
           "[ANCHOR MISSING - rubric owner to confirm]" and reported.
  loop     columns: slot, interviewer, criterion_ids, method, minutes, questions_ref
  --scale  number of score levels; default 4 because the Harper rubric uses 1-4
           (hiring-rubric-design). Use the company's own scale if it has one.

Outputs, per interviewer, in <out_dir>:
  scorecard-<candidate>-<interviewer>.md   the form the interviewer fills in
  scorecard-<candidate>-<interviewer>.csv  the same rows, machine-readable;
                                           candidate-interview-debrief reads it
<interviewer> is an ASCII slug (accents folded; a name with no Latin letters
becomes id-<hash>). If two interviewers would share a file name, the second
gets -slot<n>, so no card overwrites another. A rubric that repeats a
criterion_id is refused (exit 2).
The CSV columns are fixed:
  candidate_id,interviewer,slot,criterion_id,criterion,score,evidence_quote,
  source,confidence,submitted_at
`score` accepts 1..N or "not assessed". The layout follows
templates/scorecard-template.md.

The script never writes a total, average or overall rating field, and adds no
demeanour, confidence, enthusiasm or "fit" row.
Exit 0 = written, 1 = written with warnings (missing anchors), 2 = bad input.
"""

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tables import read_table, split_ids, slug, fail  # noqa: E402

MISSING = "[ANCHOR MISSING - rubric owner to confirm]"
COLUMNS = ["candidate_id", "interviewer", "slot", "criterion_id", "criterion", "score",
           "evidence_quote", "source", "confidence", "submitted_at"]


def anchor(row: dict, level: int) -> str:
    for key in (f"anchor_{level}", str(level), f"score_{level}", f"level_{level}"):
        if row.get(key):
            return row[key]
    return ""


def file_names(by_person: dict) -> dict:
    """One file name per interviewer: never let two people share a name, or the
    second card would silently overwrite the first."""
    names: dict[str, str] = {}
    taken: set[str] = set()
    for who, items in by_person.items():
        name = slug(who)
        if name in taken:
            name = f"{name}-slot{items[0][0].get('slot', '') or len(taken) + 1}"
        if name in taken:
            fail(f"interviewer '{who}' would share the file name '{name}' with another interviewer; "
                 "give the loop distinct interviewer names")
        taken.add(name)
        names[who] = name
    return names


def selftest() -> int:
    cases = {"李明": [({"slot": "1"}, "C1")], "王芳": [({"slot": "2"}, "C2")],
             "José Núñez": [({"slot": "3"}, "C3")], "Jose Nunez": [({"slot": "4"}, "C1")]}
    got = file_names(cases)
    bad = 0
    if len(set(got.values())) != len(cases):
        print(f"FAIL file names collide: {got}")
        bad += 1
    if got["José Núñez"] != "jose-nunez" or got["Jose Nunez"] != "jose-nunez-slot4":
        print(f"FAIL accent folding / slot suffix: {got}")
        bad += 1
    if got["李明"] != slug("李明") or not got["李明"].startswith("id-"):
        print(f"FAIL non-Latin name is not a stable id: {got['李明']}")
        bad += 1
    print("selftest OK" if not bad else f"selftest: {bad} failure(s)")
    return 1 if bad else 0


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    ap = argparse.ArgumentParser()
    ap.add_argument("rubric")
    ap.add_argument("loop")
    ap.add_argument("out_dir")
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--role", default="")
    ap.add_argument("--scale", type=int, default=4)
    a = ap.parse_args()
    if not 2 <= a.scale <= 7:
        fail("--scale must be between 2 and 7")

    rubric_rows = [r for r in read_table(a.rubric) if r.get("criterion_id")]
    seen_ids: set[str] = set()
    for r in rubric_rows:
        if r["criterion_id"] in seen_ids:
            fail(f"criterion {r['criterion_id']} appears more than once in the rubric; the rubric "
                 "owner must keep one row per criterion (run check_loop.py first)")
        seen_ids.add(r["criterion_id"])
    rubric = {r["criterion_id"]: r for r in rubric_rows}
    if not rubric:
        fail("rubric has no criterion_id rows (see templates/rubric.csv)")
    loop = read_table(a.loop)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    by_person: dict[str, list[tuple[dict, str]]] = {}
    for row in loop:
        who = row.get("interviewer", "").strip()
        if not who:
            fail(f"slot {row.get('slot', '?')} has no interviewer; run check_loop.py first")
        for cid in split_ids(row.get("criterion_ids", "")):
            if cid not in rubric:
                fail(f"criterion {cid} is not in the rubric; run check_loop.py first")
            by_person.setdefault(who, []).append((row, cid))

    gaps = 0
    cand = slug(a.candidate)
    levels = list(range(1, a.scale + 1))
    names = file_names(by_person)

    for who, items in by_person.items():
        base = out / f"scorecard-{cand}-{names[who]}"
        md = [
            f"# Scorecard: {a.role or 'role'} | candidate {a.candidate} | interviewer {who}",
            "",
            "**Submit this before you read anyone else's scorecard or discuss the candidate.**",
            "Rate each criterion on its own, using the anchors below, before writing anything overall.",
            "Write what the candidate said or did (a quote or a specific action), not an impression.",
            "Do not rate or note demeanour, confidence, nerves, enthusiasm, honesty, accent, appearance,",
            "age, family, origin, health or \"fit\". Use `not assessed` if you did not test the criterion.",
            "",
        ]
        rows = []
        for slot_row, cid in items:
            r = rubric[cid]
            md += [f"## {cid}: {r.get('criterion', '')}",
                   f"Slot: {slot_row.get('slot', '')} | method: {slot_row.get('method', '')} | "
                   f"questions: {slot_row.get('questions_ref', '') or 'see question bank'}", "",
                   "| Score | Anchor (what this level looks like) |", "|---|---|"]
            for lv in levels:
                text = anchor(r, lv)
                if not text:
                    text, gaps = MISSING, gaps + 1
                md.append(f"| {lv} | {text} |")
            md += ["| not assessed | The criterion was not tested in this slot, or time ran out. |", "",
                   "- Score (" + " / ".join(str(x) for x in levels) + " / not assessed): ",
                   "- Evidence (quote or observed action): ",
                   "- Source (question / work sample / portfolio / reference): ",
                   "- Confidence in this evidence (high / medium / low): ", ""]
            rows.append({"candidate_id": a.candidate, "interviewer": who,
                         "slot": slot_row.get("slot", ""), "criterion_id": cid,
                         "criterion": r.get("criterion", ""), "score": "", "evidence_quote": "",
                         "source": slot_row.get("method", ""), "confidence": "", "submitted_at": ""})
        md += ["## Filing", "",
               "- Submitted at (date, time and timezone): ",
               "- I filed this before seeing other interviewers' scores (yes / no): ", ""]
        base.with_suffix(".md").write_text("\n".join(md), encoding="utf-8")
        with base.with_suffix(".csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=COLUMNS)
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {base.name}.md and .csv ({len(rows)} criteria)")

    if gaps:
        print(f"WARNING {gaps} anchor(s) missing; ask the rubric owner before distributing.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
