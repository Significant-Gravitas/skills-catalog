#!/usr/bin/env python3
"""Before chasing, look for customer money that reached the bank but is not
applied to the invoice in the receivables records.

    cd ~/skills/accounts-receivable-follow-up && python3 scripts/find_unapplied.py \
        --bank /home/user/work/bank.canonical.csv --invoices /home/user/in/invoices.csv \
        [--payments /home/user/in/payments.csv] --cutoff "2026-04-30 17:00" \
        --out /home/user/work/unapplied.csv

--bank is a canonical CSV (normalize_export.py): money in is positive.
For each open invoice (amount - credits - recorded payments > 0), a bank
credit dated on or after the invoice's issue date is a candidate when:
  - its description contains the invoice number (not inside a longer
    number), or a digit run of the invoice (4+ digits) as a whole word, e.g.
    'REF 1047' for INV-1047 (strongest). A run shared by two invoice numbers
    ('2026' in 2026-0042 and 2026-0043) never counts on its own, or
  - its amount equals the open balance and the description carries the
    customer name, or
  - its amount equals the open balance (listed, flagged amount-only), or
  - the description carries the customer name but the amount differs
    (weakest: "customer name, amount differs (possible part or combined
    payment)").
The customer name is matched with accents folded ('Cafe Nord' = 'CAFE NORD',
'Zoe Avila' = 'ZOE AVILA') on words of 3+ letters, legal suffixes (Ltd, LLC,
GmbH, ...) and 'and' dropped; a name with no such word ('A1 Ltd') is matched
as its squashed alphanumeric name, as a whole word.
Bank credits already accounted for by a recorded payment are skipped. Each
recorded payment accounts for at most one credit: same amount, within 3 days
(default, confirm with the owner), never a credit that names a different
invoice; it takes the credit naming its own invoice, then its own customer,
then the nearest date. So a second customer's equal payment stays a candidate.
Each bank credit is offered to its strongest invoice match. When it ties at
that strength for several invoices it stays on all of them, marked
'ambiguous: also <invoices>'. A credit whose best match is customer-name-only
is offered to every open invoice of that customer, since it may be a combined
payment; a credit whose best match is amount-only also stays on the invoices
of any customer it names.

Output: invoice, customer, open_balance, bank_row, bank_date, bank_amount,
bank_description, match.

Bank coverage: the bank export's date range is printed, and with --out it is
also written beside the output as <out>.coverage.json (bank_first, bank_last,
cutoff, gap), which ar_aging.py --unapplied reads. When the last bank
date is before the cutoff date, it prints `BANK_COVERAGE_GAP: bank ends <d>,
cutoff <c>` (stdout and stderr) and exits 1: a payment received after <d>
cannot be seen, so no invoice may be chased until the owner supplies a newer
bank export or confirms, in words recorded verbatim, that nothing arrived after
<d>. Exit 0: no gap. Exit 2: bad input.

Candidate invoices go to `status unconfirmed` in
ar_aging.py (--unapplied) and get no chase draft. Candidates are never applied
here; applying cash is a ledger action for the owner.
"""

import argparse
import os
import re
import sys
import unicodedata
from datetime import timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bkio  # noqa: E402

FIELDS = ["invoice", "customer", "open_balance", "bank_row", "bank_date", "bank_amount", "bank_description", "match"]
APPLIED_WINDOW = 3  # days; default, confirm with the owner
NAME_ONLY = "customer name, amount differs (possible part or combined payment)"
STRENGTH = {"invoice number in description": 3, "amount and customer name": 2, "amount only": 1, NAME_ONLY: 0}
# legal suffixes and filler words that never identify a customer
STOP = {"ltd", "limited", "llc", "llp", "inc", "plc", "co", "corp", "gmbh", "aps", "sa", "bv", "ag", "nv", "srl",
        "and", "the", "company", "group", "studio"}
FOLD = str.maketrans({"ø": "o", "Ø": "O", "æ": "ae", "Æ": "AE", "ß": "ss", "đ": "d", "Đ": "D", "ł": "l",
                      "Ł": "L", "œ": "oe", "Œ": "OE", "þ": "th", "Þ": "TH", "ð": "d", "Ð": "D"})


def fold(text):
    """'Café Nørd' -> 'cafe nord': accents dropped and casefolded, so it meets the bank's 'CAFE NORD'."""
    t = unicodedata.normalize("NFKD", (text or "").translate(FOLD))
    return "".join(ch for ch in t if not unicodedata.combining(ch)).casefold()


def tokens(name):
    return set(re.findall(r"[a-z]{3,}", fold(name))) - STOP


