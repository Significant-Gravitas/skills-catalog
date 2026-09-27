#!/usr/bin/env python3
"""Recompute an invoice draft's totals exactly and show the rounding choices.

    cd ~/skills/invoice-drafting-and-issue && python3 scripts/invoice_totals.py \
        /home/user/work/draft.json [--write]

Input: draft.json (templates/draft.json). Per line: qty, rate, optional
discount (amount) and tax_rate (percent, e.g. "20"; null when not supplied).
Top level: currency, optional invoice discount {amount}, and tax
{requested: true/false, rounding: "per_line" | "per_invoice" | null}.

Output: line totals (qty x rate - discount), subtotal, invoice discount, tax
computed per line and per invoice (grouped by rate) with the difference, and
the grand total. Money is Decimal, rounded half-up to the currency's minor
unit only where a value is presented or charged (rounding mode is a default;
confirm with the owner or accountant). When per-line and per-invoice tax
differ and the draft does not name a method, no grand total including tax is
given: "owner/accountant to choose".

--write stores the computed figures under "computed" in draft.json (the lines
and terms are never changed).
Exit 0 ok; 2 bad input, or tax requested while a line's tax_rate is null.
"""

import argparse
import json
import os
import sys
from decimal import Decimal, ROUND_HALF_UP

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bkio  # noqa: E402


def dec(value, where):
    if value is None or value == "":
        raise bkio.InputError(f"{where} is empty")
    v, _ = bkio.parse_amount(str(value))
    if v is None:
        raise bkio.InputError(f"{where} is empty")
    return v


def compute(draft):
    ccy = draft.get("currency")
    if not ccy:
        raise bkio.InputError("currency is missing; it must come from the contract or the owner")
    q = lambda v: bkio.quantize(v, ccy, ROUND_HALF_UP)  # noqa: E731
    lines = draft.get("lines") or []
    if not lines:
        raise bkio.InputError("draft has no lines")
    tax = draft.get("tax") or {}
    requested = bool(tax.get("requested"))
    out_lines, subtotal = [], Decimal(0)
    per_line_tax, by_rate = Decimal(0), {}
    for i, ln in enumerate(lines, 1):
        qty = dec(ln.get("qty"), f"line {i} qty")
        rate = dec(ln.get("rate"), f"line {i} rate")
        disc = dec(ln.get("discount"), f"line {i} discount") if ln.get("discount") not in (None, "", "0") else Decimal(0)
        gross = qty * rate
        net = q(gross - disc)
        exact_note = "" if gross - disc == net else f"rounded from {gross - disc}"
        tr = ln.get("tax_rate")
        if requested and tr in (None, ""):
            raise bkio.InputError(f"line {i} has no tax_rate but tax is requested; the rate must come from the accountant")
        line_tax = None
        if requested:
            r = dec(tr, f"line {i} tax_rate") / Decimal(100)
            line_tax = q(net * r)
            per_line_tax += line_tax
            by_rate[str(tr)] = by_rate.get(str(tr), Decimal(0)) + net
        subtotal += net
        out_lines.append({"line": i, "key": ln.get("key"), "qty": str(qty), "rate": str(rate),
                          "discount": str(disc), "net": str(net), "tax": None if line_tax is None else str(line_tax),
                          "note": exact_note})
    inv_disc = Decimal(0)
    if (draft.get("discount") or {}).get("amount") not in (None, ""):
        inv_disc = q(dec(draft["discount"]["amount"], "invoice discount"))
        if requested and inv_disc:
            raise bkio.InputError("an invoice-level discount with tax needs the accountant to say how tax applies; "
                                  "put the discount on the lines or leave tax blank")
    net_total = subtotal - inv_disc
    result = {"currency": ccy, "lines": out_lines, "subtotal": str(subtotal), "invoice_discount": str(inv_disc),
              "net_total": str(net_total), "tax_requested": requested}
    if requested:
        per_invoice_tax = sum((q(base * dec(rate, "rate") / Decimal(100)) for rate, base in by_rate.items()), Decimal(0))
        result.update({"tax_per_line": str(per_line_tax), "tax_per_invoice": str(per_invoice_tax),
                       "tax_difference": str(per_line_tax - per_invoice_tax)})
        method = tax.get("rounding")
        if method == "per_line":
            result["tax_total"] = str(per_line_tax)
        elif method == "per_invoice":
            result["tax_total"] = str(per_invoice_tax)
        elif per_line_tax == per_invoice_tax:
            result["tax_total"] = str(per_line_tax)
        else:
            result["tax_total"] = None
            result["note"] = "per-line and per-invoice tax differ: owner/accountant to choose the method"
        result["grand_total"] = None if result["tax_total"] is None else str(net_total + Decimal(result["tax_total"]))
    else:
        result["grand_total"] = str(net_total)
        result["note"] = "no tax requested: total is before any tax; tax fields stay blank until the accountant supplies them"
    return result


