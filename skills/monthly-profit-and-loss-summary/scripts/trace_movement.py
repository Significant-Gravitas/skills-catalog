#!/usr/bin/env python3
"""Trace a P&L line's movement to source rows, and state how much is untraced.

Python 3 standard library only. Reads CSVs, prints and writes a trace. Never edits inputs.

    cd ~/skills/monthly-profit-and-loss-summary && python3 scripts/trace_movement.py \
        --account "Sales - Retainers" --current-period 2026-04 --prior-period 2026-03 \
        --pl /home/user/out/pl/2026-04/pl_variance.json \
        --sources /home/user/in/invoice-register.csv /home/user/in/bills-export.csv \
        [--out /home/user/out/pl/2026-04/trace.csv]

    python3 scripts/trace_movement.py --selftest

Source CSV columns: date (YYYY-MM-DD), account, amount [, ref, source]. Rows are
counted when their account equals --account (case-insensitive) and their date
falls in the period.

Real exports rarely have that shape. Reshape each one first (read-only; the
input is not changed):

    # Ledger transaction detail by account (general ledger) export: preferred source.
    python3 scripts/trace_movement.py --reshape --in /home/user/in/gl-detail.csv \
        --date-col Date --account-col Account --amount-col Amount --ref-col Num \
        --out /home/user/in/trace-gl.csv

    # Kit invoice register (invoice-drafting-and-issue; no account column).
    # line_key is one contract line for one period ("SOW-014/retainer/2026-04"),
    # so --key-strip-period maps on "SOW-014/retainer". Accounts come ONLY from
    # an owner-confirmed key -> account map; unmapped rows are listed, never guessed.
    # Only issued rows count (default for --key-col: --include-status issued_per_owner);
    # approved_to_issue, draft_in_ledger and voided_per_owner rows go to
    # <out>.skipped.csv, even with an empty issued_on. Accrual revenue only: on a
    # cash basis trace from the GL detail export or the payments, not invoices.
    python3 scripts/trace_movement.py --reshape --in ~/workspace/bookkeeping/<entity>/invoice-register.csv \
        --date-col issued_on --amount-col amount --ref-col number \
        --key-col line_key --key-strip-period --account-map ~/workspace/bookkeeping/<entity>/line-accounts.csv \
        --include-status issued_per_owner --status-col status --out /home/user/in/trace-invoices.csv

    # Expense review table (expense-categorization, <state>/expenses/<YYYY-MM>-review.csv):
    # card/bank outflows are negative and proposed_account is only proposed, so
    # count owner-approved rows only and flip the sign.
    python3 scripts/trace_movement.py --reshape --in ~/workspace/bookkeeping/<entity>/expenses/2026-04-review.csv \
        --date-col txn_date --amount-col amount --account-col proposed_account \
        --include-status approved --status-col status --negate --out /home/user/in/trace-expenses.csv

--account-map columns: key, account (confirmed_by, confirmed_on optional).
Rows whose key is not in the map go to <out>.unmapped.csv and stay untraced.
The P&L amounts come from pl_variance.json (or pass --pl-current and --pl-prior).
Source rows whose total has the opposite sign to the P&L line are refused (exit
2): reshape that source with --negate. The untraced figure goes into the brief
as it is: a driver is "explained" only up to the traced amount.
"""

import argparse
import csv
import json
import os
import re
import sys
from decimal import Decimal, InvalidOperation

Q = Decimal("0.01")
PERIOD_TAIL = re.compile(r"/\d{4}-\d{2}$")  # "SOW-014/retainer/2026-04" -> "SOW-014/retainer"


class InputError(Exception):
    pass


def money(v, where):
    try:
        return Decimal(str(v).strip().replace(",", "")).quantize(Q)
    except InvalidOperation:
        raise InputError(f"{where}: '{v}' is not a number")


def rows_for(paths, account, period):
    out = []
    for path in paths:
        if not os.path.isfile(path):
            raise InputError(f"source not found: {path}")
        with open(path, newline="", encoding="utf-8-sig") as fh:
            rd = csv.DictReader(fh)
            cols = [c.strip().lower() for c in rd.fieldnames or []]
            for need in ("date", "account", "amount"):
                if need not in cols:
                    raise InputError(f"{os.path.basename(path)}: needs date, account, amount; found {cols}")
            for n, raw in enumerate(rd, start=2):
                r = {k.strip().lower(): (v or "").strip() for k, v in raw.items() if k}
                if r["account"].lower() == account.lower() and r["date"][:7] == period:
                    out.append({"period": period, "date": r["date"], "ref": r.get("ref", ""),
                                "source": r.get("source") or os.path.basename(path), "line": n,
                                "amount": money(r["amount"], f"{os.path.basename(path)} line {n}")})
    return out


