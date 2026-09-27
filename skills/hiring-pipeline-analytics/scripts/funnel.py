#!/usr/bin/env python3
"""Funnel, pacing, quality and hygiene numbers from the hiring tracker or a normalised ATS export.

Run from the package dir:
  cd ~/skills/hiring-pipeline-analytics && python3 scripts/funnel.py \
    --tracker ~/workspace/hiring/tracker \
    --shortlist ~/workspace/hiring/shortlist.csv \
    --outreach ~/workspace/hiring/outreach-log.csv \
    --prefs ~/workspace/hiring/preferences.md \
    --history ~/workspace/hiring/reports \
    --window 2026-10-05:2026-10-11 --prior auto \
    --out /home/user/pipeline/2026-10-11

Inputs (all optional except a candidates source):
  --tracker DIR        roles.csv, candidates.csv, loops.csv (interview-coordination columns)
  --candidates FILE    instead of DIR/candidates.csv (e.g. normalize_export.py output)
  --roles/--loops FILE override files in --tracker
  --shortlist, --outreach  sourcing and outreach logs
  --hires FILE         name,role,start_on,left_on,exit_reason (early attrition)
  --costs FILE         line,type(internal|external),amount,currency[,estimate(yes|no)]
                       (cost per hire; any estimate line makes the total INFERENCE)
  --hm-survey FILE     role,score,scale_max (hiring-manager satisfaction)
  --offers DIR         ~/workspace/hiring/offers: each <role>-<cand>/close-plan.csv is read for
                       open answer-by tracks already past (job-offer-and-close-plan's file)
  --history DIR        earlier *-snapshot.json files (snapshot_and_chart.py); used only to
                       fill missing dates, and everything taken from it is labelled INFERENCE
  --stage-map FILE     user_stage,funnel_stage for stage names the defaults do not know
  --prefs FILE         preferences.md (keys: stalled_bar, min_sample, touch_limit,
                       attrition_window_days, heavy_day_per_interviewer, outreach_cadence,
                       outreach_day_kind)
                       touch_limit = follow-ups after the first note (default 3, so the
                       sequence is complete after touch 4) and outreach_cadence = days after
                       the first note (default 2,5,8, business days), both as
                       passive-candidate-outreach defines them.
  --window A:B --prior auto|A:B|none --today YYYY-MM-DD --role NAME
  --date-order dayfirst|monthfirst   only needed for ambiguous 03/04/2026 dates

Outputs: OUT/report.json (every number with label FACT|INFERENCE|UNKNOWN, n and basis)
and OUT/report.md (internal: names candidates in stuck lists; run share_safe.py before
sharing). Protected columns (references/protected-columns.txt) are dropped on read and
listed. No group rates by any protected trait are ever computed.
Duplicate name + role rows are listed under hygiene and counted once (furthest stage kept).
Cost amounts must be plain numbers (1800 or 1800.00); anything else is a bad cost line and
cost per hire is UNKNOWN until it is fixed. A hires.csv row that left before it started is
hygiene, not an early leaver. Outreach status and names are compared case-insensitively.
Exit: 0 ok, 2 no candidate rows / bad arguments (including a --today that is not YYYY-MM-DD).
"""

import argparse
import datetime as dt
import glob
import json
import os
import re
import statistics
import sys
import unicodedata
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_io as io  # noqa: E402

DEFAULTS = {  # every one: default - confirm with the owner
    "min_sample": 30, "stalled_bar": "5 business days", "touch_limit": 3,
    "attrition_window_days": 90, "heavy_day_per_interviewer": 3, "outreach_cadence": "2,5,8",
    "outreach_day_kind": "business",
}


def add_outreach_days(start, n, kind):
    """passive-candidate-outreach's rule (followups_due.py): business = count weekdays only;
    calendar = count every day, then roll a weekend due date to Monday. No holiday list."""
    if kind == "calendar":
        d = start + dt.timedelta(days=n)
        while d.weekday() >= 5:
            d += dt.timedelta(days=1)
        return d
    d, left = start, n
    while left > 0:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            left -= 1
    return d


def num(value, label, n=None, basis=""):
    return {"value": value, "label": label, "n": n, "basis": basis}


def median(values):
    return statistics.median(values) if values else None


def parse_window(text, order):
    if not text or text == "none":
        return None
    a, b = text.split(":")
    start, end = io.parse_date(a, order), io.parse_date(b, order)
    if not start or not end or end < start:
        raise ValueError(f"bad window '{text}' (use YYYY-MM-DD:YYYY-MM-DD)")
    return start, end


def in_window(d, window):
    return window is None or (d is not None and window[0] <= d <= window[1])


def load_history(path):
    """-> {(name, role): {'first_seen': date, 'level_first': {level: date}, 'bucket_since': (bucket, date)}}"""
    out = {}
    files = sorted(glob.glob(os.path.join(path, "*-snapshot.json"))) if path else []
    for f in files:
        try:
            with open(f, encoding="utf-8") as fh:
                snap = json.load(fh)
            day = dt.date.fromisoformat(snap["as_of"])
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            continue
        for c in snap.get("candidates", []):
            key = (c.get("name", "").lower(), c.get("role", "").lower())
            h = out.setdefault(key, {"first_seen": day, "level_first": {}, "bucket_since": None})
            h["first_seen"] = min(h["first_seen"], day)
            lvl = c.get("level")
            if isinstance(lvl, int) and lvl not in h["level_first"]:
                h["level_first"][lvl] = day
            if not h["bucket_since"] or h["bucket_since"][0] != c.get("bucket"):
                h["bucket_since"] = (c.get("bucket"), day)
    return out


