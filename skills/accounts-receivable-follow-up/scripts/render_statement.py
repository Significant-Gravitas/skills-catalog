#!/usr/bin/env python3
"""Render a statement of account for ONE customer from ar_aging.py output.

    cd ~/skills/accounts-receivable-follow-up && python3 scripts/render_statement.py \
        --aging /home/user/work/aging.csv --customer "Kestrel Joinery Ltd" \
        --seller "Bramble Design Ltd" --approver "Sam" --cutoff "2026-04-30 17:00" \
        --out /home/user/out/statement-kestrel.html [--pdf]

Includes open and part-paid invoices for that customer only (open balance
above zero). Refuses (exit 2) if the customer matches no row, if the rows mix
currencies (one statement per currency), or if any other customer's row
would appear. Invoices in `disputed or blocked`, `status unconfirmed` or
`promised payment not yet due` are left off and listed, because the statement
must not chase them. The DRAFT
banner stays until the owner sends it. --pdf tries headless Chrome/Chromium;
otherwise the HTML is the deliverable. Never sends anything.
"""

import argparse
import html
import os
import shutil
import subprocess
import sys
from decimal import Decimal
from string import Template

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bkio  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "templates", "statement-of-account.html")
SKIP_GROUPS = {"disputed or blocked", "status unconfirmed", "promised payment not yet due", "paid",
               "credit balance"}


def render(aging_path, customer, seller, approver, cutoff, as_at=None):
    _, rows = bkio.read_csv(aging_path)
    mine = [r for r in rows if r["customer"] == customer]
    if not mine:
        raise bkio.InputError(f"no rows for customer '{customer}'; names must match the aging exactly")
    keep = [r for r in mine if r["group"] not in SKIP_GROUPS and Decimal(r["open_balance"]) > 0]
    left_off = [f"{r['invoice']} ({r['group']})" for r in mine if r not in keep and Decimal(r["open_balance"]) != 0]
    if not keep:
        raise bkio.InputError(f"nothing to state for '{customer}': every open item is disputed, unconfirmed, "
                              "promised for a later date or paid")
    if any(r["customer"] != customer for r in keep):
        raise bkio.InputError("another customer's row would appear on this statement")
    currencies = {r["currency"] for r in keep}
    if len(currencies) != 1:
        raise bkio.InputError(f"rows mix currencies {sorted(currencies)}: render one statement per currency")
    ccy = currencies.pop()
    total = sum((Decimal(r["open_balance"]) for r in keep), Decimal(0))
    lines = []
    for r in keep:
        paid = Decimal(r["amount"]) - Decimal(r["open_balance"])
        lines.append("    <tr>" + "".join(f"<td{c}>{html.escape(v)}</td>" for c, v in [
            ("", r["invoice"]), ("", r["issue_date"]), ("", r["due_date"]),
            (" class='num'", r["amount"]), (" class='num'", str(paid)), (" class='num'", r["open_balance"])]) + "</tr>")
    with open(TEMPLATE, encoding="utf-8") as fh:
        text = Template(fh.read()).substitute(
            customer=html.escape(customer), seller=html.escape(seller), approver=html.escape(approver),
            as_at=html.escape(as_at or cutoff.split(" ")[0]), cutoff=html.escape(cutoff),
            rows="\n".join(lines), currency=html.escape(ccy), total=str(total))
    return text, left_off, total, ccy


def to_pdf(path):
    for exe in ("google-chrome", "chromium", "chromium-browser", "google-chrome-stable"):
        b = shutil.which(exe)
        if not b:
            continue
        pdf = os.path.splitext(path)[0] + ".pdf"
        try:
            r = subprocess.run([b, "--headless", "--no-sandbox", "--disable-gpu", f"--print-to-pdf={pdf}", path],
                               capture_output=True, timeout=90)
        except subprocess.TimeoutExpired:
            continue
        if r.returncode == 0 and os.path.exists(pdf):
            return pdf
    return None


def selftest():
    import tempfile
    import ar_aging
    ex = os.path.join(HERE, "..", "examples", "bramble-april-ar")
    out, _, _, _ = ar_aging.age(os.path.join(ex, "invoices.csv"), os.path.join(ex, "payments.csv"), "2026-04-30 17:00",
                             os.path.join(ex, "dispute-log.csv"), os.path.join(ex, "contact-log.csv"),
                             os.path.join(ex, "unapplied-expected.csv"))
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "aging.csv")
        bkio.write_csv(p, ar_aging.OUT_FIELDS, out)
        text, left, total, ccy = render(p, "Tallow & Wick", "Bramble Design Ltd", "Sam", "2026-04-30 17:00")
        assert total == Decimal("640.00") and "Tallow &amp; Wick" in text
        assert "Kestrel" not in text and "Greyline" not in text
        try:
            render(p, "Greyline Studio", "Bramble Design Ltd", "Sam", "2026-04-30 17:00")
            raise AssertionError("disputed-only customer must not get a statement")
        except bkio.InputError:
            pass
        try:
            render(p, "Marsh & Co", "Bramble Design Ltd", "Sam", "2026-04-30 17:00")
            raise AssertionError("an invoice with a promised date still to come must not get a statement")
        except bkio.InputError as e:
            assert "promised" in str(e), e
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--aging")
    ap.add_argument("--customer")
    ap.add_argument("--seller")
    ap.add_argument("--approver")
    ap.add_argument("--cutoff")
    ap.add_argument("--as-at")
    ap.add_argument("--out")
    ap.add_argument("--pdf", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not all([a.aging, a.customer, a.seller, a.approver, a.cutoff, a.out]):
        bkio.die("--aging, --customer, --seller, --approver, --cutoff and --out are required")
    try:
        text, left_off, total, ccy = render(a.aging, a.customer, a.seller, a.approver, a.cutoff, a.as_at)
    except bkio.InputError as e:
        bkio.die(str(e))
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"statement for {a.customer}: {total} {ccy} open; written to {a.out}")
    if left_off:
        print(f"left off (not chased): {', '.join(left_off)}")
    if a.pdf:
        pdf = to_pdf(os.path.abspath(a.out))
        print(f"PDF written to {pdf}" if pdf else "no headless Chrome/Chromium found: deliver the HTML")


if __name__ == "__main__":
    main()
