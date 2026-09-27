#!/usr/bin/env python3
"""Record debrief decisions and read them back for patterns.

    cd ~/skills/hiring-debrief-and-decision && python3 scripts/decision_log.py append \
        --date 2026-10-09 --role "Senior Backend Engineer" --candidate "Priya Nair" \
        --decision yes|no|hold|no-clear-call --decider "Lena Ortiz" --reason "<their words, verbatim>" \
        [--splits 1] [--filed-ratio 1.0] [--no-decision-count 0] [--fcra yes|no] \
        [--stage "<new stage, owner's wording>" --next-step "<next step>"] \
        [--decisions ~/workspace/hiring/debriefs/decisions.csv] [--tracker ~/workspace/hiring/tracker]

    python3 scripts/decision_log.py report [--role R] [--last 10] [--bar 0.2] [--similar 0.75]

append
- Only after the decision-maker has stated the decision. --reason is their
  words verbatim (required for a no; the weekly review looks for repeats).
- --fcra yes marks that a background check is part of the decision: the
  record says the FCRA process applies before any decline, and the tracker's
  next_step is set to "FCRA process" instead of a decline draft.
- --stage / --next-step also update that candidate's row in
  <tracker>/candidates.csv (stage, stage_since, next_step). Run it only after the
  owner confirms the row change. The row must exist; nothing else is touched.

report
- Share of no-clear-call decisions over the last --last debriefs (default 10),
  overall and per role. Above --bar (default 0.2: the skill's "more than one in
  five" flag; confirm with the owner) the anchors are loose: propose the fix
  through interview-kit-design.
- Repeated "no" reasons: exact and near matches (difflib ratio >= --similar,
  default 0.75, a named default), grouped with counts.

Exit 0; 1 when report finds the no-clear-call share above the bar; 2 on bad input.
--selftest uses a temp folder.
"""

import argparse
import csv
import datetime as dt
import difflib
import os
import re
import sys
import tempfile
import unicodedata

COLS = ["date", "role", "candidate", "decision", "decider", "reason_verbatim", "splits_count",
        "filed_ratio", "no_decision_count", "fcra"]
DECISIONS = {"yes", "no", "hold", "no-clear-call"}


