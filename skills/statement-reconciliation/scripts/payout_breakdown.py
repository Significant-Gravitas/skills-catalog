#!/usr/bin/env python3
"""Break processor payouts into gross, fees, refunds, disputes and net, and tie them to bank deposits.

Python 3 standard library only. Reads exports, writes result files. Never edits inputs.

Stripe (Payout reconciliation report, itemised CSV):
    cd ~/skills/statement-reconciliation && python3 scripts/payout_breakdown.py stripe \
        --report /home/user/in/stripe-payout-recon.csv \
        --bank /home/user/in/statement.csv --cutoff 2026-04-30 \
        --out /home/user/out/rec/stripe-2026-04

PayPal (Activity download CSV):
    python3 scripts/payout_breakdown.py paypal --report /home/user/in/paypal.csv \
        --bank /home/user/in/statement.csv --cutoff 2026-04-30 --out /home/user/out/rec/paypal-2026-04 \
        [--currency GBP] [--opening 0.00 --closing 0.00]

    PayPal keeps one balance per currency. The script never adds currencies
    together: with more than one currency in the export it exits 2 unless
    --currency names the one that ties to this bank account. Other currencies
    are listed per currency, and "General Currency Conversion" rows are shown
    as FX for the accountant, never as sales. Debit payment rows (money paid out
    of PayPal) are "payments_sent", never netted against gross sales.

    python3 scripts/payout_breakdown.py --selftest

Columns are matched case-insensitively. On a miss the script exits 2 and lists the
columns it expects. `--bank` is the canonical statement CSV (id,date,amount,description).
Clearing equation checked per payout: gross sales - fees - refunds - disputes = net.
"""

import argparse
import csv
import datetime as dt
import json
import os
import sys
from decimal import Decimal, InvalidOperation

# Days either side of a payout date within which a bank deposit may tie.
# default — confirm with the owner.
DEFAULT_TIE_WINDOW_DAYS = 3
Q = Decimal("0.01")

STRIPE_KEY = ["automatic_payout_id"]
STRIPE_DATE = ["automatic_payout_effective_at", "effective_at", "available_on", "created"]
STRIPE_NEED = ["gross", "fee", "net"]
PAYPAL_NEED = ["date", "currency", "gross", "fee", "net", "balance impact"]


class InputError(Exception):
    pass


def money(v, where):
    t = str(v or "0").strip().replace(",", "")
    if t in ("", "-"):
        t = "0"
    try:
        return Decimal(t).quantize(Q)
    except InvalidOperation:
        raise InputError(f"{where}: '{v}' is not a number")


DATE_FORMAT = None  # set by --date-format for non-ISO exports


def parse_day(v, where):
    t = str(v or "").strip()
    try:
        return dt.date.fromisoformat(t[:10])
    except ValueError:
        pass
    if DATE_FORMAT:
        try:
            return dt.datetime.strptime(t, DATE_FORMAT).date()
        except ValueError:
            raise InputError(f"{where}: date '{v}' does not fit --date-format {DATE_FORMAT}")
    raise InputError(f"{where}: date '{v}' is not ISO. Pass --date-format '%m/%d/%Y' or '%d/%m/%Y' "
                     "as the export shows it; the script will not guess day/month order.")


def load(path, need, label):
    if not os.path.isfile(path):
        raise InputError(f"{label}: file not found: {path}")
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rd = csv.DictReader(fh)
        cols = {c.strip().lower(): c for c in rd.fieldnames or []}
        missing = [c for c in need if c not in cols]
        if missing:
            raise InputError(f"{label}: missing columns {missing}. Expected at least {need}; found {list(cols)}.")
        return [{k.strip().lower(): (v or "").strip() for k, v in r.items() if k} for r in rd], cols


def first(cols, options):
    for o in options:
        if o in cols:
            return o
    return None


def fee_sign(gross, fee, net, where):
    if gross - fee == net:
        return fee  # fee reported positive
    if gross + fee == net:
        return -fee  # fee reported negative
    raise InputError(f"{where}: gross {gross}, fee {fee}, net {net} do not agree either way; check the export")


def category(text):
    t = (text or "").lower()
    if "refund" in t:
        return "refunds"
    if "dispute" in t or "chargeback" in t:
        return "disputes"
    if t in ("fee", "other_adjustment", "network_cost") or "fee" in t:
        return "other_fees"
    if t in ("charge", "payment", "") or "charge" in t or "payment" in t:
        return "gross_sales"
    return "other"


