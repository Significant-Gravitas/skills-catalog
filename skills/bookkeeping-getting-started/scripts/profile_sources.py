#!/usr/bin/env python3
"""Profile raw bank, card, billing or ledger CSV exports before any bookkeeping.

Run (from the package copy in the sandbox):
    cd ~/skills/bookkeeping-getting-started && \
      python3 scripts/profile_sources.py /home/user/in/*.csv --out /home/user/out/profile.json

Per file it reports: data rows, blank rows skipped, the column it used for each
role, date range and every date format that fits (with an AMBIGUOUS flag when
day/month and month/day both fit), amount layout (one signed column or separate
debit/credit), inflow/outflow/net totals as exact decimals, currencies seen,
running-balance continuity (first break row), duplicate keys (reference/FITID
if present, else date + amount + description), rows whose amount could not
be read, RAGGED_ROWS (more cells than the header or the normal row width,
counting empty cells: an unquoted comma that shifts the amount; Blocked until a
properly quoted export arrives), and BOTH_DEBIT_AND_CREDIT (a row with both a
debit and a credit filled: usually the same shift; Blocked). Bank preamble
lines (account name, sort code ...) above the header are skipped. It never
edits an input file.

Options
    --map role=Column[,role=Column]   override detected columns (roles: date,
                                      description, amount, debit, credit,
                                      balance, currency, reference)
    --header-line N                   the 1-based line that holds the column
                                      names, when the header is not detected
    --out PATH                        also write the profile as JSON
    --selftest                        run against examples/ fixtures and exit

Exit codes: 0 profiled (read the flags), 2 input problem (message says what to fix).
XLSX: save the sheet as CSV first; this script reads CSV only.
"""

import argparse
import json
import os
import sys
from collections import Counter
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bkio  # noqa: E402


