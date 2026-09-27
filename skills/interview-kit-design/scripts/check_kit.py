#!/usr/bin/env python3
"""Check an interview kit before interview coordination books it.

    cd ~/skills/interview-kit-design && python3 scripts/check_kit.py \
        ~/workspace/hiring/roles/<role-slug>/kit.md [--scorecard <role scorecard.md>] \
        [--min-questions 4] [--max-questions 6] [--max-slots 4] [--json]

Kit shape: templates/kit.md. With --scorecard, the must-haves are also read
from the role scorecard (lines "- M1: ..." or "M1." / "M1 -") and every one
must appear in the kit.

ERROR
- a must-have owned by no slot, or by more than one slot ("exactly one owner")
- a slot owning an M-id that is not a must-have
- a slot with no length, or clock segments that do not add up to its length
- a slot (other than one marked "owns: none") with no questions
- an owned must-have with no anchors, or anchors missing any of 1-5
WARN
- a slot with no interviewer (UNASSIGNED): name it in the hand-back
- questions per slot outside 4-6 (skill default range; owner may change)
- more than --max-slots slots (default 4: Google's analysis found four
  interviews predicted the hire decision with 86% confidence [29]; a longer
  loop needs a stated reason)
- the main-problem segment is over two thirds of the slot: it overruns and
  eats the candidate's questions (skill guidance)
- anchors marked draft, or the kit status is draft

Exit 0 with no ERROR, 1 with any ERROR, 2 on bad input. --selftest runs a fixture.
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitparse  # noqa: E402

LEVELS = ["1", "2", "3", "4", "5"]


def scorecard_ids(path):
    ids = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r"^\s*(?:[-*|]\s*)?(M\d+)\s*[:.)|-]\s*(.+)", line)
            if m:
                ids.setdefault(m.group(1), m.group(2).strip(" |"))
    return ids


def check(kit, extra_ids, min_q, max_q, max_slots):
    errors, warns = [], []
    musts = dict(kit["must_haves"])
    for k, v in extra_ids.items():
        if k not in musts:
            errors.append(f"{k} is on the role scorecard but not in the kit's must-haves: {v}")
            musts[k] = v
    if not musts:
        errors.append("no must-haves found (lines '- M1: ...' under '## Must-haves')")
    owners = {k: [] for k in musts}
    for s in kit["slots"]:
        tag = f"slot {s['n']} ({s['title']})"
        for mid in s["owns"]:
            if mid not in musts:
                errors.append(f"{tag} owns {mid}, which is not a must-have")
            else:
                owners[mid].append(s["n"])
        close_only = not s["owns"] and "none" in s.get("owns_raw", "").lower()
        if not s["owns"] and not close_only:
            errors.append(f"{tag} owns no competency; add one or write 'owns: none' for the close")
        if not s["interviewer"] or s["interviewer"].upper().startswith("UNASSIGNED"):
            warns.append(f"{tag} has no interviewer")
        if s["length"] is None:
            errors.append(f"{tag} has no length")
        elif not s["clock"]:
            errors.append(f"{tag} has no clock (e.g. 'clock: 5 context, 30 main, 10 candidate questions')")
        else:
            total = sum(m for m, _ in s["clock"])
            if total != s["length"]:
                errors.append(f"{tag} clock adds to {total} min, slot is {s['length']} min")
            main = [m for m, lbl in s["clock"] if "main" in lbl.lower() or "problem" in lbl.lower()]
            if main and main[0] > s["length"] * 2 / 3:
                warns.append(f"{tag} main segment is {main[0]} of {s['length']} min; it will overrun "
                             "and eat the candidate's questions")
            if not any("candidate" in lbl.lower() for _, lbl in s["clock"]):
                warns.append(f"{tag} clock has no time for the candidate's questions")
        nq = len(s["questions"])
        if nq == 0 and not close_only:
            errors.append(f"{tag} has no questions")
        elif not close_only and not (min_q <= nq <= max_q):
            warns.append(f"{tag} has {nq} questions (default range {min_q}-{max_q})")
        for q in s["questions"]:
            if not close_only and (not q["strong"] or not q["probe"]):
                warns.append(f"{tag} question '{q['text'][:50]}' lacks a strong-answer note or a probe")
        for mid in s["owns"]:
            anchors = s["anchors"].get(mid)
            if not anchors:
                errors.append(f"{tag} has no anchors for {mid}")
                continue
            missing = [lv for lv in LEVELS if lv not in anchors]
            if missing:
                errors.append(f"{tag} anchors for {mid} miss level(s) {', '.join(missing)}")
            if any("draft" in v.lower() for v in anchors.values()):
                warns.append(f"{tag} anchors for {mid} are still marked draft")
    for mid, slots in owners.items():
        if not slots:
            errors.append(f"{mid} ({musts[mid][:60]}) has no owner slot: it would be 'not assessed' for everyone")
        elif len(slots) > 1:
            errors.append(f"{mid} is owned by slots {slots}; give it exactly one owner")
    if len(kit["slots"]) > max_slots:
        warns.append(f"{len(kit['slots'])} slots; default is {max_slots} (four interviews predicted the "
                     "decision with 86% confidence [29]). State the reason for the extra slot(s).")
    if kit["meta"].get("status", "").lower().startswith("draft"):
        warns.append("kit status is draft: the owner has not approved it")
    return errors, warns


FIXTURE = """# Interview kit: Test
role_slug: test
status: draft

