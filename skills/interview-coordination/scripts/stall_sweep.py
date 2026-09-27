#!/usr/bin/env python3
"""Find what is stalled in hiring, grouped by who holds each item.

    cd ~/skills/interview-coordination && python3 scripts/stall_sweep.py --tz Europe/Lisbon \
        [--hiring ~/workspace/hiring] [--today YYYY-MM-DD] [--now YYYY-MM-DDTHH:MM] \
        [--thresholds templates/stall-thresholds.csv] [--holidays holidays.txt] \
        [--no-history] [--json]

Reads <hiring>/tracker/{candidates,loops,roles}.csv (fixed columns) and, if
present, <hiring>/outreach-log.csv. Thresholds come from
templates/stall-thresholds.csv (the skill's defaults); the owner's values in
<hiring>/preferences.md override them: "stall.<item>: <number>" per item,
"stalled_bar: <n>" for no_update, "response_window_hours: <n>" for response_window.

Items (defaults in the thresholds file; business days skip weekends and any
--holidays date; without a holiday list the output says so):
    awaiting_feedback    candidate's last interview ended N business days ago, no update since
    scorecard_late       interview ended N days ago and scorecards are not all in
    offer_open           stage is an offer and due_by has passed
    scheduling_unbooked  stage is a scheduling stage for N business days and no loop is booked ahead
    no_reply             outreach sequence at N touches with no reply
    invite_unaccepted    loop status still invited/pending inside N hours of the start
    decline_undrafted    stage is a no / rejection for N hours and next_step does not say drafted or sent
    no_update            last_contact N business days ago on an open candidate (not raised when
                         response_window or scheduling_unbooked is already open for them: one
                         missing update is one line)
    response_window      candidate waiting on someone and not updated inside N hours (promise: 24, 48 at most)
Prospects (is_prospect=yes) and closed stages (hired, withdrawn, archived, closed,
or a rejection already sent) are skipped.

History: <hiring>/flags/stall-history.csv. A second stall (second_stall=true,
with the days it has cost since first flagged) is an item that cleared and came
back, or one still open at least twice its own bar after it was first flagged
(bar in days or business days x2, hours converted to days x2; at least 2 days;
a touches bar never escalates by time). Any other item already flagged on an
earlier day is carried_over=true with unchanged_since=<first_seen>: the brief
collapses those into one rollup line. --no-history reads without writing (use
it for previews).

Output: markdown grouped by holder, oldest first, one line each with the single
action that frees it, then one "Unchanged since an earlier brief" rollup line;
or --json. Exit 0; 2 on bad input. --selftest runs a fixture.
"""

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import tempfile
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_THRESHOLDS = os.path.join(HERE, "..", "templates", "stall-thresholds.csv")
CLOSED = re.compile(r"(hired|withdr|archiv|closed|declined offer|offer declined|accepted)", re.I)
NO_STAGE = re.compile(r"(reject|no hire|not moving forward|not progressing|unsuccessful|decline)", re.I)
OFFER = re.compile(r"offer", re.I)
SCHED = re.compile(r"(schedul|to book|needs? (a )?loop|awaiting loop)", re.I)
DONE_LOOP = re.compile(r"(done|complete|held|happened|booked|confirmed|accepted)", re.I)
INVITE_OPEN = re.compile(r"(invited|pending|tentative|needs action|awaiting|sent)", re.I)
CANCELLED = re.compile(r"cancel", re.I)
ALL_IN = re.compile(r"^(in|all in|filed|done|complete|yes)$", re.I)
ACTIONS = {
    "awaiting_feedback": "{holder} gives the decision or the next step; candidate update drafted",
    "scorecard_late": "{holder} files the scorecard (alone, before the debrief)",
    "offer_open": "{holder} calls the candidate for an answer or agrees a new date",
    "scheduling_unbooked": "owner picks one of the loop options",
    "no_reply": "send the close-out or stop the sequence",
    "invite_unaccepted": "{holder} accepts, or names a substitute who can take the competency",
    "decline_undrafted": "draft the decline (phone talking points if late-stage)",
    "no_update": "{holder} sends an update (drafted)",
    "response_window": "send the candidate a holding update (drafted) while {holder} decides",
}