def profile(path, mapping=None, header_line=None):
    header, rows, ragged = bkio.read_csv_report(path, header_line=header_line)
    cols = {role: bkio.find_column(header, role, mapping) for role in bkio.COLUMN_HINTS}
    if cols["amount"] is None and (cols["debit"] is None and cols["credit"] is None):
        raise bkio.InputError(
            f"{path}: no amount column found in {header}; pass --map amount=<Column> "
            "or --map debit=<Column>,credit=<Column>; if those are not column names, the header "
            "was not found: pass --header-line <N> (the line holding the column names)")
    if cols["date"] is None:
        raise bkio.InputError(f"{path}: no date column found in {header}; pass --map date=<Column>")
    flags = []
    if ragged:
        flags.append(f"RAGGED_ROWS on lines {ragged[:10]}{'...' if len(ragged) > 10 else ''}: more cells "
                     f"than the {len(header)} header columns (usually an unquoted comma in a description); "
                     "the amounts on these lines cannot be trusted. Blocked: ask for a properly quoted export")
    layout = "signed" if cols["amount"] else "debit_credit"

    date_values = [r.get(cols["date"], "") for r in rows]
    formats, ambiguous = bkio.detect_date_formats(date_values)
    if not rows:
        flags.append("NO_ROWS: the export has a header but no transactions; confirm there were no "
                     "transactions in the period and get the statement balance")
    elif not formats:
        bad = next((v for v in date_values if v and not bkio.detect_date_formats([v])[0]), "?")
        flags.append(f"UNREADABLE_DATES (example '{bad}')")
    if ambiguous:
        flags.append("AMBIGUOUS_DATE_FORMAT: day/month and month/day both fit every row; "
                     "ask the owner which the bank uses")
    fmt = formats[0] if formats else None

    amounts, unreadable, amount_flags, both = [], [], Counter(), []
    for r in rows:
        try:
            if layout == "signed":
                val, fl = bkio.parse_amount(r.get(cols["amount"]))
            else:
                d, fl1 = bkio.parse_amount(r.get(cols["debit"])) if cols["debit"] else (None, [])
                c, fl2 = bkio.parse_amount(r.get(cols["credit"])) if cols["credit"] else (None, [])
                fl = fl1 + fl2
                if d is not None and c is not None and d != 0 and c != 0:
                    both.append(r["_row"])
                val = None if d is None and c is None else (c or Decimal(0)) - abs(d or Decimal(0))
            amount_flags.update(fl)
            if val is None:
                unreadable.append(r["_row"])
            amounts.append(val)
        except bkio.InputError:
            unreadable.append(r["_row"])
            amounts.append(None)
    if unreadable:
        flags.append(f"UNREADABLE_AMOUNTS on lines {unreadable[:10]}{'...' if len(unreadable) > 10 else ''}")
    if both:
        flags.append(f"BOTH_DEBIT_AND_CREDIT on lines {both[:10]}{'...' if len(both) > 10 else ''}: "
                     "a debit and a credit on one row (usually an unquoted comma that shifted the cells); "
                     "the amounts on these lines cannot be trusted. Blocked: ask for a properly quoted export")
    if amount_flags.get("decimal_comma"):
        flags.append("DECIMAL_COMMA seen: confirm the export locale")

    dates = []
    if fmt:
        for v in date_values:
            try:
                dates.append(bkio.parse_date(v, fmt) if v else None)
            except bkio.InputError:
                dates.append(None)
    real = [d for d in dates if d]
    order = "unknown"
    if len(real) > 1:
        if all(a <= b for a, b in zip(real, real[1:])):
            order = "oldest_first"
        elif all(a >= b for a, b in zip(real, real[1:])):
            order = "newest_first"
        else:
            order = "unsorted"

    inflow = sum((a for a in amounts if a is not None and a > 0), Decimal(0))
    outflow = sum((a for a in amounts if a is not None and a < 0), Decimal(0))
    positives = sum(1 for a in amounts if a is not None and a > 0)
    negatives = sum(1 for a in amounts if a is not None and a < 0)

    if positives > negatives:
        flags.append(f"SIGN_CHECK: {positives} positive vs {negatives} negative rows. Card exports often "
                     "show charges as positive; confirm with the owner, then normalise with --flip-sign")

    currencies = Counter(r.get(cols["currency"], "") for r in rows) if cols["currency"] else Counter()
    if len([c for c in currencies if c]) > 1:
        flags.append(f"MULTIPLE_CURRENCIES {dict(currencies)}: keep them apart")

    balance_check = None
    if cols["balance"]:
        balance_check = _balance_continuity(rows, cols["balance"], amounts)
        if balance_check.get("first_break_line"):
            flags.append(f"BALANCE_BREAK at line {balance_check['first_break_line']}: "
                         "a missing page, a missing row or a mid-file sort; do not use this file "
                         "as a control total until explained")

    keys = Counter()
    for r, a in zip(rows, amounts):
        if cols["reference"] and r.get(cols["reference"]):
            keys[("ref", r.get(cols["reference"]))] += 1
        else:
            keys[("dad", r.get(cols["date"]), str(a), (r.get(cols["description"]) or "").strip().lower())] += 1
    dups = [{"key": list(k), "count": n} for k, n in keys.items() if n > 1]
    if dups:
        flags.append(f"DUPLICATE_KEYS x{len(dups)}: could be real repeats; list them for the owner, never drop")

    return {
        "file": os.path.basename(path),
        "rows": len(rows),
        "columns_used": {k: v for k, v in cols.items() if v},
        "amount_layout": layout,
        "row_order": order,
        "date_formats_that_fit": formats,
        "date_format_ambiguous": ambiguous,
        "date_min": min(real).isoformat() if real else None,
        "date_max": max(real).isoformat() if real else None,
        "inflow_total": str(inflow),
        "outflow_total": str(outflow),
        "net_total": str(inflow + outflow),
        "positive_rows": positives,
        "negative_rows": negatives,
        "currencies": {k: v for k, v in currencies.items()},
        "balance_check": balance_check,
        "duplicate_keys": dups[:50],
        "unreadable_amount_lines": unreadable,
        "ragged_lines": ragged,
        "both_debit_and_credit_lines": both,
        "flags": flags,
    }