def reshape(a):
    """Rename an export's columns to date,account,amount,ref,source. Never infers an account."""
    if not os.path.isfile(a.inp):
        raise InputError(f"--in not found: {a.inp}")
    if bool(a.account_col) == bool(a.key_col):
        raise InputError("pass exactly one of --account-col (the export has an account column) "
                         "or --key-col with --account-map (an owner-confirmed key -> account map)")
    amap = {}
    if a.key_col:
        if not a.account_map or not os.path.isfile(a.account_map):
            raise InputError("--key-col needs --account-map <csv with key,account>, confirmed by the owner. "
                             "Never assign P&L accounts to invoices yourself.")
        with open(a.account_map, newline="", encoding="utf-8-sig") as fh:
            rd = csv.DictReader(fh)
            cols = [c.strip().lower() for c in rd.fieldnames or []]
            if "key" not in cols or "account" not in cols:
                raise InputError(f"{os.path.basename(a.account_map)}: needs columns key, account; found {cols}")
            for raw in rd:
                r = {k.strip().lower(): (v or "").strip() for k, v in raw.items() if k}
                if r["key"] and r["account"]:
                    amap[r["key"].lower()] = r["account"]
    skip = {s.strip().lower() for s in (a.skip_status or "").split(",") if s.strip()}
    include_arg = getattr(a, "include_status", None)
    if include_arg is None and a.key_col and not skip:
        include_arg = "issued_per_owner"  # the kit register: only issued invoices are revenue
    include = {s.strip().lower() for s in (include_arg or "").split(",") if s.strip()}
    sign = Decimal(-1) if getattr(a, "negate", False) else Decimal(1)
    src = os.path.basename(a.inp)
    out, unmapped, skipped_rows = [], [], []
    with open(a.inp, newline="", encoding="utf-8-sig") as fh:
        rd = csv.DictReader(fh)
        cols = {c.strip().lower(): c for c in rd.fieldnames or []}
        need = [a.date_col, a.amount_col] + [c for c in (a.account_col, a.key_col, a.ref_col) if c]
        if skip or include:
            need.append(a.status_col)
        missing = [c for c in need if c.lower() not in cols]
        if missing:
            raise InputError(f"{src}: missing column(s) {missing}; found {list(cols)}")
        for n, raw in enumerate(rd, start=2):
            r = {k.strip().lower(): (v or "").strip() for k, v in raw.items() if k}
            status = r.get(a.status_col.lower(), "").lower() if (skip or include) else ""
            if (include and status not in include) or (skip and status in skip):
                skipped_rows.append({"line": n, "status": status, "date": r.get(a.date_col.lower(), ""),
                                     "amount": r.get(a.amount_col.lower(), ""),
                                     "ref": r.get(a.ref_col.lower(), "") if a.ref_col else ""})
                continue
            date = r[a.date_col.lower()]
            if len(date) < 10 or date[4] != "-" or date[7] != "-":
                raise InputError(f"{src} line {n}: date '{date}' is not YYYY-MM-DD. Convert dates first; never guess day/month order.")
            amount = money(r[a.amount_col.lower()], f"{src} line {n}") * sign
            ref = r.get(a.ref_col.lower(), "") if a.ref_col else ""
            if a.account_col:
                account = r[a.account_col.lower()]
            else:
                key = r[a.key_col.lower()]
                lookup = PERIOD_TAIL.sub("", key) if getattr(a, "key_strip_period", False) else key
                account = amap.get(lookup.lower(), "")
                if not account:
                    unmapped.append({"line": n, "key": key, "date": date[:10], "amount": str(amount), "ref": ref})
                    continue
            out.append({"date": date[:10], "account": account, "amount": str(amount), "ref": ref, "source": f"{src} line {n}"})
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=["date", "account", "amount", "ref", "source"])
        wr.writeheader()
        wr.writerows(out)
    if unmapped:
        with open(a.out + ".unmapped.csv", "w", newline="", encoding="utf-8") as fh:
            wr = csv.DictWriter(fh, fieldnames=["line", "key", "date", "amount", "ref"])
            wr.writeheader()
            wr.writerows(unmapped)
    if skipped_rows:
        with open(a.out + ".skipped.csv", "w", newline="", encoding="utf-8") as fh:
            wr = csv.DictWriter(fh, fieldnames=["line", "status", "date", "amount", "ref"])
            wr.writeheader()
            wr.writerows(skipped_rows)
    return out, unmapped, len(skipped_rows)


