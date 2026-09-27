#!/usr/bin/env python3
"""Mask bank, card and contact identifiers in a copy of a CSV before its rows
are read into the conversation (data minimisation).

    cd ~/skills/bookkeeping-getting-started && \
      python3 scripts/redact.py /home/user/in/bank.csv --out /home/user/work/bank.masked.csv

Masks, keeping the last 4 characters: IBANs; UK sort code + account number
pairs; US routing + account style digit runs of 8-17 digits next to the words
account/acct/routing/ABA; 13-19 digit card numbers that pass the Luhn check;
e-mail addresses (kept as first letter + domain); a sort code (NN-NN-NN, with
or without a leading apostrophe) alone in a cell.

Column-aware: in any column whose header names an identifier (account, acct,
a/c, sort code, iban, card, pan, routing, aba), every cell holding 6 or more
digits is masked to its last 4 characters whether or not a keyword is in the
cell (sort codes become **-**-**). The header row is masked too, and a cell
labelled "Account Number:" / "Sort Code:" etc. masks the cell after it. Bank
preamble lines above the header are not copied. Prints how many values were
masked per column and which columns were masked as identifiers.

Options
    --keep-column NAME   never mask this column (e.g. an invoice reference that
                         the matching needs); repeatable
    --header-line N      the 1-based line holding the column names, when the
                         header is not detected
    --out PATH           masked copy (required; the input is never modified)
    --selftest

Work from the masked copy. The original stays in /home/user/in and is not
read into the conversation.
"""

import argparse
import csv
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bkio  # noqa: E402

IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){2,7}(?:\s?[A-Z0-9]{1,4})?\b")
SORT_ACC = re.compile(r"\b(\d{2}-\d{2}-\d{2})\s*(\d{8})\b")
CARD = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")   # ends on a digit: keeps the separator after it
ACCT = re.compile(r"(?i)\b(account|acct|a/c|routing|aba)\b[\s:#no.]*([0-9]{8,17})")
SORT_ONLY = re.compile(r"^'?\d{2}-\d{2}-\d{2}$")
ID_HEADER = re.compile(r"(?i)(\baccount|\bacct|\ba/c\b|\bsort\s*code|\biban\b|\bcard|\bpan\b|"
                       r"\brouting|\baba\b)")
ID_LABEL = re.compile(r"(?i)^\s*(account|acct|a/c|sort\s*code|iban|card|routing|aba)\b[^,]{0,20}:\s*$")
EMAIL = re.compile(r"\b([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")


def luhn_ok(digits):
    total, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        total += d
        alt = not alt
    return total % 10 == 0


def mask_tail(s, keep=4):
    core = re.sub(r"\s|-", "", s)
    return "*" * max(len(core) - keep, 0) + core[-keep:]


def redact_text(text):
    n = 0

    def card(m):
        nonlocal n
        digits = re.sub(r"\D", "", m.group(0))
        if 13 <= len(digits) <= 19 and luhn_ok(digits):
            n += 1
            return mask_tail(digits)
        return m.group(0)

    def iban(m):
        nonlocal n
        n += 1
        return mask_tail(m.group(0))

    def sort_acc(m):
        nonlocal n
        n += 1
        return "**-**-** " + mask_tail(m.group(2))

    def acct(m):
        nonlocal n
        n += 1
        return f"{m.group(1)} {mask_tail(m.group(2))}"

    def email(m):
        nonlocal n
        n += 1
        return f"{m.group(1)}***@{m.group(2)}"

    if SORT_ONLY.match(text.strip()):
        return "**-**-**", 1
    text = IBAN.sub(iban, text)
    text = SORT_ACC.sub(sort_acc, text)
    text = ACCT.sub(acct, text)
    text = CARD.sub(card, text)
    text = EMAIL.sub(email, text)
    return text, n


def mask_id_cell(v):
    """Mask a cell of an identifier column: 6+ digits -> last 4 only."""
    t = v.strip()
    if SORT_ONLY.match(t):
        return "**-**-**", 1
    if len(re.sub(r"\D", "", t)) < 6:
        return v, 0
    core = re.sub(r"[^A-Za-z0-9]", "", t)
    return "*" * max(len(core) - 4, 0) + core[-4:], 1