def _balance_continuity(rows, col, amounts):
    bals = []
    for r in rows:
        try:
            b, _ = bkio.parse_amount(r.get(col))
        except bkio.InputError:
            b = None
        bals.append(b)
    result = {"opening_implied": None, "closing": None, "first_break_line": None, "order_used": None}
    if not rows:
        return result
    for order_name, idx in (("as_listed", list(range(len(rows)))),
                            ("reversed", list(reversed(range(len(rows)))))):
        breaks = []
        for p, c in zip(idx, idx[1:]):
            if None in (bals[p], bals[c], amounts[c]):
                continue
            if bals[p] + amounts[c] != bals[c]:
                breaks.append(rows[c]["_row"])
        if not breaks:
            first, last = idx[0], idx[-1]
            if bals[first] is not None and amounts[first] is not None:
                result["opening_implied"] = str(bals[first] - amounts[first])
            result["closing"] = None if bals[last] is None else str(bals[last])
            result["order_used"] = order_name
            result["first_break_line"] = None   # an earlier order's break is not a break
            result.pop("_n", None)
            return result
        if result["first_break_line"] is None or len(breaks) < result.get("_n", 10**9):
            result["first_break_line"] = breaks[0]
            result["_n"] = len(breaks)
            result["order_used"] = order_name
    result.pop("_n", None)
    return result