def pl_amounts(a):
    if a.pl:
        with open(a.pl, encoding="utf-8") as fh:
            res = json.load(fh)
        for l in res["lines"]:
            if l["line"].lower() == a.account.lower():
                return money(l["current"], "pl"), money(l.get("prior", "0"), "pl")
        raise InputError(f"'{a.account}' is not a line in {a.pl}")
    if a.pl_current is None or a.pl_prior is None:
        raise InputError("pass --pl pl_variance.json, or both --pl-current and --pl-prior")
    return money(a.pl_current, "pl-current"), money(a.pl_prior, "pl-prior")


def trace(a):
    cur_pl, pri_pl = pl_amounts(a)
    cur = rows_for(a.sources, a.account, a.current_period)
    pri = rows_for(a.sources, a.account, a.prior_period)
    sc = sum((r["amount"] for r in cur), Decimal(0))
    sp = sum((r["amount"] for r in pri), Decimal(0))
    for label, src_total, pl_total in (("current", sc, cur_pl), ("prior", sp, pri_pl)):
        if src_total and pl_total and (src_total > 0) != (pl_total > 0):
            raise InputError(f"{a.account} {label}: source rows total {src_total} but the P&L line is {pl_total} (opposite sign). "
                             "Card or bank outflows are negative: reshape that source with --negate, then trace again")
    change = cur_pl - pri_pl
    traced = sc - sp
    return {"account": a.account, "pl_current": str(cur_pl), "pl_prior": str(pri_pl), "change": str(change),
            "sources_current": str(sc), "sources_prior": str(sp), "traced_change": str(traced),
            "untraced_change": str(change - traced), "untraced_current": str(cur_pl - sc),
            "untraced_prior": str(pri_pl - sp), "rows": cur + pri}


def show(t):
    print(f"{t['account']}: P&L {t['pl_prior']} -> {t['pl_current']} (change {t['change']})")
    print(f"  source rows: prior {t['sources_prior']}, current {t['sources_current']}; traced change {t['traced_change']}; "
          f"UNTRACED change {t['untraced_change']} (current untraced {t['untraced_current']}, prior untraced {t['untraced_prior']})")
    for r in t["rows"]:
        print(f"  {r['period']} {r['date']} {r['ref']} {r['amount']} ({r['source']} line {r['line']})")


