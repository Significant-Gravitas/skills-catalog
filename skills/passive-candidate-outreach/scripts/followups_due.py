#!/usr/bin/env python3
"""List which outreach follow-ups are due, overdue or coming up.

    cd ~/skills/passive-candidate-outreach && python3 scripts/followups_due.py \
        [--log ~/workspace/hiring/outreach-log.csv] [--today YYYY-MM-DD] \
        [--cadence 2,5,8] [--day-kind business|calendar] [--owner-tz Europe/Lisbon] \
        [--holidays holidays.txt] [--json]

Rules (all from the skill; defaults are the skill's, confirm with the owner):
- Cadence: follow-ups fall on day 2, 5 and 8 after the FIRST note was sent
  (default 2,5,8; the owner's saved cadence wins). --day-kind business (default)
  counts weekdays only, so nothing falls due on a weekend; calendar counts
  every day and then rolls a weekend due date to Monday.
- Only people whose latest touch is "sent" and who have not replied get a
  follow-up. declined / not-interested / positive replies are never listed.
  not-now is listed as a check-back only on or after check_back_date, and
  only until a touch dated on or after that date is logged (so once).
- The first note plus three follow-ups is the whole sequence; after touch 4
  the person is listed as "sequence complete, stop".
- A drafted-but-unsent touch is listed as "awaiting send confirmation".
- Suggested send slot: a weekday, in the candidate's stated timezone
  (the first non-empty candidate_tz on any of the person's rows). Times rotate
  09:30, 13:30, 11:00 (default: "weekday morning first, then vary"). No
  candidate_tz on any row -> UNKNOWN, never guessed from a city.
- --holidays: one ISO date per line, skipped as non-working days. Without it,
  only weekends are skipped, and the output says so.

Output: markdown (default) or --json with due / overdue / upcoming (next 3
working days) / check-back / awaiting-send / complete.
Exit 0; 2 on bad input. --selftest checks the date arithmetic.
"""

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import unicodedata

DEFAULT_CADENCE = [2, 5, 8]
SLOT_TIMES = ["09:30", "13:30", "11:00", "10:00"]   # rotation per touch; defaults
UPCOMING_WINDOW = 3                                  # working days ahead to preview


