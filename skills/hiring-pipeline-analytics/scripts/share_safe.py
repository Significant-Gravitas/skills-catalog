#!/usr/bin/env python3
"""Build the shareable copy of a pipeline read: role-level numbers only, no per-person line. Fails closed.

Usage (cd ~/skills/hiring-pipeline-analytics first):

  python3 scripts/share_safe.py /home/user/pipeline/<date>/report.json \
      --names ~/workspace/hiring/tracker/candidates.csv \
      [--names ~/workspace/hiring/shortlist.csv --names ~/workspace/hiring/outreach-log.csv] \
      [--allow "Ana"] [--out report-share.md]

(A report.md path is accepted too; the report.json next to it is read.)

The share copy is built from report.json, never by scrubbing report.md:
  - per role and for all roles: the funnel table and conversions with labels,
    time to hire / fill / slate, req age, offer acceptance, offers open,
    source mix, stalled count and stalled count by stage, rejection and
    withdrawal counts (no free-text reasons: with small numbers a reason
    identifies the person);
  - quality: early attrition, cost per hire, hiring-manager satisfaction;
  - sourcing and outreach as counts; hygiene as counts per check;
  - next week's interview load by day and interviewer (staff, not candidates).
No candidate name, stage-and-days line, waiting-on, reply status, link, email
or phone is emitted.

Second gate, a residue check: any first or last name of a candidate from the
--names files still in the text is listed and the script exits 1 WITHOUT
writing. An interviewer who shares a candidate's first name is passed with
--allow after you have checked each hit.
Output: report-share.md next to the input (or --out). Exit 0 clean, 1 residue, 2 bad input.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_io as io  # noqa: E402

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
URL = re.compile(r"https?://\S+|www\.\S+", re.I)


def fmt(x):
    if not isinstance(x, dict):
        return str(x)
    v = x.get("value")
    if isinstance(v, dict):
        v = ", ".join(f"{k} {w}" for k, w in v.items() if w is not None)
    n = x.get("n")
    return f"{'-' if v is None else v} [{x.get('label')}{', n=' + str(n) if n is not None else ''}]"


def build(r):
    head = f"# Hiring pipeline: role-level summary, no candidate details, as of {r['as_of']}"
    if r.get("window"):
        head += f" (window {r['window'][0]} to {r['window'][1]}"
        head += f", prior {r['prior'][0]} to {r['prior'][1]})" if r.get("prior") else ")"
    out = [head]
    out += [f"> {b}" for b in r.get("banners", [])]
    for name, sec in list(r["roles"].items()) + [("All roles", r["overall"])]:
        out += ["", f"## {name}", "", "| Stage | Reached | Prior | Conversion to next |", "|---|---|---|---|"]
        convs = list(sec["conversion_pct"].values())
        for i, stage in enumerate(sec["funnel"]):
            prior = sec.get("prior_funnel", {}).get(stage, "-")
            conv = fmt(convs[i]) if i < len(convs) else ""
            out.append(f"| {stage} | {fmt(sec['funnel'][stage])} | {prior} | {conv} |")
        if sec.get("biggest_loss"):
            bl = sec["biggest_loss"]
            out.append(f"\nBiggest loss: {bl['step']}, closed there: {bl['lost']} (conversion {bl['conversion_pct']}%) [{bl['label']}]")
        out.append("Pipeline now: " + ", ".join(f"{k} {v}" for k, v in sec["pipeline_now"].items() if v))
        out.append(f"Time to hire: {fmt(sec['time_to_hire_days'])}. Time to fill: {fmt(sec['time_to_fill_days'])}."
                   + (f" Time to slate: {fmt(sec['time_to_slate_days'])}." if "time_to_slate_days" in sec else ""))
        if "req_age_days" in sec:
            out.append(f"Req age (open req): {fmt(sec['req_age_days'])} days.")
        out.append(f"Offer acceptance: {fmt(sec['offer_acceptance_pct'])}; offers open: {sec['offers_open']}.")
        out.append(f"Source mix: {sec['source_mix']}.")
        ours = sum(k for _, k in sec["reasons"]["we_rejected"])
        theirs = sum(k for _, k in sec["reasons"]["they_withdrew_or_declined"])
        out.append(f"Closed in the cohort: we rejected {ours}; they withdrew or declined {theirs}.")
        by_stage = Counter(s.get("stage") or "?" for s in sec.get("oldest_stuck", []))
        stalled_n = sec["stalled"].get("value")
        note = "" if not by_stage else (" - by stage: " + ", ".join(f"{k} {v}" for k, v in by_stage.items())
                                        + (" (oldest five only)" if isinstance(stalled_n, int) and stalled_n > 5 else ""))
        out.append(f"Stalled: {fmt(sec['stalled'])}{note}" + (" - NO MOVEMENT in this role" if sec.get("no_movement") else ""))
    out += ["", "## Quality", f"Early attrition: {fmt(r['early_attrition'])}",
            f"Cost per hire: {fmt(r['cost_per_hire'])} - {r['cost_per_hire']['basis']}"]
    if "hm_satisfaction_pct_of_max" in r:
        out.append(f"Hiring-manager satisfaction: {fmt(r['hm_satisfaction_pct_of_max'])}")
    out += ["", "## Sourcing and outreach"]
    for role_name, s in r.get("sourcing", {}).items():
        out.append(f"- {role_name}: {fmt(s['added'])} added to the shortlist")
    o = r["outreach"]
    out.append(f"Outreach: {fmt(o['contacted'])} contacted; reply types {o['reply_types']}; "
               f"follow-ups due: {len(o['followups_due'])}; sequences complete with no reply: "
               f"{len(r['hygiene'].get('outreach_sequence_complete', []))}.")
    out += ["", "## Hygiene (counts; details are in the internal report)"]
    for k, v in r["hygiene"].items():
        out.append(f"- {k.replace('_', ' ')}: {len(v) if isinstance(v, list) else v}")
    out += ["", "## Next week's interview load"]
    out += [f"- {day}: " + ", ".join(f"{w} {k}" for w, k in c.items()) for day, c in r["next_week_load"].items()] or ["- none booked"]
    out += [f"- HEAVY: {h}" for h in r.get("heavy_days", [])]
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report", help="report.json (or report.md: the report.json beside it is read)")
    ap.add_argument("--names", action="append", default=[])
    ap.add_argument("--allow", action="append", default=[])
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    path = a.report
    if path.lower().endswith(".md"):
        path = os.path.join(os.path.dirname(os.path.abspath(path)), "report.json")
    try:
        with open(path, encoding="utf-8") as fh:
            report = json.load(fh)
        text = build(report)
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"error: cannot build the share copy from {path}: {exc}. Run funnel.py first; "
              "the share copy is built from its report.json.", file=sys.stderr)
        return 2
    if not a.names:
        print("error: pass at least one --names file (the tracker's candidates.csv).", file=sys.stderr)
        return 2
    people = set()
    for names_path in a.names:
        for row in io.read_csv(names_path):
            name = io.first(row, "name", "candidate", "candidate_name")
            if name:
                people.add(name.strip())
    for c in report.get("candidates", []):
        if c.get("name"):
            people.add(c["name"].strip())
    text = EMAIL.sub("[email removed]", text)
    text = URL.sub("[link removed]", text)

    allow = {x.lower() for x in a.allow}
    tokens = {t for name in people for t in re.split(r"[\s'-]+", name) if len(t) >= 3 and t.lower() not in allow}
    residue = []
    for n, line in enumerate(text.splitlines(), start=1):
        for t in sorted(tokens):
            if re.search(rf"(?<!\w){re.escape(t)}(?!\w)", line, flags=re.I):
                residue.append(f"line {n}: '{t}' -> {line.strip()[:100]}")
    if residue:
        print("NOT WRITTEN: possible candidate identifiers remain. Check each hit; if it is an interviewer's "
              "or hiring manager's name, rerun with --allow <token>:")
        print("\n".join(residue))
        return 1
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(path)), "report-share.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"wrote {out} (role-level only; {len(people)} candidate names checked, 0 remaining)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