def print_table(profiles):
    print("| File | Rows | Dates | Format | Layout | In | Out | Net | Flags |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for p in profiles:
        fmt = "AMBIGUOUS" if p["date_format_ambiguous"] else (p["date_formats_that_fit"] or ["?"])[0]
        print(f"| {p['file']} | {p['rows']} | {p['date_min']} to {p['date_max']} | {fmt} | "
              f"{p['amount_layout']} | {p['inflow_total']} | {p['outflow_total']} | {p['net_total']} | "
              f"{len(p['flags'])} |")
    for p in profiles:
        for f in p["flags"]:
            print(f"- {p['file']}: {f}")


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    ex = os.path.join(here, "..", "examples", "bramble-april-intake")
    bank = profile(os.path.join(ex, "bank-main-2026-04.csv"))
    assert bank["rows"] == 8, bank["rows"]
    assert bank["date_format_ambiguous"] is True, "03/04 style dates must be ambiguous"
    assert bank["balance_check"]["first_break_line"] == 8, bank["balance_check"]
    assert bank["net_total"] == "-179.80", bank["net_total"]
    card = profile(os.path.join(ex, "amex-2026-04.csv"))
    assert card["date_format_ambiguous"] is False
    assert card["amount_layout"] == "signed"
    assert any("DUPLICATE_KEYS" in f for f in card["flags"]), card["flags"]
    assert bkio.parse_amount("(1,234.50)")[0] == Decimal("-1234.50")
    assert bkio.parse_amount("£12.00-")[0] == Decimal("-12.00")
    assert bkio.parse_amount("1.234,56")[0] == Decimal("1234.56")
    # an unquoted comma in a description shifts the amount: flag it, never read it
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        rag = os.path.join(d, "ragged.csv")
        with open(rag, "w", encoding="utf-8") as fh:
            fh.write("Date,Description,Amount\n2026-04-04,TESCO STORES,-12.40\n"
                     "2026-04-05,SCREWFIX TRADE 2,5,89.00\n")
        p = profile(rag)
        assert p["ragged_lines"] == [3], p["ragged_lines"]
        assert any(f.startswith("RAGGED_ROWS") for f in p["flags"]), p["flags"]
        try:
            bkio.read_csv(rag)
            raise AssertionError("read_csv must refuse ragged rows")
        except bkio.InputError as e:
            assert "RAGGED_ROWS on lines [3]" in str(e), e
        # the shifted row's last column is empty: count cells, not non-empty cells
        rag2 = os.path.join(d, "ragged-trailing-empty.csv")
        with open(rag2, "w", encoding="utf-8") as fh:
            fh.write("Date,Description,Amount,Reference\n2026-04-03,FIGMA,-45.00,FT1\n"
                     "2026-04-05,SCREWFIX TRADE 2,5,-89.00,\n2026-04-07,TRAINLINE,-118.40,FT3\n")
        p2 = profile(rag2)
        assert p2["ragged_lines"] == [3], p2["ragged_lines"]
        rag3 = os.path.join(d, "ragged-debcred.csv")
        with open(rag3, "w", encoding="utf-8") as fh:
            fh.write("Date,Description,Paid out,Paid in,Balance\n2026-04-03,FIGMA,45.00,,955.00\n"
                     "2026-04-05,SCREWFIX 2,5,89.00,,\n2026-04-07,CLIENT,,500.00,1366.00\n")
        p3 = profile(rag3)
        assert p3["ragged_lines"] == [3], p3["ragged_lines"]
        assert p3["both_debit_and_credit_lines"] == [3], p3
        assert any(f.startswith("BOTH_DEBIT_AND_CREDIT") for f in p3["flags"]), p3["flags"]
        # every line ending in a comma is a normal width, not ragged
        tc = os.path.join(d, "trailing-comma.csv")
        with open(tc, "w", encoding="utf-8") as fh:
            fh.write("Transaction Date,Transaction Type,Sort Code,Account Number,Transaction Description,"
                     "Debit Amount,Credit Amount,Balance,\n"
                     "03/04/2026,DD,'30-94-57,12345678,FIGMA,45.00,,955.00,\n"
                     "13/04/2026,FPI,'30-94-57,12345678,CLIENT,,500.00,1455.00,\n")
        p4 = profile(tc)
        assert p4["ragged_lines"] == [] and p4["net_total"] == "455.00", p4
        # a bank preamble as wide as the header is not taken as the header
        pre = os.path.join(d, "preamble.csv")
        with open(pre, "w", encoding="utf-8") as fh:
            fh.write("Account Name:,Bramble Design Ltd,Sort Code:,20-00-00\nAccount Number:,12345678,,\n\n"
                     "Date,Description,Amount,Balance\n02/04/2026,FIGMA,-45.00,955.00\n"
                     "13/04/2026,CLIENT,500.00,1455.00\n")
        p5 = profile(pre)
        assert p5["rows"] == 2 and p5["columns_used"]["amount"] == "Amount", p5
        assert profile(pre, header_line=4)["net_total"] == "455.00"
        # a clean newest-first export with a running balance is not a break
        nf = os.path.join(d, "newest.csv")
        with open(nf, "w", encoding="utf-8") as fh:
            fh.write("Date,Description,Amount,Balance\n20/04/2026,CLIENT,500.00,1455.00\n"
                     "13/04/2026,FIGMA,-45.00,955.00\n02/04/2026,OPENING TFR,1000.00,1000.00\n")
        p6 = profile(nf)
        assert p6["balance_check"]["order_used"] == "reversed", p6["balance_check"]
        assert p6["balance_check"]["first_break_line"] is None and "_n" not in p6["balance_check"], p6
        assert not any(f.startswith("BALANCE_BREAK") for f in p6["flags"]), p6["flags"]
        # a header-only export has no rows, not unreadable dates
        ho = os.path.join(d, "header-only.csv")
        with open(ho, "w", encoding="utf-8") as fh:
            fh.write("Date,Description,Amount,Balance\n")
        p7 = profile(ho)
        assert p7["rows"] == 0 and any(f.startswith("NO_ROWS") for f in p7["flags"]), p7["flags"]
        assert not any(f.startswith("UNREADABLE_DATES") for f in p7["flags"]), p7["flags"]
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--map", action="append")
    ap.add_argument("--out")
    ap.add_argument("--header-line", type=int)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.files:
        bkio.die("no files given", "pass one or more CSV paths, e.g. /home/user/in/bank.csv")
    try:
        mapping = bkio.parse_mapping(a.map)
        profiles = []
        for f in a.files:
            if f.lower().endswith((".xlsx", ".xls", ".pdf")):
                bkio.die(f"{f}: not a CSV", "export the statement as CSV, or for a PDF statement type "
                         "the opening balance, closing balance and period into the intake instead")
            profiles.append(profile(f, mapping, a.header_line))
    except bkio.InputError as e:
        bkio.die(str(e), "check the file is the right export, or pass --map role=Column")
    print_table(profiles)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(profiles, fh, indent=2)
        print(f"profile written to {a.out}")


if __name__ == "__main__":
    main()
