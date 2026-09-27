#!/usr/bin/env python3
"""Write one raw export as a canonical CSV that every bookkeeping script reads.

Run only after profile_sources.py, and only after the owner has confirmed the
date format when it was AMBIGUOUS and the sign convention when SIGN_CHECK fired:

    cd ~/skills/<slug> && python3 scripts/normalize_export.py /home/user/in/bank.csv \
        --date-format %d/%m/%Y --currency GBP --out /home/user/work/bank.canonical.csv

Canonical columns: source_file, source_row, date (ISO), description,
amount (money in +, money out -), currency, reference, balance.

Options
    --date-format FMT   required; strptime format confirmed with the owner
    --currency CCY      required when the file has no currency column; no default
    --flip-sign         multiply amounts by -1 (card exports that show charges
                        as positive); only after the owner confirms
    --map role=Column   override detected columns (see profile_sources.py)
    --header-line N     the 1-based line holding the column names, when a bank
                        preamble above it is not skipped automatically
    --skip-row LINE     leave out one file line (repeatable), only for a row the
                        owner confirmed is not a transaction, such as an
                        "Opening balance / brought forward" row with a balance
                        and no amount; each skipped line and its balance is
                        printed to stderr so it can be quoted
    --out PATH          output file (default: stdout)
    --selftest

The column map used is printed to stderr so the user can check it. Rows whose
date or amount cannot be read stop the run (exit 2) with the line number;
so does a row with more cells than the header or the normal row width
(RAGGED_ROWS: an unquoted comma would shift the amount, even when the last
column is empty) and a row with both a debit and a credit filled
(BOTH_DEBIT_AND_CREDIT). Nothing is skipped silently. The input file is never
modified.
"""

import argparse
import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bkio  # noqa: E402


def normalize(path, date_format, currency=None, flip=False, mapping=None, skip=(), header_line=None):
    header, rows = bkio.read_csv(path, header_line=header_line)
    cols = {role: bkio.find_column(header, role, mapping) for role in bkio.COLUMN_HINTS}
    if cols["date"] is None:
        raise bkio.InputError(f"no date column in {header}; pass --map date=<Column>")
    if cols["amount"] is None and cols["debit"] is None and cols["credit"] is None:
        raise bkio.InputError(f"no amount column in {header}; pass --map amount=<Column>, or "
                              "--header-line <N> if these are not the column names")
    if cols["currency"] is None and not currency:
        raise bkio.InputError("the file has no currency column; pass --currency (ask the owner, never assume)")
    print("column map: " + ", ".join(f"{k}={v}" for k, v in cols.items() if v), file=sys.stderr)
    out = []
    name = os.path.basename(path)
    skip = {int(x) for x in skip or ()}
    unknown = skip - {r["_row"] for r in rows}
    if unknown:
        raise bkio.InputError(f"--skip-row {sorted(unknown)}: no such data line in {os.path.basename(path)}")
    for r in rows:
        line = r["_row"]
        if line in skip:
            bal = r.get(cols["balance"], "") if cols["balance"] else ""
            print(f"skipped line {line} (--skip-row): {r.get(cols['description'], '') if cols['description'] else ''}"
                  f" balance={bal or 'none'}", file=sys.stderr)
            continue
        try:
            d = bkio.parse_date(r.get(cols["date"], ""), date_format)
            if cols["amount"]:
                amt, _ = bkio.parse_amount(r.get(cols["amount"]))
            else:
                db, _ = bkio.parse_amount(r.get(cols["debit"])) if cols["debit"] else (None, [])
                cr, _ = bkio.parse_amount(r.get(cols["credit"])) if cols["credit"] else (None, [])
                if db is not None and cr is not None and db != 0 and cr != 0:
                    raise bkio.InputError(
                        f"BOTH_DEBIT_AND_CREDIT: debit {db} and credit {cr} on one row (usually an "
                        "unquoted comma that shifted the cells); ask the owner for a properly quoted "
                        "export, never pick one")
                amt = None if db is None and cr is None else (cr or Decimal(0)) - abs(db or Decimal(0))
            if amt is None:
                raise bkio.InputError("empty amount (an opening-balance or brought-forward row? "
                                      "if the owner confirms it is not a transaction, rerun with --skip-row "
                                      f"{line} and quote its balance separately)")
            bal = None
            if cols["balance"]:
                bal, _ = bkio.parse_amount(r.get(cols["balance"]))
        except bkio.InputError as e:
            raise bkio.InputError(f"{name} line {line}: {e}") from None
        if flip:
            amt = -amt
        out.append({
            "source_file": name,
            "source_row": line,
            "date": d.isoformat(),
            "description": r.get(cols["description"], "") if cols["description"] else "",
            "amount": str(amt),
            "currency": (r.get(cols["currency"]) if cols["currency"] else currency) or currency or "",
            "reference": r.get(cols["reference"], "") if cols["reference"] else "",
            "balance": "" if bal is None else str(bal),
        })
    return out


