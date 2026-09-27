#!/usr/bin/env python3
"""Freeze filed scorecards and report any change after filing.

    cd ~/skills/hiring-debrief-and-decision && python3 scripts/snapshot_scorecards.py \
        --dir ~/workspace/hiring/debriefs/<role-slug>/<candidate-slug>/scorecards \
        --tz Europe/Lisbon [--debrief-start 2026-10-09T11:00]

A scorecard is frozen once filed; if one changes, both versions are kept
(skill rule). Run at roll-call, and again just before writing the record.

- Ledger: <dir>/../scorecard-ledger.csv (file, version, sha256, first_seen with
  zone, filed_at as written in the card).
- Versions: <dir>/../versions/<file>.v1, .v2 ... (a copy of each distinct content).
- On a changed hash: saves the new version and prints a unified diff of the
  two versions, with both timestamps.
- --debrief-start: lists cards first seen after it (filed after discussion began,
  so not independent evidence). Times without an offset are read in --tz.

Scorecards kept in a live Google Doc or Sheet change without files: export
them into <dir> at roll-call and snapshot the export.

Exit 0 when nothing changed and nothing is late, 1 when something changed or
was filed late, 2 on bad input. --selftest uses a temp folder.
"""

import argparse
import csv
import datetime as dt
import difflib
import glob
import hashlib
import os
import re
import shutil
import sys
import tempfile

COLS = ["file", "version", "sha256", "first_seen", "filed_at"]


def Z(name):
    from zoneinfo import ZoneInfo
    return ZoneInfo(name)


def run(d, tz, start, now=None):
    d = os.path.expanduser(d)
    if not os.path.isdir(d):
        raise ValueError(f"no scorecard folder at {d}")
    parent = os.path.dirname(os.path.abspath(d))
    ledger = os.path.join(parent, "scorecard-ledger.csv")
    vdir = os.path.join(parent, "versions")
    rows = []
    if os.path.exists(ledger):
        with open(ledger, newline="", encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
    now = now or dt.datetime.now(Z(tz))
    changed, late, new = [], [], []
    for path in sorted(glob.glob(os.path.join(d, "*"))):
        if not os.path.isfile(path):
            continue
        name = os.path.basename(path)
        with open(path, "rb") as fh:
            data = fh.read()
        h = hashlib.sha256(data).hexdigest()
        mine = [r for r in rows if r["file"] == name]
        m = re.search(rb"^filed_at:\s*(.+)$", data, re.M)
        filed_at = m.group(1).decode("utf-8", "replace").strip() if m else ""
        if not mine:
            rows.append({"file": name, "version": "1", "sha256": h, "first_seen": now.isoformat(timespec="minutes"),
                         "filed_at": filed_at})
            os.makedirs(vdir, exist_ok=True)
            shutil.copyfile(path, os.path.join(vdir, f"{name}.v1"))
            new.append(name)
            first_seen = now
        else:
            last = max(mine, key=lambda r: int(r["version"]))
            first_seen = dt.datetime.fromisoformat(mine[0]["first_seen"])
            if last["sha256"] != h:
                v = int(last["version"]) + 1
                rows.append({"file": name, "version": str(v), "sha256": h,
                             "first_seen": now.isoformat(timespec="minutes"), "filed_at": filed_at})
                shutil.copyfile(path, os.path.join(vdir, f"{name}.v{v}"))
                with open(os.path.join(vdir, f"{name}.v{v - 1}"), encoding="utf-8", errors="replace") as fh:
                    old = fh.read().splitlines()
                diff = list(difflib.unified_diff(old, data.decode("utf-8", "replace").splitlines(),
                                                 f"{name} v{v - 1} (seen {last['first_seen']})",
                                                 f"{name} v{v} (seen {now.isoformat(timespec='minutes')})",
                                                 lineterm="", n=0))
                changed.append((name, diff))
        if start:
            t = start if start.tzinfo else start.replace(tzinfo=Z(tz))
            filed = None
            try:
                filed = dt.datetime.fromisoformat(filed_at) if filed_at else None
                if filed and not filed.tzinfo:
                    filed = filed.replace(tzinfo=Z(tz))
            except ValueError:
                filed = None
            when = filed or first_seen
            if when > t:
                late.append(f"{name}: {'filed_at ' + filed_at if filed else 'first seen ' + first_seen.isoformat(timespec='minutes')}"
                            f" is after the debrief start {t.isoformat(timespec='minutes')}")
    with open(ledger, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    return new, changed, late


def selftest():
    root = tempfile.mkdtemp()
    d = os.path.join(root, "scorecards")
    os.makedirs(d)
    p = os.path.join(d, "ana.md")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("filed_at: 2026-10-05T16:40+01:00\n| M2 | x | 2 | \"no rollback\" |\n")
    t0 = dt.datetime(2026, 10, 6, 9, 0, tzinfo=Z("Europe/Lisbon"))
    new, changed, late = run(d, "Europe/Lisbon", None, t0)
    assert new == ["ana.md"] and not changed
    with open(p, "w", encoding="utf-8") as fh:
        fh.write("filed_at: 2026-10-05T16:40+01:00\n| M2 | x | 3 | \"no rollback\" |\n")
    new, changed, late = run(d, "Europe/Lisbon", dt.datetime(2026, 10, 9, 11, 0), t0 + dt.timedelta(days=3))
    assert changed and any("+| M2 | x | 3" in l for l in changed[0][1]), changed
    assert os.path.exists(os.path.join(root, "versions", "ana.md.v2"))
    assert not late
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir")
    ap.add_argument("--tz")
    ap.add_argument("--debrief-start")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.dir or not a.tz:
        ap.error("--dir and --tz are required")
    try:
        start = dt.datetime.fromisoformat(a.debrief_start) if a.debrief_start else None
        new, changed, late = run(a.dir, a.tz, start)
    except (ValueError, OSError) as exc:
        print(f"bad input: {exc}", file=sys.stderr)
        return 2
    print(f"{len(new)} new scorecard(s) frozen; {len(changed)} changed since filing; {len(late)} filed late")
    for name, diff in changed:
        print(f"\nCHANGED AFTER FILING: {name} (both versions kept)")
        print("\n".join(diff[:40]))
    for l in late:
        print(f"LATE: {l}")
    return 1 if changed or late else 0


if __name__ == "__main__":
    sys.exit(main())
