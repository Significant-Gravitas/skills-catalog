#!/usr/bin/env python3
"""Extract statement lines from a text-based PDF and PROVE the extraction with the running balance.

Standard library, plus pdfplumber if it is importable, else the `pdftotext` command.
Scanned (image) PDFs will not extract: ask the owner for the bank's CSV export instead.

    cd ~/skills/statement-reconciliation && python3 scripts/extract_statement.py \
        --pdf /home/user/in/statement.pdf --date-format "%d %b %Y" \
        [--opening 20000.00] --closing 23392.50 \
        --out /home/user/in/statement.csv

    # already-extracted text (one statement line per text line):
    python3 scripts/extract_statement.py --text /home/user/in/statement.txt ...

    python3 scripts/extract_statement.py --selftest

How a line is read: it starts with a date in --date-format (or has no date and
inherits the previous one), ends with two money figures: the movement and the
running balance. The sign of each movement is taken from the change in the
running balance, and the size must agree with the printed movement.

Proof (never skippable): every running balance chains from the previous one,
and opening + sum(movements) = closing. Any break prints the page and line and
exits 2: stop and ask for a CSV export. The script never corrects a figure.
"""

import argparse
import csv
import datetime as dt
import os
import re
import shutil
import subprocess
import sys
from decimal import Decimal, InvalidOperation

Q = Decimal("0.01")
MONEY = re.compile(r"^\(?-?£?\$?€?[\d,]*\d\.\d{2}\)?(CR|DR|-)?$", re.IGNORECASE)
OPENING_WORDS = re.compile(r"brought forward|opening balance|balance b/?f|previous balance", re.IGNORECASE)
CLOSING_WORDS = re.compile(r"carried forward|closing balance|balance c/?f|new balance", re.IGNORECASE)


class ProofError(Exception):
    pass


def to_money(tok):
    t = tok.upper().replace(",", "").replace("£", "").replace("$", "").replace("€", "")
    neg = t.startswith("(") or t.endswith("DR") or t.endswith("-") or t.startswith("-")
    t = re.sub(r"[()A-Z\-]", "", t)
    try:
        v = Decimal(t).quantize(Q)
    except InvalidOperation:
        raise ProofError(f"'{tok}' is not a money figure")
    return -v if neg else v


def pdf_lines(path):
    try:
        import pdfplumber  # type: ignore
        out = []
        with pdfplumber.open(path) as pdf:
            for pn, page in enumerate(pdf.pages, start=1):
                for ln, line in enumerate((page.extract_text() or "").splitlines(), start=1):
                    out.append((pn, ln, line))
        return out, "pdfplumber"
    except ImportError:
        pass
    if shutil.which("pdftotext"):
        text = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True, check=True).stdout
        out = []
        for pn, page in enumerate(text.split("\f"), start=1):
            for ln, line in enumerate(page.splitlines(), start=1):
                out.append((pn, ln, line))
        return out, "pdftotext"
    raise ProofError("no PDF text tool: run 'pip install --user pdfplumber' (or install poppler-utils), "
                     "or ask the owner for the bank's CSV export")


def text_lines(path):
    with open(path, encoding="utf-8") as fh:
        pages = fh.read().split("\f")
    return [(pn, ln, line) for pn, pg in enumerate(pages, 1) for ln, line in enumerate(pg.splitlines(), 1)], "text"


def leading_date(tokens, fmt, year):
    for n in (3, 2, 1):
        if len(tokens) < n:
            continue
        cand = " ".join(tokens[:n])
        f = fmt if "%Y" in fmt or "%y" in fmt else fmt + " %Y"
        c = cand if f == fmt else f"{cand} {year}"
        try:
            return dt.datetime.strptime(c, f).date(), n
        except ValueError:
            continue
    return None, 0


