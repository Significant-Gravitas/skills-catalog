#!/usr/bin/env python3
"""Compare two P&L exports on the same basis: detail-to-total check, changes, shares, plan variance.

Python 3 standard library only. Reads CSVs, writes result files. Never edits inputs.

    cd ~/skills/monthly-profit-and-loss-summary && python3 scripts/pl_variance.py \
        --current /home/user/in/pl-2026-04.csv --current-period 2026-04 --current-basis accrual \
        --prior /home/user/in/pl-2026-03.csv --prior-period 2026-03 --prior-basis accrual \
        --currency GBP [--reported-current /home/user/in/reported-2026-04.csv] \
        [--plan /home/user/in/budget.csv] [--entity "Bramble Design Ltd"] [--source "ledger P&L export 6 May"] \
        --out /home/user/out/pl/2026-04

    python3 scripts/pl_variance.py --selftest

P&L CSV columns: account, group, amount [, basis]. Groups: revenue, direct_costs,
operating_expenses, other_income, other_expenses. A blank or other group is
UNMAPPED: listed, excluded from subtotals, and it blocks the net result line.
Amounts are as a P&L shows them: revenue and costs positive; contra items negative.
Exit 2 when the bases differ or either is unknown: the periods are not comparable.
A single period with no --prior and no --plan may have an unknown basis; it is
printed as "unknown (open)" and no comparison is made.
"""

import argparse
import csv
import json
import os
import re
import sys
import tempfile
from decimal import Decimal, InvalidOperation

GROUPS = ["revenue", "direct_costs", "operating_expenses", "other_income", "other_expenses"]
BASES = {"cash", "accrual"}
# Percentage change is suppressed when |prior| is below this share of prior revenue.
# default — confirm with the owner.
DEFAULT_PCT_FLOOR_SHARE = Decimal("0.01")
Q = Decimal("0.01")

TRAPS = [
    (re.compile(r"sales tax|\bvat\b|\bgst\b", re.I), ("direct_costs", "operating_expenses", "other_expenses"),
     "sales tax or VAT in the P&L: tax collected from customers is a liability, not revenue or expense; tax paid on purchases may be an expense where it cannot be recovered; list it, the accountant decides"),
    (re.compile(r"1099-?k", re.I), ("revenue", "other_income"),
     "revenue taken from a 1099-K total: those totals mix personal and business receipts and are not revenue"),
    (re.compile(r"owner|drawing|personal|director.?s? loan", re.I), tuple(GROUPS),
     "owner or personal item in the P&L: belongs in equity (contribution or draw); owner question"),
    (re.compile(r"suspense|ask my accountant|uncategori[sz]ed|unclassified", re.I), tuple(GROUPS),
     "unresolved holding account: its items are not yet coded"),
]


class NotComparable(Exception):
    pass


class InputError(Exception):
    pass


def money(v, where):
    t = str(v or "").strip().replace(",", "")
    if t.startswith("(") and t.endswith(")"):
        t = "-" + t[1:-1]
    try:
        return Decimal(t).quantize(Q)
    except InvalidOperation:
        raise InputError(f"{where}: '{v}' is not a number")


def load(path, label):
    if not os.path.isfile(path):
        raise InputError(f"{label}: file not found: {path}")
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rd = csv.DictReader(fh)
        cols = [c.strip().lower() for c in rd.fieldnames or []]
        for need in ("account", "amount"):
            if need not in cols:
                raise InputError(f"{label}: needs columns account, group, amount; found {cols}")
        rows, bases, seen = [], set(), {}
        for n, raw in enumerate(rd, start=2):
            r = {k.strip().lower(): (v or "").strip() for k, v in raw.items() if k}
            if not r.get("account"):
                continue
            # Lines are keyed on the account name, so a repeated name (a leaf such
            # as "Other" under two parents in a flattened export) would silently
            # overwrite one account with the other. Refuse it instead.
            key = r["account"].casefold()
            if key in seen:
                raise InputError(f"{label} line {n}: account '{r['account']}' appears twice (first on line {seen[key]}). "
                                 "Each account must be one row: put the full account name ('Parent:Child') or the account "
                                 "code in the account column, then re-run.")
            seen[key] = n
            g = r.get("group", "").lower().replace(" ", "_")
            rows.append({"account": r["account"], "group": g if g in GROUPS else "", "amount": money(r["amount"], f"{label} line {n}")})
            if r.get("basis"):
                bases.add(r["basis"].lower())
        return rows, bases


