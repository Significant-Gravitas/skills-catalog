#!/usr/bin/env python3
"""Save this run as a dated snapshot, diff it against the last one, and draw the charts.

Usage (cd ~/skills/hiring-pipeline-analytics first; run after funnel.py):

  python3 scripts/snapshot_and_chart.py /home/user/pipeline/2026-10-09/report.json \
      --reports ~/workspace/hiring/reports [--monthly auto|yes|no] [--no-charts]

Writes:
  REPORTS/<as_of>-snapshot.json   the report.json (with per-candidate state) - internal
  OUTDIR/diff.md                  movement since the previous snapshot, new names, cleared
                                  stalls, and still-stalled items as one rollup line each
                                  with the date first reported
  OUTDIR/funnel.png               people reaching each stage (all roles; n on every bar;
                                  no candidate names) - needs matplotlib
  OUTDIR/trend.png, trend.csv     monthly: median time to hire by role family per month,
                                  from every snapshot's hires (first Friday of the month when
                                  --monthly auto), plus offer acceptance over the previous
                                  calendar month from the snapshots (accepted vs declined
                                  offers resolved in that month, one per name + role)
  OUTDIR/tables.xlsx or tables/*.csv   full tables (xlsx needs openpyxl; else CSV)
OUTDIR is the folder holding report.json. Charts and tables carry role-level numbers only.
Exit: 0 ok, 2 unreadable report.
"""

import argparse
import csv
import datetime as dt
import glob
import json
import os
import shutil
import statistics
import sys
from collections import defaultdict

INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]  # validated categorical slots 1-3 (reference palette)


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def previous_snapshot(reports, as_of):
    files = sorted(f for f in glob.glob(os.path.join(reports, "*-snapshot.json"))
                   if os.path.basename(f)[:10] < as_of)
    return (load(files[-1]), files[-1]) if files else (None, None)


def first_reported(reports, key, as_of):
    """Earliest snapshot date whose oldest_stuck lists this (name, role)."""
    for f in sorted(glob.glob(os.path.join(reports, "*-snapshot.json"))):
        if os.path.basename(f)[:10] >= as_of:
            continue
        snap = load(f)
        for sec in snap.get("roles", {}).values():
            if any((s["name"].lower(), s["role"].lower()) == key for s in sec.get("oldest_stuck", [])):
                return snap["as_of"]
    return None


def diff(cur, prev, reports):
    lines = []
    if not prev:
        return ["First snapshot: no previous run to compare with. Movement will appear from the next run."]
    pc = {(c["name"].lower(), c["role"].lower()): c for c in prev.get("candidates", [])}
    cc = {(c["name"].lower(), c["role"].lower()): c for c in cur.get("candidates", [])}
    lines.append(f"Compared with the snapshot of {prev['as_of']}.")
    moves = [(cc[k], pc[k]) for k in cc if k in pc and cc[k]["stage"] != pc[k]["stage"]]
    lines.append(f"Movement: {len(moves)} stage changes.")
    lines += [f"- {c['name']} ({c['role']}): {p['stage']} -> {c['stage']}" for c, p in moves]
    new = [cc[k] for k in cc if k not in pc]
    gone = [pc[k] for k in pc if k not in cc]
    lines.append(f"New in tracker: {len(new)}" + (": " + ", ".join(f"{c['name']} ({c['role']}{', prospect' if c.get('bucket') == 'prospect' else ''})" for c in new) if new else ""))
    if gone:
        lines.append(f"No longer in tracker: {len(gone)} (removed or merged - check before reading counts)")
    prev_stuck = {(s["name"].lower(), s["role"].lower()) for sec in prev.get("roles", {}).values() for s in sec.get("oldest_stuck", [])}
    cur_stuck = {(s["name"].lower(), s["role"].lower()): s for sec in cur.get("roles", {}).values() for s in sec.get("oldest_stuck", [])}
    cleared = prev_stuck - set(cur_stuck)
    if cleared:
        lines.append(f"Stalls cleared: {len(cleared)}")
    for key, s in cur_stuck.items():
        if key in prev_stuck:
            since = first_reported(reports, key, cur["as_of"]) or prev["as_of"]
            lines.append(f"- ROLLUP still stalled since first reported {since}: {s['name']} ({s['role']}, {s['stage']}), "
                         f"{s['days']} days, waiting on {s['waiting_on'] or '?'}")
        else:
            lines.append(f"- NEW STALL: {s['name']} ({s['role']}, {s['stage']}), {s['days']} days, owner {s['owner'] or '?'}")
    return lines


