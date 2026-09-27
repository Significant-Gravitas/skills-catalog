#!/usr/bin/env python3
"""Keep the outreach log and the do-not-contact list consistent.

    cd ~/skills/passive-candidate-outreach && python3 scripts/log_touch.py <command> [options]

Files (defaults; override with --log / --dnc):
    ~/workspace/hiring/outreach-log.csv   header: templates/outreach-log.csv
    ~/workspace/hiring/dnc.csv            header: name,flag

Commands
    init                      create both files with headers if absent
    add     --candidate --role --touch N --channel --route-source --sender
            [--candidate-tz IANA] [--date YYYY-MM-DD]
                              log a new draft (status drafted). Refused for
                              anyone on the DNC list or already closed
                              (declined, not-interested).
    update  --candidate --role --touch N --status sent|replied|declined
            [--reply-type positive|not-now|not-interested] [--check-back YYYY-MM-DD]
            [--date YYYY-MM-DD]
                              move a touch forward. "sent" only after the owner
                              confirms they sent it. A reply needs a reply_type:
                              replied+positive, replied+not-now (check-back date
                              only if the owner set one), declined+not-interested.
    dnc     --candidate       add "name,do-not-contact" to dnc.csv and delete every
                              log row for that person: the name and the flag are
                              all that is kept. Prints the count removed, never
                              the removed content.
    show    [--candidate]     print the log (or one person's rows).

Exit 0 on success, 1 when a rule refuses the change, 2 on bad input.
--selftest runs against a temporary folder.
"""

import argparse
import csv
import datetime as dt
import os
import re
import sys
import tempfile
import unicodedata

HEADER = ["candidate", "role", "date", "channel", "route_source", "touch", "status",
          "reply_type", "check_back_date", "sender", "candidate_tz"]
STATUSES = {"drafted", "sent", "replied", "declined"}
REPLY_TYPES = {"positive", "not-now", "not-interested", "none"}
MAX_TOUCHES = 4   # first note + up to three follow-ups (skill default; owner may change)


def key(name):
    t = unicodedata.normalize("NFKD", name or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", t).split())


def read(path, header):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    return [{h: (r.get(h) or "").strip() for h in header} for r in rows]


def write(path, header, rows):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, path)


def valid_date(s):
    dt.date.fromisoformat(s)
    return s


def refuse(msg):
    print(f"REFUSED: {msg}")
    return 1


def cmd(a):
    today = a.date or dt.date.today().isoformat()
    if a.command == "init":
        if not os.path.exists(a.log):
            write(a.log, HEADER, [])
        if not os.path.exists(a.dnc):
            write(a.dnc, ["name", "flag"], [])
        print(f"ok: {a.log} and {a.dnc} exist")
        return 0
    log = read(a.log, HEADER)
    dnc = read(a.dnc, ["name", "flag"])
    dnc_keys = {key(r["name"]) for r in dnc}
    if a.command == "show":
        rows = [r for r in log if not a.candidate or key(r["candidate"]) == key(a.candidate)]
        w = csv.DictWriter(sys.stdout, fieldnames=HEADER)
        w.writeheader()
        w.writerows(rows)
        return 0
    if not a.candidate:
        print("bad input: --candidate is required", file=sys.stderr)
        return 2
    k = key(a.candidate)
    mine = [r for r in log if key(r["candidate"]) == k]
    if a.command == "dnc":
        kept = [r for r in log if key(r["candidate"]) != k]
        write(a.log, HEADER, kept)
        if k not in dnc_keys:
            dnc.append({"name": a.candidate.strip(), "flag": "do-not-contact"})
            write(a.dnc, ["name", "flag"], dnc)
        print(f"ok: do-not-contact recorded; {len(log) - len(kept)} log row(s) deleted for this person")
        return 0
    if k in dnc_keys:
        return refuse("this person is on the do-not-contact list; no draft, no log row")
    if any(r["status"] == "declined" or r["reply_type"] == "not-interested" for r in mine):
        return refuse("this person already said no; the sequence is over")
    if a.command == "add":
        for need in ("role", "touch", "channel", "route_source", "sender"):
            if not getattr(a, need):
                print(f"bad input: --{need.replace('_', '-')} is required for add", file=sys.stderr)
                return 2
        if a.touch < 1:
            print("bad input: --touch starts at 1", file=sys.stderr)
            return 2
        if a.touch > MAX_TOUCHES and not a.allow_extra:
            return refuse(f"touch {a.touch} is past the default limit of {MAX_TOUCHES}; "
                          "only with the owner's explicit say-so (then pass --allow-extra)")
        if any(r["touch"] == str(a.touch) and key(r["role"]) == key(a.role) for r in mine):
            return refuse(f"touch {a.touch} for this person and role is already logged; use update")
        if a.touch > 1 and not any(r["touch"] == str(a.touch - 1)
                                   and key(r["role"]) == key(a.role) for r in mine):
            return refuse(f"touch {a.touch - 1} is not in the log; log the touches in order")
        log.append({"candidate": a.candidate.strip(), "role": a.role, "date": today,
                    "channel": a.channel, "route_source": a.route_source,
                    "touch": str(a.touch), "status": "drafted", "reply_type": "none",
                    "check_back_date": "", "sender": a.sender,
                    "candidate_tz": a.candidate_tz or ""})
        write(a.log, HEADER, log)
        print(f"ok: touch {a.touch} drafted for {a.candidate.strip()}")
        return 0
    if a.command == "update":
        if a.status not in STATUSES:
            print(f"bad input: --status must be one of {sorted(STATUSES)}", file=sys.stderr)
            return 2
        rows = [r for r in mine if r["touch"] == str(a.touch)
                and (not a.role or key(r["role"]) == key(a.role))]
        if len(rows) != 1:
            return refuse(f"expected one logged row for touch {a.touch}, found {len(rows)}; "
                          "pass --role to disambiguate or add the touch first")
        row = rows[0]
        if a.status == "sent" and a.touch > 1 and not any(
                r["touch"] == str(a.touch - 1) and r["status"] != "drafted"
                and key(r["role"]) == key(row["role"]) for r in mine):
            return refuse(f"touch {a.touch - 1} has not been sent; follow-ups go out in order")
        rt = a.reply_type or "none"
        if rt not in REPLY_TYPES:
            print(f"bad input: --reply-type must be one of {sorted(REPLY_TYPES)}", file=sys.stderr)
            return 2
        if a.status == "replied" and rt not in {"positive", "not-now"}:
            return refuse("a reply is logged as positive or not-now; a no is --status declined")
        if a.status == "declined":
            rt = "not-interested"
        if a.status in {"drafted", "sent"}:
            rt = "none"
        if a.check_back and rt != "not-now":
            return refuse("a check-back date only goes with a not-now reply")
        row.update({"status": a.status, "reply_type": rt, "date": today,
                    "check_back_date": a.check_back or row["check_back_date"]})
        write(a.log, HEADER, log)
        print(f"ok: touch {a.touch} for {row['candidate']} is {a.status}"
              + (f" ({rt})" if rt != "none" else ""))
        return 0
    return 2