def extract(lines, fmt, year, opening, closing):
    rows, cur_date, prev_bal = [], None, opening
    for pn, ln, raw in lines:
        tokens = raw.split()
        if not tokens:
            continue
        d, used = leading_date(tokens, fmt, year)
        rest = tokens[used:]
        money_tail = []
        while rest and MONEY.match(rest[-1]) and len(money_tail) < 2:
            money_tail.insert(0, rest.pop())
        desc = " ".join(rest)
        if OPENING_WORDS.search(raw) and money_tail:
            bal = to_money(money_tail[-1])
            if prev_bal is None:
                prev_bal = bal
            elif bal != prev_bal:
                raise ProofError(f"page {pn} line {ln}: brought-forward balance {bal} differs from opening {prev_bal}")
            if d:
                cur_date = d
            continue
        if CLOSING_WORDS.search(raw):
            continue
        if d:
            cur_date = d
        if len(money_tail) < 2 or cur_date is None:
            continue  # headers, addresses, page furniture
        if prev_bal is None:
            raise ProofError("no opening balance: pass --opening or make sure the 'brought forward' line is extracted")
        printed, bal = to_money(money_tail[0]), to_money(money_tail[1])
        move = bal - prev_bal
        if abs(move) != abs(printed):
            raise ProofError(f"page {pn} line {ln}: running balance moved {move} but the line shows {printed}. "
                             f"Text: '{raw.strip()}'. A line is missing, merged or misread")
        rows.append({"id": f"p{pn}-l{ln}", "date": str(cur_date), "amount": str(move), "description": desc,
                     "reference": "", "fitid": "", "page": pn, "line": ln})
        prev_bal = bal
    if not rows:
        raise ProofError("no statement lines found: check --date-format against the PDF, or ask for a CSV")
    total = sum((Decimal(r["amount"]) for r in rows), Decimal(0))
    start = opening if opening is not None else prev_bal - total
    if closing is not None and start + total != closing:
        raise ProofError(f"opening {start} + movements {total} = {start + total}, but the statement closing is {closing}")
    if closing is not None and prev_bal != closing:
        raise ProofError(f"last running balance {prev_bal} is not the statement closing {closing}")
    return rows, start, total


def selftest():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d = os.path.join(here, "examples", "scenarios", "f-pdf-text")
    lines, _ = text_lines(os.path.join(d, "statement.txt"))
    rows, start, total = extract(lines, "%d %b", 2026, None, Decimal("23392.50"))
    assert start == Decimal("20000.00"), start
    assert len(rows) == 6, len(rows)
    assert rows[5]["amount"] == "-12.50" and rows[1]["date"] == "2026-04-05", rows
    broken, _ = text_lines(os.path.join(d, "statement-missing-line.txt"))
    try:
        extract(broken, "%d %b", 2026, None, Decimal("23392.50"))
    except ProofError as exc:
        assert "running balance moved" in str(exc), exc
    else:
        raise AssertionError("a dropped line was not detected")
    print("selftest ok")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    src = p.add_mutually_exclusive_group()
    src.add_argument("--pdf")
    src.add_argument("--text")
    p.add_argument("--date-format", default="%Y-%m-%d", help="strptime format of the leading date, e.g. '%%d %%b %%Y' or '%%d/%%m/%%Y'")
    p.add_argument("--year", type=int, help="year for dates printed without one")
    p.add_argument("--opening")
    p.add_argument("--closing")
    p.add_argument("--out")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    if a.selftest:
        return selftest()
    if not ((a.pdf or a.text) and a.out and a.closing):
        p.error("--pdf or --text, --closing and --out are required")
    if "%Y" not in a.date_format and "%y" not in a.date_format and not a.year:
        p.error("the date format has no year: pass --year")
    try:
        lines, tool = pdf_lines(a.pdf) if a.pdf else text_lines(a.text)
        opening = Decimal(a.opening).quantize(Q) if a.opening else None
        rows, start, total = extract(lines, a.date_format, a.year, opening, Decimal(a.closing).quantize(Q))
    except (ProofError, subprocess.CalledProcessError) as exc:
        print(f"error: extraction not proven: {exc}\nStop. Do not reconcile from this file; ask for the bank's CSV export.", file=sys.stderr)
        return 2
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "date", "amount", "description", "reference", "fitid", "page", "line"])
        w.writeheader()
        w.writerows(rows)
    print(f"PROVEN ({tool}): {len(rows)} lines; opening {start} + movements {total} = closing {a.closing}. Wrote {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
