#!/usr/bin/env python3
"""Draw a bridge chart (prior operating result -> current) from pl_variance.json. Optional.

Needs matplotlib. If it is missing, try `pip install --user matplotlib`; if that
fails, skip the chart: the table in the brief is complete without it.

    cd ~/skills/monthly-profit-and-loss-summary && python3 scripts/pl_chart.py \
        --pl /home/user/out/pl/2026-04/pl_variance.json --out /home/user/out/pl/2026-04/bridge.png

The title always carries entity, period, basis, currency and DRAFT. The chart
uses only figures already in pl_variance.json (one basis by construction), and
refuses a file without a prior period.
"""

import argparse
import json
import sys
from decimal import Decimal


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--pl", required=True)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    with open(a.pl, encoding="utf-8") as fh:
        res = json.load(fh)
    if not res.get("prior_period"):
        print("error: no prior period in this file; a bridge needs two periods", file=sys.stderr)
        return 2
    if res.get("unmapped_prior"):
        print("error: the prior period has unmapped accounts, so the subtotal changes are not measurable; no bridge",
              file=sys.stderr)
        return 2
    try:
        import matplotlib  # type: ignore
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # type: ignore
    except ImportError:
        print("matplotlib not available: chart skipped. Run 'pip install --user matplotlib' to enable it.")
        return 0
    st = {r["line"]: r for r in res["subtotals"]}
    steps = [("Revenue", Decimal(st["revenue"]["change"])),
             ("Direct costs", -Decimal(st["direct_costs"]["change"])),
             ("Operating expenses", -Decimal(st["operating_expenses"]["change"]))]
    start = Decimal(st["operating_result"]["prior"])
    end = Decimal(st["operating_result"]["current"])
    labels = [f"Operating result\n{res['prior_period']}"] + [s[0] for s in steps] + [f"Operating result\n{res['current_period']}"]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    running = start
    ax.bar(0, float(start), color="#6b7280")
    for i, (_, d) in enumerate(steps, start=1):
        bottom = running if d >= 0 else running + d
        ax.bar(i, float(abs(d)), bottom=float(bottom), color="#2563eb" if d >= 0 else "#dc2626")
        ax.text(i, float(max(running, running + d)), f"{d:+,.0f}", ha="center", va="bottom", fontsize=9)
        running += d
    ax.bar(len(labels) - 1, float(end), color="#6b7280")
    if running != end:
        ax.text(len(labels) - 1, float(end), "check: bridge does not close", color="#dc2626", ha="center")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_title(f"DRAFT - {res.get('entity') or ''} operating result bridge, {res['prior_period']} to {res['current_period']}\n"
                 f"{res['basis']} basis, {res['currency']}; excludes unmapped items; not final accounts", fontsize=9)
    ax.axhline(0, color="black", linewidth=0.6)
    fig.tight_layout()
    fig.savefig(a.out, dpi=150)
    print(f"wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