def selftest():
    d = tempfile.mkdtemp()
    base = ["--log", os.path.join(d, "log.csv"), "--dnc", os.path.join(d, "dnc.csv")]
    run = lambda *args: main(list(args) + base)
    assert run("init") == 0
    assert run("add", "--candidate", "Priya Nair", "--role", "Billing", "--touch", "1",
               "--channel", "email", "--route-source", "her site", "--sender", "Maya") == 0
    assert run("add", "--candidate", "Priya Nair", "--role", "Billing", "--touch", "3",
               "--channel", "email", "--route-source", "her site", "--sender", "Maya") == 1
    assert run("add", "--candidate", "Priya Nair", "--role", "Billing", "--touch", "2",
               "--channel", "email", "--route-source", "her site", "--sender", "Maya") == 0
    assert run("update", "--candidate", "Priya Nair", "--touch", "2", "--status", "sent") == 1
    assert run("update", "--candidate", "Priya Nair", "--touch", "1", "--status", "sent") == 0
    assert run("update", "--candidate", "Priya Nair", "--touch", "1", "--status", "replied",
               "--reply-type", "not-interested") == 1
    assert run("update", "--candidate", "Priya Nair", "--touch", "1", "--status", "declined") == 0
    assert run("add", "--candidate", "Priya Nair", "--role", "Billing", "--touch", "3",
               "--channel", "email", "--route-source", "her site", "--sender", "Maya") == 1
    assert run("dnc", "--candidate", "Priya  NAIR") == 0
    assert read(os.path.join(d, "log.csv"), HEADER) == [], "dnc must clear the log"
    assert run("add", "--candidate", "Priya Nair", "--role", "Other", "--touch", "1",
               "--channel", "email", "--route-source", "x", "--sender", "Maya") == 1
    print("selftest ok")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", nargs="?", choices=["init", "add", "update", "dnc", "show"])
    ap.add_argument("--log", default=os.path.expanduser("~/workspace/hiring/outreach-log.csv"))
    ap.add_argument("--dnc", default=os.path.expanduser("~/workspace/hiring/dnc.csv"))
    ap.add_argument("--candidate")
    ap.add_argument("--role")
    ap.add_argument("--touch", type=int)
    ap.add_argument("--channel")
    ap.add_argument("--route-source", dest="route_source")
    ap.add_argument("--sender")
    ap.add_argument("--candidate-tz", dest="candidate_tz")
    ap.add_argument("--status")
    ap.add_argument("--reply-type", dest="reply_type")
    ap.add_argument("--check-back", dest="check_back", type=valid_date)
    ap.add_argument("--date", type=valid_date)
    ap.add_argument("--allow-extra", action="store_true",
                    help="owner explicitly asked for touches past the limit")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        selftest()
        return 0
    if not a.command:
        ap.error("give a command: init, add, update, dnc or show")
    return cmd(a)


if __name__ == "__main__":
    sys.exit(main())
