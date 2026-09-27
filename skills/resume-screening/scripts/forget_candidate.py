#!/usr/bin/env python3
"""Remove one candidate from a screening batch's working files, in the same turn the owner asks.

Usage:
  python3 scripts/forget_candidate.py <batch_dir> [<scratch_dir> ...] (--id A-003 | --name "Full Name")

Input:  the durable batch folder (matrix, records, idmap, manifest) and any
        scratch folders (in/, txt/, red/) used for the same batch.
Does:   looks the id up in idmap.csv/manifest.csv when --name is given
        (accents, case and word order ignored, so "Jose Perez" finds "José
        Pérez"; the name is never printed; two matches stop and ask for --id);
        deletes <id>.txt, <id>.json and the source file at its exact path
        under <dir>/in (never another file with the same base name); removes the id's rows from matrix.csv,
        manifest.csv, idmap.csv, hidden.json,
        redaction_log.csv and merge_problems.csv; rewrites matrices.md
        without its section.
Output: what was removed, by file (id only).
Does not: touch the applicant tracking system, the original .zip upload
        (named in the output when the file came from one), delivered cloud copies, or
        email. List delivered files for the owner; deleting a cloud workspace
        file uses delete_workspace_file, which the platform may ask to approve.
        Record-retention questions go to the people lead or counsel.
Exit:   0 removed (or nothing found), 2 bad input.
Stdlib only, no network.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import screenio  # noqa: E402

CSV_FILES = ["matrix.csv", "manifest.csv", "idmap.csv", "redaction_log.csv", "merge_problems.csv"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="+")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--id")
    g.add_argument("--name")
    args = ap.parse_args()
    dirs = [Path(d).expanduser() for d in args.dirs]

    cid = args.id
    source_files: list[str] = []
    zips: set[str] = set()
    if args.name:
        # Accents, case and word order are ignored: "Jose Perez" finds "José Pérez".
        found = set()
        for d in dirs:
            for fname in ("idmap.csv", "manifest.csv"):
                for p in d.rglob(fname):
                    rows, _ = screenio.read_csv(p)
                    found |= {r["id"] for r in rows if r.get("id") and screenio.same_name(r.get("name_hint", ""), args.name)}
        if len(found) > 1:
            print(f"that name matches {len(found)} records ({', '.join(sorted(found, key=screenio.id_key))}); "
                  "ask the owner which one (or all), then re-run with --id")
            return 0
        cid = next(iter(found), None)
    for d in dirs:
        for fname in ("idmap.csv", "manifest.csv"):
            for p in d.rglob(fname):
                rows, _ = screenio.read_csv(p)
                for r in rows:
                    if cid and r.get("id") == cid and r.get("source_file"):
                        source_files.append(r["source_file"])
                    if cid and r.get("id") == cid:
                        zips |= set(re.findall(r"from zip (.+?)(?:;|$)", r.get("note", "")))
    if not cid:
        print("nothing found for that name in this batch (checked idmap.csv and manifest.csv)")
        return 0

    removed = []
    source_gone = not source_files
    for d in dirs:
        for p in list(d.rglob(f"{cid}.txt")) + list(d.rglob(f"{cid}.json*")) + list(d.rglob(f"{cid}__*")):
            p.unlink()
            removed.append(str(p))
        # The source file by its exact path under <dir>/in (or <dir>), never by base name:
        # another applicant's "Resume.pdf" in a sibling folder is a hiring record and stays.
        root = d if d.name == "in" else d / "in"
        for sf in set(source_files):
            p = root / sf
            if p.is_file() and root.resolve() in p.resolve().parents:
                p.unlink()
                removed.append(f"{root}/<source file>")
                source_gone = True
        for fname in CSV_FILES:
            for p in d.rglob(fname):
                rows, fields = screenio.read_csv(p)
                keep = [r for r in rows if r.get("id") != cid and r.get("candidate_id") != cid]
                if len(keep) != len(rows):
                    screenio.write_csv(p, keep, fields)
                    removed.append(f"{p} ({len(rows) - len(keep)} row(s))")
        for p in d.rglob("hidden.json"):
            data = json.loads(p.read_text(encoding="utf-8"))
            if cid in data:
                data.pop(cid)
                p.write_text(json.dumps(data, indent=2), encoding="utf-8")
                removed.append(str(p))
        for p in d.rglob("matrices.md"):
            text = p.read_text(encoding="utf-8")
            new = re.sub(rf"### {re.escape(cid)}\n.*?(?=\n### |\Z)", "", text, flags=re.S)
            if new != text:
                p.write_text(new.strip() + "\n", encoding="utf-8")
                removed.append(str(p))
    print(f"removed {cid} from {len(removed)} place(s):")
    for r in removed:
        print(f"- {r}")
    print("Not touched: the applicant tracking system and any delivered cloud copies. List those for the owner.")
    if not source_gone and not zips:
        print("Not found: the original resume file under an in/ folder of the directories given; find it by the "
              "source_file in the owner's copy of the manifest and delete it by hand.")
    for z in sorted(zips):
        print(f"Not touched: the original upload {z} still holds this file; delete or replace the zip.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
