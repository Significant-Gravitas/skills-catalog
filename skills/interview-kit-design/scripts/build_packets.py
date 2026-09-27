#!/usr/bin/env python3
"""Build one prep packet per interview on a date, from the tracker and the kits.

    cd ~/skills/interview-kit-design && python3 scripts/build_packets.py \
        --date tomorrow --tz Europe/Lisbon \
        [--hiring ~/workspace/hiring] [--scorecard-hours 24] [--dry-run] [--json]

Reads (paths under --hiring, default ~/workspace/hiring):
    tracker/loops.csv               one row per interview; needs date, start, end, tz
                                    (IANA zone the times are written in); optional
                                    candidate_tz, location, coverage, interviewers, status
    roles/<role-slug>/kit.md        the kit (templates/kit.md shape)
    debriefs/<role-slug>/*<candidate-slug>*.md   "## Open questions" from earlier rounds
    roles/, screens/, debriefs/     any file whose name holds the candidate slug as whole
                                    words is listed as material on file for the summary
                                    ("jo-park-resume.txt" for Jo Park; never
                                    "jo-parker-resume.txt")
Writes:
    packets/<date>-<role-slug>-<candidate-slug>-<HHMM owner time>-slot<n>.md  (not with --dry-run)

What it fills: times in the candidate's zone and the owner's (zoneinfo, DST
safe), interviewer, competency, that slot's questions with strong-answer notes
and probes, earlier rounds covered, open questions, logistics, reminders, and
the scorecard deadline (--scorecard-hours after the slot ends; default 24 is
the skill's default window, confirm with the owner).
What it leaves: the candidate summary, marked for the model to fill with at most
five direct quotes, each with its source (then run verify_quotes.py).
Flags: no timezone on the row (the row is refused, never assumed), no
interviewer, no competency, no kit, no matching slot, no candidate material.

No interviews on the date: prints "no interviews on <date>", writes nothing,
exit 0. Exit 2 on bad input. --selftest builds packets in a temp folder.
"""

import argparse
import csv
import datetime as dt
import glob
import json
import os
import re
import sys
import tempfile
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitparse  # noqa: E402

DEFAULT_SCORECARD_HOURS = 24