def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        card = os.path.join(d, "amex-test.csv")
        with open(card, "w", encoding="utf-8") as fh:
            fh.write("Date,Description,Amount,Currency\n"
                     "2026-04-03,FIGMA,45.00,GBP\n"
                     "2026-04-22,FIGMA REFUND,-45.00,GBP\n")
        rows = normalize(card, "%Y-%m-%d", flip=True)
        assert rows[0]["amount"] == "-45.00" and rows[1]["amount"] == "45.00", rows
        assert rows[0]["source_row"] == 2
        assert all(r["currency"] == "GBP" for r in rows)
        try:
            normalize(card, "%d/%m/%Y")
            raise AssertionError("wrong date format must fail")
        except bkio.InputError as e:
            assert "line 2" in str(e)
        bank = os.path.join(d, "bank-test.csv")
        with open(bank, "w", encoding="utf-8") as fh:
            fh.write("Date,Details,Paid out,Paid in,Balance\n"
                     "03/04/2026,HMRC VAT,\"1,204.40\",,31868.19\n")
        try:
            normalize(bank, "%d/%m/%Y")
            raise AssertionError("missing currency must fail")
        except bkio.InputError:
            pass
        rows = normalize(bank, "%d/%m/%Y", currency="GBP")
        assert rows[0]["amount"] == "-1204.40" and rows[0]["date"] == "2026-04-03", rows
        opening = os.path.join(d, "opening.csv")
        with open(opening, "w", encoding="utf-8") as fh:
            fh.write("Date,Description,Amount,Balance\n01/04/2026,Opening balance,,33072.59\n"
                     "02/04/2026,FIGMA,-45.00,33027.59\n")
        try:
            normalize(opening, "%d/%m/%Y", currency="GBP")
            raise AssertionError("an empty amount must stop the run")
        except bkio.InputError as e:
            assert "--skip-row 2" in str(e), e
        rows = normalize(opening, "%d/%m/%Y", currency="GBP", skip=[2])
        assert [r["source_row"] for r in rows] == [3], rows
        ragged = os.path.join(d, "ragged.csv")
        with open(ragged, "w", encoding="utf-8") as fh:
            fh.write("Date,Description,Amount\n2026-04-05,SCREWFIX TRADE 2,5,89.00\n")
        try:
            normalize(ragged, "%Y-%m-%d", currency="GBP")
            raise AssertionError("a ragged row must stop the run, not shift the amount")
        except bkio.InputError as e:
            assert "RAGGED_ROWS on lines [2]" in str(e), e
        # the shifted row's last column is empty: still ragged, never +5 income
        rag2 = os.path.join(d, "ragged-trailing-empty.csv")
        with open(rag2, "w", encoding="utf-8") as fh:
            fh.write("Date,Description,Amount,Reference\n2026-04-03,FIGMA,-45.00,FT1\n"
                     "2026-04-05,SCREWFIX TRADE 2,5,-89.00,\n2026-04-07,TRAINLINE,-118.40,FT3\n")
        try:
            normalize(rag2, "%Y-%m-%d", currency="GBP")
            raise AssertionError("a ragged row with an empty last cell must stop the run")
        except bkio.InputError as e:
            assert "RAGGED_ROWS on lines [3]" in str(e), e
        rag3 = os.path.join(d, "ragged-debcred.csv")
        with open(rag3, "w", encoding="utf-8") as fh:
            fh.write("Date,Description,Paid out,Paid in,Balance\n2026-04-03,FIGMA,45.00,,955.00\n"
                     "2026-04-05,SCREWFIX 2,5,89.00,,\n2026-04-07,CLIENT,,500.00,1366.00\n")
        try:
            normalize(rag3, "%Y-%m-%d", currency="GBP")
            raise AssertionError("a shifted debit/credit row must stop the run")
        except bkio.InputError as e:
            assert "RAGGED_ROWS on lines [3]" in str(e), e
        both = os.path.join(d, "both.csv")
        with open(both, "w", encoding="utf-8") as fh:
            fh.write("Date,Description,Paid out,Paid in\n2026-04-05,ODD ROW,5.00,89.00\n")
        try:
            normalize(both, "%Y-%m-%d", currency="GBP")
            raise AssertionError("a row with debit and credit must stop the run")
        except bkio.InputError as e:
            assert "line 2" in str(e) and "BOTH_DEBIT_AND_CREDIT" in str(e), e
        pre = os.path.join(d, "preamble.csv")
        with open(pre, "w", encoding="utf-8") as fh:
            fh.write("Account Name:,Bramble Design Ltd,Sort Code:,20-00-00\nAccount Number:,12345678,,\n\n"
                     "Date,Description,Amount,Balance\n02/04/2026,FIGMA,-45.00,955.00\n")
        rows = normalize(pre, "%d/%m/%Y", currency="GBP")
        assert rows[0]["amount"] == "-45.00" and rows[0]["source_row"] == 5, rows
        assert normalize(pre, "%d/%m/%Y", currency="GBP", header_line=4) == rows
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?")
    ap.add_argument("--date-format")
    ap.add_argument("--currency")
    ap.add_argument("--flip-sign", action="store_true")
    ap.add_argument("--map", action="append")
    ap.add_argument("--skip-row", action="append", default=[])
    ap.add_argument("--out")
    ap.add_argument("--header-line", type=int)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.file or not a.date_format:
        bkio.die("a file and --date-format are required",
                 "run profile_sources.py first; if the date format is AMBIGUOUS, ask the owner")
    try:
        rows = normalize(a.file, a.date_format, a.currency, a.flip_sign, bkio.parse_mapping(a.map),
                         [int(x) for x in a.skip_row], a.header_line)
    except ValueError:
        bkio.die("--skip-row takes a file line number", "e.g. --skip-row 2")
    except bkio.InputError as e:
        bkio.die(str(e), "fix the mapping, format or --skip-row and rerun, or ask the owner for a "
                 "corrected export; do not edit the source export")
    bkio.write_csv(a.out, bkio.CANONICAL, rows)
    if a.out:
        print(f"{len(rows)} rows written to {a.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
