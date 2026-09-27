#!/usr/bin/env python3
"""Find complete interview-loop options that fit everyone, in both timezones.

    cd ~/skills/interview-coordination && python3 scripts/tz_slots.py /home/user/coord/availability.json [--json]

Input shape: templates/availability-example.json
    owner_tz, candidate_tz        IANA names (e.g. Europe/Lisbon). Required.
    candidate_windows             [{start, end, tz}] local times in tz (ISO, no offset)
    owner_hours                   {days: [Mon..Sun], start: "HH:MM", end: "HH:MM"} in owner_tz
    slots                         [{label, minutes, interviewers: [..], alternates: [..]}] in loop order
    busy                          {person: [{start, end}]}  ISO with offset, or with "tz"
    buffer_minutes                gap between interviews (default 10: the skill's default
                                  for a four-slot onsite; confirm with the owner)
    break_after_slot, break_minutes   a longer break after slot N (default after slot 2,
                                  30 minutes: "a proper break near the midpoint"; confirm)
    step_minutes                  start-time granularity (default 15)
    max_options                   default 3 ("two or three complete loop options")

Every slot must sit inside one candidate window, inside the owner's interview
hours on one local day, and clear of each interviewer's busy times. Loops are
single-day; for a split loop run once per day.

Strict options come first. If fewer than max_options exist, a relaxed pass
allows exactly one kind of compromise per option and names it:
    "5-minute turnarounds"  (buffer cut to 5)
    "stand-in <alt> for <primary> (<slot>)"   (an alternate who can take that competency
                                              and is not already interviewing in this loop)
Options are ranked: fewest compromises, then earliest; one per day where possible.

Output: every slot as "Tue 13 Oct 10:00–11:00 Europe/Berlin / 09:00–10:00 Europe/Lisbon".
Exit 0 with options; exit 2 with the binding constraint named when nothing fits
or the input is bad. --selftest checks DST and the constraint report.
"""

import argparse
import collections
import datetime as dt
import json
import sys

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DEFAULTS = {"buffer_minutes": 10, "break_after_slot": 2, "break_minutes": 30,
            "step_minutes": 15, "max_options": 3}
RELAXED_BUFFER = 5


def Z(name):
    from zoneinfo import ZoneInfo
    return ZoneInfo(name)


def parse_local(s, tz):
    t = dt.datetime.fromisoformat(s)
    return t if t.tzinfo else t.replace(tzinfo=Z(tz))


def fmt(s, e, tz):
    a, b = s.astimezone(Z(tz)), e.astimezone(Z(tz))
    return f"{a:%a %d %b %H:%M}–{b:%H:%M} {tz}"


class Plan:
    def __init__(self, cfg):
        self.cfg = {**DEFAULTS, **cfg}
        c = self.cfg
        for k in ("owner_tz", "candidate_tz", "candidate_windows", "slots", "owner_hours"):
            if not c.get(k):
                raise ValueError(f"'{k}' is required (see templates/availability-example.json)")
        Z(c["owner_tz"]), Z(c["candidate_tz"])
        self.windows = [(parse_local(w["start"], w.get("tz", c["candidate_tz"])),
                         parse_local(w["end"], w.get("tz", c["candidate_tz"]))) for w in c["candidate_windows"]]
        oh = c["owner_hours"]
        self.days = {DAYS.index(d[:3].title()) for d in oh.get("days", DAYS[:5])}
        self.oh_start = dt.time.fromisoformat(oh["start"])
        self.oh_end = dt.time.fromisoformat(oh["end"])
        self.busy = collections.defaultdict(list)
        for person, spans in (c.get("busy") or {}).items():
            for sp in spans:
                tz = sp.get("tz", c["owner_tz"])
                self.busy[person].append((parse_local(sp["start"], tz), parse_local(sp["end"], tz)))

    def free(self, person, s, e):
        return all(e <= bs or s >= be for bs, be in self.busy.get(person, []))

    def in_owner_hours(self, s, e):
        ls, le = s.astimezone(Z(self.cfg["owner_tz"])), e.astimezone(Z(self.cfg["owner_tz"]))
        return (ls.date() == le.date() and ls.weekday() in self.days
                and ls.time() >= self.oh_start and le.time() <= self.oh_end)

    def lay(self, start, w_end, buffer, allow_standin, fails):
        c = self.cfg
        t = start
        out, comp = [], []
        for i, slot in enumerate(c["slots"]):
            s, e = t, t + dt.timedelta(minutes=int(slot["minutes"]))
            if e > w_end:
                fails["candidate window too short for the whole loop"] += 1
                return None
            if not self.in_owner_hours(s, e):
                fails["outside the owner's interview hours"] += 1
                return None
            people = list(slot.get("interviewers") or [])
            if not people:
                fails[f"slot '{slot.get('label')}' has no interviewer"] += 1
                return None
            chosen = []
            for p in people:
                if self.free(p, s, e):
                    chosen.append(p)
                    continue
                in_loop = {x for sl in c["slots"] for x in (sl.get("interviewers") or [])}
                alt = next((a for a in slot.get("alternates") or []
                            if a not in chosen and a not in in_loop and self.free(a, s, e)), None)
                if allow_standin and alt and not comp:
                    chosen.append(alt)
                    comp.append(f"stand-in {alt} for {p} ({slot.get('label')})")
                    continue
                fails[f"{p} busy"] += 1
                return None
            out.append({"label": slot.get("label"), "interviewers": chosen, "start": s, "end": e})
            gap = c["break_minutes"] if (i + 1) == c["break_after_slot"] else buffer
            t = e + dt.timedelta(minutes=gap)
        if buffer < c["buffer_minutes"]:
            comp.append(f"{buffer}-minute turnarounds")
        return out, comp

    def search(self):
        c = self.cfg
        step = dt.timedelta(minutes=c["step_minutes"])
        found, fails = [], collections.Counter()
        passes = [(c["buffer_minutes"], False)]
        passes += [(c["buffer_minutes"], True), (RELAXED_BUFFER, False)]
        for buffer, standin in passes:
            for ws, we in self.windows:
                t = ws
                while t < we:
                    r = self.lay(t, we, buffer, standin, fails)
                    if r and (len(r[1]) <= 1):
                        found.append(r)
                    t += step
            strict = [f for f in found if not f[1]]
            if len({f[0][0]["start"].astimezone(Z(c["owner_tz"])).date() for f in strict}) >= c["max_options"]:
                break
        seen, uniq = set(), []
        for slots, comp in found:
            k = (slots[0]["start"], tuple(tuple(s["interviewers"]) for s in slots), tuple(comp))
            if k not in seen:
                seen.add(k)
                uniq.append((slots, comp))
        uniq.sort(key=lambda r: (len(r[1]), r[0][0]["start"]))
        picked, days = [], set()
        for slots, comp in uniq:
            d = slots[0]["start"].astimezone(Z(c["owner_tz"])).date()
            if d not in days:
                picked.append((slots, comp))
                days.add(d)
            if len(picked) == c["max_options"]:
                break
        for slots, comp in uniq:
            if len(picked) >= c["max_options"]:
                break
            if all(abs(slots[0]["start"] - p[0][0]["start"]) >= dt.timedelta(hours=1) for p in picked):
                picked.append((slots, comp))
        picked.sort(key=lambda r: (len(r[1]), r[0][0]["start"]))
        return picked, fails