def resolve_basis(arg, file_bases, label, allow_unknown=False):
    b = (arg or "").lower()
    if file_bases:
        if len(file_bases) > 1:
            raise NotComparable(f"{label}: rows carry more than one basis {sorted(file_bases)}")
        fb = next(iter(file_bases))
        if b and b != fb:
            raise NotComparable(f"{label}: --basis says {b} but the file says {fb}")
        b = fb
    if b not in BASES and allow_unknown:
        return "unknown (open)"
    if b not in BASES:
        raise NotComparable(f"{label}: basis is '{b or 'unknown'}'. State cash or accrual from the export header; do not assume")
    return b


def totals(rows):
    t = {g: Decimal(0) for g in GROUPS}
    for r in rows:
        if r["group"]:
            t[r["group"]] += r["amount"]
    t["gross_result"] = t["revenue"] - t["direct_costs"]
    t["operating_result"] = t["gross_result"] - t["operating_expenses"]
    t["net_result"] = t["operating_result"] + t["other_income"] - t["other_expenses"]
    return t


def pct(cur, pri, floor):
    if pri == 0:
        return None, "n/m (prior is zero)"
    if abs(pri) < floor:
        return None, f"n/m (prior below {floor}, the percentage floor)"
    if (pri < 0) != (cur < 0) and cur != 0:
        return None, "n/m (sign changed)"
    return ((cur - pri) / abs(pri) * 100).quantize(Decimal("0.1")), ""


