#!/usr/bin/env python3
"""Append to the search log and (after the owner's yes) to the shortlist.

Usage (cd ~/skills/candidate-sourcing-strategy first):
    python3 scripts/append_rows.py search --role <slug> --engine <web_search|gh|xray|owner-export|orbit>
        --query "<query text>" --results <n> --cards <n>
    python3 scripts/append_rows.py shortlist --role <slug> --cards <ready.json>
        (--approved "Name One;Name Two" | --all-approved)

Files:  $HIRING_DIR/searches.csv  search_id,date,role,engine,query,results_seen,cards_made
        $HIRING_DIR/shortlist.csv name,company,role,date_added,source_url,tier,reason,status,search_id,channel,stage
        (HIRING_DIR defaults to ~/workspace/hiring; headers are written if absent)
Dates:  today's date in the owner's timezone, read from
        $HIRING_DIR/preferences.md (timezone: ...); UTC with a warning if UNSET.
Rules:  shortlist rows need a source_url (the card's first verified evidence
        link); rows without one are refused. A person already on the shortlist
        for the same role (same name AND same company, after Unicode NFC,
        case and company-suffix folding; or same name where the old row has
        no company) is skipped. A same-named person at another company is
        added, with a note to check. Names are compared NFC-normalised, so
        "Zoë" typed with a combining accent still matches the card. --all-approved is only for when the
        owner said yes to the whole batch; otherwise name the approved people.
        An approved name that matches no card is printed as "not found in
        cards: <name>" and nothing is added for it.
Output: the search_id (for search) or counts added/skipped (for shortlist).
Exit:   0 ok; 1 nothing appended; 2 usage or unreadable input.
Stdlib only, no network.
"""

import csv
import datetime as dt
import json
import os
import sys
import unicodedata
from pathlib import Path

from dedupe_names import norm_company  # same company folding as dedupe (suffixes, accents)


def name_key(name):
    return " ".join(unicodedata.normalize("NFC", name or "").casefold().split())

HIRING_DIR = Path(os.environ.get("HIRING_DIR", str(Path.home() / "workspace" / "hiring")))
SEARCH_COLS = ["search_id", "date", "role", "engine", "query", "results_seen", "cards_made"]
SHORT_COLS = ["name", "company", "role", "date_added", "source_url", "tier", "reason", "status",
              "search_id", "channel", "stage"]
ENGINES = {"web_search", "gh", "xray", "owner-export", "orbit", "web_fetch"}


def today():
    tz = "UNSET"
    prefs = HIRING_DIR / "preferences.md"
    if prefs.exists():
        for line in prefs.read_text(encoding="utf-8").splitlines():
            if line.startswith("timezone:"):
                tz = line.split(":", 1)[1].strip()
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo(tz)).date().isoformat()
    except Exception:
        print(f"warning: timezone '{tz}' unusable; dating rows in UTC", file=sys.stderr)
        return dt.datetime.now(dt.timezone.utc).date().isoformat()


def rows(path):
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def append(path, cols, new_rows):
    HIRING_DIR.mkdir(parents=True, exist_ok=True)
    fresh = not path.exists() or path.stat().st_size == 0
    with path.open("a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        if fresh:
            w.writeheader()
        w.writerows(new_rows)


def opt(args, flag):
    if flag in args:
        i = args.index(flag)
        if i + 1 < len(args):
            return args[i + 1]
    return None


def main(argv):
    if len(argv) < 2 or argv[1] not in ("search", "shortlist"):
        print(__doc__, file=sys.stderr)
        return 2
    args = argv[2:]
    role = opt(args, "--role")
    if not role:
        print("error: --role <slug> is required", file=sys.stderr)
        return 2
    date = today()
    if argv[1] == "search":
        engine, query = opt(args, "--engine"), opt(args, "--query")
        if engine not in ENGINES or not query:
            print(f"error: need --engine one of {sorted(ENGINES)} and --query", file=sys.stderr)
            return 2
        path = HIRING_DIR / "searches.csv"
        n = sum(1 for r in rows(path) if r.get("date") == date) + 1
        sid = f"S-{date}-{n:02d}"
        append(path, SEARCH_COLS, [{"search_id": sid, "date": date, "role": role, "engine": engine,
                                    "query": query, "results_seen": opt(args, "--results") or "",
                                    "cards_made": opt(args, "--cards") or ""}])
        print(sid)
        return 0
    cards_file = opt(args, "--cards")
    if not cards_file:
        print("error: --cards <ready.json> is required", file=sys.stderr)
        return 2
    try:
        cards = json.loads(Path(cards_file).expanduser().read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"error: cannot read {cards_file}: {exc}", file=sys.stderr)
        return 2
    if "--all-approved" in args:
        approved = None
    elif opt(args, "--approved"):
        approved = {name_key(n): n.strip() for n in opt(args, "--approved").split(";") if n.strip()}
    else:
        print("error: name the approved people with --approved, or pass --all-approved", file=sys.stderr)
        return 2
    path = HIRING_DIR / "shortlist.csv"
    existing = [(name_key(r.get("name", "")), r.get("role", ""), norm_company(r.get("company", ""))) for r in rows(path)]
    new, skipped = [], 0
    for c in cards:
        name = (c.get("name") or "").strip()
        if approved is not None and name_key(name) not in approved:
            continue
        ev = c.get("evidence") or []
        url = ev[0].get("url") if ev else ""
        if not url:
            print(f"refused: {name} has no source_url")
            skipped += 1
            continue
        comp = norm_company(c.get("company", ""))
        same = [e for e in existing if e[0] == name_key(name) and e[1] == role]
        if any(not e[2] or e[2] == comp for e in same):
            print(f"skipped: {name} already on the shortlist for {role}")
            skipped += 1
            continue
        if same:
            print(f"note: another {name} (different company) is on the shortlist for {role}; added as a separate person, check")
        new.append({"name": name, "company": c.get("company", ""), "role": role, "date_added": date,
                    "source_url": url, "tier": c.get("tier", ""), "reason": c.get("reason", ""),
                    "status": "sourced", "search_id": c.get("search_id", ""),
                    "channel": c.get("channel", ""), "stage": "sourced"})
    if approved is not None:
        names = {name_key(c.get("name") or "") for c in cards}
        for key, shown in approved.items():
            if key not in names:
                print(f"not found in cards: {shown} (use the full name exactly as on the card)")
    if new:
        append(path, SHORT_COLS, new)
    print(f"shortlist: {len(new)} added, {skipped} skipped, dated {date}")
    return 0 if new else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
