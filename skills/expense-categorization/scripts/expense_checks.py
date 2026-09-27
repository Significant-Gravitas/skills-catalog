#!/usr/bin/env python3
"""Deterministic checks on a transaction export before and after coding.

    cd ~/skills/expense-categorization && python3 scripts/expense_checks.py \
        --tx /home/user/work/amex.canonical.csv \
        [--receipts /home/user/work/receipts.csv] [--control-total -900.69] \
        [--threshold 75 --threshold-source "26 CFR 1.274-5, per Dev 2026-05-02"] \
        --out /home/user/work/checks.json

Input --tx is a canonical CSV (normalize_export.py); repeat it to check a bank
and a card export together, which also finds the same cost paid on both.
Amounts: money out of the account negative. Row ids are "<file>:<line>".

It reports, per row and in total:
- totals: rows, money out, money in, net; tie to --control-total if given
  (exit 1 when they differ, with the difference);
- exact duplicates (same date, amount, description) and likely duplicates
  (same amount and vendor key within --dup-window-days); both rows are kept;
- special lines that must not be coded as operating expense without a
  question: refund/reversal, transfer, card payment, owner, loan, tax,
  payroll, processor, foreign currency, money in (patterns in
  references/special-lines.md; override with --patterns CSV of kind,regex);
- receipts (optional CSV: receipt_id,date,amount,currency,merchant,file) tied
  one-to-one to a payment line with the same absolute amount and currency and
  a date within --receipt-window-days; a receipt with no payment line is an
  exception, never support;
- rows at or above an owner-supplied substantiation threshold (off unless
  --threshold is given; it must come with --threshold-source).

Defaults (confirm with the owner): --dup-window-days 14, --receipt-window-days 3.
Never edits an input. Exit 0 ok, 1 control total mismatch, 2 bad input.
"""

import argparse
import csv
import json
import os
import re
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bkio  # noqa: E402

DEFAULT_PATTERNS = [
    ("refund", r"\b(REFUND|REVERSAL|REVERSED|RETURN|CHARGEBACK|CREDIT VOUCHER)\b"),
    ("card_payment", r"\b(AMEX PAYMENT|CARD PAYMENT|PAYMENT RECEIVED|PAYMENT THANK YOU|CC PAYMENT)\b"),
    ("transfer", r"\b(TFR|TRANSFER|XFER|TRF|INTERNAL TRANSFER|TO SAVINGS)\b"),
    ("owner", r"\b(DRAWINGS?|OWNER|DIRECTOR'?S? LOAN|DLA|PERSONAL)\b"),
    ("loan", r"\b(LOAN|FUNDING CIRCLE|IWOCA|MORTGAGE|LENDING|FINANCE DD|SBA)\b"),
    ("tax", r"\b(HMRC|IRS|EFTPS|VAT|SALES TAX|FRANCHISE TAX|CORP TAX|COMPANIES HOUSE)\b"),
    ("payroll", r"\b(PAYROLL|GUSTO|ADP|SALARY|SALARIES|WAGES|PAYE|NEST|PENSION)\b"),
    ("processor", r"\b(STRIPE|PAYPAL|SQUARE|SUMUP|ZETTLE|SHOPIFY PAYMENTS)\b"),
    ("foreign_currency", r"\b(USD|EUR|GBP|CAD|AUD|NZD|CHF|JPY)\s?\d|\b(FX|NON[- ]STERLING|FOREIGN|INTL)\b"),
]
DEFAULT_DUP_WINDOW = 14      # days; default, confirm with the owner
DEFAULT_RECEIPT_WINDOW = 3   # days; default, confirm with the owner


def load_patterns(path):
    if not path:
        return [(k, re.compile(p, re.I)) for k, p in DEFAULT_PATTERNS]
    _, rows = bkio.read_csv(path)
    return [(r["kind"], re.compile(r["regex"], re.I)) for r in rows]


def read_receipts(path):
    _, rows = bkio.read_csv(path)
    out = []
    for r in rows:
        for col in ("receipt_id", "date", "amount"):
            if not r.get(col):
                raise bkio.InputError(f"receipts file {path} line {r['_row']}: {col} is empty; "
                                      "fix the receipts CSV after confirming the value with the user")
        amt, _ = bkio.parse_amount(r["amount"])
        try:
            rdate = bkio.parse_iso(r["date"])
        except bkio.InputError:
            raise bkio.InputError(f"receipts file {path} line {r['_row']}: date '{r['date']}' is not "
                                  "YYYY-MM-DD; confirm the date with the user and fix the receipts CSV") from None
        out.append({"receipt_id": r["receipt_id"], "date": rdate,
                    "amount": abs(amt), "currency": r.get("currency", ""),
                    "merchant": r.get("merchant", ""), "file": r.get("file", "")})
    return out