def show(r):
    ccy = r["currency"]
    print("| Line | Qty | Rate | Discount | Net | Tax | Note |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    for ln in r["lines"]:
        print(f"| {ln['line']} | {ln['qty']} | {ln['rate']} | {ln['discount']} | {ln['net']} | {ln['tax'] or '-'} | {ln['note']} |")
    print(f"Subtotal {r['subtotal']} {ccy}; invoice discount {r['invoice_discount']}; net {r['net_total']} {ccy}")
    if r["tax_requested"]:
        print(f"Tax per line {r['tax_per_line']}; per invoice {r['tax_per_invoice']}; difference {r['tax_difference']}")
        print(f"Tax total {r['tax_total'] or 'NOT SET'}; grand total {r['grand_total'] or 'NOT SET'}")
    else:
        print(f"Total before tax {r['grand_total']} {ccy}")
    if r.get("note"):
        print(f"Note: {r['note']}")
    print("Script: invoice_totals.py (Decimal, half-up to the currency minor unit; default, confirm with the owner)")


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "..", "examples", "oriel-april", "draft.json"), encoding="utf-8") as fh:
        d = json.load(fh)
    r = compute(d)
    assert r["subtotal"] == "4400.00" and r["grand_total"] == "4400.00", r
    vat = {"currency": "GBP", "tax": {"requested": True, "rounding": None},
           "lines": [{"qty": "3", "rate": "0.335", "tax_rate": "20"}, {"qty": "1", "rate": "10.01", "tax_rate": "20"}]}
    r2 = compute(vat)
    # 3 x 0.335 = 1.005 -> 1.01; tax per line 0.20 + 2.00 = 2.20; per invoice 11.02 x 20% = 2.204 -> 2.20
    assert r2["subtotal"] == "11.02", r2
    assert r2["tax_per_line"] == "2.20" and r2["tax_per_invoice"] == "2.20", r2
    vat["lines"] = [{"qty": "1", "rate": "0.03", "tax_rate": "20"}] * 3
    r3 = compute(vat)   # per line 0.01 x 3 = 0.03; per invoice 0.09 x 20% = 0.018 -> 0.02
    assert r3["tax_difference"] == "0.01" and r3["grand_total"] is None, r3
    try:
        compute({"currency": "GBP", "tax": {"requested": True}, "lines": [{"qty": "1", "rate": "5", "tax_rate": None}]})
        raise AssertionError("null tax rate must fail")
    except bkio.InputError:
        pass
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft", nargs="?")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.draft:
        bkio.die("no draft.json given", "build it from templates/draft.json")
    try:
        with open(a.draft, encoding="utf-8") as fh:
            draft = json.load(fh)
        r = compute(draft)
    except (OSError, json.JSONDecodeError) as e:
        bkio.die(f"cannot read {a.draft}: {e}", "check the path and JSON syntax")
    except bkio.InputError as e:
        bkio.die(str(e), "leave the field blank in the draft and list it as missing; never fill it by guess")
    show(r)
    if a.write:
        draft["computed"] = r
        with open(a.draft, "w", encoding="utf-8") as fh:
            json.dump(draft, fh, indent=2)
        print(f"computed totals stored in {a.draft}")


if __name__ == "__main__":
    main()
