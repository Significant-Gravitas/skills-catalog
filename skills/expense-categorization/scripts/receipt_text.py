#!/usr/bin/env python3
"""Pull candidate date, total and merchant from receipt files so they can be
tied to payment lines. Candidates are never evidence on their own.

    cd ~/skills/expense-categorization && python3 scripts/receipt_text.py \
        /home/user/in/receipts/*.pdf --out /home/user/work/receipts-extracted.csv

Reads: .pdf (with the `pdftotext` command if present, else the `pypdf`
module if importable), .txt, and images (.jpg/.png) only if the `tesseract`
command is present. Whether these tools exist in the sandbox is not known in
advance; when none is available the script says so (exit 2) and the fallback
is to ask the user for date, total and merchant per receipt.

Output CSV columns: receipt_id, date, amount, currency, merchant, file,
extraction (pdftotext | pypdf | text | tesseract), status = `unconfirmed`.
Several candidate totals on one receipt -> amount left blank and all
candidates listed in `note`; the user picks. A date is written as YYYY-MM-DD
only when it reads one way; a date like 07/04/2026 (day/month or month/day)
is left blank with both readings in `note`. No currency found, or a bare `$`
(CA$, A$, NZ$ and US$ are read as such) -> blank with a
note. Confirm every row with the user (date, total, currency) before use. Then run expense_checks.py
--receipts on the confirmed file: a receipt counts as support only when it
ties to a card or bank line.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bkio  # noqa: E402

TOTAL_RX = re.compile(r"(?i)\b(total|amount due|balance due|grand total|total paid|amount paid)\b[^\d\-£$€]*([£$€]?\s?-?\d[\d,]*\.\d{2})")
DATE_RX = re.compile(r"\b(\d{4}-\d{2}-\d{2}|\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}|\d{1,2} [A-Z][a-z]{2,8} \d{4})\b")
# prefixed dollars first: CA$, A$ and NZ$ are not US dollars. A bare '$' is
# left blank with a question, never read as USD.
CCY_RX = re.compile(r"((?<![A-Z])(?:US|CA|C|AU|A|NZ)\$|£|€|\$|\b(?:GBP|USD|EUR|CAD|AUD|NZD)\b)")
CCY_MAP = {"£": "GBP", "€": "EUR", "US$": "USD", "CA$": "CAD", "C$": "CAD", "AU$": "AUD", "A$": "AUD",
           "NZ$": "NZD", "$": ""}
BARE_DOLLAR = "dollar: which currency? (US, Canadian, Australian, New Zealand ...) ask the user"
FIELDS = ["receipt_id", "date", "amount", "currency", "merchant", "file", "extraction", "status", "note"]


def extract_text(path):
    low = path.lower()
    if low.endswith(".txt"):
        with open(path, encoding="utf-8", errors="replace") as fh:
            return fh.read(), "text"
    if low.endswith(".pdf"):
        if shutil.which("pdftotext"):
            r = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True, timeout=60)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout, "pdftotext"
        try:
            import pypdf
            reader = pypdf.PdfReader(path)
            text = "\n".join((p.extract_text() or "") for p in reader.pages)
            if text.strip():
                return text, "pypdf"
        except ImportError:
            pass
        raise bkio.InputError(f"{path}: no PDF text tool available or the PDF is a scan")
    if low.endswith((".jpg", ".jpeg", ".png", ".heic", ".webp")):
        if shutil.which("tesseract"):
            r = subprocess.run(["tesseract", path, "-"], capture_output=True, text=True, timeout=90)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout, "tesseract"
        raise bkio.InputError(f"{path}: image and no OCR tool available")
    raise bkio.InputError(f"{path}: unsupported file type")


def candidates(text):
    totals = []
    for m in TOTAL_RX.finditer(text):
        try:
            totals.append(abs(bkio.parse_amount(m.group(2))[0]))
        except bkio.InputError:
            continue
    dates = DATE_RX.findall(text)
    ccy = None
    m = CCY_RX.search(text)
    if m:
        ccy = CCY_MAP.get(m.group(1), m.group(1)) or "$"
    merchant = next((ln.strip() for ln in text.splitlines() if ln.strip()), "")
    return sorted(set(totals)), dates, ccy, merchant[:60]


def iso_date(text):
    """(ISO date, note). Blank date with both readings when ambiguous."""
    fits, ambiguous = bkio.detect_date_formats([text])
    if not fits:
        return "", f"date '{text}' not understood: ask the user"
    readings = sorted({bkio.parse_date(text, f).isoformat() for f in fits})
    if ambiguous and len(readings) > 1:
        return "", f"date '{text}' reads as {' or '.join(readings)}: ask the user which"
    return readings[0], ""


def run(paths):
    out, failed = [], []
    for i, p in enumerate(paths, 1):
        try:
            text, how = extract_text(p)
        except bkio.InputError as e:
            failed.append(str(e))
            continue
        totals, dates, ccy, merchant = candidates(text)
        note = []
        amount = ""
        if len(totals) == 1:
            amount = str(totals[0])
        elif totals:
            note.append("several totals: " + ", ".join(str(t) for t in totals))
        else:
            note.append("no total found")
        date = ""
        if len(set(dates)) > 1:
            note.append("several dates: " + ", ".join(sorted(set(dates))))
        elif dates:
            date, why = iso_date(dates[0])
            if why:
                note.append(why)
        else:
            note.append("no date found")
        if ccy == "$":
            ccy = ""
            note.append(BARE_DOLLAR)
        elif not ccy:
            note.append("no currency found: ask the user")
        out.append({"receipt_id": f"X{i}", "date": date,
                    "amount": amount, "currency": ccy or "", "merchant": merchant,
                    "file": os.path.basename(p), "extraction": how, "status": "unconfirmed",
                    "note": "; ".join(note)})
    return out, failed


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    p = os.path.join(here, "..", "examples", "bramble-april-card", "receipt-trainline.txt")
    out, failed = run([p])
    assert not failed, failed
    assert out[0]["amount"] == "118.40", out[0]
    assert out[0]["date"] == "", out[0]    # 07/04/2026 reads two ways
    assert "2026-04-07 or 2026-07-04" in out[0]["note"], out[0]
    assert out[0]["currency"] == "GBP"
    assert iso_date("13/04/2026") == ("2026-04-13", ""), iso_date("13/04/2026")
    assert iso_date("2026-04-07")[0] == "2026-04-07"
    assert candidates("CAFE\nTOTAL CA$ 20.00")[2] == "CAD"
    assert candidates("CAFE\nTOTAL A$20.00")[2] == "AUD"
    assert candidates("CAFE\nTOTAL NZ$ 20.00")[2] == "NZD"
    assert candidates("CAFE\nTOTAL US$ 20.00")[2] == "USD"
    assert candidates("CAFE\nTOTAL $20.00")[2] == "$"
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.files:
        bkio.die("no receipt files given")
    out, failed = run(a.files)
    bkio.write_csv(a.out, FIELDS, out)
    for f in failed:
        print(f"could not read: {f}", file=sys.stderr)
    if failed and not out:
        bkio.die("no receipt could be read",
                 "ask the user for date, total and merchant per receipt and type them into receipts.csv")
    print(f"{len(out)} receipts extracted (unconfirmed), {len(failed)} unreadable", file=sys.stderr)


if __name__ == "__main__":
    main()