def names_customer(customer, desc):
    """True when the bank description carries the customer's name: a shared word
    of 3+ letters (legal suffixes dropped), or, for a name with no such word
    ('A1 Ltd'), the squashed alphanumeric name as a whole word."""
    ct = tokens(customer)
    if ct:
        return bool(ct & tokens(desc))
    squashed = "".join(w for w in re.findall(r"[a-z0-9]+", fold(customer)) if w not in STOP)
    return bool(squashed) and re.search(rf"(?<![a-z0-9]){re.escape(squashed)}(?![a-z0-9])", fold(desc)) is not None


def squash(text):
    return re.sub(r"[^A-Z0-9]", "", fold(text).upper())


def names_invoice(key, runs, desc):
    """The invoice's full normalised number in the description (never as part of
    a longer number: INV-104 is not in INV-1047), or one of its own digit runs
    as a whole word ('REF 1047')."""
    if key and re.search(rf"(?<!\d){re.escape(key)}(?!\d)", squash(desc)):
        return True
    return any(re.search(rf"(?<!\d){d}(?!\d)", desc or "") for d in runs)


def bank_coverage(bank_path, cutoff_date):
    """(first date, last date, gap message or None) for a canonical bank CSV."""
    rows = bkio.read_canonical(bank_path)
    if not rows:
        return None, None, f"BANK_COVERAGE_GAP: {bank_path} has no rows, cutoff {cutoff_date}"
    first, last = min(r["date"] for r in rows), max(r["date"] for r in rows)
    gap = None
    if last < cutoff_date:
        gap = (f"BANK_COVERAGE_GAP: bank ends {last.isoformat()}, cutoff {cutoff_date.isoformat()}; "
               f"payments received {(last + timedelta(days=1)).isoformat()} to {cutoff_date.isoformat()} "
               "cannot be seen. Ask for a newer bank export before any chase")
    return first, last, gap


def invoice_keys(inv):
    """{invoice: (full key, digit runs of 4+ that identify only this invoice)}.
    A run shared with another invoice ('2026' in 2026-0042 and 2026-0043)
    never counts on its own."""
    runs = {r["invoice"]: {d for d in re.findall(r"\d+", r["invoice"]) if len(d) >= 4} for r in inv}
    owners = {}
    for i, rs in runs.items():
        for d in rs:
            owners.setdefault(d, set()).add(i)
    return {i: (squash(i), sorted(d for d in rs if len(owners[d]) == 1)) for i, rs in runs.items()}


def match_recorded(bank, recorded, keys, customer_of):
    """Indexes of bank credits already accounted for by a recorded payment. Each
    recorded payment accounts for at most one credit: same amount, within the
    window, never a credit that names a different invoice; it prefers the credit
    naming its own invoice, then its own customer, then one naming no other
    customer, then the nearest date."""
    used = set()
    for d, a, pinv in sorted(recorded, key=lambda x: (x[0], x[2])):
        cust = customer_of.get(pinv)
        best = None
        for i, b in enumerate(bank):
            if i in used or b["amount"] != a or abs((b["date"] - d).days) > APPLIED_WINDOW:
                continue
            desc = b["description"] or ""
            if any(names_invoice(*keys[o], desc) for o in keys if o != pinv):
                continue
            if pinv in keys and names_invoice(*keys[pinv], desc):
                affinity = 3
            elif cust and names_customer(cust, desc):
                affinity = 2
            elif any(names_customer(c, desc) for c in set(customer_of.values()) if c != cust):
                affinity = 0
            else:
                affinity = 1
            rank = (-affinity, abs((b["date"] - d).days), i)
            if best is None or rank < best[0]:
                best = (rank, i)
        if best:
            used.add(best[1])
    return used