def build_candidates(rows, stage_map, order, today, history, hygiene):
    cands, seen = [], Counter()
    for r in rows:
        name, role = r.get("name", ""), r.get("role", "")
        seen[(name.lower(), role.lower())] += 1
        stage = r.get("stage", "")
        bucket = "prospect" if io.truthy(r.get("is_prospect")) else io.classify_stage(stage, stage_map)
        if not stage:
            hygiene["missing_stage"].append(f"line {r['_line']}: {name or '?'} ({role or '?'})")
        if not r.get("owner"):
            hygiene["missing_owner"].append(f"line {r['_line']}: {name or '?'} ({role or '?'})")
        if stage and bucket is None:
            hygiene["unmapped_stage"].append(stage)
        c = {"name": name, "role": role, "stage": stage, "bucket": bucket, "line": r["_line"],
             "source": r.get("source", "") or "UNKNOWN", "owner": r.get("owner", ""),
             "waiting_on": r.get("waiting_on", ""), "next_step": r.get("next_step", ""),
             "reason": io.first(r, "reason", "rejection_reason", "archive_reason", "decline_reason"),
             "reason_type": io.first(r, "reason_type").lower(), "role_family": io.first(r, "role_family"),
             "inferred": []}
        dates = {}
        for key, aliases in {
            "entry": ("applied_on", "applied", "application_date", "date_applied", "sourced_on", "created_on", "date_added"),
            "stage_entered": ("stage_entered_on", "entered_stage_on", "in_stage_since"),
            "offer_out": ("offer_out_on", "offer_sent_on", "offer_extended_on"),
            "answer_by": ("answer_by", "offer_answer_by"),
            "resolved": ("offer_resolved_on", "offer_accepted_on", "offer_declined_on"),
            "accepted": ("accepted_on", "hired_on", "hire_date", "offer_accepted_on"),
        }.items():
            raw = io.first(r, *aliases)
            d = io.parse_date(raw, order)
            if raw and d is None:
                hygiene["bad_date"].append(f"line {r['_line']}: {key} '{raw}'")
            dates[key] = d
        hist = history.get((name.lower(), role.lower()))
        c["entry_real"] = dates["entry"]
        if dates["entry"] is None and hist:
            dates["entry"] = hist["first_seen"]
            c["inferred"].append("entry date = first snapshot seen")
        c.update(dates)
        rt = c["reason_type"]
        c["theirs"] = bucket in ("withdrew", "declined_offer") or any(w in rt for w in ("they", "candidate", "withdr"))
        if bucket == "rejected" and c["theirs"] and dates["offer_out"]:
            bucket = c["bucket"] = "declined_offer"  # the candidate turned the offer down
        lvl = io.LEVEL.get(bucket) if bucket in io.LEVEL else None
        if bucket == "declined_offer":
            lvl = io.LEVEL["offer"]
        furthest = io.classify_stage(r.get("furthest_stage", ""), stage_map)
        if furthest in io.LEVEL:
            lvl = max(lvl if lvl is not None else -1, io.LEVEL[furthest])
        if lvl is None and bucket in io.TERMINAL and hist and hist["level_first"]:
            lvl = max(hist["level_first"])
            c["inferred"].append("furthest stage from snapshots")
        if dates["offer_out"] and (lvl is None or lvl < io.LEVEL["offer"]):
            lvl = io.LEVEL["offer"]  # an offer went out, so the offer stage was reached
        c["level"] = lvl
        if bucket in io.TERMINAL and lvl is None:
            hygiene["closed_no_furthest_stage"].append(f"line {r['_line']}: {name}")
        # days in stage
        dis, basis = None, None
        if r.get("days_in_stage", "").strip().isdigit():
            dis, basis = int(r["days_in_stage"]), "tracker days_in_stage"
        elif dates["stage_entered"]:
            dis, basis = (today - dates["stage_entered"]).days, "stage_entered_on"
        elif hist and hist["bucket_since"] and hist["bucket_since"][0] == bucket:
            dis, basis = (today - hist["bucket_since"][1]).days, "snapshots (INFERENCE)"
        c["days_in_stage"], c["days_basis"] = dis, basis
        if dates["accepted"] and dates["entry"] and dates["accepted"] < dates["entry"]:
            hygiene["accepted_before_entry"].append(f"line {r['_line']}: {name}")
        if not c["reason"] and bucket in io.TERMINAL and r.get("notes"):
            c["reason"] = r["notes"]  # Sofia's tracker keeps the pass/withdraw reason in notes
        cands.append(c)
    for (name, role), k in seen.items():
        if k > 1 and name:
            hygiene["duplicates"].append(f"{name} / {role} x{k} (counted once: furthest stage kept; owner merges)")
    return dedupe(cands)


def dedupe(cands):
    """One entry per (name, role): duplicate rows are listed in hygiene, not
    counted twice. Keep the furthest level, then the latest stage date, then
    the later tracker line. Rows with no name are kept as they are."""
    def rank(c):
        return (c["level"] if c["level"] is not None else -1, c["stage_entered"] or dt.date.min, c["line"])
    out, where = [], {}
    for c in cands:
        key = (c["name"].strip().lower(), c["role"].strip().lower())
        if not key[0]:
            out.append(c)
            continue
        if key in where:
            if rank(c) > rank(out[where[key]]):
                out[where[key]] = c
            continue
        where[key] = len(out)
        out.append(c)
    return out


def fold(text):
    """Lower case without accents: 'Zoë Ångström' -> 'zoe angstrom'."""
    return "".join(ch for ch in unicodedata.normalize("NFKD", text or "") if not unicodedata.combining(ch)).lower()


COST_AMOUNT = re.compile(r"-?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d{1,2})?")