def redact_file(path, out, keep=(), header_line=None):
    """Write a masked copy. Returns (counts per column, counts per identifier
    column). Ragged rows are copied with every cell, so profile_sources.py
    still sees and flags them on the masked copy."""
    header, rows, _ragged = bkio.read_csv_report(path, header_line=header_line)
    counts, by_column = Counter(), Counter()
    id_cols = {h for h in header if h and h not in keep and ID_HEADER.search(h)}
    masked_header = []
    for h in header:
        v, n = redact_text(h)
        counts["(header)"] += n
        masked_header.append(v)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(masked_header)
        for r in rows:
            cells, label_next = [], False
            for h in [k for k in r if k != "_row"]:
                v = r.get(h, "")
                if h in keep:
                    cells.append(v)
                    label_next = False
                    continue
                if h in id_cols or label_next:
                    v, n = mask_id_cell(v)
                    by_column[h] += n
                    counts[h] += n
                v, n = redact_text(v)
                counts[h] += n
                label_next = bool(ID_LABEL.match(r.get(h, "")))
                cells.append(v)
            w.writerow(cells)
    return counts, by_column


def selftest():
    t, n = redact_text("Card 4111 1111 1111 1111 paid to GB29 NWBK 6016 1331 9268 19, jo@bramble.example")
    assert "1111" in t and "4111 1111" not in t, t
    assert "9268" not in t or "GB29" not in t, t
    assert "j***@bramble.example" in t, t
    assert n == 3, n
    t2, n2 = redact_text("INV-1042 ref 1234567890123")   # not Luhn-valid, no account keyword
    assert n2 == 0 and t2 == "INV-1042 ref 1234567890123", t2
    t3, _ = redact_text("TFR 20-00-00 12345678")
    assert "12345678" not in t3 and "5678" in t3, t3
    t4, _ = redact_text("CARD 4111 1111 1111 1111 TESCO")
    assert t4 == "CARD ************1111 TESCO", t4
    assert redact_text("'30-94-57") == ("**-**-**", 1)
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        # Lloyds/Halifax layout: sort code and account number in their own columns
        src = os.path.join(d, "lloyds.csv")
        with open(src, "w", encoding="utf-8") as fh:
            fh.write("Transaction Date,Transaction Type,Sort Code,Account Number,Transaction Description,"
                     "Debit Amount,Credit Amount,Balance,\n"
                     "03/04/2026,DD,'30-94-57,12345678,FIGMA,45.00,,955.00,\n"
                     "13/04/2026,FPI,'30-94-57,12345678,CLIENT,,500.00,1455.00,\n")
        out = os.path.join(d, "lloyds.masked.csv")
        counts, by_col = redact_file(src, out)
        text = open(out, encoding="utf-8").read()
        assert "12345678" not in text and "30-94-57" not in text, text
        assert "****5678" in text and "FIGMA" in text and "45.00" in text, text
        assert by_col["Account Number"] == 2 and by_col["Sort Code"] == 2, by_col
        # the kept column is left alone
        _, by_col2 = redact_file(src, out, keep={"Account Number"})
        assert "Account Number" not in by_col2 and "12345678" in open(out, encoding="utf-8").read()
        # a bank preamble: identifiers above the header never reach the copy
        pre = os.path.join(d, "preamble.csv")
        with open(pre, "w", encoding="utf-8") as fh:
            fh.write("Account Name:,Bramble Design Ltd,Sort Code:,20-00-00\nAccount Number:,12345678,,\n\n"
                     "Date,Description,Amount,Balance\n02/04/2026,FIGMA,-45.00,955.00\n")
        out2 = os.path.join(d, "preamble.masked.csv")
        redact_file(pre, out2)
        text2 = open(out2, encoding="utf-8").read()
        assert "12345678" not in text2 and "20-00-00" not in text2 and "FIGMA" in text2, text2
        # forced to the preamble line as header: labels and header cells are still masked
        redact_file(pre, out2, header_line=1)
        text3 = open(out2, encoding="utf-8").read()
        assert "12345678" not in text3 and "20-00-00" not in text3, text3
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--keep-column", action="append", default=[])
    ap.add_argument("--header-line", type=int)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.file or not a.out:
        bkio.die("a file and --out are required", "e.g. redact.py /home/user/in/bank.csv --out /home/user/work/bank.masked.csv")
    if os.path.abspath(a.file) == os.path.abspath(a.out):
        bkio.die("--out is the input file", "write the masked copy to a different path")
    try:
        counts, by_column = redact_file(a.file, a.out, set(a.keep_column), a.header_line)
    except bkio.InputError as e:
        bkio.die(str(e))
    total = sum(counts.values())
    print(f"masked {total} values -> {a.out}")
    for col, n in counts.items():
        if n:
            print(f"  {col}: {n}")
    for col, n in by_column.items():
        print(f"masked by column: {col} ({n})")


if __name__ == "__main__":
    main()