def selftest():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = os.path.join(here, "examples", "april-2026", "sources.csv")
    mk = lambda acc, c, p: argparse.Namespace(account=acc, current_period="2026-04", prior_period="2026-03", pl=None,
                                              pl_current=c, pl_prior=p, sources=[src])
    t = trace(mk("Sales - Retainers", "16500.00", "13000.00"))
    assert t["traced_change"] == "3500.00" and t["untraced_change"] == "0.00", t
    t = trace(mk("Sales - Projects", "5350.00", "5200.00"))
    assert t["untraced_change"] == "150.00", t
    t = trace(mk("Freelancers", "6900.00", "5100.00"))
    assert t["untraced_change"] == "0.00", t
    # The same trace from the real shapes: kit invoice register + owner map, and a GL detail export.
    import tempfile
    ex = os.path.join(here, "examples", "april-2026")
    with tempfile.TemporaryDirectory() as tmp:
        # The register in invoice-drafting-and-issue's shape: per-period line_keys,
        # issued_per_owner / voided_per_owner / approved_to_issue (no issued_on yet).
        inv = argparse.Namespace(inp=os.path.join(ex, "invoice-register.csv"), date_col="issued_on", amount_col="amount",
                                 ref_col="number", account_col=None, key_col="line_key", key_strip_period=True,
                                 account_map=os.path.join(ex, "line-accounts.csv"), skip_status=None, include_status=None,
                                 negate=False, status_col="status", out=os.path.join(tmp, "inv.csv"))
        rows, unmapped, skipped = reshape(inv)
        assert skipped == 2 and [u["key"] for u in unmapped] == ["C-7/deposit/2026-04"], (skipped, unmapped)
        assert not any(r["ref"] == "INV-1046" for r in rows), "voided invoice traced as revenue"
        nomap = reshape(argparse.Namespace(**dict(vars(inv), key_strip_period=False, out=os.path.join(tmp, "x.csv"))))[1]
        assert len(nomap) == 11, nomap  # per-period keys never match a stable map without stripping
        try:
            reshape(argparse.Namespace(**dict(vars(inv), account_map=None)))
            raise AssertionError("reshape without an owner map accepted")
        except InputError:
            pass
        gl = argparse.Namespace(inp=os.path.join(ex, "gl-detail.csv"), date_col="Date", amount_col="Amount", ref_col="Num",
                                account_col="Account", key_col=None, account_map=None, skip_status="", status_col="status",
                                include_status=None, key_strip_period=False, negate=False, out=os.path.join(tmp, "gl.csv"))
        reshape(gl)
        real = [inv.out, gl.out]
        for acc, c, p, untraced in (("Sales - Retainers", "16500.00", "13000.00", "0.00"),
                                    ("Sales - Projects", "5350.00", "5200.00", "150.00"),
                                    ("Freelancers", "6900.00", "5100.00", "0.00")):
            t = trace(argparse.Namespace(**dict(vars(mk(acc, c, p)), sources=real)))
            assert t["untraced_change"] == untraced, (acc, t)
        # Expense review rows are outflows (negative): refused unless reshaped with --negate.
        rv = os.path.join(tmp, "review.csv")
        with open(rv, "w", encoding="utf-8") as fh:
            fh.write("txn_date,vendor,amount,proposed_account,status\n"
                     "2026-03-05,FIGMA,-580.00,Software,approved\n"
                     "2026-04-03,FIGMA,-620.00,Software,approved\n"
                     "2026-04-15,FIGMA,-45.00,Software,proposed\n")
        ex_ns = argparse.Namespace(inp=rv, date_col="txn_date", amount_col="amount", ref_col=None, account_col="proposed_account",
                                   key_col=None, account_map=None, skip_status=None, include_status="approved",
                                   key_strip_period=False, negate=False, status_col="status", out=os.path.join(tmp, "exp.csv"))
        reshape(ex_ns)
        try:
            trace(argparse.Namespace(**dict(vars(mk("Software", "620.00", "580.00")), sources=[ex_ns.out])))
            raise AssertionError("opposite-sign source accepted")
        except InputError:
            pass
        _, _, skipped = reshape(argparse.Namespace(**dict(vars(ex_ns), negate=True)))
        assert skipped == 1, "a proposed (unapproved) row was counted"
        t = trace(argparse.Namespace(**dict(vars(mk("Software", "620.00", "580.00")), sources=[ex_ns.out])))
        assert t["traced_change"] == "40.00" and t["untraced_change"] == "0.00", t
    print("selftest ok")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--account")
    p.add_argument("--current-period")
    p.add_argument("--prior-period")
    p.add_argument("--pl")
    p.add_argument("--pl-current")
    p.add_argument("--pl-prior")
    p.add_argument("--sources", nargs="+")
    p.add_argument("--out")
    p.add_argument("--reshape", action="store_true", help="rename an export's columns to the trace shape (see above)")
    p.add_argument("--in", dest="inp")
    p.add_argument("--date-col", default="date")
    p.add_argument("--amount-col", default="amount")
    p.add_argument("--ref-col")
    p.add_argument("--account-col")
    p.add_argument("--key-col", help="column holding a key (e.g. line_key) that --account-map turns into an account")
    p.add_argument("--account-map", help="owner-confirmed CSV: key,account")
    p.add_argument("--skip-status", help="comma list of status values to leave out")
    p.add_argument("--include-status", help="comma list of the only status values to count, e.g. issued_per_owner "
                   "(default with --key-col: issued_per_owner); other rows go to <out>.skipped.csv")
    p.add_argument("--key-strip-period", action="store_true",
                   help="drop a trailing /YYYY-MM from the key before the map lookup (kit line_key)")
    p.add_argument("--negate", action="store_true", help="flip the amount sign (card/bank outflows to P&L cost)")
    p.add_argument("--status-col", default="status")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    if a.selftest:
        return selftest()
    if a.reshape:
        if not (a.inp and a.out):
            p.error("--reshape needs --in and --out")
        try:
            rows, unmapped, skipped = reshape(a)
        except InputError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(f"wrote {len(rows)} rows to {a.out}; skipped {skipped} by status"
              + (f" (listed in {a.out}.skipped.csv; they are not traced)" if skipped else ""))
        if unmapped:
            total = sum((Decimal(u["amount"]) for u in unmapped), Decimal(0))
            print(f"UNMAPPED: {len(unmapped)} rows ({total}) have a key not in the account map; listed in {a.out}.unmapped.csv. "
                  "They stay untraced. Ask the owner to map the key; never assign an account yourself.")
        return 0
    if not (a.account and a.current_period and a.prior_period and a.sources):
        p.error("--account, --current-period, --prior-period and --sources are required")
    try:
        t = trace(a)
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    show(t)
    if a.out:
        new = not os.path.exists(a.out)
        with open(a.out, "a", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            if new:
                w.writerow(["account", "period", "date", "ref", "amount", "source", "line", "untraced_change_for_account"])
            for r in t["rows"]:
                w.writerow([t["account"], r["period"], r["date"], r["ref"], r["amount"], r["source"], r["line"], t["untraced_change"]])
        print(f"appended to {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