def trend(reports, cur):
    hires = {}
    for f in sorted(glob.glob(os.path.join(reports, "*-snapshot.json"))) + [None]:
        snap = cur if f is None else load(f)
        for c in snap.get("candidates", []):
            if c.get("bucket") == "hired" and c.get("accepted") and c.get("entry"):
                days = (dt.date.fromisoformat(c["accepted"]) - dt.date.fromisoformat(c["entry"])).days
                if days > 0:
                    hires[(c["name"].lower(), c["role"].lower())] = (c.get("role_family") or c["role"], c["accepted"][:7], days)
    table = defaultdict(list)
    for fam, month, days in hires.values():
        table[(fam, month)].append(days)
    return sorted((fam, month, statistics.median(v), len(v)) for (fam, month), v in table.items())


def previous_month(as_of):
    first = as_of.replace(day=1)
    last_month_end = first - dt.timedelta(days=1)
    return last_month_end.strftime("%Y-%m")


def monthly_acceptance(reports, cur, month):
    """Accepted / (accepted + declined) for offers resolved in `month` (YYYY-MM), across all snapshots
    and this run; the latest state of each name + role wins. Returns (pct or None, n, accepted)."""
    final = {}
    for f in sorted(glob.glob(os.path.join(reports, "*-snapshot.json"))) + [None]:
        snap = cur if f is None else load(f)
        for c in snap.get("candidates", []):
            final[(c["name"].lower(), c["role"].lower())] = c
    accepted = declined = 0
    for c in final.values():
        if c.get("bucket") == "hired":
            when = c.get("accepted") or c.get("resolved")
        elif c.get("bucket") == "declined_offer":
            when = c.get("resolved") or c.get("offer_out")
        else:
            continue
        if when and when[:7] == month:
            if c["bucket"] == "hired":
                accepted += 1
            else:
                declined += 1
    n = accepted + declined
    return (round(accepted / n * 100, 1) if n else None), n, accepted


def charts(cur, outdir, rows):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return ["charts skipped: matplotlib missing (pip install --user matplotlib)"]
    made = []
    funnel = cur["overall"]["funnel"]
    stages = list(funnel)
    values = [funnel[s]["value"] for s in stages]
    fig, ax = plt.subplots(figsize=(7, 3.2), dpi=150)
    y = list(range(len(stages)))[::-1]
    ax.barh(y, values, color=SERIES[0], height=0.6)
    for yi, v in zip(y, values):
        ax.text(v, yi, f"  {v}", va="center", color=INK, fontsize=9)
    ax.set_yticks(y, [s.replace("_", " ") for s in stages], color=INK2)
    ax.set_xlabel("people reaching the stage", color=INK2)
    label = funnel[stages[0]]["label"]
    small = " - small sample, directional" if any(b.startswith("SMALL SAMPLE") for b in cur.get("banners", [])) else ""
    ax.set_title(f"Hiring funnel, all roles - as of {cur['as_of']} ({label}, n={cur['overall']['cohort_n']}){small}",
                 color=INK, fontsize=10, loc="left")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "funnel.png"))
    plt.close(fig)
    made.append("funnel.png")
    if rows:
        fams = []
        for fam, *_ in rows:
            if fam not in fams:
                fams.append(fam)
        fig, axes = plt.subplots(1, min(len(fams), 3), figsize=(7, 3), dpi=150, squeeze=False)
        for i, fam in enumerate(fams[:3]):  # at most three series-slots; facet, never cycle hues
            ax = axes[0][i]
            pts = [(m, d, n) for f, m, d, n in rows if f == fam]
            ax.plot([p[0] for p in pts], [p[1] for p in pts], color=SERIES[0], linewidth=2, marker="o", markersize=5)
            for m, d, n in pts:
                ax.annotate(f"{d:g}d (n={n})", (m, d), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=7, color=INK)
            ax.set_title(fam, fontsize=9, color=INK, loc="left")
            ax.tick_params(colors=INK2, labelsize=7)
            for spine in ("top", "right"):
                ax.spines[spine].set_visible(False)
        axes[0][0].set_ylabel("median days to hire", color=INK2)
        fig.suptitle("Time to hire by role family, per month", fontsize=10, color=INK, x=0.01, ha="left")
        fig.tight_layout()
        fig.savefig(os.path.join(outdir, "trend.png"))
        plt.close(fig)
        made.append("trend.png" + (f" (first 3 of {len(fams)} families; see trend.csv)" if len(fams) > 3 else ""))
    return made


