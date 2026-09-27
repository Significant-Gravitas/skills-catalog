#!/usr/bin/env python3
"""Sofia only, and only after the owner's yes: mark screened candidates in the tracker.

Usage:
  python3 scripts/tracker_mark_screened.py <candidates.csv> <idmap.csv> --matrix <matrix.csv> --role <role>
      [--ids A-001,A-004] [--date YYYY-MM-DD]

Input:  Sofia's tracker ~/workspace/hiring/tracker/candidates.csv (header
        name,role,stage,source,owner,last_contact,next_step,waiting_on,days_in_stage,notes)
        and the batch's idmap.csv (owner-only file from redact.py).
Does:   for each id that has rows in matrix.csv (records that were actually
        screened; needs-a-look and held records are never marked), optionally
        limited by --ids, finds the
        tracker row with the same name and role and sets stage "screened",
        next_step "owner decision", waiting_on "owner"; appends a row with
        source "inbound" when none exists. Keeps every other column and the
        header exactly. Never writes a result, score, rank or quote into the
        tracker: the evidence matrix stays in the screens folder.
        Skips anyone whose tracker row says do not contact.
Output: counts only (updated, added, skipped); no names printed.
Exit:   0 done, 2 bad input.
Stdlib only, no network.
"""

import argparse
import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import screenio  # noqa: E402

HEADER = ["name", "role", "stage", "source", "owner", "last_contact", "next_step", "waiting_on", "days_in_stage", "notes"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("candidates")
    ap.add_argument("idmap")
    ap.add_argument("--role", required=True)
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--ids", default="")
    ap.add_argument("--date")
    args = ap.parse_args()

    cpath = Path(args.candidates).expanduser()
    try:
        idmap, _ = screenio.read_csv(args.idmap)
        screened = {r["candidate_id"] for r in screenio.read_csv(args.matrix)[0]}
        rows, fields = screenio.read_csv(cpath) if cpath.is_file() else ([], HEADER)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if not fields:
        fields = HEADER
    missing = [c for c in ("name", "role", "stage") if c not in fields]
    if missing:
        print(f"error: tracker header lacks {missing}; expected {HEADER}", file=sys.stderr)
        return 2
    wanted = {i.strip() for i in args.ids.split(",") if i.strip()}
    today = args.date or dt.date.today().isoformat()
    updated = added = skipped = 0
    for m in idmap:
        if (wanted and m["id"] not in wanted) or m["id"] not in screened:
            continue
        name = (m.get("name_hint") or "").strip()
        if not name:
            skipped += 1
            continue
        # Same words, accents and case ignored: a "Jose Perez" do-not-contact row covers "José Pérez".
        hit = [r for r in rows if screenio.same_name(r.get("name", ""), name)
               and screenio.norm_text(r.get("role", "")) == screenio.norm_text(args.role)]
        if any("do not contact" in (r.get("notes", "") + r.get("stage", "")).lower() for r in hit):
            skipped += 1
            continue
        if hit:
            for r in hit:
                r["stage"] = "screened"
                if "next_step" in fields:
                    r["next_step"] = "owner decision"
                if "waiting_on" in fields:
                    r["waiting_on"] = "owner"
                if "days_in_stage" in fields:
                    r["days_in_stage"] = "0"
            updated += 1
        else:
            new = {f: "" for f in fields}
            new.update({"name": name, "role": args.role, "stage": "screened"})
            for k, v in (("source", "inbound"), ("next_step", "owner decision"), ("waiting_on", "owner"),
                         ("days_in_stage", "0"), ("last_contact", "")):
                if k in fields:
                    new[k] = v
            if "notes" in fields:
                new["notes"] = f"screened {today}; evidence matrix in screens folder ({m['id']})"
            rows.append(new)
            added += 1
    screenio.write_csv(cpath, rows, fields)
    print(f"tracker updated: {updated} row(s) set to screened, {added} added, {skipped} skipped (no name, or do not contact)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
