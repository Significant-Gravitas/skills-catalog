#!/usr/bin/env python3
"""Read and write Sofia's hiring preferences file.

Usage (from the package dir, cd ~/skills/sofia-getting-started):
    python3 scripts/prefs.py get <key>
    python3 scripts/prefs.py set <key> "<value>"
    python3 scripts/prefs.py unset <key>
    python3 scripts/prefs.py dump            # every key, UNSET included
    python3 scripts/prefs.py missing         # keys still UNSET
    python3 scripts/prefs.py dnc-add "<name>"

File:  $HIRING_DIR/preferences.md (default ~/workspace/hiring/preferences.md),
       one "key: value" per line. Created from templates/preferences.md if absent.
DNC:   $HIRING_DIR/dnc.csv with columns name,flag. Only the name and the flag.
Exit:  0 ok; 1 validation error (message says what to fix); 2 usage error.

Stdlib only. No network. Refuses keys outside the list below, so candidate
data cannot be written here by accident.
"""

import csv
import os
import re
import sys
import unicodedata
from pathlib import Path

HIRING_DIR = Path(os.environ.get("HIRING_DIR", str(Path.home() / "workspace" / "hiring")))
PREFS = HIRING_DIR / "preferences.md"
DNC = HIRING_DIR / "dnc.csv"
TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "preferences.md"

# Keys other Sofia skills and the persona routines read. <role> keys take a role slug.
PLAIN_KEYS = [
    "roles_open", "timezone", "interview_hours", "morning_brief_hour",
    "evening_prep_hour", "stalled_bar", "scorecard_due_hours", "pipeline_source",
    "weekly_batch_size", "outreach_sender", "outreach_voice_sample_ref",
    "offer_approval_chain", "first_week_owner", "brief_destination",
    "hiring_jurisdictions", "candidate_ai_policy", "retention_policy",
    "background_check_owner", "linear_team", "routines_on",
]
ROLE_KEYS = ["hiring_manager", "panel", "loop_shape"]
ROLE_KEY_RE = re.compile(r"^(%s)\.([a-z0-9][a-z0-9-]{0,63})$" % "|".join(ROLE_KEYS))
HOUR_RE = re.compile(r"^([01]?\d|2[0-3]):[0-5]\d$")
UNSET = "UNSET"