def tables(cur, outdir):
    sheets = {"funnel": [["role", "stage", "reached", "label"]]}
    for role, sec in list(cur["roles"].items()) + [("All roles", cur["overall"])]:
        for stage, x in sec["funnel"].items():
            sheets["funnel"].append([role, stage, x["value"], x["label"]])
    sheets["conversion"] = [["role", "step", "pct", "label", "basis"]]
    for role, sec in list(cur["roles"].items()) + [("All roles", cur["overall"])]:
        for step, x in sec["conversion_pct"].items():
            sheets["conversion"].append([role, step, x["value"], x["label"], x["basis"]])
    sheets["hygiene"] = [["check", "count"]] + [[k, len(v) if isinstance(v, list) else v] for k, v in cur["hygiene"].items()]
    try:
        import openpyxl  # type: ignore
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        for name, rows in sheets.items():
            ws = wb.create_sheet(name)
            for r in rows:
                ws.append(r)
        wb.save(os.path.join(outdir, "tables.xlsx"))
        return "tables.xlsx"
    except ImportError:
        tdir = os.path.join(outdir, "tables")
        os.makedirs(tdir, exist_ok=True)
        for name, rows in sheets.items():
            with open(os.path.join(tdir, f"{name}.csv"), "w", newline="", encoding="utf-8") as fh:
                csv.writer(fh).writerows(rows)
        return "tables/*.csv (openpyxl missing)"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("report")
    ap.add_argument("--reports", required=True)
    ap.add_argument("--monthly", default="auto", choices=["auto", "yes", "no"])
    ap.add_argument("--no-charts", action="store_true")
    a = ap.parse_args(argv)
    try:
        cur = load(a.report)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read {a.report}: {exc}", file=sys.stderr)
        return 2
    outdir = os.path.dirname(os.path.abspath(a.report))
    os.makedirs(a.reports, exist_ok=True)
    prev, prev_path = previous_snapshot(a.reports, cur["as_of"])
    lines = diff(cur, prev, a.reports)
    as_of = dt.date.fromisoformat(cur["as_of"])
    monthly = a.monthly == "yes" or (a.monthly == "auto" and as_of.weekday() == 4 and as_of.day <= 7)
    rows = trend(a.reports, cur) if monthly else []
    if monthly:
        with open(os.path.join(outdir, "trend.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["role_family", "month", "median_days_to_hire", "hires"])
            w.writerows(rows)
        month = previous_month(as_of)
        pct, n, accepted = monthly_acceptance(a.reports, cur, month)
        shown = "-" if pct is None else f"{pct}%"
        label = "FACT" if n else "UNKNOWN"
        lines.append(f"Monthly: offer acceptance {month}: {shown} [{label}, n={n}; {accepted} accepted of {n} "
                     f"offers resolved in {month}, from the snapshots]; time-to-hire trend rows: {len(rows)} (trend.csv)")
    with open(os.path.join(outdir, "diff.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    shutil.copyfile(a.report, os.path.join(a.reports, f"{cur['as_of']}-snapshot.json"))
    made = [] if a.no_charts else charts(cur, outdir, rows)
    tab = tables(cur, outdir)
    print("\n".join(lines))
    print(f"snapshot saved: {os.path.join(a.reports, cur['as_of'] + '-snapshot.json')}"
          + (f" (previous: {os.path.basename(prev_path)})" if prev_path else ""))
    print("files: diff.md, " + ", ".join(made + [tab]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