def tie(payouts, bank_rows, window):
    used = set()
    for p in payouts:
        hits = [b for b in bank_rows if b["id"] not in used and money(b["amount"], "bank") == p["net"]
                and abs((parse_day(b["date"], "bank") - p["date"]).days) <= window]
        if len(hits) == 1:
            p["bank_line"] = hits[0]["id"]
            p["bank_date"] = hits[0]["date"]
            used.add(hits[0]["id"])
        elif len(hits) > 1:
            p["bank_line"] = "AMBIGUOUS: " + ";".join(h["id"] for h in hits)
    return used


def run_stripe(a):
    rows, cols = load(a.report, STRIPE_NEED, "stripe report")
    key = first(cols, STRIPE_KEY)
    dcol = first(cols, STRIPE_DATE)
    if not key or not dcol:
        raise InputError(f"stripe report: needs {STRIPE_KEY} and one of {STRIPE_DATE}. "
                         "For manual payouts run the by-payout report with the payout ID instead.")
    cat_col = first(cols, ["reporting_category", "type", "category"])
    payouts, unassigned = {}, []
    for n, r in enumerate(rows, start=2):
        where = f"stripe line {n}"
        g, f, nt = money(r["gross"], where), money(r["fee"], where), money(r["net"], where)
        fee = fee_sign(g, f, nt, where)
        c = category(r.get(cat_col, "") if cat_col else "")
        if not r.get(key):
            unassigned.append({"line": n, "gross": str(g), "fee": str(fee), "net": str(nt), "category": c})
            continue
        p = payouts.setdefault(r[key], {"payout": r[key], "date": parse_day(r[dcol], where),
                                        "gross_sales": Decimal(0), "refunds": Decimal(0), "disputes": Decimal(0),
                                        "other": Decimal(0), "fees": Decimal(0), "net": Decimal(0), "rows": 0})
        if c == "other_fees":
            p["fees"] += -nt  # a standalone fee row: its net is the cost
        else:
            p[c] += g
            p["fees"] += fee
        p["net"] += nt
        p["rows"] += 1
    return list(payouts.values()), unassigned, []


def run_paypal(a):
    rows, cols = load(a.report, PAYPAL_NEED, "paypal report")
    type_col = first(cols, ["type"])
    id_col = first(cols, ["transaction id"])
    if any(not r["currency"] for r in rows):
        raise InputError("paypal report: some rows have an empty Currency. Re-export the Activity download with all columns.")
    currencies = sorted({r["currency"].upper() for r in rows})
    want = (getattr(a, "currency", None) or "").upper()
    if not want:
        if len(currencies) > 1:
            raise InputError(f"paypal report: more than one currency {currencies}. PayPal keeps a balance per currency and "
                             "the script will not add them together. Re-run with --currency <the one paid out to this bank account>.")
        want = currencies[0] if currencies else ""
    elif currencies and want not in currencies:
        raise InputError(f"paypal report: --currency {want} does not appear; currencies found {currencies}.")
    tot = {"gross_sales": Decimal(0), "payments_sent": Decimal(0), "refunds": Decimal(0), "disputes": Decimal(0),
           "fx_conversion": Decimal(0), "other": Decimal(0), "fees": Decimal(0), "net": Decimal(0), "rows": 0}
    memo, transfers, fx_rows = [], [], []
    other_ccy = {}
    for n, r in enumerate(rows, start=2):
        where = f"paypal line {n}"
        impact = r["balance impact"].lower()
        g, f, nt = money(r["gross"], where), money(r["fee"], where), money(r["net"], where)
        t = (r.get(type_col, "") if type_col else "").lower()
        ccy = r["currency"].upper()
        if ccy != want:
            if impact != "memo":
                o = other_ccy.setdefault(ccy, {"rows": 0, "gross": Decimal(0), "fee": Decimal(0), "net": Decimal(0)})
                o["rows"] += 1
                o["gross"] += g
                o["fee"] += f
                o["net"] += nt
            continue
        if impact == "memo":
            memo.append({"line": n, "type": t, "gross": str(g), "note": "Memo: does not move the balance (excluded)"})
            continue
        if impact not in ("debit", "credit"):
            raise InputError(f"{where}: Balance Impact '{r['balance impact']}' is not Debit, Credit or Memo")
        if "withdraw" in t or "transfer to bank" in t or "bank deposit" in t:
            transfers.append({"payout": r.get(id_col, f"line{n}") if id_col else f"line{n}",
                              "date": parse_day(r["date"], where), "net": -nt,
                              "gross_sales": Decimal(0), "refunds": Decimal(0), "disputes": Decimal(0),
                              "other": Decimal(0), "fees": Decimal(0), "rows": 1})
            continue
        cost = fee_sign(g, f, nt, where)
        if "currency conversion" in t:
            tot["fx_conversion"] += nt
            tot["net"] += nt
            tot["rows"] += 1
            fx_rows.append({"line": n, "type": t, "net": str(nt), "note": "FX conversion: for the accountant, not sales"})
            continue
        c = category(t)
        if c == "gross_sales" and impact == "debit":
            c = "payments_sent"  # money paid out of PayPal (purchases), never netted against sales
        if c == "other_fees":
            tot["fees"] += -nt
        else:
            tot[c] += g
            tot["fees"] += cost
        tot["net"] += nt
        tot["rows"] += 1
    activity = {"payout": f"activity (non-transfer rows, {want})", "date": None, "currency": want, **tot}
    extra = {"memo": memo, "fx_rows": fx_rows,
             "other_currencies": {k: {kk: str(vv) for kk, vv in v.items()} for k, v in other_ccy.items()}}
    return transfers, [], [activity, extra]