## Must-haves
- M1: Go services
- M2: Billing debugging

## Slot 1: Screen
length: 30
interviewer: Sam Lee
owns: M1
clock: 5 context, 20 main, 5 candidate questions

### Questions
1. "Walk me through a Go service you own."
   - Strong answer: names the service.
   - Probe: Which part was yours?

### Anchors M1
- 1: a
- 2: b
- 3: c
- 4: d
- 5: e

## Slot 2: Debugging
length: 60
interviewer: UNASSIGNED
owns: M2, M1
clock: 5 context, 45 main problem, 5 candidate questions
"""


def selftest():
    kit = kitparse.parse(FIXTURE)
    assert kit["must_haves"] == {"M1": "Go services", "M2": "Billing debugging"}, kit["must_haves"]
    assert kit["slots"][0]["clock"] == [(5, "context"), (20, "main"), (5, "candidate questions")]
    errors, warns = check(kit, {"M3": "Owns on-call"}, 4, 6, 4)
    text = "\n".join(errors + warns)
    for needle in ("M3 is on the role scorecard", "M1 is owned by slots [1, 2]", "clock adds to 55",
                   "slot 2 (Debugging) has no questions", "no anchors for M2", "no interviewer",
                   "status is draft"):
        assert needle in text, (needle, text)
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("kit", nargs="?")
    ap.add_argument("--scorecard")
    ap.add_argument("--min-questions", type=int, default=4)
    ap.add_argument("--max-questions", type=int, default=6)
    ap.add_argument("--max-slots", type=int, default=4)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.kit:
        ap.error("give the kit path")
    try:
        with open(a.kit, encoding="utf-8") as fh:
            kit = kitparse.parse(fh.read())
        extra = scorecard_ids(a.scorecard) if a.scorecard else {}
    except OSError as exc:
        print(f"bad input: {exc}", file=sys.stderr)
        return 2
    if not kit["slots"]:
        print("bad input: no '## Slot N: title' sections; use templates/kit.md", file=sys.stderr)
        return 2
    errors, warns = check(kit, extra, a.min_questions, a.max_questions, a.max_slots)
    if a.json:
        print(json.dumps({"errors": errors, "warnings": warns,
                          "slots": [{"n": s["n"], "title": s["title"], "interviewer": s["interviewer"],
                                     "owns": s["owns"], "length": s["length"],
                                     "questions": len(s["questions"])} for s in kit["slots"]]}, indent=1))
    else:
        print(f"{len(kit['slots'])} slot(s), {len(kit['must_haves'])} must-have(s)")
        for e in errors:
            print(f"ERROR\t{e}")
        for w in warns:
            print(f"WARN\t{w}")
        if not errors:
            print("ok: every must-have has exactly one owner and every clock adds up")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