def analyse(a):
    cur, cb = load(a.current, "current")
    basis = resolve_basis(a.current_basis, cb, "current", allow_unknown=not (a.prior or a.plan))
    pri, prior_basis = [], None
    if a.prior:
        pri, pb = load(a.prior, "prior")
        prior_basis = resolve_basis(a.prior_basis, pb, "prior")
        if prior_basis != basis:
            raise NotComparable(f"current is {basis} basis and prior is {prior_basis}: not comparable. "
                                "Get both periods on the same basis from the ledger; never convert by estimate")
    tc, tp = totals(cur), totals(pri) if pri else None
    floor = (abs(tp["revenue"]) * a.pct_floor_share).quantize(Q) if tp else Decimal(0)
    unmapped = [{"account": r["account"], "amount": str(r["amount"])} for r in cur if not r["group"]]
    # A prior-period unmapped account is missing from the prior subtotals, so every
    # subtotal change would be measured against an understated base.
    unmapped_prior = [{"account": r["account"], "amount": str(r["amount"])} for r in pri if not r["group"] and r["amount"] != 0]
    flags = []
    for r in cur:
        for rx, groups, msg in TRAPS:
            if rx.search(r["account"]) and (r["group"] in groups or not r["group"]):
                flags.append(f"{r['account']} ({r['amount']}): {msg}")
    lines = []
    pri_by = {r["account"]: r for r in pri}
    accounts = [r["account"] for r in cur] + [r["account"] for r in pri if r["account"] not in {c["account"] for c in cur}]
    cur_by = {r["account"]: r for r in cur}
    rev = tc["revenue"]
    for acc in accounts:
        c = cur_by.get(acc, {"amount": Decimal(0), "group": pri_by.get(acc, {}).get("group", "")})
        p = pri_by.get(acc)
        row = {"line": acc, "group": c["group"] or "UNMAPPED", "current": str(c["amount"])}
        if tp is not None:
            pv = p["amount"] if p else Decimal(0)
            pc, why = pct(c["amount"], pv, floor)
            row.update(prior=str(pv), change=str(c["amount"] - pv), pct=f"{pc}%" if pc is not None else why)
        row["share_of_revenue"] = f"{(c['amount'] / rev * 100).quantize(Decimal('0.1'))}%" if rev else "n/m"
        lines.append(row)
    subtotal_rows = []
    for key in ["revenue", "direct_costs", "gross_result", "operating_expenses", "operating_result", "other_income", "other_expenses", "net_result"]:
        row = {"line": key, "current": str(tc[key])}
        if tp is not None:
            pc, why = pct(tc[key], tp[key], floor)
            row.update(prior=str(tp[key]), change=str(tc[key] - tp[key]), pct=f"{pc}%" if pc is not None else why)
            if unmapped_prior:
                row.update(change="n/m (prior has unmapped accounts)", pct="n/m (prior has unmapped accounts)")
        row["share_of_revenue"] = f"{(tc[key] / rev * 100).quantize(Decimal('0.1'))}%" if rev else "n/m"
        subtotal_rows.append(row)
    checks, compared, not_compared = [], [], []
    if a.reported_current:
        rep, _ = load_reported(a.reported_current)
        compared = [g for g in REPORTED_NAMES if g in rep]
        for g in compared:
            amt = rep[g]
            if tc[g] != amt:
                checks.append(f"reported {g} {amt} differs from mapped detail {tc[g]} by {amt - tc[g]}"
                              + (" (equals the unmapped total)" if amt - tc[g] == sum((Decimal(u['amount']) for u in unmapped), Decimal(0)) else ""))
        # A group with detail but no report total was not checked.
        not_compared = [g for g in GROUPS if g not in rep and tc[g] != 0]
    enough = "revenue" in compared and any(g in compared for g in COST_GROUPS)
    if not a.reported_current:
        detail_to_total = "not checked (no report totals supplied)"
    elif checks:
        detail_to_total = f"differs from report totals (compared: {', '.join(compared)})"
    elif not enough:
        detail_to_total = (f"not checked (report totals must include revenue and at least one cost group; "
                           f"compared: {', '.join(compared) or 'none'})")
    elif not_compared:
        detail_to_total = (f"partly checked: ties for {', '.join(compared)}; not checked: {', '.join(not_compared)} "
                           "(no report total supplied)")
    else:
        detail_to_total = f"ties to report totals (compared: {', '.join(compared)})"
    net_ok = not unmapped and not checks and enough and not not_compared
    if net_ok:
        net_note = ""
    elif unmapped or checks:
        net_note = "unmapped accounts or a detail-to-total difference remain"
    else:
        net_note = f"detail-to-total {detail_to_total}"
    plan_rows = []
    if a.plan:
        plan_rows = plan_variance(a.plan, a.current_period, basis, a.currency, cur_by, tc)
    movers = sorted([l for l in lines if "change" in l], key=lambda l: abs(Decimal(l["change"])), reverse=True)[: a.top]
    return {
        "entity": a.entity, "source": a.source, "currency": a.currency, "basis": basis,
        "current_period": a.current_period, "prior_period": a.prior_period if a.prior else None,
        "status": "DRAFT for review, not final accounts",
        "pct_floor": str(floor), "pct_floor_note": "default — confirm with the owner" if a.pct_floor_share == DEFAULT_PCT_FLOOR_SHARE else "as supplied",
        "subtotals": subtotal_rows, "lines": lines, "largest_movements": movers,
        "unmapped": unmapped, "unmapped_prior": unmapped_prior, "flags": flags, "detail_to_total_checks": checks,
        "detail_to_total": detail_to_total,
        "net_result_shown": net_ok,
        "net_result_note": net_note,
        "plan": plan_rows, "script": "monthly-profit-and-loss-summary/scripts/pl_variance.py",
    }


REPORTED_NAMES = GROUPS + ["gross_result", "operating_result", "net_result"]
COST_GROUPS = ("direct_costs", "operating_expenses")


