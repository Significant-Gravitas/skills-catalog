#!/usr/bin/env python3
"""Render a draft invoice as HTML (and PDF when a headless Chrome/Chromium is
available) with a DRAFT - NOT AN INVOICE watermark that cannot be turned off.

    cd ~/skills/invoice-drafting-and-issue && python3 scripts/render_invoice.py \
        /home/user/work/draft.json --out /home/user/out/draft-<id>.html [--pdf]

Uses templates/invoice-draft.html (string.Template, values HTML-escaped).
Blank fields render as a red "[missing: <field>]". Totals come from
invoice_totals.py (run with --write first, or they are computed here).
--pdf tries google-chrome, chromium, chromium-browser in headless mode; if
none is present the HTML is the deliverable and the script says so.
Never sends or uploads anything.
"""

import argparse
import html
import json
import os
import shutil
import subprocess
import sys
from string import Template

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bkio  # noqa: E402
import invoice_totals  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "templates", "invoice-draft.html")
WATERMARK = "DRAFT - NOT AN INVOICE"


def val(v, label):
    if v in (None, "", [], "not supplied"):
        return f'<span class="missing">[missing: {html.escape(label)}]</span>'
    return html.escape(str(v))


def block(party, label):
    if not party:
        return val(None, label)
    parts = [val(party.get("legal_name"), f"{label} name"), val(party.get("address"), f"{label} address")]
    for k in ("contact", "billing_contact", "company_number", "vat_number"):
        if k in party:
            parts.append(f"{k.replace('_', ' ')}: {val(party.get(k), f'{label} {k}')}")
    return "<br>".join(parts)


def render(draft):
    totals = draft.get("computed") or invoice_totals.compute(draft)
    rows = []
    for ln, t in zip(draft.get("lines") or [], totals["lines"]):
        rows.append("    <tr>" + "".join([
            f"<td>{val(ln.get('description'), 'description')}</td>",
            f"<td>{val(ln.get('period') or ln.get('supply_date'), 'period')}</td>",
            f"<td class='num'>{val(ln.get('qty'), 'qty')}</td>",
            f"<td class='num'>{val(ln.get('rate'), 'rate')}</td>",
            f"<td class='num'>{val(ln.get('tax_rate'), 'tax rate')}</td>",
            f"<td class='num'>{html.escape(t['net'])}</td>",
            f"<td>{val(ln.get('source'), 'source')}</td>"]) + "</tr>")
    refs = draft.get("references") or {}
    number = draft.get("number")
    fields = {
        "draft_id": html.escape(str(draft.get("draft_id", ""))),
        "approver": val(draft.get("approver"), "approver"),
        "number": "(number to be assigned)" if number in (None, "", "to be assigned") else html.escape(number),
        "invoice_date": val(draft.get("invoice_date"), "invoice date"),
        "supply_period": val(draft.get("supply_period"), "supply date"),
        "due_date": val(draft.get("due_date"), "due date"),
        "terms": val(draft.get("terms"), "terms"),
        "seller_block": block(draft.get("seller"), "seller"),
        "customer_block": block(draft.get("customer"), "customer"),
        "references": " / ".join(html.escape(str(v)) for v in refs.values() if v) or val(None, "contract or PO reference"),
        "line_rows": "\n".join(rows),
        "subtotal": html.escape(totals["subtotal"]),
        "discount": html.escape(totals["invoice_discount"]),
        "tax_total": (html.escape(totals["tax_total"]) if totals.get("tax_total")
                      else val(None, "tax (treatment not supplied by the accountant)")),
        "grand_total": (html.escape(totals["grand_total"]) + ("" if totals.get("tax_requested") else " before tax")
                        if totals.get("grand_total") else val(None, "total (tax rounding method to choose)")),
        "currency": val(draft.get("currency"), "currency"),
        "payment_instructions": val((draft.get("payment") or {}).get("instructions"), "payment instructions"),
        "remittance_reference": val((draft.get("payment") or {}).get("remittance_reference"), "remittance reference"),
    }
    with open(TEMPLATE, encoding="utf-8") as fh:
        out = Template(fh.read()).substitute(fields)
    if out.count(WATERMARK) < 2:
        raise bkio.InputError("template lost its DRAFT watermark; restore templates/invoice-draft.html")
    return out


def to_pdf(html_path):
    for exe in ("google-chrome", "chromium", "chromium-browser", "google-chrome-stable"):
        path = shutil.which(exe)
        if not path:
            continue
        pdf = os.path.splitext(html_path)[0] + ".pdf"
        cmd = [path, "--headless", "--no-sandbox", "--disable-gpu", f"--print-to-pdf={pdf}", html_path]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        except subprocess.TimeoutExpired:
            continue
        if r.returncode == 0 and os.path.exists(pdf):
            return pdf
    return None


def selftest():
    with open(os.path.join(HERE, "..", "examples", "oriel-april", "draft.json"), encoding="utf-8") as fh:
        d = json.load(fh)
    out = render(d)
    assert out.count(WATERMARK) >= 2
    assert "[missing: payment instructions]" in out
    assert "4400.00 before tax" in out
    assert "<script" not in out.lower()
    d["customer"]["legal_name"] = "<script>x</script>"
    assert "<script>x" not in render(d)
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft", nargs="?")
    ap.add_argument("--out")
    ap.add_argument("--pdf", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.draft or not a.out:
        bkio.die("draft path and --out are required")
    try:
        with open(a.draft, encoding="utf-8") as fh:
            draft = json.load(fh)
        text = render(draft)
    except (OSError, json.JSONDecodeError) as e:
        bkio.die(f"cannot read {a.draft}: {e}")
    except bkio.InputError as e:
        bkio.die(str(e), "fix the draft; blanks are allowed, wrong types are not")
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"HTML draft written to {a.out}")
    if a.pdf:
        pdf = to_pdf(os.path.abspath(a.out))
        print(f"PDF written to {pdf}" if pdf else "no headless Chrome/Chromium found: deliver the HTML draft")


if __name__ == "__main__":
    main()