def key(name):
    """Fold accents, case, punctuation and spacing (same as log_touch.key)."""
    t = unicodedata.normalize("NFKD", name or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", t).split())


def working(d, holidays):
    return d.weekday() < 5 and d not in holidays


def add_days(start, n, kind, holidays):
    if kind == "calendar":
        d = start + dt.timedelta(days=n)
        while not working(d, holidays):
            d += dt.timedelta(days=1)
        return d
    d = start
    left = n
    while left > 0:
        d += dt.timedelta(days=1)
        if working(d, holidays):
            left -= 1
    return d


def working_days_between(a, b, holidays):
    """Working days from a (exclusive) to b (inclusive); 0 if b <= a."""
    n, d = 0, a
    while d < b:
        d += dt.timedelta(days=1)
        if working(d, holidays):
            n += 1
    return n


def slot(date, touch, tz_name, owner_tz):
    if not tz_name:
        return "UNKNOWN (no candidate timezone on the log row; ask, never guess from a city)"
    t = SLOT_TIMES[(touch - 1) % len(SLOT_TIMES)]
    try:
        from zoneinfo import ZoneInfo
        local = dt.datetime.combine(date, dt.time.fromisoformat(t), ZoneInfo(tz_name))
        text = f"{local:%a %d %b %H:%M} {tz_name}"
        if owner_tz and owner_tz != tz_name:
            other = local.astimezone(ZoneInfo(owner_tz))
            text += f" / {other:%a %d %b %H:%M} {owner_tz}"
        return text
    except Exception as exc:  # unknown zone or no tzdata
        return f"{date:%a %d %b} {t} {tz_name} (zone check failed: {exc}; pip install --user tzdata)"


def plan(rows, today, cadence, kind, holidays, owner_tz):
    people = {}
    for r in rows:
        # same key as log_touch.py: 'José Araújo' and 'Jose Araujo' are one person
        k = (key(r.get("candidate", "")), key(r.get("role", "")))
        people.setdefault(k, []).append(r)
    out = {"due": [], "overdue": [], "upcoming": [], "check_back": [],
           "awaiting_send": [], "complete": []}
    max_touch = 1 + len(cadence)
    for k, rs in people.items():
        rs.sort(key=lambda r: int(r.get("touch") or 0))
        latest = rs[-1]
        name = next((r["candidate"] for r in rs if r.get("touch") == "1"), latest["candidate"])
        base = {"candidate": name, "role": latest.get("role", ""), "channel": latest.get("channel", ""),
                "last_touch": int(latest.get("touch") or 0)}
        if any(r.get("status") == "declined" or r.get("reply_type") in {"not-interested", "positive"}
               for r in rs):
            continue
        tz = next((r.get("candidate_tz", "") for r in rs if r.get("candidate_tz", "")), "")
        notnow = [r for r in rs if r.get("reply_type") == "not-now"]
        if notnow:
            cb = notnow[-1].get("check_back_date")
            # once: a touch dated on or after the check-back date means it was used
            used = cb and any((r.get("date") or "") >= cb for r in rs)
            if cb and not used and dt.date.fromisoformat(cb) <= today:
                out["check_back"].append({**base, "check_back_date": cb,
                                          "note": "one check-back note, then stop unless they re-engage"})
            continue
        sent_rows = [r for r in rs if r.get("status") in {"sent", "replied"}]
        drafted = [r for r in rs if r.get("status") == "drafted"]
        if not sent_rows:
            out["awaiting_send"].append({**base, "note": "touch 1 drafted, not confirmed sent"})
            continue
        last_sent = max(int(r["touch"]) for r in sent_rows)
        if last_sent >= max_touch:
            out["complete"].append({**base, "note": "sequence complete, stop"})
            continue
        first = next((r for r in rs if r.get("touch") == "1"), None)
        if not first or first.get("status") == "drafted":
            continue
        first_sent = dt.date.fromisoformat(first["date"])
        nxt = last_sent + 1
        due = add_days(first_sent, cadence[nxt - 2], kind, holidays)
        item = {**base, "next_touch": nxt, "due_date": due.isoformat(),
                "send_slot": slot(max(due, today) if working(max(due, today), holidays)
                                  else add_days(max(due, today), 1, "business", holidays),
                                  nxt, tz, owner_tz),
                "drafted_already": any(r.get("touch") == str(nxt) for r in drafted)}
        if due < today:
            item["days_overdue"] = working_days_between(due, today, holidays)
            out["overdue"].append(item)
        elif due == today:
            out["due"].append(item)
        elif working_days_between(today, due, holidays) <= UPCOMING_WINDOW:
            out["upcoming"].append(item)
    for v in out.values():
        v.sort(key=lambda i: (i.get("due_date", ""), i["candidate"]))
    return out


def render(out, today, kind, has_holidays):
    lines = [f"# Follow-ups as of {today.isoformat()} ({kind} days"
             + ("" if has_holidays else "; weekends skipped, no holiday list given") + ")"]
    labels = [("overdue", "Overdue"), ("due", "Due today"), ("upcoming", "Coming up"),
              ("check_back", "Check-back dates reached"), ("awaiting_send", "Drafted, not confirmed sent"),
              ("complete", "Sequence complete (stop)")]
    for k, title in labels:
        items = out[k]
        if not items:
            continue
        lines.append(f"\n## {title}")
        for i in items:
            bits = [i["candidate"], i["role"]]
            if "next_touch" in i:
                bits.append(f"touch {i['next_touch']} due {i['due_date']}")
                if i.get("days_overdue"):
                    bits.append(f"{i['days_overdue']} working day(s) late")
                bits.append(f"send {i['send_slot']}")
                if i["drafted_already"]:
                    bits.append("draft already in the log")
            else:
                bits.append(i.get("note", "") + (f" ({i['check_back_date']})" if i.get("check_back_date") else ""))
            lines.append("- " + " | ".join(b for b in bits if b))
    if len(lines) == 1:
        lines.append("\nNothing due.")
    return "\n".join(lines)


def selftest():
    fri = dt.date(2026, 10, 9)
    assert add_days(fri, 2, "business", set()) == dt.date(2026, 10, 13)
    assert add_days(fri, 1, "calendar", set()) == dt.date(2026, 10, 12)
    rows = [
        {"candidate": "A", "role": "R", "touch": "1", "status": "sent", "date": "2026-10-05",
         "reply_type": "none", "candidate_tz": "Europe/Dublin"},
        {"candidate": "B", "role": "R", "touch": "1", "status": "declined", "date": "2026-10-05",
         "reply_type": "not-interested"},
        {"candidate": "C", "role": "R", "touch": "1", "status": "replied", "date": "2026-10-05",
         "reply_type": "not-now", "check_back_date": "2026-10-07"},
        {"candidate": "D", "role": "R", "touch": "1", "status": "drafted", "date": "2026-10-05",
         "reply_type": "none"},
    ]
    out = plan(rows, dt.date(2026, 10, 7), DEFAULT_CADENCE, "business", set(), "Europe/Lisbon")
    assert [i["candidate"] for i in out["due"]] == ["A"], out
    assert out["due"][0]["due_date"] == "2026-10-07"
    assert [i["candidate"] for i in out["check_back"]] == ["C"]
    assert [i["candidate"] for i in out["awaiting_send"]] == ["D"]
    assert not any(i["candidate"] == "B" for v in out.values() for i in v)
    # the zone on touch 1 carries to a later row logged without --candidate-tz
    rows2 = rows + [{"candidate": "A", "role": "R", "touch": "2", "status": "sent",
                     "date": "2026-10-07", "reply_type": "none", "candidate_tz": ""}]
    out = plan(rows2, dt.date(2026, 10, 9), DEFAULT_CADENCE, "business", set(), None)
    a_items = [i for v in out.values() for i in v if i["candidate"] == "A"]
    assert a_items and "Europe/Dublin" in a_items[0]["send_slot"], out
    # a check-back is listed once: a touch dated on or after it suppresses it
    rows3 = rows + [{"candidate": "C", "role": "R", "touch": "2", "status": "drafted",
                     "date": "2026-10-08", "reply_type": "none"}]
    out = plan(rows3, dt.date(2026, 10, 9), DEFAULT_CADENCE, "business", set(), None)
    assert not out["check_back"], out
    rows[0]["candidate_tz"] = ""
    out = plan(rows, dt.date(2026, 10, 9), DEFAULT_CADENCE, "business", set(), None)
    assert out["overdue"][0]["send_slot"].startswith("UNKNOWN")
    # an accented and an unaccented spelling are one person (as in log_touch.py)
    rows4 = [{"candidate": "José Araújo", "role": "SBE", "touch": "1", "status": "sent",
              "date": "2026-10-05", "reply_type": "none"},
             {"candidate": "Jose  Araujo", "role": "sbe", "touch": "2", "status": "sent",
              "date": "2026-10-07", "reply_type": "none"}]
    out = plan(rows4, dt.date(2026, 10, 8), DEFAULT_CADENCE, "business", set(), None)
    items = [i for v in out.values() for i in v]
    assert len(items) == 1 and items[0]["candidate"] == "José Araújo", out
    assert items[0]["next_touch"] == 3 and items[0]["due_date"] == "2026-10-12", out
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log", default=os.path.expanduser("~/workspace/hiring/outreach-log.csv"))
    ap.add_argument("--today")
    ap.add_argument("--cadence", default=",".join(map(str, DEFAULT_CADENCE)))
    ap.add_argument("--day-kind", choices=["business", "calendar"], default="business")
    ap.add_argument("--owner-tz")
    ap.add_argument("--holidays")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    try:
        today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
        cadence = [int(x) for x in a.cadence.split(",") if x.strip()]
        if cadence != sorted(cadence) or not cadence:
            raise ValueError("cadence must be increasing day numbers, e.g. 2,5,8")
        holidays = set()
        if a.holidays:
            with open(a.holidays, encoding="utf-8") as fh:
                holidays = {dt.date.fromisoformat(l.strip()) for l in fh if l.strip()}
        if not os.path.exists(a.log):
            print(f"no outreach log at {a.log}; run log_touch.py init first")
            return 0
        with open(a.log, newline="", encoding="utf-8-sig") as fh:
            rows = [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(fh)]
        out = plan(rows, today, cadence, a.day_kind, holidays, a.owner_tz)
    except (ValueError, OSError) as exc:
        print(f"bad input: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(out, indent=1) if a.json else render(out, today, a.day_kind, bool(holidays)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