def load_reported(path):
    """Report totals, one row per group name. An export label ("Total Income",
    "Net Profit") is refused: the model maps each total row to a group name
    explicitly, so a total is never skipped without a word."""
    if not os.path.isfile(path):
        raise InputError(f"reported: file not found: {path}")
    out = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rd = csv.DictReader(fh)
        cols = [c.strip().lower() for c in rd.fieldnames or []]
        if "group" not in cols or "amount" not in cols:
            raise InputError(f"reported: needs columns group, amount (templates/reported-totals.csv); found {cols}")
        for n, r in enumerate(rd, start=2):
            r = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
            if not r.get("group") and not r.get("amount"):
                continue
            g = r["group"].lower().replace(" ", "_")
            if g not in REPORTED_NAMES:
                raise InputError(f"reported line {n}: '{r['group']}' is not a group name. Map each export total row to one of "
                                 f"{REPORTED_NAMES} (for example 'Total Income' -> revenue, 'Net Profit' -> net_result) "
                                 "and leave out rows you cannot map")
            if g in out:
                raise InputError(f"reported line {n}: {g} appears twice")
            if not r.get("amount"):
                continue  # template row left blank: that group is not checked
            out[g] = money(r["amount"], f"reported line {n}")
    return out, None


def plan_variance(path, period, basis, currency, cur_by, tc):
    rows = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for n, r in enumerate(csv.DictReader(fh), start=2):
            r = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
            if r.get("period") != period:
                continue
            if r.get("basis", "").lower() != basis:
                raise NotComparable(f"plan line {n}: plan basis '{r.get('basis')}' differs from actuals ({basis}); plan not used")
            if r.get("currency", "").upper() != (currency or "").upper():
                raise NotComparable(f"plan line {n}: plan currency '{r.get('currency')}' differs from {currency}")
            acc = r["account"]
            actual = cur_by.get(acc, {}).get("amount", Decimal(0))
            amt = money(r["amount"], f"plan line {n}")
            rows.append({"line": acc, "actual": str(actual), "plan": str(amt), "variance": str(actual - amt),
                         "plan_source": r.get("source", "")})
    return rows


def fmt(x):
    try:
        d = Decimal(x)
    except (InvalidOperation, TypeError):
        return str(x)
    s = f"{abs(d):,.2f}"
    return f"({s})" if d < 0 else s


def markdown(res):
    head = (f"{res['entity'] or '(entity)'}, {res['current_period']}"
            + (f" vs {res['prior_period']}" if res["prior_period"] else "")
            + f", {res['currency']}, {res['basis']} basis. Source: {res['source'] or '(not stated)'}. **{res['status']}**")
    cols = ["line", "current", "prior", "change", "pct", "share_of_revenue"] if res["prior_period"] else ["line", "current", "share_of_revenue"]
    out = [head, "", "| " + " | ".join(c.replace("_", " ").title() for c in cols) + " |", "|" + " --- |" * len(cols)]
    for r in res["subtotals"]:
        if r["line"] == "net_result" and not res["net_result_shown"]:
            out.append(f"| net result | not shown: {res['net_result_note']} |" + " |" * (len(cols) - 2))
            continue
        out.append("| " + " | ".join(fmt(r.get(c, "")) if c not in ("line", "pct", "share_of_revenue") else str(r.get(c, "")).replace("_", " ")
                                     for c in cols) + " |")
    out += ["", "Largest movements: " + "; ".join(f"{m['line']} {fmt(m['change'])}" for m in res["largest_movements"])]
    if res["unmapped"]:
        out.append("Unmapped (excluded from subtotals): " + "; ".join(f"{u['account']} {fmt(u['amount'])}" for u in res["unmapped"]))
    if res.get("unmapped_prior"):
        out.append("Prior period unmapped (subtotal changes not measurable): "
                   + "; ".join(f"{u['account']} {fmt(u['amount'])}" for u in res["unmapped_prior"]))
    if res["plan"]:
        out += ["", "Plan comparison (plan figures as supplied; none created here):", "",
                "| Line | Actual | Plan | Variance | Plan source |", "| --- | --- | --- | --- | --- |"]
        for r in res["plan"]:
            out.append(f"| {r['line']} | {fmt(r['actual'])} | {fmt(r['plan'])} | {fmt(r['variance'])} | {r['plan_source']} |")
        out.append("")
    out.append(f"Detail-to-total: {res['detail_to_total']}.")
    for f in res["flags"] + res["detail_to_total_checks"]:
        out.append(f"- {f}")
    out.append(f"Percentages suppressed below a prior of {fmt(res['pct_floor'])} ({res['pct_floor_note']}).")
    return "\n".join(out) + "\n"