def rid(t):
    return f"{t['source_file']}:{t['source_row']}"


def run(tx_paths, receipts_path=None, control_total=None, dup_window=DEFAULT_DUP_WINDOW,
        receipt_window=DEFAULT_RECEIPT_WINDOW, threshold=None, threshold_source=None,
        patterns_path=None):
    if isinstance(tx_paths, str):
        tx_paths = [tx_paths]
    tx = []
    for path in tx_paths:
        part = bkio.read_canonical(path)
        if not part:
            raise bkio.InputError(f"{path} has no rows")
        tx.extend(part)
    patterns = load_patterns(patterns_path)
    rows = []
    for t in tx:
        special = [k for k, rx in patterns if rx.search(t["description"] or "")]
        if t["amount"] > 0 and "refund" not in special and "card_payment" not in special:
            special.append("money_in")
        rows.append({
            "id": rid(t), "source_file": t["source_file"], "source_row": int(t["source_row"]),
            "date": t["date"].isoformat(), "description": t["description"],
            "amount": str(t["amount"]), "currency": t["currency"],
            "special": special, "duplicate_of": [], "likely_duplicate_of": [],
            "receipt": None, "threshold_flag": False,
        })

    # duplicates: keep both rows, point each at the other
    for i, a in enumerate(tx):
        for j in range(i + 1, len(tx)):
            b = tx[j]
            if a["amount"] != b["amount"] or a["currency"] != b["currency"]:
                continue
            same_desc = (a["description"] or "").strip().lower() == (b["description"] or "").strip().lower()
            if a["date"] == b["date"] and same_desc:
                rows[i]["duplicate_of"].append(rows[j]["id"])
                rows[j]["duplicate_of"].append(rows[i]["id"])
            elif (abs((a["date"] - b["date"]).days) <= dup_window
                  and bkio.norm_text(a["description"]) == bkio.norm_text(b["description"])):
                rows[i]["likely_duplicate_of"].append(rows[j]["id"])
                rows[j]["likely_duplicate_of"].append(rows[i]["id"])

    receipts_report = None
    if receipts_path:
        receipts = read_receipts(receipts_path)
        used = set()
        unmatched = []
        for rc in sorted(receipts, key=lambda r: r["date"]):
            best = None
            for idx, t in enumerate(tx):
                if idx in used or abs(t["amount"]) != rc["amount"]:
                    continue
                if rc["currency"] and t["currency"] and rc["currency"] != t["currency"]:
                    continue
                gap = abs((t["date"] - rc["date"]).days)
                if gap <= receipt_window and (best is None or gap < best[1]):
                    best = (idx, gap)
            if best is None:
                unmatched.append(rc["receipt_id"])
            else:
                used.add(best[0])
                rows[best[0]]["receipt"] = rc["receipt_id"]
        receipts_report = {
            "receipts": len(receipts),
            "tied": len(receipts) - len(unmatched),
            "receipts_without_payment_line": unmatched,
            "rows_without_receipt": [r["id"] for r in rows
                                     if r["receipt"] is None and Decimal(r["amount"]) < 0],
        }

    if threshold is not None:
        for r in rows:
            if Decimal(r["amount"]) < 0 and abs(Decimal(r["amount"])) >= threshold:
                r["threshold_flag"] = True

    out_total = sum((t["amount"] for t in tx if t["amount"] < 0), Decimal(0))
    in_total = sum((t["amount"] for t in tx if t["amount"] > 0), Decimal(0))
    net = out_total + in_total
    currencies = sorted({t["currency"] for t in tx})
    tie = None
    if control_total is not None:
        tie = {"control_total": str(control_total), "net": str(net),
               "difference": str(net - control_total), "ties": net == control_total}
    return {
        "file": ", ".join(os.path.basename(p) for p in tx_paths),
        "totals": {"rows": len(tx), "money_out": str(out_total), "money_in": str(in_total),
                   "net": str(net), "currencies": currencies},
        "control_tie": tie,
        "exact_duplicate_rows": [r["id"] for r in rows if r["duplicate_of"]],
        "likely_duplicate_rows": [r["id"] for r in rows if r["likely_duplicate_of"]],
        "duplicate_pairs": sorted({tuple(sorted((r["id"], o))) for r in rows
                                   for o in r["duplicate_of"] + r["likely_duplicate_of"]}),
        "special_rows": {r["id"]: r["special"] for r in rows if r["special"]},
        "receipts": receipts_report,
        "threshold": None if threshold is None else {"value": str(threshold), "source": threshold_source,
                                                    "rows": [r["id"] for r in rows if r["threshold_flag"]]},
        "rows": rows,
    }


