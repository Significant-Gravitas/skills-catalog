#!/usr/bin/env python3
"""Check a draft against the invoice register (and a billing export if given)
for double billing and numbering problems.

    cd ~/skills/invoice-drafting-and-issue && python3 scripts/register_check.py \
        /home/user/work/draft.json --register ~/workspace/bookkeeping/<entity>/invoice-register.csv \
        [--billing-export /home/user/in/invoices.csv]

Register columns: number, customer, contract_ref, line_key, amount, currency,
status, issued_on, issued_by, ledger_id, evidence (templates/invoice-register.csv).
A billing export needs at least a number column (invoice number / number /
invoice no); line keys are only checked against the register.

Reports:
- REPEAT: a draft line_key already in the register with a status other than
  voided_per_owner (the same contract line for the same period billed twice);
- REPEAT IN DRAFT: two lines of the draft with the same key (lines are
  numbered from 1);
- numbers used twice, and gaps in the numeric sequence (per prefix);
- the next number as a SUGGESTION only (the billing system or owner assigns it);
- the draft's own number, if set, already in use.
The register is a working index, not the system of record: when a billing
export is supplied it wins, and differences are listed.
Exit 0 clean, 1 conflicts found, 2 bad input.
"""

import argparse
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bkio  # noqa: E402

NUM_RX = re.compile(r"^(.*?)(\d+)$")


def numbers_from(rows, col_names=("number", "invoice number", "invoice no", "invoice", "invoice_number")):
    if not rows:
        return []
    cols = {k.lower(): k for k in rows[0] if k != "_row"}
    col = next((cols[c] for c in col_names if c in cols), None)
    if col is None:
        raise bkio.InputError(f"no invoice number column in {list(cols.values())}")
    return [r[col].strip() for r in rows if r.get(col, "").strip()]


def sequence_report(numbers):
    counts = Counter(numbers)
    dups = sorted(n for n, c in counts.items() if c > 1)
    by_prefix = {}
    for n in set(numbers):
        m = NUM_RX.match(n)
        if m:
            by_prefix.setdefault(m.group(1), []).append((int(m.group(2)), len(m.group(2))))
    gaps, suggestion = {}, {}
    for prefix, vals in by_prefix.items():
        ints = sorted(v for v, _ in vals)
        width = max(w for _, w in vals)
        missing = sorted(set(range(ints[0], ints[-1] + 1)) - set(ints))
        if missing:
            gaps[prefix] = [f"{prefix}{str(m).zfill(width)}" for m in missing][:20]
        suggestion[prefix] = f"{prefix}{str(ints[-1] + 1).zfill(width)}"
    return dups, gaps, suggestion


def check(draft, register_path, export_path=None):
    reg_rows = []
    if register_path and os.path.exists(register_path):
        _, reg_rows = bkio.read_csv(register_path)
    live = {}
    for r in reg_rows:
        if (r.get("status") or "").lower() != "voided_per_owner" and r.get("line_key"):
            live.setdefault(r["line_key"], []).append(r.get("number") or r.get("status"))
    repeats = []
    at = {}
    for i, ln in enumerate(draft.get("lines") or [], 1):
        if ln.get("key"):
            at.setdefault(ln["key"], []).append(i)
    for key, idx in at.items():
        if len(idx) > 1:
            repeats.append(f"REPEAT IN DRAFT {key}: lines {idx}")
    for ln in draft.get("lines") or []:
        key = ln.get("key")
        if not key:
            repeats.append(f"line '{ln.get('description')}' has no key; set contract/line/period so double billing can be checked")
        elif key in live:
            repeats.append(f"REPEAT {key}: already in register as {live[key]}")
    numbers = [r.get("number") for r in reg_rows if r.get("number")]
    export_diff = []
    if export_path:
        _, exp_rows = bkio.read_csv(export_path)
        exp_numbers = numbers_from(exp_rows)
        export_diff = sorted(set(exp_numbers) - set(numbers))
        numbers = exp_numbers + [n for n in numbers if n not in exp_numbers]
    dups, gaps, suggestion = sequence_report(numbers)
    own = draft.get("number")
    clash = own if own and own not in ("to be assigned",) and own in numbers else None
    return {"repeats": repeats, "duplicate_numbers": dups, "gaps": gaps, "next_number_suggestion": suggestion,
            "draft_number_in_use": clash, "in_export_not_register": export_diff,
            "register_rows": len(reg_rows)}


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    ex = os.path.join(here, "..", "examples", "oriel-april")
    with open(os.path.join(ex, "draft.json"), encoding="utf-8") as fh:
        d = json.load(fh)
    r = check(d, os.path.join(ex, "invoice-register.csv"))
    assert any("REPEAT SOW-014/retainer/2026-04" in x for x in r["repeats"]), r
    assert r["duplicate_numbers"] == [], r
    assert "INV-1044" in r["gaps"]["INV-"] and "INV-1045" not in r["gaps"]["INV-"], r["gaps"]
    assert r["next_number_suggestion"] == {"INV-": "INV-1056"}, r
    # the same contract line and period twice in one draft is double billing too
    d2 = {"lines": [dict(d["lines"][0]), dict(d["lines"][0])]}
    r2 = check(d2, os.path.join(ex, "invoice-register.csv"))
    assert any(x.startswith("REPEAT IN DRAFT") and "lines [1, 2]" in x for x in r2["repeats"]), r2
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("draft", nargs="?")
    ap.add_argument("--register")
    ap.add_argument("--billing-export")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.draft:
        bkio.die("no draft.json given")
    try:
        with open(a.draft, encoding="utf-8") as fh:
            draft = json.load(fh)
        r = check(draft, a.register, a.billing_export)
    except (OSError, json.JSONDecodeError) as e:
        bkio.die(f"cannot read input: {e}")
    except bkio.InputError as e:
        bkio.die(str(e), "pass the register from templates/invoice-register.csv or a billing export with a number column")
    if not r["register_rows"] and not a.billing_export:
        print("register is empty or missing: double billing cannot be checked; ask for the billing export")
    for x in r["repeats"]:
        print(x)
    print(f"duplicate numbers: {r['duplicate_numbers'] or 'none'}")
    print(f"gaps in sequence: {r['gaps'] or 'none'}")
    print(f"next number (suggestion only): {r['next_number_suggestion'] or 'n/a'}")
    if r["draft_number_in_use"]:
        print(f"CONFLICT: draft number {r['draft_number_in_use']} is already used")
    if r["in_export_not_register"]:
        print(f"in billing export but not in register (export wins): {r['in_export_not_register']}")
    bad = r["repeats"] or r["duplicate_numbers"] or r["draft_number_in_use"]
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