def fold(t):
    t = unicodedata.normalize("NFKD", t or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", t).split())


def load(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def write(path, cols, rows):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, path)


def append(a):
    if a.decision not in DECISIONS:
        raise ValueError(f"--decision must be one of {sorted(DECISIONS)}")
    if not (a.role and a.candidate and a.decider):
        raise ValueError("--role, --candidate and --decider are required")
    if a.decision == "no" and not (a.reason or "").strip():
        raise ValueError("a no needs --reason in the decider's own words")
    dt.date.fromisoformat(a.date)
    rows = load(a.decisions)
    rows.append({"date": a.date, "role": a.role, "candidate": a.candidate, "decision": a.decision,
                 "decider": a.decider, "reason_verbatim": a.reason or "", "splits_count": a.splits or "",
                 "filed_ratio": a.filed_ratio or "", "no_decision_count": a.no_decision_count or "",
                 "fcra": a.fcra or "no"})
    write(a.decisions, COLS, rows)
    print(f"recorded: {a.candidate}, {a.role}: {a.decision} (by {a.decider})")
    if a.fcra == "yes":
        print("NOTE: a background check is part of this decision; the FCRA process applies before any decline")
    if a.stage or a.next_step or a.fcra == "yes":
        path = os.path.join(a.tracker, "candidates.csv")
        if not os.path.exists(path):
            print(f"tracker row not updated: no {path}")
            return 0
        with open(path, newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            cols = list(reader.fieldnames or [])
            trows = list(reader)
        hit = [r for r in trows if fold(r.get("name")) == fold(a.candidate) and fold(r.get("role")) == fold(a.role)]
        if len(hit) != 1:
            print(f"tracker row not updated: {len(hit)} matching rows for name + role; fix by hand")
            return 0
        r = hit[0]
        before = {k: r.get(k, "") for k in ("stage", "stage_since", "next_step")}
        if a.stage:
            r["stage"] = a.stage
            if "stage_since" in cols:
                r["stage_since"] = a.date
        nxt = "FCRA process (no decline draft)" if a.fcra == "yes" and a.decision == "no" else a.next_step
        if nxt and "next_step" in cols:
            r["next_step"] = nxt
        write(path, cols, trows)
        after = {k: r.get(k, "") for k in before}
        for k in before:
            if before[k] != after[k]:
                print(f"tracker: {a.candidate} {k} '{before[k]}' -> '{after[k]}'")
    return 0


def report(a):
    rows = load(a.decisions)
    if a.role:
        rows = [r for r in rows if fold(r["role"]) == fold(a.role)]
    rows.sort(key=lambda r: r["date"])
    recent = rows[-a.last:]
    if not recent:
        print("no decisions recorded yet")
        return 0
    flag = False
    by_role = {}
    for r in recent:
        by_role.setdefault(r["role"], []).append(r)
    ncc = sum(1 for r in recent if r["decision"] == "no-clear-call")
    share = ncc / len(recent)
    print(f"Last {len(recent)} debrief(s){' for ' + a.role if a.role else ''}: {ncc} without a clear call "
          f"({share:.0%}; bar {a.bar:.0%})" + (" -> anchors look loose: propose a fix via interview-kit-design"
                                               if share > a.bar else ""))
    flag = share > a.bar
    if not a.role and len(by_role) > 1:
        for role, rs in sorted(by_role.items()):
            n = sum(1 for r in rs if r["decision"] == "no-clear-call")
            print(f"  {role}: {n} of {len(rs)}")
    if len(recent) < 5:
        print(f"  small sample ({len(recent)} debriefs): read as a signal, not a rate")
    reasons = [(r["candidate"], r["reason_verbatim"]) for r in rows if r["decision"] == "no" and r["reason_verbatim"]]
    groups = []
    for cand, text in reasons:
        for g in groups:
            if difflib.SequenceMatcher(None, fold(text), fold(g[0][1])).ratio() >= a.similar:
                g.append((cand, text))
                break
        else:
            groups.append([(cand, text)])
    repeats = [g for g in groups if len(g) > 1]
    if repeats:
        print("Repeated 'no' reasons (verbatim, for the weekly review):")
        for g in repeats:
            print(f"  x{len(g)}: \"{g[0][1]}\"" + "".join(f" / \"{t}\"" for _, t in g[1:]))
    return 1 if flag else 0


def selftest():
    d = tempfile.mkdtemp()
    dec = os.path.join(d, "decisions.csv")
    os.makedirs(os.path.join(d, "tracker"))
    with open(os.path.join(d, "tracker", "candidates.csv"), "w", encoding="utf-8") as fh:
        fh.write("name,role,stage,next_step,stage_since\nPriya Nair,SBE,Onsite done,,2026-10-05\n")

    class A:
        decisions, tracker, fcra, splits, filed_ratio, no_decision_count = dec, os.path.join(d, "tracker"), None, "1", "1.0", "0"
        date, role, candidate, decider = "2026-10-09", "SBE", "Priya Nair", "Lena Ortiz"
        decision, reason, stage, next_step = "yes", "Move to offer.", "Offer prep", "Offer brief to Lena"
    assert append(A) == 0
    with open(os.path.join(d, "tracker", "candidates.csv"), encoding="utf-8") as fh:
        assert "Offer prep" in fh.read()
    A.candidate, A.decision, A.reason, A.stage, A.next_step = "Tom B", "no", "", None, None
    try:
        append(A)
        raise AssertionError("a no without a reason must fail")
    except ValueError:
        pass
    for i, (dcs, why) in enumerate([("no", "Could not explain rollback on a live migration"),
                                    ("no", "could not explain the rollback on a live migration"),
                                    ("no-clear-call", ""), ("no-clear-call", "")]):
        A.candidate, A.decision, A.reason, A.date = f"C{i}", dcs, why, f"2026-10-1{i}"
        append(A)

    class R:
        decisions, role, last, bar, similar = dec, None, 10, 0.2, 0.75
    assert report(R) == 1
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", nargs="?", choices=["append", "report"])
    ap.add_argument("--decisions", default=os.path.expanduser("~/workspace/hiring/debriefs/decisions.csv"))
    ap.add_argument("--tracker", default=os.path.expanduser("~/workspace/hiring/tracker"))
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--role")
    ap.add_argument("--candidate")
    ap.add_argument("--decision")
    ap.add_argument("--decider")
    ap.add_argument("--reason")
    ap.add_argument("--splits")
    ap.add_argument("--filed-ratio", dest="filed_ratio")
    ap.add_argument("--no-decision-count", dest="no_decision_count")
    ap.add_argument("--fcra", choices=["yes", "no"])
    ap.add_argument("--stage")
    ap.add_argument("--next-step", dest="next_step")
    ap.add_argument("--last", type=int, default=10)
    ap.add_argument("--bar", type=float, default=0.2)
    ap.add_argument("--similar", type=float, default=0.75)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    try:
        if a.command == "append":
            return append(a)
        if a.command == "report":
            return report(a)
    except (ValueError, OSError) as exc:
        print(f"bad input: {exc}", file=sys.stderr)
        return 2
    ap.error("give a command: append or report")


if __name__ == "__main__":
    sys.exit(main())