def find(bank_path, invoices_path, payments_path=None):
    bank = [b for b in bkio.read_canonical(bank_path) if b["amount"] > 0]
    _, inv = bkio.read_csv(invoices_path)
    keys = invoice_keys(inv)
    customer_of = {r["invoice"]: r["customer"] for r in inv}
    recorded = []
    paid = {}
    if payments_path:
        _, pays = bkio.read_csv(payments_path)
        for p in pays:
            amt = bkio.parse_amount(p["amount"])[0]
            recorded.append((bkio.parse_iso(p["date"]), amt, p.get("invoice") or ""))
            paid[p["invoice"]] = paid.get(p["invoice"], Decimal(0)) + amt
    used = match_recorded(bank, recorded, keys, customer_of)
    free = [b for i, b in enumerate(bank) if i not in used]
    cands, done = [], set()
    for r in inv:
        amount = bkio.parse_amount(r["amount"])[0]
        credits = bkio.parse_amount(r.get("credits") or "0")[0] or Decimal(0)
        open_bal = amount - credits - paid.get(r["invoice"], Decimal(0))
        if open_bal <= 0:
            continue
        issue = bkio.parse_iso(r["issue_date"])
        inv_key, digit_runs = keys[r["invoice"]]
        for b in free:
            if b["date"] < issue or (r.get("currency") and b["currency"] != r["currency"]):
                continue
            bank_row = f"{b['source_file']}:{b['source_row']}"
            if (r["invoice"], bank_row) in done:
                continue            # a repeated invoice row is listed once
            desc = b["description"] or ""
            match = None
            shares_name = names_customer(r["customer"], desc)
            if names_invoice(inv_key, digit_runs, desc):
                match = "invoice number in description"
            elif b["amount"] == open_bal and shares_name:
                match = "amount and customer name"
            elif b["amount"] == open_bal:
                match = "amount only"
            elif shares_name:
                match = NAME_ONLY
            if match:
                done.add((r["invoice"], bank_row))
                cands.append({"invoice": r["invoice"], "customer": r["customer"], "open_balance": str(open_bal),
                              "bank_row": bank_row, "bank_date": b["date"].isoformat(),
                              "bank_amount": str(b["amount"]), "bank_description": b["description"], "match": match})
    # each bank credit goes to its strongest match. When it ties at that strength
    # for several invoices it stays on all of them, marked ambiguous. A credit
    # whose best match is amount-only also stays on every invoice of a customer
    # it names (a part or combined payment from that customer).
    top = {}
    for c in cands:
        top[c["bank_row"]] = max(top.get(c["bank_row"], -1), STRENGTH[c["match"]])
    keep = [c for c in cands if STRENGTH[c["match"]] == top[c["bank_row"]]
            or (c["match"] == NAME_ONLY and top[c["bank_row"]] == STRENGTH["amount only"])]
    for c in keep:
        others = sorted({o["invoice"] for o in keep if o["bank_row"] == c["bank_row"]
                         and o["invoice"] != c["invoice"] and o["match"] == c["match"]})
        if others and c["match"] != NAME_ONLY:
            c["ambiguous"] = f"; ambiguous: also {', '.join(others)}"
    for c in keep:
        c["match"] += c.pop("ambiguous", "")
    return sorted(keep, key=lambda c: (c["invoice"], c["bank_date"]))


def coverage_path(out):
    return (out[:-4] if out.lower().endswith(".csv") else out) + ".coverage.json"