def funnel_counts(cohort):
    reached = [0] * len(io.LADDER)
    unknown_closed = 0
    for c in cohort:
        if c["level"] is None:
            if c["bucket"] in io.TERMINAL:
                unknown_closed += 1
                reached[0] += 1
            continue
        for lvl in range(c["level"] + 1):
            reached[lvl] += 1
    conv = []
    for i in range(len(io.LADDER) - 1):
        conv.append(round(reached[i + 1] / reached[i] * 100, 1) if reached[i] else None)
    return reached, conv, unknown_closed


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for flag in ("--tracker", "--candidates", "--roles", "--loops", "--shortlist", "--outreach", "--hires",
                 "--costs", "--hm-survey", "--history", "--stage-map", "--prefs", "--window", "--role", "--out",
                 "--offers"):
        ap.add_argument(flag)
    ap.add_argument("--prior", default="auto")
    ap.add_argument("--today")
    ap.add_argument("--date-order", choices=["dayfirst", "monthfirst"])
    ap.add_argument("--cph-variant", default="standard", choices=["standard", "comparable"])
    for key in ("min-sample", "touch-limit", "attrition-window-days", "heavy-day-per-interviewer"):
        ap.add_argument(f"--{key}", type=int)
    ap.add_argument("--stalled-bar")
    a = ap.parse_args(argv)
    order = a.date_order
    today = io.parse_date(a.today) if a.today else dt.date.today()
    if today is None:
        print(f"error: --today '{a.today}' is not a date; use YYYY-MM-DD", file=sys.stderr)
        return 2
    prefs = io.read_prefs(a.prefs)
    settings, settings_src = {}, {}
    for key, default in DEFAULTS.items():
        cli = getattr(a, key, None)
        if cli is not None:
            settings[key], settings_src[key] = cli, "argument"
        elif key in prefs:
            settings[key], settings_src[key] = prefs[key], "preferences.md"
        else:
            settings[key], settings_src[key] = default, "default - confirm with the owner"
    for key in ("min_sample", "touch_limit", "attrition_window_days", "heavy_day_per_interviewer"):
        try:
            settings[key] = int(str(settings[key]).split()[0])
        except ValueError:
            settings[key], settings_src[key] = DEFAULTS[key], "default - confirm with the owner"
    if not re.match(r"\s*\d+", str(settings["stalled_bar"])):
        settings_src["stalled_bar"] = (f"default - could not read '{settings['stalled_bar']}' "
                                       f"({settings_src['stalled_bar']}); confirm with the owner")
        settings["stalled_bar"] = DEFAULTS["stalled_bar"]
    bar_n, bar_kind = io.parse_stalled_bar(str(settings["stalled_bar"]))
    cadence = [int(x) for x in str(settings["outreach_cadence"]).replace("/", ",").split(",") if x.strip().isdigit()] or [2, 5, 8]
    day_kind = "calendar" if str(settings["outreach_day_kind"]).strip().lower().startswith("cal") else "business"

    try:
        window = parse_window(a.window, order)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    prior = None
    if window and a.prior == "auto":
        length = (window[1] - window[0]).days + 1
        prior = (window[0] - dt.timedelta(days=length), window[0] - dt.timedelta(days=1))
    elif a.prior not in ("auto", "none"):
        prior = parse_window(a.prior, order)

    tdir = a.tracker or ""
    path = lambda override, name: override or (os.path.join(tdir, name) if tdir else None)  # noqa: E731
    dropped = []
    cand_rows = io.read_csv(path(a.candidates, "candidates.csv"), dropped)
    if not cand_rows:
        print("error: no candidate rows found. Pass --tracker DIR or --candidates FILE "
              "(an export normalised with normalize_export.py).", file=sys.stderr)
        return 2
    role_rows = io.read_csv(path(a.roles, "roles.csv"), dropped)
    loop_rows = io.read_csv(path(a.loops, "loops.csv"), dropped)
    shortlist = io.read_csv(a.shortlist, dropped)
    outreach = io.read_csv(a.outreach, dropped)
    hires = io.read_csv(a.hires, dropped)
    costs = io.read_csv(a.costs, dropped)
    survey = io.read_csv(a.hm_survey, dropped)
    stage_map = io.load_stage_map(a.stage_map)
    history = load_history(a.history)

    hygiene = defaultdict(list)
    cands = build_candidates(cand_rows, stage_map, order, today, history, hygiene)
    if a.role:
        cands = [c for c in cands if c["role"].lower() == a.role.lower()]
    prospects = [c for c in cands if c["bucket"] == "prospect"]
    pipeline = [c for c in cands if c["bucket"] not in ("prospect", None)]
    has_entry = any(c["entry_real"] for c in pipeline)
    entry_inferred = any("entry date = first snapshot seen" in c["inferred"] for c in pipeline)

    def cohort_for(win):
        if win is None or not has_entry:
            return pipeline
        return [c for c in pipeline if in_window(c["entry_real"], win)]

    report = {"as_of": today.isoformat(), "window": [d.isoformat() for d in window] if window else None,
              "prior": [d.isoformat() for d in prior] if prior else None,
              "settings": {k: {"value": settings[k], "source": settings_src[k]} for k in settings},
              "dropped_columns": dropped, "roles": {}, "overall": {}, "hygiene": {}, "banners": []}
    if dropped:
        report["banners"].append("Protected columns dropped before any number was computed: " + ", ".join(dropped))
    if window and not has_entry:
        report["banners"].append("No entry dates (applied_on / sourced_on) in the tracker: the funnel covers every row "
                                 "in the tracker, not the window. Window comparisons come from snapshots only.")
    if entry_inferred:
        report["banners"].append("Some entry dates come from the first snapshot a person appeared in; they are used "
                                 "only for time to hire, labelled INFERENCE (accurate to the snapshot interval).")
    no_entry = [c for c in pipeline if not c["entry_real"]] if window and has_entry else []
    if no_entry:
        report["banners"].append(f"{len(no_entry)} rows have no entry date and are outside every window (UNKNOWN).")

    roles = sorted({c["role"] for c in pipeline}, key=lambda r: sum(1 for c in pipeline if c["role"] == r))
    role_info = {r.get("role", "").lower(): r for r in role_rows}
    label_counts = "FACT"
    prev_snap = None
    if a.history and not has_entry:
        snaps = sorted(f for f in glob.glob(os.path.join(a.history, "*-snapshot.json"))
                       if os.path.basename(f)[:10] < today.isoformat())
        if snaps:
            with open(snaps[-1], encoding="utf-8") as fh:
                prev_snap = json.load(fh)
            report["banners"].append(f"Prior column = previous snapshot of {prev_snap['as_of']} (same all-rows basis).")

    past_offers = {}

    def section(members_all, role_name=None):
        ids = {id(c) for c in members_all}
        coh = [c for c in cohort_for(window) if id(c) in ids]
        coh_prior = [c for c in cohort_for(prior) if id(c) in ids] if prior and has_entry else None
        reached, conv, unknown_closed = funnel_counts(coh)
        sec = {"cohort_n": len(coh), "funnel": {}, "conversion_pct": {}, "pipeline_now": {}}
        for i, stage in enumerate(io.LADDER):
            sec["funnel"][stage] = num(reached[i], label_counts, len(coh), "reached this stage or beyond")
        for i in range(len(io.LADDER) - 1):
            lab = "FACT" if unknown_closed == 0 and label_counts == "FACT" else "INFERENCE"
            basis = "reached next / reached this"
            if unknown_closed:
                basis += f"; {unknown_closed} closed rows with unknown furthest stage counted at entry only (lower bound)"
            if any(c["bucket"] not in io.TERMINAL and c["bucket"] != "hired" for c in coh):
                basis += "; open cohort - still-active people may convert later"
            sec["conversion_pct"][f"{io.LADDER[i]}->{io.LADDER[i + 1]}"] = num(conv[i], lab, reached[i], basis)
        if coh_prior is not None:
            pr, pc, _ = funnel_counts(coh_prior)
            sec["prior_funnel"] = {s: pr[i] for i, s in enumerate(io.LADDER)}
            sec["prior_conversion_pct"] = {f"{io.LADDER[i]}->{io.LADDER[i + 1]}": pc[i] for i in range(len(pc))}
        elif prev_snap is not None:
            psec = prev_snap["overall"] if role_name is None else prev_snap.get("roles", {}).get(role_name)
            if psec:
                sec["prior_funnel"] = {s: psec["funnel"][s]["value"] for s in io.LADDER if s in psec["funnel"]}
                sec["prior_conversion_pct"] = {k: v["value"] for k, v in psec["conversion_pct"].items()}
        for b in io.LADDER + sorted(io.TERMINAL):
            sec["pipeline_now"][b] = sum(1 for c in members_all if c["bucket"] == b)
        # biggest loss
        # the stage losing the most people = most closed (rejected/withdrew/declined) at that furthest stage
        lost_at = Counter(c["level"] for c in coh if c["bucket"] in io.TERMINAL and c["level"] is not None)
        if lost_at:
            idx, k = sorted(lost_at.items(), key=lambda kv: (-kv[1], conv[kv[0]] if kv[0] < len(conv) and conv[kv[0]] is not None else 101))[0]
            lost = [c for c in coh if c["bucket"] in io.TERMINAL and c["level"] == idx]
            reasons = Counter((c["reason"] or "no reason recorded") for c in lost).most_common(2)
            nxt = io.LADDER[idx + 1] if idx + 1 < len(io.LADDER) else "hired"
            sec["biggest_loss"] = {"step": f"{io.LADDER[idx]}->{nxt}", "lost": k,
                                   "conversion_pct": conv[idx] if idx < len(conv) else None,
                                   "top_reasons": reasons, "label": "FACT"}
        # pacing
        hired = [c for c in members_all if c["bucket"] == "hired" and in_window(c["accepted"], window)]
        tth, artefacts = [], []
        for c in hired:
            if c["accepted"] and c["entry"]:
                d = (c["accepted"] - c["entry"]).days
                (tth if d > 0 else artefacts).append(d if d > 0 else f"{c['name']}: {d} days")
        lab_tth = "INFERENCE" if any(c["inferred"] for c in hired) else "FACT"
        sec["time_to_hire_days"] = num({"median": median(tth), "min": min(tth) if tth else None,
                                        "max": max(tth) if tth else None} if tth else None,
                                       lab_tth if tth else "UNKNOWN", len(tth),
                                       "entry (applied/sourced) -> accepted" + ("" if tth else "; no hire with both dates"))
        ttf = []
        for c in hired:
            opened = io.parse_date(io.first(role_info.get(c["role"].lower(), {}), "opened_on", "open_date", "req_opened_on"), order)
            if opened and c["accepted"]:
                d = (c["accepted"] - opened).days
                (ttf if d > 0 else artefacts).append(
                    d if d > 0 else f"{c['name']}: fill {d} days"
                    + (" (hired the day the opening opened: Greenhouse's zero-day case [84])" if d == 0 else ""))
        evergreen = any(io.truthy(role_info.get(c["role"].lower(), {}).get("evergreen")) for c in hired) or             len({c["name"].lower() for c in hired if c["role"] == (role_name or c["role"])}) > 1 and role_name is not None
        sec["time_to_fill_days"] = num({"median": median(ttf), "min": min(ttf), "max": max(ttf)} if ttf else None,
                                       ("INFERENCE" if evergreen else "FACT") if ttf else "UNKNOWN", len(ttf),
                                       "opening open date -> accepted" + ("" if ttf else "; no opening open date or no hire")
                                       + ("; EVERGREEN/multi-hire opening: the open date is the req's, not each hire's - unreliable" if evergreen and ttf else ""))
        if artefacts:
            hygiene["zero_or_negative_durations"].extend(artefacts)
        if role_name:
            ri = role_info.get(role_name.lower(), {})
            o, s = io.parse_date(io.first(ri, "opened_on", "open_date"), order), io.parse_date(io.first(ri, "slate_ready_on"), order)
            sec["time_to_slate_days"] = num((s - o).days if o and s else None, "FACT" if o and s else "UNKNOWN", None,
                                            "opened_on -> slate_ready_on (roles.csv)")
            if (ri.get("stage") or "open").strip().lower() == "open":
                sec["req_age_days"] = num((today - o).days if o else None, "FACT" if o else "UNKNOWN", None,
                                          "today - opened_on (roles.csv), open req" if o
                                          else "no opened_on in roles.csv; ask the owner when the req opened")
            if sum(1 for c in members_all if c["bucket"] == "hired") > 1 or io.truthy(ri.get("evergreen")):
                hygiene["evergreen_or_multi_hire_roles"].append(role_name)
        # stuck
        active = [c for c in members_all if c["bucket"] in ("entered", "screened", "in_loop", "offer")]
        def over_bar(c):
            if c["days_in_stage"] is None:
                return False
            if bar_kind == "business" and c["days_basis"] != "tracker days_in_stage":
                since = today - dt.timedelta(days=c["days_in_stage"])
                return io.business_days(since, today) > bar_n
            return c["days_in_stage"] > bar_n
        stuck = sorted([c for c in active if over_bar(c)], key=lambda c: -c["days_in_stage"])
        unknown_days = sum(1 for c in active if c["days_in_stage"] is None)
        sec["stalled"] = num(len(stuck), "UNKNOWN" if active and unknown_days == len(active) else "FACT", len(active),
                             f"days in stage over the bar ({bar_n} {bar_kind} days)"
                             + (f"; days in stage unknown for {unknown_days}" if unknown_days else ""))
        sec["oldest_stuck"] = [{"name": c["name"], "role": c["role"], "stage": c["stage"], "days": c["days_in_stage"],
                                "owner": c["owner"], "waiting_on": c["waiting_on"], "basis": c["days_basis"]} for c in stuck[:5]]
        if active and all(over_bar(c) for c in active):
            sec["no_movement"] = True
        sec["days_in_stage_unknown"] = sum(1 for c in active if c["days_in_stage"] is None)
        # mix and quality
        sec["source_mix"] = dict(Counter(c["source"] for c in coh).most_common())
        sec["source_of_hire"] = dict(Counter(c["source"] for c in hired).most_common())
        resolved = [c for c in members_all if c["bucket"] in ("hired", "declined_offer")
                    and in_window(c["resolved"] or c["accepted"] or c["offer_out"], window)]
        acc = sum(1 for c in resolved if c["bucket"] == "hired")
        sec["offer_acceptance_pct"] = num(round(acc / len(resolved) * 100, 1) if resolved else None,
                                          "FACT" if resolved else "UNKNOWN", len(resolved),
                                          "accepted / (accepted + declined), offers resolved in window (offer date when no resolution date)")
        open_offers = [c for c in members_all if c["bucket"] == "offer"]
        sec["offers_open"] = len(open_offers)
        for c in open_offers:
            if c["answer_by"] and c["answer_by"] < today:
                past_offers[(c["name"].lower(), c["role"].lower())] = {
                    "name": c["name"], "role": c["role"], "date": c["answer_by"], "owner": None, "plan": None}
        ours = Counter(c["reason"] or "no reason recorded" for c in coh if c["bucket"] == "rejected" and not c["theirs"])
        theirs = Counter(c["reason"] or "no reason recorded" for c in coh if c["bucket"] in io.TERMINAL and c["theirs"])
        sec["reasons"] = {"we_rejected": ours.most_common(5), "they_withdrew_or_declined": theirs.most_common(5)}
        return sec

    for r in roles:
        report["roles"][r] = section([c for c in pipeline if c["role"] == r], r)
    report["overall"] = section(pipeline)
    report["overall"]["prospects_excluded"] = len(prospects)
    n = report["overall"]["cohort_n"]
    if n < settings["min_sample"]:
        report["banners"].append(f"SMALL SAMPLE: {n} people in the cohort, below the minimum of {settings['min_sample']} "
                                 f"({settings_src['min_sample']}). Read every rate as directional, not truth.")

    # loops: scorecards overdue, next-week load
    next_mon = today + dt.timedelta(days=(7 - today.weekday()) % 7 or 7)
    load = defaultdict(Counter)
    for lp in loop_rows:
        d = io.parse_date(lp.get("date", ""), order)
        cards = (lp.get("scorecards") or io.first(lp, "scorecards_in_or_out")).strip().lower()
        if d and d < today - dt.timedelta(days=1) and lp.get("status", "").lower() not in ("cancelled", "canceled"):
            done = cards in ("in", "all in", "filed", "yes", "done", "complete", "all")
            if "/" in cards:
                x, _, y = cards.partition("/")
                done = x.strip().isdigit() and y.strip().isdigit() and int(x) >= int(y)
            if not done:
                hygiene["scorecards_overdue"].append(f"{lp.get('candidate')} ({lp.get('role')}) {d}: scorecards '{cards or 'blank'}'")
        if d and next_mon <= d <= next_mon + dt.timedelta(days=6):
            for who in [w.strip() for w in lp.get("interviewers", "").replace(";", ",").replace("/", ",").split(",") if w.strip()]:
                load[d.isoformat()][who] += 1
    report["next_week_load"] = {day: dict(c) for day, c in sorted(load.items())}
    report["heavy_days"] = [f"{day}: {who} x{k}" for day, c in sorted(load.items()) for who, k in c.items()
                            if k >= settings["heavy_day_per_interviewer"]]
    for c in pipeline:
        if c["bucket"] in ("entered", "screened", "in_loop", "offer") and not c["next_step"]:
            hygiene["no_next_step"].append(f"{c['name']} ({c['role']}, {c['stage']})")

    # sourcing
    new_src = defaultdict(list)
    for s in shortlist:
        d = io.parse_date(io.first(s, "date_added", "added_on", "date"), order)
        if in_window(d, window) and d is not None:
            new_src[s.get("role", "")].append(s)
    report["sourcing"] = {}
    for role_name, items in new_src.items():
        linked = [s for s in items if s.get("source_url")]
        def tier_key(s):
            t = s.get("tier", "")
            return (0, int(t)) if t.isdigit() else (1, t.lower())
        report["sourcing"][role_name] = {
            "added": num(len(items), "FACT", None, "shortlist rows with date_added in window"),
            "first_three_by_recorded_tier": [{"name": s.get("name"), "tier": s.get("tier"), "reason": s.get("reason"),
                                              "link": s.get("source_url")} for s in sorted(linked, key=tier_key)[:3]],
            "without_link": len(items) - len(linked)}

    # outreach
    by_person, shown = defaultdict(list), {}
    known_status = {"sent", "replied", "declined", "drafted"}
    for o in outreach:
        o = dict(o, status=(o.get("status") or "").strip().lower(),
                 reply_type=(o.get("reply_type") or "").strip().lower())
        key = (o.get("candidate", "").strip().lower(), o.get("role", "").strip().lower())
        shown.setdefault(key, (o.get("candidate", "").strip(), o.get("role", "").strip()))
        if o["status"] not in known_status:
            hygiene["outreach_unknown_status"].append(
                f"line {o['_line']}: {o.get('candidate') or '?'} status '{o['status'] or 'blank'}' "
                "(expected sent, replied, declined or drafted) - not counted")
        by_person[key].append(o)
    contacted, types, due = 0, Counter(), []
    if settings["touch_limit"] != len(cadence):
        hygiene["outreach_cadence_mismatch"].append(
            f"touch_limit {settings['touch_limit']} but outreach_cadence has {len(cadence)} days "
            f"({','.join(map(str, cadence))}): a follow-up with no cadence day is listed, not dropped; "
            "align the two in preferences.md")
    for key, touches in by_person.items():
        cand, role_name = shown[key]
        sent = [t for t in touches if t.get("status") in ("sent", "replied", "declined")]
        drafted = [t for t in touches if t.get("status") == "drafted"]
        if not sent:
            if drafted:
                due.append(f"{cand} ({role_name}): touch 1 drafted, not confirmed sent - confirm before drafting again")
            continue
        notnow = [t for t in touches if t.get("reply_type") == "not-now"]
        if notnow:
            cb = io.parse_date(notnow[-1].get("check_back_date", ""), order)
            # once: a touch dated on or after the check-back date means it was used
            used = cb and any((io.parse_date(t.get("date", ""), order) or dt.date.min) >= cb for t in touches)
            if cb and not used and cb <= today:
                due.append(f"{cand} ({role_name}): check-back date {cb} reached (not-now reply) - "
                           "one check-back note, then stop unless they re-engage")
        first_sent = min((io.parse_date(t.get("date", ""), order) for t in sent if io.parse_date(t.get("date", ""), order)), default=None)
        if window and not in_window(first_sent, window):
            pass
        else:
            contacted += 1
            rtypes = [t.get("reply_type") for t in touches if t.get("reply_type") and t.get("reply_type") != "none"]
            types[rtypes[-1] if rtypes else "no reply"] += 1
        replied = any(t.get("status") in ("replied", "declined") for t in touches)
        k = max((int(t["touch"]) for t in sent if t.get("touch", "").isdigit()), default=len(sent))
        if not replied and first_sent:
            # touch_limit counts follow-ups after the first note (passive-candidate-outreach):
            # with the default 3 the sequence is complete after touch 1 + 3 = 4.
            if k >= 1 + settings["touch_limit"]:
                hygiene["outreach_sequence_complete"].append(
                    f"{cand} ({role_name}): first note + {k - 1} follow-ups, no reply - sequence complete, stop")
            elif k - 1 < len(cadence):
                nxt = add_outreach_days(first_sent, cadence[k - 1], day_kind)
                if nxt <= today:
                    late = io.business_days(nxt, today)
                    drafted_already = any(t.get("touch") == str(k + 1) for t in drafted)
                    due.append(f"{cand} ({role_name}): touch {k + 1} due {nxt}"
                               + (f", {late} working days late" if late else " (today)")
                               + ("; draft already in the log - confirm it was sent, do not draft again"
                                  if drafted_already else ""))
            else:
                due.append(f"{cand} ({role_name}): touch {k + 1} has no cadence day "
                           f"(outreach_cadence {','.join(map(str, cadence))}, touch_limit {settings['touch_limit']}) - "
                           "owner decides; fix preferences.md")
    report["outreach"] = {"contacted": num(contacted, "FACT", None, "people with a sent touch (first touch in window)"),
                          "reply_types": dict(types), "followups_due": due,
                          "cadence": None if not outreach else f"touches on day {','.join(map(str, cadence))} after the first note, "
                                     f"{day_kind} days, first note + {settings['touch_limit']} follow-ups "
                                     "(passive-candidate-outreach's rule; drafts come from that skill)",
                          "note": "A 'response' that says not interested is not a positive reply; rates are split by reply type."}

    # attrition, cost per hire, HM satisfaction
    win_days = settings["attrition_window_days"]
    eligible, early, reasons = 0, 0, Counter()
    for h in hires:
        start, left = io.parse_date(h.get("start_on", ""), order), io.parse_date(h.get("left_on", ""), order)
        if start and left and left < start:
            hygiene["left_before_start"].append(f"line {h['_line']}: {h.get('name') or '?'} left_on {left} is before "
                                                f"start_on {start} - fix the dates; not counted")
            continue
        if start and start + dt.timedelta(days=win_days) <= today:
            eligible += 1
            if left and (left - start).days <= win_days:
                early += 1
                reasons[h.get("exit_reason") or "no exit note"] += 1
    report["early_attrition"] = num({"left": early, "eligible": eligible, "pct": round(early / eligible * 100, 1)} if eligible else None,
                                    "FACT" if eligible else "UNKNOWN", eligible,
                                    f"left within {win_days} days of start ({settings_src['attrition_window_days']})")
    report["early_attrition_reasons"] = dict(reasons)
    hires_in_window = report["overall"]["funnel"]["hired"]["value"] if not window else \
        sum(1 for c in pipeline if c["bucket"] == "hired" and in_window(c["accepted"], window))
    if costs:
        lines, total, currencies, estimated, unreadable = [], 0.0, set(), [], 0
        for c in costs:
            raw = (c.get("amount") or "").strip()
            if not COST_AMOUNT.fullmatch(raw):
                hygiene["bad_cost_line"].append(
                    f"line {c['_line']}: '{raw}' - write a plain number such as 1800 or 1800.00 "
                    "(no dot or space thousands separator, no decimal comma); ask the owner")
                unreadable += 1
                continue
            amt = float(raw.replace(",", ""))
            total += amt
            currencies.add(c.get("currency", ""))
            is_est = io.truthy(c.get("estimate"))
            if is_est:
                estimated.append(c.get("line"))
            lines.append({"line": c.get("line"), "type": c.get("type"), "amount": amt, "estimate": is_est})
        if unreadable:
            report["cost_per_hire"] = num(None, "UNKNOWN", hires_in_window,
                                          f"{unreadable} cost line(s) unreadable (see hygiene: bad cost line); "
                                          "a partial total would be wrong - fix the amounts and re-run")
            report["cost_per_hire"]["lines"] = lines
        elif len(currencies) > 1:
            report["cost_per_hire"] = num(None, "UNKNOWN", hires_in_window, f"mixed currencies {sorted(currencies)}; convert first")
        else:
            report["cost_per_hire"] = num(round(total / hires_in_window, 2) if hires_in_window else None,
                                          ("INFERENCE" if estimated else "FACT") if hires_in_window else "UNKNOWN",
                                          hires_in_window,
                                          f"(internal + external) / hires, {a.cph_variant} variant, {''.join(currencies)}"
                                          + (f"; includes owner estimates: {'; '.join(estimated)}" if estimated else ""))
            report["cost_per_hire"]["lines"] = lines
    else:
        report["cost_per_hire"] = num(None, "UNKNOWN", None, "no cost lines supplied by the owner")
    if survey:
        scores = []
        for s in survey:
            try:
                scores.append(float(s["score"]) / float(s.get("scale_max") or 5) * 100)
            except (KeyError, ValueError, ZeroDivisionError):
                continue
        report["hm_satisfaction_pct_of_max"] = num(round(sum(scores) / len(scores), 1) if scores else None,
                                                   "FACT" if scores else "UNKNOWN", len(scores), "owner-supplied survey")
    for plan in sorted(glob.glob(os.path.join(a.offers, "*", "close-plan.csv"))) if a.offers else []:
        for row in io.read_csv(plan):
            due = io.parse_date(row.get("due_date", ""))
            if re.search(r"answer[- ]by", row.get("track", ""), re.I) and row.get("status", "open").lower() in ("open", "blocked") \
                    and due and due < today:
                slug = os.path.basename(os.path.dirname(plan))
                slug_tokens = set(re.split(r"[^a-z0-9]+", fold(slug)))
                # the same offer from the tracker row and its close plan: one entry, close-plan owner kept
                match = next((k for k, v in past_offers.items() if v["date"] == due and not v["plan"]
                              and set(t for t in re.split(r"[^a-z0-9]+", fold(v["name"])) if len(t) > 1) & slug_tokens),
                             None)
                if match:
                    past_offers[match].update(owner=row.get("owner") or None, plan=slug)
                else:
                    past_offers[("", slug)] = {"name": None, "role": None, "date": due,
                                               "owner": row.get("owner") or None, "plan": slug}
    for v in past_offers.values():
        who = f"{v['name']} ({v['role']})" if v["name"] else v["plan"]
        extra = (f", owner {v['owner'] or '?'}" if v["plan"] else "") + \
            (f" (close plan {v['plan']})" if v["plan"] and v["name"] else "")
        hygiene["offers_past_answer_by"].append(f"{who}: answer-by {v['date']}{extra}")
    hygiene["unmapped_stage"] = sorted(set(hygiene["unmapped_stage"]))
    for key in list(hygiene):
        hygiene[key] = list(dict.fromkeys(hygiene[key]))  # sections run per role and overall: dedupe
    report["hygiene"] = {k: v for k, v in hygiene.items() if v}
    report["hygiene"]["prospects_excluded_from_applicant_counts"] = len(prospects)

    report["candidates"] = [  # internal state for snapshots; never shared
        {"name": c["name"], "role": c["role"], "role_family": c["role_family"] or c["role"], "stage": c["stage"],
         "bucket": c["bucket"], "level": c["level"], "days_in_stage": c["days_in_stage"], "owner": c["owner"],
         "source": c["source"], "entry": c["entry"].isoformat() if c["entry"] else None,
         "accepted": c["accepted"].isoformat() if c["accepted"] else None,
         "resolved": c["resolved"].isoformat() if c["resolved"] else None,
         "offer_out": c["offer_out"].isoformat() if c["offer_out"] else None} for c in cands]
    out = a.out or "."
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, default=str)
    md = render_md(report)
    with open(os.path.join(out, "report.md"), "w", encoding="utf-8") as fh:
        fh.write(md)
    print(md)
    return 0