def print_summary(res):
    t = res["totals"]
    print(f"{res['file']}: {t['rows']} rows; out {t['money_out']}; in {t['money_in']}; net {t['net']}; "
          f"currencies {', '.join(t['currencies'])}")
    if res["control_tie"]:
        c = res["control_tie"]
        print(f"control total {c['control_total']}: {'TIES' if c['ties'] else 'DOES NOT TIE, difference ' + c['difference']}")
    print(f"exact duplicates (keep both, ask): {res['exact_duplicate_rows'] or 'none'}")
    print(f"likely duplicates (keep both, ask): {res['likely_duplicate_rows'] or 'none'}")
    for a, b in res["duplicate_pairs"]:
        print(f"  pair: {a} <-> {b}")
    for row, kinds in res["special_rows"].items():
        print(f"special line row {row}: {', '.join(kinds)}")
    if res["receipts"]:
        r = res["receipts"]
        print(f"receipts: {r['tied']} of {r['receipts']} tied to a payment line")
        if r["receipts_without_payment_line"]:
            print(f"EXCEPTION receipts with no payment line: {r['receipts_without_payment_line']}")
        print(f"money-out rows without a receipt: {r['rows_without_receipt'] or 'none'}")
    if res["threshold"]:
        print(f"at or above owner-supplied threshold {res['threshold']['value']} "
              f"({res['threshold']['source']}): rows {res['threshold']['rows'] or 'none'}")


def selftest():
    import tempfile
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, here)
    import normalize_export
    ex = os.path.join(here, "..", "examples", "bramble-april-card")
    rows = normalize_export.normalize(os.path.join(ex, "amex-2026-04.csv"), "%Y-%m-%d", flip=True)
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "amex.canonical.csv")
        bkio.write_csv(p, bkio.CANONICAL, rows)
        res = run(p, os.path.join(ex, "receipts.csv"), control_total=Decimal("-900.69"))
    assert res["totals"]["net"] == "-900.69", res["totals"]
    assert res["control_tie"]["ties"] is True
    a = "amex-2026-04.csv:"
    assert res["exact_duplicate_rows"] == [a + "6", a + "7"], res["exact_duplicate_rows"]
    assert res["likely_duplicate_rows"] == [a + "2", a + "5"], res["likely_duplicate_rows"]
    assert "refund" in res["special_rows"][a + "8"], res["special_rows"]
    assert {"foreign_currency", "processor"} <= set(res["special_rows"][a + "9"])
    assert res["receipts"]["receipts_without_payment_line"] == ["R4"], res["receipts"]
    assert res["receipts"]["tied"] == 3
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tx", action="append", help="canonical CSV; repeat to check bank and card together")
    ap.add_argument("--receipts")
    ap.add_argument("--control-total")
    ap.add_argument("--dup-window-days", type=int, default=DEFAULT_DUP_WINDOW)
    ap.add_argument("--receipt-window-days", type=int, default=DEFAULT_RECEIPT_WINDOW)
    ap.add_argument("--threshold")
    ap.add_argument("--threshold-source")
    ap.add_argument("--patterns")
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.tx:
        bkio.die("--tx is required", "normalise the export first, then pass the canonical CSV")
    if a.threshold and not a.threshold_source:
        bkio.die("--threshold needs --threshold-source",
                 "quote where the owner or accountant gave the figure; never use a figure from memory")
    try:
        ct = bkio.parse_amount(a.control_total)[0] if a.control_total else None
        th = bkio.parse_amount(a.threshold)[0] if a.threshold else None
        res = run(a.tx, a.receipts, ct, a.dup_window_days, a.receipt_window_days, th,
                  a.threshold_source, a.patterns)
    except bkio.InputError as e:
        bkio.die(str(e), "check the file paths and columns; correct a receipts CSV if the error names it, "
                 "but never edit the source export")
    print_summary(res)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=2)
        print(f"checks written to {a.out}")
    if res["control_tie"] and not res["control_tie"]["ties"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