def slug(text):
    t = unicodedata.normalize("NFKD", text or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def zone(name):
    from zoneinfo import ZoneInfo
    return ZoneInfo(name)


def pref(hiring, key):
    path = os.path.join(hiring, "preferences.md")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = re.match(rf"^\s*{re.escape(key)}\s*:\s*(.+?)\s*$", line)
            if m and m.group(1).upper() != "UNSET":
                return m.group(1)
    return None


def fmt(start, end, tz_name):
    z = zone(tz_name)
    s, e = start.astimezone(z), end.astimezone(z)
    return f"{s:%a %d %b %H:%M}–{e:%H:%M} {tz_name}"


def names_candidate(filename, cand_slug):
    """True when the file name holds the candidate slug as whole words:
    'jo-park-resume.txt' names Jo Park, 'jo-parker-resume.txt' does not."""
    t = unicodedata.normalize("NFKD", filename or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    t = re.sub(r"[^a-z0-9.]+", "-", t).strip("-")
    return bool(cand_slug) and re.search(rf"(^|[-_.]){re.escape(cand_slug)}([-_.]|$)", t) is not None


def open_questions(hiring, role_slug, cand_slug):
    lines = []
    folder = os.path.join(hiring, "debriefs", role_slug)
    names = sorted(os.listdir(folder)) if os.path.isdir(folder) else []
    for path in [os.path.join(folder, n) for n in names
                 if n.lower().endswith(".md") and names_candidate(n, cand_slug)]:
        grab = False
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if re.match(r"^##\s+open questions", line, re.I):
                    grab = True
                    continue
                if grab and line.startswith("## "):
                    break
                if grab and line.strip().startswith(("-", "*")):
                    lines.append(line.strip().lstrip("-* ").strip() + f" ({os.path.basename(path)})")
    return lines


def materials(hiring, cand_slug):
    found = []
    for sub in ("roles", "screens", "debriefs"):
        for path in glob.glob(os.path.join(hiring, sub, "**", "*"), recursive=True):
            if os.path.isfile(path) and names_candidate(os.path.basename(path), cand_slug) \
                    and "/scorecards/" not in path.replace("\\", "/"):
                found.append(os.path.relpath(path, hiring).replace("\\", "/"))
    return sorted(found)


def match_slot(kit, coverage):
    if not kit:
        return None
    ids = re.findall(r"M\d+", coverage or "")
    for s in kit["slots"]:
        if ids and set(ids) & set(s["owns"]):
            return s
    for s in kit["slots"]:
        if coverage and coverage.lower() in s["title"].lower():
            return s
    return None


def build(a, hiring):
    owner_tz = a.tz or pref(hiring, "timezone")
    if not owner_tz:
        raise ValueError("no owner timezone: pass --tz <IANA> or set 'timezone:' in preferences.md")
    zone(owner_tz)
    now_owner = dt.datetime.now(zone(owner_tz))
    if a.date in (None, "tomorrow"):
        target = (now_owner + dt.timedelta(days=1)).date()
    elif a.date == "today":
        target = now_owner.date()
    else:
        target = dt.date.fromisoformat(a.date)
    loops_path = os.path.join(hiring, "tracker", "loops.csv")
    if not os.path.exists(loops_path):
        raise ValueError(f"no loop log at {loops_path}; interview-coordination keeps it")
    with open(loops_path, newline="", encoding="utf-8-sig") as fh:
        rows = [{k.strip(): (v or "").strip() for k, v in r.items() if k} for r in csv.DictReader(fh)]
    todays, flags, earlier = [], [], []
    for i, r in enumerate(rows, 2):
        if re.search(r"cancel", r.get("status", ""), re.I):
            continue
        if not r.get("tz"):
            flags.append(f"loops.csv line {i} ({r.get('candidate')}, {r.get('date')}): no tz column value; "
                         "fix the tracker, times are never assumed")
            continue
        try:
            start = dt.datetime.combine(dt.date.fromisoformat(r["date"]),
                                        dt.time.fromisoformat(r["start"]), zone(r["tz"]))
            end = dt.datetime.combine(dt.date.fromisoformat(r["date"]),
                                      dt.time.fromisoformat(r["end"]), zone(r["tz"]))
        except (KeyError, ValueError) as exc:
            flags.append(f"loops.csv line {i}: unreadable date/time/zone ({exc})")
            continue
        r["_start"], r["_end"] = start, end
        d_owner = start.astimezone(zone(owner_tz)).date()
        if d_owner == target:
            todays.append(r)
        elif d_owner < target:
            earlier.append(r)
    if not todays:
        return {"date": target.isoformat(), "packets": [], "flags": flags,
                "message": f"no interviews on {target.isoformat()}"}
    todays.sort(key=lambda r: (r["candidate"], r["_start"]))
    per_cand = {}
    for r in todays:
        per_cand.setdefault((r["candidate"], r.get("role", "")), []).append(r)
    out_dir = os.path.join(hiring, "packets")
    written = []
    hours = a.scorecard_hours
    for (cand, role), rs in per_cand.items():
        role_slug, cand_slug = slug(role), slug(cand)
        kit_path = os.path.join(hiring, "roles", role_slug, "kit.md")
        kit = None
        if os.path.exists(kit_path):
            with open(kit_path, encoding="utf-8") as fh:
                kit = kitparse.parse(fh.read())
        else:
            flags.append(f"{cand} / {role}: no kit at roles/{role_slug}/kit.md")
        mats = materials(hiring, cand_slug)
        if not mats:
            flags.append(f"{cand}: no resume or candidate material on file; summary will be thin")
        oq = open_questions(hiring, role_slug, cand_slug)
        prior = [p for p in earlier if p["candidate"] == cand and p.get("role", "") == role]
        for idx, r in enumerate(rs, 1):
            s = match_slot(kit, r.get("coverage"))
            n = s["n"] if s else None
            cand_tz = r.get("candidate_tz") or ""
            who = r.get("interviewers") or ""
            row_flags = []
            if not who:
                row_flags.append("NO INTERVIEWER")
            if not r.get("coverage"):
                row_flags.append("NO COMPETENCY")
            if kit and not s:
                row_flags.append(f"coverage '{r.get('coverage')}' matches no kit slot")
            if not cand_tz:
                row_flags.append("candidate timezone UNKNOWN (ask; never guess)")
            when = (fmt(r["_start"], r["_end"], cand_tz) if cand_tz else "candidate zone UNKNOWN") \
                + " / " + fmt(r["_start"], r["_end"], owner_tz)
            due = (r["_end"] + dt.timedelta(hours=hours)).astimezone(zone(owner_tz))
            owns = ", ".join(f"{m}: {kit['must_haves'].get(m, '?')}" for m in (s["owns"] if s else [])) \
                or (r.get("coverage") or "NOT SET")
            L = [f"# Prep packet: {cand} · {role} · interview {idx} of {len(rs)} that day · "
                 f"kit slot {n if n else 'NONE'}",
                 "", f"**When:** {when}",
                 f"**Interviewer:** {who or 'NOT SET'} · **You own:** {owns}",
                 f"**Scorecard due:** {due:%a %d %b %H:%M} {owner_tz} ({hours} h after the slot)"]
            if row_flags:
                L += ["", "**Flags:** " + "; ".join(row_flags)]
            L += ["", "## Candidate summary (max 5 lines; direct quotes only)", "",
                  "<<FILL: up to 5 lines, each `- \"exact words\" — source: <path or URL>`; "
                  "'<topic>: not stated' for gaps; then run scripts/verify_quotes.py>>", ""]
            L += ["## Sources on file", ""] + ([f"- {m}" for m in mats] or ["- none found"])
            L += ["", f"## Your questions ({', '.join(s['owns']) if s else r.get('coverage') or 'NOT SET'})", ""]
            if s and s["questions"]:
                for qi, q in enumerate(s["questions"], 1):
                    L.append(f"{qi}. {q['text']}")
                    if q["strong"]:
                        L.append(f"   - Strong answer: {q['strong']}")
                    if q["probe"]:
                        L.append(f"   - Probe: {q['probe']}")
            else:
                L.append("NO QUESTIONS: the kit has no slot for this competency")
            L += ["", "## Earlier rounds", ""]
            if prior:
                for p in sorted(prior, key=lambda p: p["_start"]):
                    L.append(f"- Covered: {p.get('coverage') or '?'} by {p.get('interviewers') or '?'} "
                             f"on {p['_start'].astimezone(zone(owner_tz)):%d %b}")
            else:
                L.append("- Covered: first round")
            L += [f"- Open question to close: {q}" for q in oq] or ["- Open question to close: none recorded"]
            L += ["", "## Logistics", "",
                  f"{r.get('location') or 'Room or video link: NOT SET'} · greeted by: "
                  f"{r.get('greeter') or 'not recorded'} · scorecard in the kit format, filed alone before "
                  "any panel discussion.", "", "## Reminders", "",
                  "- Same core questions for every candidate; follow-ups only to clarify.",
                  "- Rate evidence against the anchors; never affect, demeanour or 'fit'.",
                  f"- Accommodation requests go to {(kit or {}).get('meta', {}).get('accommodation_contact') or 'NOT SET'}; "
                  "never ask for medical detail.",
                  f"- Candidate AI use in this interview: "
                  f"{((kit or {}).get('meta', {}).get('candidate_ai_policy') or 'no policy set').rstrip('.')}."]
            hhmm = r["_start"].astimezone(zone(owner_tz)).strftime("%H%M")
            name = f"{target.isoformat()}-{role_slug}-{cand_slug}-{hhmm}-slot{n or 'none'}.md"
            if not a.dry_run:
                os.makedirs(out_dir, exist_ok=True)
                with open(os.path.join(out_dir, name), "w", encoding="utf-8") as fh:
                    fh.write("\n".join(L) + "\n")
            written.append({"file": f"packets/{name}", "candidate": cand, "role": role, "slot": n,
                            "interviewer": who, "flags": row_flags})
    return {"date": target.isoformat(), "packets": written, "flags": flags}


def selftest():
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "tracker"))
    os.makedirs(os.path.join(d, "roles", "senior-backend-engineer"))
    with open(os.path.join(d, "tracker", "loops.csv"), "w", encoding="utf-8") as fh:
        fh.write("candidate,role,date,start,end,tz,interviewers,coverage,status,scorecards,candidate_tz,location\n"
                 "Priya Nair,Senior Backend Engineer,2026-10-29,10:00,11:00,Europe/Lisbon,Dev Rao,M2,booked,out,"
                 "Europe/Dublin,Meet link in invite\n"
                 "Priya Nair,Senior Backend Engineer,2026-10-29,11:10,11:55,Europe/Lisbon,,M3,booked,out,,\n"
                 "Tom Becker,Senior Backend Engineer,2026-10-29,15:00,16:00,,Dev Rao,M2,booked,out,,\n")
    with open(os.path.join(d, "roles", "senior-backend-engineer", "kit.md"), "w", encoding="utf-8") as fh:
        fh.write("role_slug: senior-backend-engineer\naccommodation_contact: people@northwind.example\n\n"
                 "## Must-haves\n- M2: Debugs billing flows\n- M3: System design\n\n"
                 "## Slot 2: Billing debugging\nlength: 60\ninterviewer: Dev Rao\nowns: M2\n"
                 "clock: 5 context, 45 main problem, 10 candidate questions\n\n### Questions\n"
                 "1. \"A customer was charged twice. Where do you look first?\"\n"
                 "   - Strong answer: idempotency keys, webhook retries\n   - Probe: What would you log?\n")

    class A:
        tz = "Europe/Lisbon"
        date = "2026-10-29"
        scorecard_hours = 24
        dry_run = False
    res = build(A, d)
    assert len(res["packets"]) == 2, res
    assert any("no tz column" in f for f in res["flags"]), res["flags"]
    p1 = open(os.path.join(d, res["packets"][0]["file"]), encoding="utf-8").read()
    assert "10:00–11:00 Europe/Dublin" in p1 and "10:00–11:00 Europe/Lisbon" in p1, p1
    assert "charged twice" in p1 and "people@northwind.example" in p1
    assert "NO INTERVIEWER" in json.dumps(res["packets"][1])
    A.date = "2026-10-30"
    assert build(A, d)["packets"] == []
    # Jo Park never picks up Jo Parker's files or open questions
    os.makedirs(os.path.join(d, "screens"))
    os.makedirs(os.path.join(d, "debriefs", "senior-backend-engineer"))
    files = {"screens/jo-park-resume.txt": "x\n", "screens/jo-parker-resume.txt": "x\n",
             "debriefs/senior-backend-engineer/2026-10-20-jo-parker-screen.md":
                 "## Open questions\n- Ask Jo Parker about the outage\n",
             "debriefs/senior-backend-engineer/2026-10-21-jo-park-screen.md":
                 "## Open questions\n- Ask Jo Park about retries\n"}
    for rel, body in files.items():
        with open(os.path.join(d, rel), "w", encoding="utf-8") as fh:
            fh.write(body)
    got = materials(d, "jo-park")
    assert got == ["debriefs/senior-backend-engineer/2026-10-21-jo-park-screen.md",
                   "screens/jo-park-resume.txt"], got
    oq = open_questions(d, "senior-backend-engineer", "jo-park")
    assert len(oq) == 1 and "retries" in oq[0], oq
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", default="tomorrow", help="tomorrow (default), today or YYYY-MM-DD, in the owner's zone")
    ap.add_argument("--tz", help="owner IANA timezone; default: 'timezone:' in preferences.md")
    ap.add_argument("--hiring", default=os.path.expanduser("~/workspace/hiring"))
    ap.add_argument("--scorecard-hours", type=int, default=DEFAULT_SCORECARD_HOURS)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    try:
        res = build(a, a.hiring)
    except ModuleNotFoundError:
        print("zoneinfo missing: python3 -m pip install --user tzdata", file=sys.stderr)
        return 2
    except (ValueError, OSError, KeyError) as exc:
        print(f"bad input: {exc}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(res, indent=1))
    else:
        if res.get("message"):
            print(res["message"])
        for p in res["packets"]:
            print(f"{'(dry run) ' if a.dry_run else ''}{p['file']}"
                  + (f"  FLAGS: {'; '.join(p['flags'])}" if p["flags"] else ""))
        for f in res["flags"]:
            print(f"FLAG\t{f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