def fail(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def valid_key(key: str) -> bool:
    return key in PLAIN_KEYS or bool(ROLE_KEY_RE.match(key))


def validate(key: str, value: str) -> str:
    value = value.strip()
    if not value:
        fail(f"empty value for {key}; use 'unset {key}' to clear it")
    if "\n" in value:
        fail(f"{key}: one line only")
    if value == UNSET:
        return value
    if key == "timezone":
        # "EST", "PST", "Etc/GMT+5" are fixed offsets with no daylight saving: an
        # owner in New York who says "EST" would get routines an hour off for
        # most of the year. Ask for the city zone instead.
        if value not in ("UTC", "Etc/UTC") and ("/" not in value or value.startswith("Etc/")):
            fail(f"'{value}' is a fixed-offset or legacy zone (no daylight saving); use the city zone "
                 "the owner lives by, e.g. America/New_York, America/Los_Angeles, Europe/London, Asia/Kolkata. "
                 "UTC is accepted if they really work in UTC")
        try:
            from zoneinfo import ZoneInfo  # Python 3.9+
            ZoneInfo(value)
        except ImportError:
            print("warning: zoneinfo unavailable; timezone not validated", file=sys.stderr)
        except Exception:
            fail(f"'{value}' is not an IANA timezone; use a name like Europe/Lisbon or America/New_York")
    elif key in ("morning_brief_hour", "evening_prep_hour"):
        if not HOUR_RE.match(value):
            fail(f"{key} must be HH:MM in 24-hour time, e.g. 08:00")
    elif key in ("weekly_batch_size", "scorecard_due_hours"):
        if not (value.isascii() and value.isdigit()) or int(value) < 1:
            fail(f"{key} must be a whole number of at least 1")
    elif key == "stalled_bar":
        if not re.match(r"^\d+ (business )?days?$", value):
            fail("stalled_bar must look like '3 business days' or '5 days'")
    return value


def load() -> dict:
    if not PREFS.exists():
        HIRING_DIR.mkdir(parents=True, exist_ok=True)
        if TEMPLATE.exists():
            PREFS.write_text(TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            PREFS.write_text("# Hiring preferences\n", encoding="utf-8")
    prefs = {}
    for line in PREFS.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        prefs[k.strip()] = v.strip()
    return prefs


def save(prefs: dict) -> None:
    header = [l for l in PREFS.read_text(encoding="utf-8").splitlines() if l.startswith("#")]
    ordered = [k for k in PLAIN_KEYS if k in prefs] + sorted(k for k in prefs if k not in PLAIN_KEYS)
    body = [f"{k}: {prefs[k]}" for k in ordered]
    tmp = PREFS.with_suffix(".tmp")
    tmp.write_text("\n".join(header + body) + "\n", encoding="utf-8")
    tmp.replace(PREFS)


def dnc_add(name: str) -> None:
    name = " ".join(name.split())
    if not name:
        fail("dnc-add needs a name")
    HIRING_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    if DNC.exists():
        with DNC.open(encoding="utf-8-sig", newline="") as fh:  # tolerate Excel's BOM
            reader = csv.DictReader(fh)
            reader.fieldnames = [(f or "").strip().lower() for f in (reader.fieldnames or [])]
            rows = list(reader)
        if reader.fieldnames and "name" not in reader.fieldnames:
            fail(f"{DNC} has no 'name' column (header: {','.join(reader.fieldnames)}); "
                 "fix the first line to 'name,flag' so the list is read, then rerun")
    key = unicodedata.normalize("NFC", name).casefold()
    if any(unicodedata.normalize("NFC", (r.get("name") or "").strip()).casefold() == key for r in rows):
        print(f"already on the do-not-contact list: {name}")
        return
    new = not DNC.exists() or DNC.stat().st_size == 0
    with DNC.open("a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["name", "flag"])
        w.writerow([name, "dnc"])
    print(f"added to do-not-contact: {name}")


def main(argv: list) -> None:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    cmd = argv[1]
    if cmd == "dnc-add":
        if len(argv) != 3:
            fail('usage: prefs.py dnc-add "<name>"', 2)
        dnc_add(argv[2])
        return
    prefs = load()
    if cmd == "dump":
        for k in PLAIN_KEYS:
            print(f"{k}: {prefs.get(k, UNSET)}")
        for k in sorted(k for k in prefs if k not in PLAIN_KEYS):
            print(f"{k}: {prefs[k]}")
    elif cmd == "missing":
        for k in PLAIN_KEYS:
            if prefs.get(k, UNSET) == UNSET:
                print(k)
    elif cmd == "get":
        if len(argv) != 3:
            fail("usage: prefs.py get <key>", 2)
        print(prefs.get(argv[2], UNSET))
    elif cmd in ("set", "unset"):
        want = 4 if cmd == "set" else 3
        if len(argv) != want:
            fail(f"usage: prefs.py {cmd} <key>{' <value>' if cmd == 'set' else ''}", 2)
        key = argv[2]
        if not valid_key(key):
            fail(
                f"unknown key '{key}'. Allowed: {', '.join(PLAIN_KEYS)}, or "
                f"{'/'.join(ROLE_KEYS)}.<role-slug>. Candidate data and DNC names never go here."
            )
        value = validate(key, argv[3]) if cmd == "set" else UNSET
        prefs[key] = value
        save(prefs)
        print(f"{key}: {value}")
    else:
        fail(f"unknown command '{cmd}'", 2)


if __name__ == "__main__":
    main(sys.argv)