def write(out, res):
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "pl_variance.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2)
    with open(os.path.join(out, "pl_table.md"), "w", encoding="utf-8") as fh:
        fh.write(markdown(res))
    with open(os.path.join(out, "pl_state.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["period", "account", "group", "amount", "currency", "basis", "source", "status"])
        for l in res["lines"]:
            w.writerow([res["current_period"], l["line"], l["group"], l["current"], res["currency"], res["basis"], res["source"], "draft"])


def selftest():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d = os.path.join(here, "examples", "april-2026")
    base = dict(current=os.path.join(d, "pl-2026-04.csv"), current_period="2026-04", current_basis="accrual",
                prior=os.path.join(d, "pl-2026-03.csv"), prior_period="2026-03", prior_basis="accrual",
                currency="GBP", reported_current=os.path.join(d, "reported-2026-04.csv"), plan=os.path.join(d, "budget.csv"),
                entity="Bramble Design Ltd", source="fixture", pct_floor_share=DEFAULT_PCT_FLOOR_SHARE, top=3)
    res = analyse(argparse.Namespace(**base))
    st = {r["line"]: r for r in res["subtotals"]}
    assert st["revenue"]["change"] == "4550.00" and st["revenue"]["pct"] == "25.0%", st["revenue"]
    assert st["operating_result"]["current"] == "4430.00" and st["operating_result"]["pct"] == "109.0%", st["operating_result"]
    ln = {r["line"]: r for r in res["lines"]}
    assert ln["Workshops"]["pct"].startswith("n/m"), ln["Workshops"]
    assert not res["net_result_shown"] and res["unmapped"], "unmapped must block net result"
    assert any("equals the unmapped total" in c for c in res["detail_to_total_checks"]), res["detail_to_total_checks"]
    assert any(p["line"] == "Sales - Retainers" and p["variance"] == "500.00" for p in res["plan"]), res["plan"]
    try:
        analyse(argparse.Namespace(**dict(base, prior=os.path.join(d, "pl-2026-03-cash.csv"), prior_basis="")))
    except NotComparable:
        pass
    else:
        raise AssertionError("cross-basis comparison was not refused")
    traps = analyse(argparse.Namespace(**dict(base, current=os.path.join(d, "pl-2026-04-traps.csv"), reported_current=None, plan=None)))
    joined = " ".join(traps["flags"])
    assert "sales tax" in joined and "owner" in joined and "1099-K" in joined, traps["flags"]
    alone = analyse(argparse.Namespace(**dict(base, prior=None, plan=None, current_basis="")))
    assert alone["basis"] == "unknown (open)" and "change" not in alone["lines"][0], "single period with unknown basis"
    march = analyse(argparse.Namespace(**dict(base, current=os.path.join(d, "pl-2026-03.csv"), current_period="2026-03",
                                              prior=None, plan=None, reported_current=None)))
    assert not march["net_result_shown"] and march["detail_to_total"].startswith("not checked"), march["net_result_note"]
    assert "not checked" in markdown(march)
    # Report totals: export labels are refused; a partial set never "ties".
    with tempfile.TemporaryDirectory() as tmp:
        bad = os.path.join(tmp, "rep_bad.csv")
        with open(bad, "w", encoding="utf-8") as fh:
            fh.write("group,amount\nTotal Income,99999.00\nNet Profit,1.00\n")
        try:
            analyse(argparse.Namespace(**dict(base, reported_current=bad)))
            raise AssertionError("export-style total labels accepted")
        except InputError as exc:
            assert "Total Income" in str(exc), exc
        only_rev = os.path.join(tmp, "rep_rev.csv")
        with open(only_rev, "w", encoding="utf-8") as fh:
            fh.write("group,amount\nrevenue,22750.00\n")
        clean = os.path.join(tmp, "pl-clean.csv")
        with open(os.path.join(d, "pl-2026-04.csv"), encoding="utf-8") as fh:
            body = fh.read().replace("Uncategorised Expense,,1040.20", "Uncategorised Expense,operating_expenses,1040.20")
        with open(clean, "w", encoding="utf-8") as fh:
            fh.write(body)
        r = analyse(argparse.Namespace(**dict(base, current=clean, reported_current=only_rev, plan=None)))
        assert r["detail_to_total"].startswith("not checked") and not r["net_result_shown"], r["detail_to_total"]
        r = analyse(argparse.Namespace(**dict(base, current=clean, plan=None)))
        assert r["detail_to_total"].startswith("ties") and r["net_result_shown"], r["detail_to_total"]
        # Prior-period unmapped account: subtotal changes are not measurable.
        pri = os.path.join(tmp, "pri.csv")
        with open(os.path.join(d, "pl-2026-03.csv"), encoding="utf-8") as fh:
            body = fh.read().rstrip("\n") + "\nConsulting income,,4000.00\n"
        with open(pri, "w", encoding="utf-8") as fh:
            fh.write(body)
        r = analyse(argparse.Namespace(**dict(base, prior=pri, plan=None)))
        st = {x["line"]: x for x in r["subtotals"]}
        assert st["revenue"]["pct"].startswith("n/m (prior has unmapped") and r["unmapped_prior"], st["revenue"]
        assert "Prior period unmapped" in markdown(r)
        # Two accounts sharing a leaf name ("Other" under two parents) are refused,
        # never merged into one line that drops the other account.
        dup = os.path.join(tmp, "dup.csv")
        with open(dup, "w", encoding="utf-8") as fh:
            fh.write("account,group,amount\nSales,revenue,10000.00\nOther,revenue,500.00\nOther,operating_expenses,300.00\n")
        try:
            analyse(argparse.Namespace(**dict(base, current=dup, plan=None, reported_current=None)))
            raise AssertionError("duplicate account name accepted")
        except InputError as exc:
            assert "'Other' appears twice" in str(exc) and "Parent:Child" in str(exc), exc
    # YTD from stored months: refuses a gap, adds a complete span
    with tempfile.TemporaryDirectory() as tmp:
        m3, m4 = os.path.join(tmp, "2026-03.csv"), os.path.join(tmp, "2026-04.csv")
        for path, per, src in ((m3, "2026-03", "pl-2026-03.csv"), (m4, "2026-04", "pl-2026-04.csv")):
            r = analyse(argparse.Namespace(**dict(base, current=os.path.join(d, src), current_period=per, prior=None,
                                                  plan=None, reported_current=None)))
            write(os.path.join(tmp, per), r)
            os.replace(os.path.join(tmp, per, "pl_state.csv"), path)
        out = os.path.join(tmp, "ytd.csv")
        try:
            sum_months([m4], month_span("2026-03", "2026-04"), out)
            raise AssertionError("YTD with a missing month accepted")
        except InputError:
            pass
        sum_months([m3, m4], month_span("2026-03", "2026-04"), out)
        ytd = {r["account"]: r["amount"] for r in csv.DictReader(open(out, encoding="utf-8"))}
        assert ytd["Sales - Retainers"] == "29500.00", ytd
    print("selftest ok")
    return 0


def sum_months(paths, months, out):
    """Add stored monthly pl_state files into one year-to-date P&L export.

    Refuses a missing or repeated month, mixed bases or currencies, or a file
    that holds a YTD total instead of one month. Never estimates a gap."""
    want = list(months)
    seen, totals_by, basis, currency = {}, {}, set(), set()
    for path in paths:
        if not os.path.isfile(path):
            raise InputError(f"sum: file not found: {path}")
        with open(path, newline="", encoding="utf-8-sig") as fh:
            rows = [{k.strip().lower(): (v or "").strip() for k, v in r.items() if k} for r in csv.DictReader(fh)]
        periods = {r.get("period", "") for r in rows}
        if len(periods) != 1 or not re.fullmatch(r"\d{4}-\d{2}", next(iter(periods))):
            raise InputError(f"sum: {os.path.basename(path)} must hold exactly one YYYY-MM period (found {sorted(periods)}); "
                             "never add a YTD file into another YTD")
        per = next(iter(periods))
        if per in seen:
            raise InputError(f"sum: month {per} appears twice ({seen[per]} and {path})")
        seen[per] = path
        for n, r in enumerate(rows, start=2):
            basis.add(r.get("basis", "").lower())
            currency.add(r.get("currency", "").upper())
            key = (r["account"], r.get("group", ""))
            totals_by[key] = totals_by.get(key, Decimal(0)) + money(r["amount"], f"{os.path.basename(path)} line {n}")
    missing = [m for m in want if m not in seen]
    extra = [m for m in seen if m not in want]
    if missing or extra:
        raise InputError(f"sum: months missing {missing}, not in the span {extra}. A missing month means no YTD figure; "
                         "get it from the ledger, never estimate it")
    if len(basis) != 1 or next(iter(basis)) not in BASES:
        raise NotComparable(f"sum: months carry bases {sorted(basis)}; all must share one known basis")
    if len(currency) != 1:
        raise NotComparable(f"sum: months carry currencies {sorted(currency)}")
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["account", "group", "amount", "basis"])
        for (acc, grp), amt in totals_by.items():
            w.writerow([acc, grp, str(amt), next(iter(basis))])
    return len(seen), next(iter(basis)), next(iter(currency))


def month_span(start, end):
    y, m = int(start[:4]), int(start[5:])
    out = []
    while f"{y}-{m:02d}" <= end:
        out.append(f"{y}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--current")
    p.add_argument("--current-period")
    p.add_argument("--current-basis")
    p.add_argument("--prior")
    p.add_argument("--prior-period")
    p.add_argument("--prior-basis")
    p.add_argument("--currency")
    p.add_argument("--reported-current")
    p.add_argument("--plan")
    p.add_argument("--entity", default="")
    p.add_argument("--source", default="")
    p.add_argument("--pct-floor-share", type=Decimal, default=DEFAULT_PCT_FLOOR_SHARE)
    p.add_argument("--top", type=int, default=5)
    p.add_argument("--out")
    p.add_argument("--sum-months", nargs="+", help="YTD: stored monthly pl/<YYYY-MM>.csv files to add together")
    p.add_argument("--span", help="YTD: fiscal-year start and end month, e.g. 2026-01:2026-04 (start from intake)")
    p.add_argument("--sum-out", help="YTD: where to write the summed export")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    if a.selftest:
        return selftest()
    if a.sum_months:
        if not (a.span and a.sum_out and re.fullmatch(r"\d{4}-\d{2}:\d{4}-\d{2}", a.span)):
            p.error("--sum-months needs --span YYYY-MM:YYYY-MM (fiscal-year start from intake) and --sum-out")
        try:
            n, b, c = sum_months(a.sum_months, month_span(*a.span.split(":")), a.sum_out)
        except (InputError, NotComparable) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(f"wrote {a.sum_out}: {n} months {a.span}, {b} basis, {c}. Use it as --current with --current-period ytd-{a.span.split(':')[1]}")
        return 0
    if not (a.current and a.current_period and a.currency and a.out):
        p.error("--current, --current-period, --currency and --out are required")
    try:
        res = analyse(a)
    except NotComparable as exc:
        print(f"NOT COMPARABLE: {exc}", file=sys.stderr)
        return 2
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    write(a.out, res)
    print(markdown(res))
    print(f"files: {a.out}/pl_variance.json, pl_table.md, pl_state.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