def fmt(x):
    if not isinstance(x, dict):
        return str(x)
    v = x["value"]
    if isinstance(v, dict):
        v = ", ".join(f"{k} {w}" for k, w in v.items() if w is not None)
    return f"{'-' if v is None else v} [{x['label']}{', n=' + str(x['n']) if x.get('n') is not None else ''}]"


def render_md(r):
    out = [f"# Pipeline read (INTERNAL: names candidates; share only via share_safe.py), as of {r['as_of']}" + (f" (window {r['window'][0]} to {r['window'][1]}"
           + (f", prior {r['prior'][0]} to {r['prior'][1]})" if r['prior'] else ")") if r['window'] else "")]
    out += [f"> {b}" for b in r["banners"]]
    for name, sec in list(r["roles"].items()) + [("All roles", r["overall"])]:
        out += ["", f"## {name}", "", "| Stage | Reached | Prior | Conversion to next |", "|---|---|---|---|"]
        convs = list(sec["conversion_pct"].values())
        for i, stage in enumerate(sec["funnel"]):
            prior = sec.get("prior_funnel", {}).get(stage, "-")
            conv = fmt(convs[i]) if i < len(convs) else ""
            out.append(f"| {stage} | {fmt(sec['funnel'][stage])} | {prior} | {conv} |")
        if sec.get("biggest_loss"):
            bl = sec["biggest_loss"]
            out.append(f"\nBiggest loss: {bl['step']}, closed there: {bl['lost']} (conversion {bl['conversion_pct']}%); top reasons: "
                       + "; ".join(f"{k} ({v})" for k, v in bl["top_reasons"]) + f" [{bl['label']}]")
        out.append("Pipeline now: " + ", ".join(f"{k} {v}" for k, v in sec["pipeline_now"].items() if v))
        out.append(f"Time to hire: {fmt(sec['time_to_hire_days'])}. Time to fill: {fmt(sec['time_to_fill_days'])}."
                   + (f" Time to slate: {fmt(sec['time_to_slate_days'])}." if "time_to_slate_days" in sec else ""))
        out.append(f"Offer acceptance: {fmt(sec['offer_acceptance_pct'])}; offers open: {sec['offers_open']}.")
        out.append(f"Source mix: {sec['source_mix']}. Source of hire: {sec['source_of_hire'] or 'none in window'}.")
        out.append(f"Reasons - we rejected: {sec['reasons']['we_rejected']}; they withdrew/declined: {sec['reasons']['they_withdrew_or_declined']}.")
        if "req_age_days" in sec:
            out.append(f"Req age (open req): {fmt(sec['req_age_days'])} days ({sec['req_age_days']['basis']}).")
        out.append(f"Stalled: {fmt(sec['stalled'])} ({sec['stalled']['basis']})" + (" - NO MOVEMENT in this role" if sec.get("no_movement") else ""))
        for s in sec["oldest_stuck"]:
            out.append(f"- {s['name']} ({s['stage']}): {s['days']} days, owner {s['owner'] or '?'}, waiting on {s['waiting_on'] or '?'}")
    out += ["", "## Quality", f"Early attrition: {fmt(r['early_attrition'])} {r['early_attrition_reasons'] or ''}",
            f"Cost per hire: {fmt(r['cost_per_hire'])} - {r['cost_per_hire']['basis']}"]
    out += [f"- cost line: {x['line']} ({x['type']}) {x['amount']:,.2f}" + (" [ESTIMATE]" if x.get("estimate") else "")
            for x in r["cost_per_hire"].get("lines", [])]
    if "hm_satisfaction_pct_of_max" in r:
        out.append(f"Hiring-manager satisfaction: {fmt(r['hm_satisfaction_pct_of_max'])}")
    out += ["", "## Sourcing and outreach"]
    for role_name, s in r["sourcing"].items():
        out.append(f"- {role_name}: {fmt(s['added'])} added; first three by recorded tier: "
                   + "; ".join(f"{x['name']} (tier {x['tier']}) {x['link']}" for x in s["first_three_by_recorded_tier"]))
    o = r["outreach"]
    out.append(f"Outreach: {fmt(o['contacted'])} contacted; reply types {o['reply_types']}.")
    out += [f"- follow-up due: {d}" for d in o["followups_due"]]
    if o.get("cadence"):
        out.append(f"Cadence: {o['cadence']}.")
    out += ["", "## Hygiene (each needs one fixing action)"]
    for k, v in r["hygiene"].items():
        if isinstance(v, list):
            out.append(f"- {k.replace('_', ' ')}: {len(v)}" + (": " + "; ".join(map(str, v[:8])) if v else ""))
        else:
            out.append(f"- {k.replace('_', ' ')}: {v}")
    out += ["", "## Next week's interview load"]
    out += [f"- {day}: " + ", ".join(f"{w} {k}" for w, k in c.items()) for day, c in r["next_week_load"].items()] or ["- none booked"]
    out += [f"- HEAVY: {h}" for h in r["heavy_days"]]
    out += ["", "Settings: " + "; ".join(f"{k}={v['value']} ({v['source']})" for k, v in r["settings"].items())]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    sys.exit(main())
