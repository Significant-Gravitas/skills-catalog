#!/usr/bin/env python3
"""One flag per thread per day for the urgent mail sweep.

    cd ~/skills/interview-coordination && python3 scripts/flag_ledger.py seen <thread_id> --tz Europe/Lisbon
    python3 scripts/flag_ledger.py add <thread_id> <type> --tz Europe/Lisbon [--hour HH]
    python3 scripts/flag_ledger.py list --tz Europe/Lisbon

Ledger: ~/workspace/hiring/flags/mail-<YYYY-MM-DD>.json, dated in the owner's
timezone (so an 08:55 and a 17:05 run on the same local day share it).
Holds only thread ids, the flag type and the hour: no message content, no
names, no addresses.

Types: withdrawal-or-move, interviewer-dropout, offer-response, owed-answer-overdue
(the four urgent kinds in the urgent-thread-check routine).

seen: exit 0 if the thread was already flagged today (skip it), 1 if not.
add:  records it; exit 0. list: prints today's flags.
Exit 2 on bad input. --selftest uses a temp folder.
"""

import argparse
import datetime as dt
import json
import os
import sys
import tempfile

TYPES = {"withdrawal-or-move", "interviewer-dropout", "offer-response", "owed-answer-overdue"}


def ledger_path(root, tz):
    from zoneinfo import ZoneInfo
    today = dt.datetime.now(ZoneInfo(tz)).date().isoformat()
    return os.path.join(root, f"mail-{today}.json"), today


def load(path):
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def run(a):
    path, today = ledger_path(a.root, a.tz)
    data = load(path)
    if a.command == "seen":
        return 0 if a.thread in data else 1
    if a.command == "list":
        print(json.dumps({"date": today, "flags": data}, indent=1))
        return 0
    if a.type not in TYPES:
        print(f"bad input: type must be one of {sorted(TYPES)}", file=sys.stderr)
        return 2
    if a.thread in data:
        print(f"already flagged today at {data[a.thread]['hour']}; not added")
        return 0
    from zoneinfo import ZoneInfo
    hour = a.hour or dt.datetime.now(ZoneInfo(a.tz)).strftime("%H")
    data[a.thread] = {"type": a.type, "hour": hour}
    os.makedirs(a.root, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
    print(f"flagged {a.thread} ({a.type}) at {hour}:00 {a.tz}")
    return 0


def selftest():
    root = tempfile.mkdtemp()

    class A:
        pass
    a = A()
    a.root, a.tz, a.hour = root, "Europe/Lisbon", "10"
    a.command, a.thread, a.type = "seen", "t-123", None
    assert run(a) == 1
    a.command, a.type = "add", "withdrawal-or-move"
    assert run(a) == 0
    a.command = "seen"
    assert run(a) == 0
    a.command, a.type = "add", "made-up"
    a.thread = "t-9"
    assert run(a) == 2
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", nargs="?", choices=["seen", "add", "list"])
    ap.add_argument("thread", nargs="?")
    ap.add_argument("type", nargs="?")
    ap.add_argument("--tz")
    ap.add_argument("--hour")
    ap.add_argument("--root", default=os.path.expanduser("~/workspace/hiring/flags"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.command or not a.tz or (a.command != "list" and not a.thread):
        ap.error("usage: seen|add <thread_id> [type] --tz <IANA>; list --tz <IANA>")
    try:
        return run(a)
    except Exception as exc:  # zone errors, unreadable ledger
        print(f"bad input: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