def render(plan, picked):
    c = plan.cfg
    lines = []
    for i, (slots, comp) in enumerate(picked, 1):
        head = f"Option {i}: {slots[0]['start'].astimezone(Z(c['owner_tz'])):%a %d %b}"
        head += " (no compromise)" if not comp else f" (compromise: {comp[0]})"
        lines.append(head)
        for s in slots:
            lines.append(f"  - {s['label']}, {', '.join(s['interviewers'])}: "
                         f"{fmt(s['start'], s['end'], c['candidate_tz'])} / {fmt(s['start'], s['end'], c['owner_tz'])}")
    return "\n".join(lines)


SAMPLE = {
    "owner_tz": "Europe/Lisbon", "candidate_tz": "America/New_York",
    "candidate_windows": [{"start": "2026-10-23T08:00", "end": "2026-10-23T12:30"},
                          {"start": "2026-10-26T08:00", "end": "2026-10-26T12:30"}],
    "owner_hours": {"days": ["Mon", "Tue", "Wed", "Thu", "Fri"], "start": "09:30", "end": "17:30"},
    "slots": [{"label": "Billing debugging", "minutes": 60, "interviewers": ["Dev Rao"], "alternates": ["Mia Chen"]},
              {"label": "Live data changes", "minutes": 45, "interviewers": ["Ana Silva"]},
              {"label": "HM close", "minutes": 45, "interviewers": ["Lena Ortiz"]}],
    "busy": {"Dev Rao": [{"start": "2026-10-23T13:00:00+01:00", "end": "2026-10-23T17:30:00+01:00"}]},
}


def selftest():
    p = Plan(SAMPLE)
    picked, fails = p.search()
    assert picked, fails
    first = picked[0][0][0]
    # Europe leaves summer time on 25 Oct 2026, the US on 1 Nov: the gap is 4 h on the 26th, 5 h on the 23rd
    texts = render(p, picked)
    assert "Mon 26 Oct" in texts, texts
    assert "08:00–09:00 America/New_York / Mon 26 Oct 12:00–13:00 Europe/Lisbon" in texts, texts
    bad = dict(SAMPLE, candidate_windows=[{"start": "2026-10-23T08:00", "end": "2026-10-23T09:00"}])
    none, fails = Plan(bad).search()
    assert not none and fails.most_common(1)[0][0].startswith("candidate window too short"), fails
    assert first
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("availability", nargs="?")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.availability:
        ap.error("give the availability JSON (shape: templates/availability-example.json)")
    try:
        with open(a.availability, encoding="utf-8") as fh:
            plan = Plan(json.load(fh))
        picked, fails = plan.search()
    except ModuleNotFoundError:
        print("zoneinfo data missing: python3 -m pip install --user tzdata", file=sys.stderr)
        return 2
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"bad input: {exc}", file=sys.stderr)
        return 2
    if not picked:
        top = fails.most_common(3)
        print("no loop fits. Binding constraint(s): " +
              "; ".join(f"{k} ({n} start times ruled out)" for k, n in top))
        print("Ask for wider candidate windows, a stand-in, or a split loop.")
        return 2
    if a.json:
        print(json.dumps([{"compromise": comp, "slots": [
            {"label": s["label"], "interviewers": s["interviewers"],
             "start": s["start"].isoformat(), "end": s["end"].isoformat(),
             "candidate_time": fmt(s["start"], s["end"], plan.cfg["candidate_tz"]),
             "owner_time": fmt(s["start"], s["end"], plan.cfg["owner_tz"])} for s in slots]}
            for slots, comp in picked], indent=1))
    else:
        print(render(plan, picked))
    return 0


if __name__ == "__main__":
    sys.exit(main())
