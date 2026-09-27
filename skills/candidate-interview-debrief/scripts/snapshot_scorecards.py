#!/usr/bin/env python3
"""Record a tamper-evident ledger of filed scorecards and report late or edited ones.

Usage:
  cd ~/skills/candidate-interview-debrief && \
  python3 scripts/snapshot_scorecards.py <filed_dir> [--debrief-start 2026-10-03T10:00+01:00]

Run it when the scorecards arrive, again just before the debrief, and again
after it. Each run:
  * hashes every .csv/.md file in <filed_dir> (sha256);
  * appends one row per file to <filed_dir>/ledger.csv:
      file,sha256,size,file_mtime_utc,first_seen_utc,run_at_utc,status
    status is NEW (first sighting), SAME, or CHANGED (hash differs from the
    last recorded hash for that file);
  * keeps a copy of every distinct version in <filed_dir>/versions/<file>.v<n>
    so an edited scorecard never silently replaces the original;
  * with --debrief-start, flags files first seen after that time (filed after
    discussion began, so they may be anchored on peers).

Why: independent assessments are what make panel evidence worth combining
(Mediating Assessments Protocol, dossier [21]); some ATSs let interviewers
see peers' scorecards before filing, or edit after filing (Greenhouse
Scorecards FAQ, dossier [90]).

Limits: file mtimes on uploads reflect when the file reached the sandbox, not
when the interviewer wrote it; the ATS's own submitted_at (used by
collate_scorecards.py) is better evidence when present. The script only
reports; it never deletes or edits a scorecard.
Exit 0 = no changes or late files, 1 = changed or late files reported, 2 = bad input.
"""

import argparse
import csv
import hashlib
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

FIELDS = ["file", "sha256", "size", "file_mtime_utc", "first_seen_utc", "run_at_utc", "status"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("filed_dir")
    ap.add_argument("--debrief-start")
    a = ap.parse_args()
    d = Path(a.filed_dir).expanduser()
    if not d.is_dir():
        print(f"error: not a directory: {d}", file=sys.stderr)
        return 2
    start = None
    if a.debrief_start:
        try:
            start = datetime.fromisoformat(a.debrief_start.replace("Z", "+00:00"))
        except ValueError:
            print("error: --debrief-start must be ISO 8601, e.g. 2026-10-03T10:00+01:00", file=sys.stderr)
            return 2
        if start.tzinfo is None:
            print("error: --debrief-start needs a timezone offset so it can be compared", file=sys.stderr)
            return 2

    ledger = d / "ledger.csv"
    history: dict[str, list[dict]] = {}
    if ledger.is_file():
        for row in csv.DictReader(ledger.read_text(encoding="utf-8").splitlines()):
            history.setdefault(row["file"], []).append(row)
    versions = d / "versions"
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    new_rows, reports = [], []
    files = sorted(p for p in d.iterdir() if p.is_file() and p.suffix.lower() in (".csv", ".md")
                   and p.name != "ledger.csv")
    if not files:
        print(f"error: no .csv or .md scorecards in {d}", file=sys.stderr)
        return 2
    for p in files:
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        mtime = datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")
        past = history.get(p.name, [])
        first_seen = past[0]["first_seen_utc"] if past else now
        if not past:
            status = "NEW"
        elif past[-1]["sha256"] == digest:
            status = "SAME"
        else:
            status = "CHANGED"
        if status in ("NEW", "CHANGED"):
            versions.mkdir(exist_ok=True)
            n = len({r["sha256"] for r in past}) + 1
            shutil.copy2(p, versions / f"{p.name}.v{n}")
        if status == "CHANGED":
            reports.append(f"CHANGED after filing: {p.name} (first seen {first_seen}; "
                           f"earlier versions kept in versions/)")
        if start and datetime.fromisoformat(first_seen) > start:
            reports.append(f"LATE: {p.name} first seen {first_seen}, after debrief start {a.debrief_start}")
        new_rows.append({"file": p.name, "sha256": digest, "size": p.stat().st_size,
                         "file_mtime_utc": mtime, "first_seen_utc": first_seen,
                         "run_at_utc": now, "status": status})

    write_header = not ledger.is_file()
    with ledger.open("a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if write_header:
            w.writeheader()
        w.writerows(new_rows)
    for r in new_rows:
        print(f"{r['status']:8} {r['file']}  first seen {r['first_seen_utc']}")
    for line in reports:
        print(line)
    print(f"ledger: {ledger}")
    return 1 if reports else 0


if __name__ == "__main__":
    sys.exit(main())