def main_run(a):
    payouts, unassigned, extra = (run_stripe if a.mode == "stripe" else run_paypal)(a)
    cutoff = dt.date.fromisoformat(a.cutoff) if a.cutoff else None
    bank = load(a.bank, ["id", "date", "amount"], "bank")[0] if a.bank else []
    tie(payouts, bank, a.window)
    out_rows, problems = [], []
    for p in sorted(payouts, key=lambda x: (x["date"] or dt.date.min, x["payout"])):
        eq = p["gross_sales"] + p["refunds"] + p["disputes"] + p["other"] - p["fees"]
        state = "tied to bank" if p.get("bank_line") and not str(p["bank_line"]).startswith("AMBIG") else "not tied"
        if cutoff and p["date"] and p["date"] > cutoff:
            state = "after cutoff: in transit (timing), not missing"
        if a.mode == "stripe" and eq.quantize(Q) != p["net"].quantize(Q):
            problems.append(f"payout {p['payout']}: components {eq} do not equal net {p['net']}")
        out_rows.append({"payout": p["payout"], "date": str(p["date"]), "gross_sales": str(p["gross_sales"]),
                         "refunds": str(p["refunds"]), "disputes": str(p["disputes"]), "other": str(p["other"]),
                         "fees": str(p["fees"]), "net": str(p["net"]), "rows": p["rows"],
                         "bank_line": p.get("bank_line", ""), "state": state})
    summary = {"mode": a.mode, "cutoff": a.cutoff, "tie_window_days": a.window,
               "tie_window_note": "default — confirm with the owner" if a.window == DEFAULT_TIE_WINDOW_DAYS else "as supplied",
               "payouts": out_rows, "unassigned_rows": unassigned, "problems": problems,
               "equation": "gross sales - fees - refunds - disputes = net deposit",
               "script": "statement-reconciliation/scripts/payout_breakdown.py"}
    if a.mode == "paypal":
        act = extra[0]
        summary["activity"] = {k: str(v) for k, v in act.items() if k not in ("date",)}
        summary["currency"] = act["currency"]
        summary["memo_rows_excluded"] = extra[1]["memo"]
        summary["fx_conversion_rows"] = extra[1]["fx_rows"]
        summary["other_currencies_not_included"] = extra[1]["other_currencies"]
        if extra[1]["other_currencies"]:
            summary["notes"] = ["Other currencies are NOT in these figures: " + ", ".join(
                f"{k} ({v['rows']} rows, net {v['net']})" for k, v in extra[1]["other_currencies"].items())
                + ". Run again with --currency <code> for each; never add them to this one."]
        if a.opening is not None and a.closing is not None:
            moved = act["net"] - sum((p["net"] for p in payouts), Decimal(0))
            ok = money(a.opening, "opening") + moved == money(a.closing, "closing")
            summary["balance_proof"] = f"opening {a.opening} + activity {act['net']} - transfers {sum((p['net'] for p in payouts), Decimal(0))} " \
                                       f"{'=' if ok else '!='} closing {a.closing}"
            if not ok:
                problems.append("PayPal balance does not prove: rows are missing (reports over 50,000 rows arrive split across files in a ZIP; the range limit is 12 months).")
    return summary


