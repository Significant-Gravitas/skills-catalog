#!/usr/bin/env python3
"""Check an invoice draft against the required-field list for the seller's
jurisdiction, and check that every line and term cites a source.

    cd ~/skills/invoice-drafting-and-issue && python3 scripts/field_check.py \
        /home/user/work/draft.json --regime uk-general|uk-vat|other

Regimes (field lists in references/invoice-field-checklists.md):
- uk-general: GOV.UK "Invoices: what they must include" [48]
- uk-vat: uk-general plus the VAT invoice fields in HMRC VAT Notice 700/21 [28]
- other: a contract-driven minimum (practitioner judgement, unsourced)

Prints BLOCKS APPROVAL items (a required field is blank or a conflict is
unresolved), BLOCKS ISSUE items (allowed on a draft but must be settled before
the invoice is issued, e.g. the number), and SOURCE gaps. Exit 0 when nothing
blocks approval, 1 when something does, 2 on bad input.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bkio  # noqa: E402

BLANK = (None, "", [], "to be assigned", "not supplied")

COMMON = [
    ("seller.legal_name", "seller name (full registered name for a limited company)"),
    ("seller.address", "seller address"),
    ("customer.legal_name", "customer name"),
    ("customer.address", "customer address"),
    ("invoice_date", "invoice date"),
    ("currency", "currency"),
    ("due_date|terms", "due date or payment terms"),
    ("payment.instructions", "payment instructions"),
]
UK_GENERAL = COMMON + [
    ("seller.contact", "seller contact information"),
    ("lines[].description", "description of each charge"),
    ("lines[].supply_date|supply_period", "supply date (date goods or services were provided)"),
]
UK_VAT_EXTRA = [
    ("seller.vat_number", "seller VAT registration number"),
    ("lines[].tax_rate", "VAT rate per line"),
    ("lines[].rate", "unit price per line"),
    ("lines[].qty", "quantity per line"),
    ("tax.requested", "VAT total shown (tax requested with rates supplied)"),
]
OTHER = COMMON + [("lines[].description", "description of each charge")]
ISSUE_ONLY = [("number", "unique invoice number (sequential; assigned at issue)")]


def get(d, path):
    cur = d
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def present(draft, spec):
    if spec.startswith("lines[]."):
        fields = spec[len("lines[]."):].split("|")
        missing = []
        for i, ln in enumerate(draft.get("lines") or [], 1):
            if all(ln.get(f) in BLANK for f in fields):
                missing.append(i)
        return missing
    alts = spec.split("|")
    if spec == "tax.requested":
        return [] if get(draft, "tax.requested") is True else ["all"]
    return [] if any(get(draft, a) not in BLANK for a in alts) else ["all"]


def check(draft, regime):
    spec = {"uk-general": UK_GENERAL, "uk-vat": UK_GENERAL + UK_VAT_EXTRA, "other": OTHER}.get(regime)
    if spec is None:
        raise bkio.InputError(f"unknown regime '{regime}'; use uk-general, uk-vat or other")
    blocks, issue, sources = [], [], []
    for path, label in spec:
        miss = present(draft, path)
        if miss:
            where = "" if miss == ["all"] else f" (lines {miss})"
            blocks.append(f"{label}{where}")
    for path, label in ISSUE_ONLY:
        if present(draft, path):
            issue.append(label)
    for c in draft.get("conflicts") or []:
        if not c.get("resolved"):
            blocks.append(f"unresolved conflict on {c.get('field')}: {' vs '.join(c.get('options', []))}")
    for i, ln in enumerate(draft.get("lines") or [], 1):
        if ln.get("source") in BLANK:
            sources.append(f"line {i} has no source")
    if draft.get("due_date") and draft.get("terms_source") in BLANK and draft.get("terms") in BLANK:
        sources.append("due date has no source term")
    if regime == "uk-vat" and get(draft, "customer.vat_number") in BLANK:
        issue.append("customer VAT number not supplied (only needed for some supplies; ask the accountant)")
    return blocks, issue, sources


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "..", "examples", "oriel-april", "draft.json"), encoding="utf-8") as fh:
        d = json.load(fh)
    blocks, issue, sources = check(d, "uk-vat")
    text = " | ".join(blocks)
    assert "seller VAT registration number" in text, text
    assert "payment instructions" in text, text
    assert "unresolved conflict" in text, text
    assert "VAT rate per line (lines [1, 2])" in text, text
    assert any("unique invoice number" in i for i in issue), issue
    assert not sources, sources
    b2, _, _ = check(d, "other")
    assert "seller VAT" not in " ".join(b2)
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft", nargs="?")
    ap.add_argument("--regime", default=None)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.draft or not a.regime:
        bkio.die("draft path and --regime are required",
                 "regime comes from intake.json (UK and VAT-registered -> uk-vat; UK not registered -> uk-general; else other)")
    try:
        with open(a.draft, encoding="utf-8") as fh:
            draft = json.load(fh)
        blocks, issue, sources = check(draft, a.regime)
    except (OSError, json.JSONDecodeError) as e:
        bkio.die(f"cannot read {a.draft}: {e}")
    except bkio.InputError as e:
        bkio.die(str(e))
    print(f"BLOCKS APPROVAL ({len(blocks)})")
    for b in blocks:
        print(f"- {b}")
    print(f"BLOCKS ISSUE ({len(issue)})")
    for b in issue:
        print(f"- {b}")
    print(f"SOURCE GAPS ({len(sources)})")
    for b in sources:
        print(f"- {b}")
    sys.exit(1 if blocks else 0)


if __name__ == "__main__":
    main()