def selftest():
    import tempfile
    here = os.path.dirname(os.path.abspath(__file__))
    import normalize_export
    ex = os.path.join(here, "..", "examples", "bramble-april-ar")
    rows = normalize_export.normalize(os.path.join(ex, "bank-main-2026-04.csv"), "%d/%m/%Y", currency="GBP")
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "bank.csv")
        bkio.write_csv(p, bkio.CANONICAL, rows)
        c = find(p, os.path.join(ex, "invoices.csv"), os.path.join(ex, "payments.csv"))
        first, last, gap = bank_coverage(p, bkio.parse_iso("2026-04-30"))
        assert last.isoformat() == "2026-04-12" and gap and gap.startswith("BANK_COVERAGE_GAP"), gap
        assert bank_coverage(p, bkio.parse_iso("2026-04-12"))[2] is None
    assert [x["invoice"] for x in c] == ["INV-1042"], c
    assert c[0]["match"] == "invoice number in description"
    # a part-payment with no invoice number and a different amount is still a
    # candidate; an invoice's bare digits ('REF 1051') count as its number
    extra = [
        {"date": "2026-04-20", "description": "KESTREL JOINERY LTD", "amount": "1000.00"},
        {"date": "2026-04-30", "description": "GS REF 1051", "amount": "2000.00"},
    ]
    rows2 = rows + [{"source_file": "bank2.csv", "source_row": 20 + i, "date": e["date"],
                     "description": e["description"], "amount": e["amount"], "currency": "GBP",
                     "reference": "", "balance": ""} for i, e in enumerate(extra)]
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "bank2.csv")
        bkio.write_csv(p, bkio.CANONICAL, rows2)
        c2 = find(p, os.path.join(ex, "invoices.csv"), os.path.join(ex, "payments.csv"))
    by = {x["invoice"]: x for x in c2}
    assert by["INV-1039"]["match"] == NAME_ONLY and by["INV-1039"]["bank_amount"] == "1000.00", c2
    assert by["INV-1051"]["match"] == "invoice number in description", c2
    assert sorted(by) == ["INV-1039", "INV-1042", "INV-1051"], c2

    def run(invoices, bank_rows, payments=None):
        inv_f = ["invoice", "customer", "currency", "issue_date", "due_date", "amount", "credits"]
        with tempfile.TemporaryDirectory() as d:
            ip, bp, pp = (os.path.join(d, n) for n in ("i.csv", "b.csv", "p.csv"))
            bkio.write_csv(ip, inv_f, [dict(zip(inv_f, (i, c, "GBP", "2026-03-01", "2026-03-31", a, "")))
                                       for i, c, a in invoices])
            bkio.write_csv(bp, bkio.CANONICAL, [{"source_file": "b.csv", "source_row": n + 2, "date": dt,
                                                 "description": ds, "amount": a, "currency": "GBP",
                                                 "reference": "", "balance": ""}
                                                for n, (dt, ds, a) in enumerate(bank_rows)])
            if payments is not None:
                bkio.write_csv(pp, ["invoice", "date", "amount"],
                               [dict(zip(["invoice", "date", "amount"], p)) for p in payments])
            return find(bp, ip, pp if payments is not None else None)

    # one recorded payment accounts for one credit only: Beta's equal payment,
    # naming its own invoice, is still a candidate
    c3 = run([("INV-2001", "Alpha Signs Ltd", "500.00"), ("INV-2002", "Beta Print Ltd", "500.00")],
             [("2026-04-10", "ALPHA SIGNS", "500.00"), ("2026-04-11", "BETA PRINT INV-2002", "500.00")],
             [("INV-2001", "2026-04-10", "500.00")])
    assert [(x["invoice"], x["match"]) for x in c3] == [("INV-2002", "invoice number in description")], c3
    # a year prefix shared by two invoice numbers never counts on its own
    c4 = run([("2026-0042", "Beta Print Ltd", "1200.00"), ("2026-0043", "Acme Signs Ltd", "800.00")],
             [("2026-04-14", "ACME SIGNS 2026-0043", "800.00")])
    assert [x["invoice"] for x in c4] == ["2026-0043"], c4
    # an amount-only credit equal to two balances stays on both, marked ambiguous
    c5 = run([("INV-3001", "Gamma Ltd", "750.00"), ("INV-3002", "Epsilon Ltd", "750.00")],
             [("2026-04-12", "FASTER PAYMENT RECEIVED", "750.00")])
    assert [x["invoice"] for x in c5] == ["INV-3001", "INV-3002"], c5
    assert c5[0]["match"] == "amount only; ambiguous: also INV-3002", c5
    # accented and short-word names still meet the bank's plain spelling
    c6 = run([("INV-2003", "Café Nørd", "800.00"), ("INV-2004", "KPM Ltd", "900.00"),
              ("INV-2005", "Zoë Ávila", "700.00"), ("INV-2006", "Oak & Co", "600.00"),
              ("INV-2008", "A1 Ltd", "250.00")],
             [("2026-04-14", "CAFE NORD", "300.00"), ("2026-04-15", "KPM LTD", "400.00"),
              ("2026-04-16", "ZOE AVILA", "200.00"), ("2026-04-17", "OAK AND CO", "100.00"),
              ("2026-04-18", "A1 LTD BACS", "50.00")])
    assert {x["invoice"]: x["match"] for x in c6} == {i: NAME_ONLY for i in
                                                      ("INV-2003", "INV-2004", "INV-2005", "INV-2006", "INV-2008")}, c6
    assert names_invoice("INV104", [], "INV-1047") is False
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bank")
    ap.add_argument("--invoices")
    ap.add_argument("--payments")
    ap.add_argument("--cutoff", help="evidence cutoff, 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD'")
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.bank or not a.invoices or not a.cutoff:
        bkio.die("--bank, --invoices and --cutoff are required",
                 "normalise the bank export first; --cutoff is the evidence cutoff of the payment records")
    try:
        cutoff = bkio.parse_iso(a.cutoff)
        first, last, gap = bank_coverage(a.bank, cutoff)
        c = find(a.bank, a.invoices, a.payments)
    except (bkio.InputError, KeyError) as e:
        bkio.die(str(e), "check the invoice export columns (invoice, customer, currency, issue_date, amount)")
    bkio.write_csv(a.out, FIELDS, c)
    if a.out:
        import json
        with open(coverage_path(a.out), "w", encoding="utf-8") as fh:
            json.dump({"bank_first": first.isoformat() if first else None,
                       "bank_last": last.isoformat() if last else None,
                       "cutoff": cutoff.isoformat(), "gap": gap}, fh, indent=2)
        print(f"bank coverage written to {coverage_path(a.out)}", file=sys.stderr)
    print(f"{len(c)} possible unapplied payments", file=sys.stderr)
    for x in c:
        print(f"  {x['invoice']} ({x['customer']}): {x['bank_amount']} on {x['bank_date']} "
              f"'{x['bank_description']}' [{x['match']}]", file=sys.stderr)
    print(f"bank export covers {first} to {last}; cutoff {cutoff}")
    if gap:
        print(gap)
        print(gap, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