def write(out, s):
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "payouts.csv"), "w", newline="", encoding="utf-8") as fh:
        f = ["payout", "date", "gross_sales", "refunds", "disputes", "other", "fees", "net", "rows", "bank_line", "state"]
        w = csv.DictWriter(fh, fieldnames=f)
        w.writeheader()
        w.writerows(s["payouts"])
    with open(os.path.join(out, "payout_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(s, fh, indent=2)


def show(s):
    print(f"{s['mode']} payouts, cutoff {s['cutoff']} (tie window {s['tie_window_days']} days, {s['tie_window_note']})")
    for p in s["payouts"]:
        print(f"  {p['payout']} {p['date']}: gross {p['gross_sales']} refunds {p['refunds']} disputes {p['disputes']} "
              f"fees {p['fees']} net {p['net']} -> {p['bank_line'] or '-'} [{p['state']}]")
    for u in s["unassigned_rows"]:
        print(f"  NO PAYOUT ID line {u['line']}: net {u['net']} ({u['category']}). Manual payout or unpaid balance: "
              "run the by-payout report with the payout ID. Not dropped.")
    if "activity" in s:
        print(f"  activity: {s['activity']}")
        for m in s["memo_rows_excluded"]:
            print(f"  memo excluded line {m['line']}: {m['type']} {m['gross']}")
        for x in s.get("fx_conversion_rows", []):
            print(f"  FX line {x['line']}: {x['type']} {x['net']} (for the accountant, not sales)")
        for n in s.get("notes", []):
            print(f"  NOTE: {n}")
        if "balance_proof" in s:
            print(f"  {s['balance_proof']}")
    for p in s["problems"]:
        print(f"  PROBLEM: {p}")


def selftest():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d = os.path.join(here, "examples", "scenarios", "e-processor-payouts")
    with open(os.path.join(d, "expected.json"), encoding="utf-8") as fh:
        exp = json.load(fh)
    bad = 0
    for mode in ("stripe", "paypal"):
        spec = exp[mode]
        ns = argparse.Namespace(mode=mode, report=os.path.join(d, spec["report"]), bank=os.path.join(d, "bank.csv"),
                                cutoff="2026-04-30", window=DEFAULT_TIE_WINDOW_DAYS, currency=None,
                                opening=spec.get("opening"), closing=spec.get("closing"))
        s = main_run(ns)
        got = {p["payout"]: {"net": p["net"], "state": p["state"], "fees": p["fees"]} for p in s["payouts"]}
        for pid, want in spec["payouts"].items():
            for k, v in want.items():
                if got.get(pid, {}).get(k) != v:
                    bad += 1
                    print(f"FAIL {mode} {pid} {k}: want {v} got {got.get(pid, {}).get(k)}")
        if len(s["unassigned_rows"]) != spec.get("unassigned", 0):
            bad += 1
            print(f"FAIL {mode} unassigned: want {spec.get('unassigned', 0)} got {len(s['unassigned_rows'])}")
        if s["problems"]:
            bad += 1
            print(f"FAIL {mode} problems: {s['problems']}")
        if mode == "paypal" and len(s["memo_rows_excluded"]) != spec["memo"]:
            bad += 1
            print("FAIL paypal memo count")
    # Two currencies: refuse without --currency; with it, never mix the other currency in.
    spec = exp["paypal_two_currency"]
    base = dict(mode="paypal", report=os.path.join(d, spec["report"]), bank=None, cutoff="2026-04-30",
                window=DEFAULT_TIE_WINDOW_DAYS, opening="0.00", closing="0.00")
    try:
        main_run(argparse.Namespace(currency=None, **base))
        bad += 1
        print("FAIL paypal two-currency: accepted without --currency")
    except InputError:
        pass
    s = main_run(argparse.Namespace(currency=spec["currency"], **base))
    for k, v in spec["activity"].items():
        if s["activity"].get(k) != v:
            bad += 1
            print(f"FAIL paypal two-currency activity {k}: want {v} got {s['activity'].get(k)}")
    if sorted(s["other_currencies_not_included"]) != spec["other_currencies"] or s["problems"]:
        bad += 1
        print(f"FAIL paypal two-currency: other {s['other_currencies_not_included']} problems {s['problems']}")
    print("selftest ok" if not bad else f"selftest FAILED ({bad})")
    return 1 if bad else 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mode", nargs="?", choices=["stripe", "paypal"])
    p.add_argument("--report")
    p.add_argument("--bank")
    p.add_argument("--cutoff")
    p.add_argument("--window", type=int, default=DEFAULT_TIE_WINDOW_DAYS)
    p.add_argument("--currency", help="PayPal: the currency paid out to this bank account (required when the export holds several)")
    p.add_argument("--opening")
    p.add_argument("--closing")
    p.add_argument("--date-format", help="strptime format for non-ISO dates, e.g. %%m/%%d/%%Y")
    p.add_argument("--out")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    global DATE_FORMAT
    DATE_FORMAT = a.date_format
    if a.selftest:
        return selftest()
    if not (a.mode and a.report and a.out):
        p.error("mode, --report and --out are required")
    try:
        s = main_run(a)
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    write(a.out, s)
    show(s)
    return 0


if __name__ == "__main__":
    sys.exit(main())