def fold_name(t):
    t = unicodedata.normalize("NFKD", t or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", t).split())


def Z(name):
    from zoneinfo import ZoneInfo
    return ZoneInfo(name)


def load(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(fh)]


def thresholds(path, hiring):
    t = {}
    for r in load(path):
        t[r["item"]] = float(r["threshold"])
    prefs = os.path.join(hiring, "preferences.md")
    if os.path.exists(prefs):
        with open(prefs, encoding="utf-8") as fh:
            for line in fh:
                m = re.match(r"^\s*(stall\.([a-z_]+)|stalled_bar|response_window_hours)\s*:\s*([\d.]+)", line)
                if m:
                    item = m.group(2) or ("no_update" if m.group(1) == "stalled_bar" else "response_window")
                    t[item] = float(m.group(3))
    return t


class Clock:
    def __init__(self, today, holidays):
        self.today, self.holidays = today, holidays

    def working(self, d):
        return d.weekday() < 5 and d not in self.holidays

    def bdays(self, a, b):
        n, d = 0, a
        while d < b:
            d += dt.timedelta(days=1)
            if self.working(d):
                n += 1
        return n


def d(s):
    try:
        return dt.date.fromisoformat(s[:10]) if s else None
    except ValueError:
        return None


def loop_times(r):
    try:
        z = Z(r["tz"])
        day = dt.date.fromisoformat(r["date"])
        s = dt.datetime.combine(day, dt.time.fromisoformat(r["start"]), z)
        e = dt.datetime.combine(day, dt.time.fromisoformat(r["end"] or r["start"]), z)
        return s, e
    except (KeyError, ValueError):
        return None, None


def sweep(hiring, tz, today, now, th, holidays):
    clk = Clock(today, holidays)
    cands = load(os.path.join(hiring, "tracker", "candidates.csv"))
    loops = load(os.path.join(hiring, "tracker", "loops.csv"))
    roles = {r.get("role", "").lower(): r for r in load(os.path.join(hiring, "tracker", "roles.csv"))}
    outreach = load(os.path.join(hiring, "outreach-log.csv"))
    items, notes = [], []

    def add(item, cand, role, holder, since, age, unit, extra=""):
        items.append({"item": item, "candidate": cand, "role": role, "holder": holder or "unassigned (us)",
                      "since": since, "age": age, "unit": unit, "threshold": th.get(item),
                      "detail": extra,
                      "frees_it": ACTIONS[item].format(holder=holder or "the owner"),
                      "key": f"{item}|{cand.lower()}|{role.lower()}|{extra}"})

    by_cand = {}
    for r in loops:
        if CANCELLED.search(r.get("status", "")):
            continue
        s, e = loop_times(r)
        if not s:
            notes.append(f"loop row for {r.get('candidate')} on {r.get('date')} has no usable date/time/tz")
            continue
        r["_s"], r["_e"] = s, e
        by_cand.setdefault((r["candidate"].lower(), r.get("role", "").lower()), []).append(r)
        who = r.get("interviewers") or "unassigned (us)"
        if e < now and not ALL_IN.match(r.get("scorecards", "")):
            m = re.match(r"^(\d+)\s*/\s*(\d+)$", r.get("scorecards", ""))
            if not (m and m.group(1) == m.group(2)):
                late = (now - e).total_seconds() / 86400
                if late >= th.get("scorecard_late", 1):
                    add("scorecard_late", r["candidate"], r.get("role", ""), who, e.astimezone(Z(tz)).isoformat(),
                        int(late), "days", f"{r.get('coverage', '')} {r['date']}")
        if s > now and INVITE_OPEN.search(r.get("status", "")) and not DONE_LOOP.search(r.get("status", "")):
            hrs = (s - now).total_seconds() / 3600
            if hrs <= th.get("invite_unaccepted", 24):
                add("invite_unaccepted", r["candidate"], r.get("role", ""), who, s.astimezone(Z(tz)).isoformat(),
                    round(hrs, 1), "hours to start", f"{r.get('coverage', '')} {r['date']} {r['start']} {r['tz']}")
    for c in cands:
        name, role, stage = c.get("name", ""), c.get("role", ""), c.get("stage", "")
        if not name or c.get("is_prospect", "").lower() == "yes":
            continue
        holder = c.get("waiting_on") or c.get("owner")
        last = d(c.get("last_contact"))
        since = d(c.get("stage_since")) or last
        nxt = c.get("next_step", "")
        if CLOSED.search(stage):
            continue
        if NO_STAGE.search(stage):
            if not re.search(r"(drafted|sent|called|phoned)", nxt, re.I) and since:
                hrs = (now - dt.datetime.combine(since, dt.time(0), Z(tz))).total_seconds() / 3600
                if hrs >= th.get("decline_undrafted", 48):
                    add("decline_undrafted", name, role, c.get("owner"), since.isoformat(), int(hrs), "hours")
            continue
        if OFFER.search(stage):
            due = d(c.get("due_by"))
            if due and due < today:
                add("offer_open", name, role, holder, due.isoformat(), (today - due).days, "days past answer-by")
        mine = by_cand.get((name.lower(), role.lower()), [])
        future = [r for r in mine if r["_s"] > now]
        past = [r for r in mine if r["_e"] <= now]
        if SCHED.search(stage) and since and not future:
            n = clk.bdays(since, today)
            if n >= th.get("scheduling_unbooked", 2):
                add("scheduling_unbooked", name, role, holder or "owner", since.isoformat(), n, "business days")
        if past and not future:
            lastloop = max(past, key=lambda r: r["_e"])
            ended = lastloop["_e"].astimezone(Z(tz)).date()
            if not last or last <= ended:
                n = clk.bdays(ended, today)
                if n >= th.get("awaiting_feedback", 2):
                    hm = roles.get(role.lower(), {}).get("hiring_manager")
                    add("awaiting_feedback", name, role, c.get("waiting_on") or hm, ended.isoformat(), n,
                        "business days")
        if last:
            hrs = (now - dt.datetime.combine(last, dt.time(0), Z(tz))).total_seconds() / 3600
            if c.get("waiting_on") and hrs >= th.get("response_window", 24):
                add("response_window", name, role, c["waiting_on"], last.isoformat(), int(hrs), "hours")
            covered = any(i["item"] in ("response_window", "scheduling_unbooked") and i["candidate"] == name
                          and i["role"] == role for i in items)
            n = clk.bdays(last, today)
            if n >= th.get("no_update", 3) and not covered:
                add("no_update", name, role, holder, last.isoformat(), n, "business days")
    people = {}
    for r in outreach:
        # accent/case/spacing folded, as log_touch.py does: 'Jose Araujo' is 'José Araújo'
        people.setdefault((fold_name(r.get("candidate", "")), fold_name(r.get("role", ""))), []).append(r)
    for (_, _), rs in people.items():
        rs.sort(key=lambda r: int(r["touch"]) if r.get("touch", "").isdigit() else 0)
        if any(r.get("reply_type") not in ("", "none") or r.get("status") in ("replied", "declined") for r in rs):
            continue
        sent = [int(r["touch"]) for r in rs if r.get("status") == "sent" and r.get("touch", "").isdigit()]
        if sent and max(sent) >= th.get("no_reply", 3):
            r = rs[-1]
            shown = next((x["candidate"] for x in rs if x.get("touch") == "1"), r["candidate"])
            add("no_reply", shown, r.get("role", ""), r.get("sender"), r.get("date", ""), max(sent), "touches")
    return items, notes


def escalation_bar(it):
    """(kind, days) an item must stay open after first_seen to count as a second stall."""
    unit, t = it.get("unit", ""), float(it.get("threshold") or 0)
    if unit.startswith("business days"):
        return "business", max(2 * t, 2)
    if unit.startswith("hours"):
        return "calendar", max(2 * t / 24, 2)
    if unit.startswith("days"):
        return "calendar", max(2 * t, 2)
    return None, None                      # touches: no time-based escalation


def apply_history(items, path, today, write, holidays=frozenset()):
    clk = Clock(today, set(holidays))
    hist = {r["key"]: r for r in load(path)}
    cols = ["key", "item", "candidate", "role", "holder", "first_seen", "last_seen", "cleared_on", "times_flagged"]
    present = set()
    for it in items:
        k = it["key"]
        present.add(k)
        h = hist.get(k)
        it["second_stall"] = False
        it["carried_over"] = False
        if h:
            first = d(h.get("first_seen"))
            kind, bar = escalation_bar(it)
            open_for = None
            if first and kind == "business":
                open_for = clk.bdays(first, today)
            elif first and kind == "calendar":
                open_for = (today - first).days
            came_back = bool(h.get("cleared_on"))
            if came_back or (open_for is not None and open_for >= bar):
                it["second_stall"] = True
                it["days_cost"] = (today - first).days if first else None
            elif first and first < today:
                it["carried_over"] = True
                it["unchanged_since"] = first.isoformat()
            if h.get("cleared_on"):
                h["times_flagged"] = str(int(h.get("times_flagged") or 1) + 1)
            h.update({"last_seen": today.isoformat(), "cleared_on": "", "holder": it["holder"]})
        else:
            hist[k] = {"key": k, "item": it["item"], "candidate": it["candidate"], "role": it["role"],
                       "holder": it["holder"], "first_seen": today.isoformat(), "last_seen": today.isoformat(),
                       "cleared_on": "", "times_flagged": "1"}
    for k, h in hist.items():
        if k not in present and not h.get("cleared_on"):
            h["cleared_on"] = today.isoformat()
    if write:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(hist.values())


def render(items, notes, today, holidays):
    if not items:
        return f"Nothing stalled as of {today.isoformat()}." + ("" if holidays else " (weekends only; no holiday list)")
    groups = {}
    carried = [it for it in items if it.get("carried_over")]
    for it in items:
        if not it.get("carried_over"):
            groups.setdefault(it["holder"], []).append(it)
    out = [f"# Stalled as of {today.isoformat()}" + ("" if holidays else " (business days skip weekends only; no holiday list given)")]
    for holder, its in sorted(groups.items(), key=lambda g: min(i["since"] for i in g[1])):
        out.append(f"\n## Waiting on {holder}")
        for it in sorted(its, key=lambda i: i["since"]):
            line = (f"- {it['candidate']}, {it['role']}: {it['item'].replace('_', ' ')}"
                    + (f" ({it['detail'].strip()})" if it['detail'].strip() else "")
                    + f"; since {it['since'][:16]} ({it['age']} {it['unit']}; bar {it['threshold']:g}). "
                    f"Frees it: {it['frees_it']}.")
            if it.get("second_stall"):
                line += f" SECOND STALL: escalate ({it.get('days_cost')} days since first flagged)."
            out.append(line)
    if carried:
        bits = [f"{i['candidate']} {i['item'].replace('_', ' ')} ({i['holder']}, since {i['unchanged_since']})"
                for i in sorted(carried, key=lambda i: i["unchanged_since"])]
        out.append(f"\nUnchanged since an earlier brief ({len(carried)}; one rollup line in the brief): "
                   + "; ".join(bits) + ".")
    for n in notes:
        out.append(f"\nneeds a look: {n}")
    return "\n".join(out)


def selftest():
    h = tempfile.mkdtemp()
    os.makedirs(os.path.join(h, "tracker"))
    with open(os.path.join(h, "tracker", "candidates.csv"), "w", encoding="utf-8") as fh:
        fh.write("name,role,stage,source,owner,last_contact,next_step,waiting_on,days_in_stage,notes,stage_since,due_by,tz,is_prospect,verification_step\n"
                 "Priya Nair,Senior Backend,Onsite done,Sourced,Maya,2026-10-05,,Lena Ortiz,,,2026-10-05,,,no,\n"
                 "Aisha Bello,Senior Backend,To schedule,Referral,Maya,2026-10-02,,,,,2026-10-02,,,no,\n"
                 "Sam Ode,Senior Backend,Offer out,Sourced,Maya,2026-10-06,,,,,2026-10-01,2026-10-07,,no,\n"
                 "Old Prospect,Senior Backend,Prospect,Sourced,Maya,2026-09-01,,,,,,,,yes,\n"
                 "Rui Costa,Senior Backend,Rejected,Applied,Maya,2026-10-02,,,,,2026-10-02,,,no,\n")
    with open(os.path.join(h, "tracker", "loops.csv"), "w", encoding="utf-8") as fh:
        fh.write("candidate,role,date,start,end,tz,interviewers,coverage,status,scorecards,candidate_tz,location\n"
                 "Priya Nair,Senior Backend,2026-10-05,10:00,11:00,Europe/Lisbon,Lena Ortiz,M2,done,3/4,,\n"
                 "Tom Becker,Senior Backend,2026-10-09,14:00,15:00,Europe/Lisbon,Dev Rao,M3,invited,,Europe/Berlin,\n")
    th = thresholds(DEFAULT_THRESHOLDS, h)
    now = dt.datetime(2026, 10, 8, 16, 0, tzinfo=Z("Europe/Lisbon"))
    items, _ = sweep(h, "Europe/Lisbon", now.date(), now, th, set())
    got = {(i["item"], i["candidate"]) for i in items}
    for want in [("scorecard_late", "Priya Nair"), ("awaiting_feedback", "Priya Nair"),
                 ("scheduling_unbooked", "Aisha Bello"), ("offer_open", "Sam Ode"),
                 ("invite_unaccepted", "Tom Becker"), ("decline_undrafted", "Rui Costa"),
                 ("response_window", "Priya Nair")]:
        assert want in got, (want, got)
    assert not any(i["candidate"] == "Old Prospect" for i in items)
    # one missing update is one line, not two
    assert ("no_update", "Priya Nair") not in got and ("no_update", "Aisha Bello") not in got, got
    hp = os.path.join(h, "flags", "stall-history.csv")
    apply_history(items, hp, now.date(), True)
    day2 = now + dt.timedelta(days=1)
    items2, _ = sweep(h, "Europe/Lisbon", day2.date(), day2, th, set())
    apply_history(items2, hp, day2.date(), True)
    # next day: still-open items roll up, they do not all escalate
    assert not any(i["second_stall"] for i in items2), [i["key"] for i in items2 if i["second_stall"]]
    assert any(i["carried_over"] for i in items2)
    assert "Unchanged since an earlier brief" in render(items2, [], day2.date(), set())
    # open for twice its bar since first flagged: escalates
    day4 = now + dt.timedelta(days=4)
    items4, _ = sweep(h, "Europe/Lisbon", day4.date(), day4, th, set())
    apply_history(items4, hp, day4.date(), False)
    esc = {(i["item"], i["candidate"]) for i in items4 if i["second_stall"]}
    assert ("scorecard_late", "Priya Nair") in esc, esc
    # cleared and came back: escalates at once
    hist = load(hp)
    for r in hist:
        if r["item"] == "scheduling_unbooked":
            r["cleared_on"] = day2.date().isoformat()
    with open(hp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(hist[0].keys()))
        w.writeheader()
        w.writerows(hist)
    items3, _ = sweep(h, "Europe/Lisbon", day2.date(), day2, th, set())
    apply_history(items3, hp, day2.date(), False)
    assert any(i["second_stall"] and i["item"] == "scheduling_unbooked" for i in items3)
    # outreach touches under an accented and an unaccented spelling are one person
    with open(os.path.join(h, "outreach-log.csv"), "w", encoding="utf-8") as fh:
        fh.write("candidate,role,touch,status,date,reply_type,sender\n"
                 "José Araújo,Senior Backend,1,sent,2026-10-01,none,Maya\n"
                 "Jose Araujo,Senior Backend,2,sent,2026-10-03,none,Maya\n"
                 "JOSÉ ARAÚJO,senior backend,3,sent,2026-10-06,none,Maya\n")
    items5, _ = sweep(h, "Europe/Lisbon", now.date(), now, th, set())
    nr = [i for i in items5 if i["item"] == "no_reply"]
    assert len(nr) == 1 and nr[0]["candidate"] == "José Araújo", nr
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hiring", default=os.path.expanduser("~/workspace/hiring"))
    ap.add_argument("--tz", help="owner IANA timezone (else 'timezone:' in preferences.md)")
    ap.add_argument("--today")
    ap.add_argument("--now")
    ap.add_argument("--thresholds", default=DEFAULT_THRESHOLDS)
    ap.add_argument("--holidays")
    ap.add_argument("--no-history", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    try:
        tz = a.tz
        prefs = os.path.join(a.hiring, "preferences.md")
        if not tz and os.path.exists(prefs):
            with open(prefs, encoding="utf-8") as fh:
                m = re.search(r"^\s*timezone\s*:\s*(\S+)", fh.read(), re.M)
                tz = m.group(1) if m and m.group(1) != "UNSET" else None
        if not tz:
            raise ValueError("no owner timezone: pass --tz or set 'timezone:' in preferences.md")
        now = dt.datetime.fromisoformat(a.now).replace(tzinfo=Z(tz)) if a.now else dt.datetime.now(Z(tz))
        today = dt.date.fromisoformat(a.today) if a.today else now.date()
        holidays = set()
        if a.holidays:
            with open(a.holidays, encoding="utf-8") as fh:
                holidays = {dt.date.fromisoformat(x.strip()) for x in fh if x.strip()}
        th = thresholds(a.thresholds, a.hiring)
        items, notes = sweep(a.hiring, tz, today, now, th, holidays)
        apply_history(items, os.path.join(a.hiring, "flags", "stall-history.csv"), today, not a.no_history,
                      holidays)
    except ModuleNotFoundError:
        print("zoneinfo data missing: python3 -m pip install --user tzdata", file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError) as exc:
        print(f"bad input: {exc}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps({"today": today.isoformat(), "items": items, "needs_a_look": notes}, indent=1))
    else:
        print(render(items, notes, today, holidays))
    return 0


if __name__ == "__main__":
    sys.exit(main())
