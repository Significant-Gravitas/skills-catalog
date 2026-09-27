#!/usr/bin/env python3
"""Build the receivables aging and follow-up queue from invoice and payment
exports at a stated cutoff.

    cd ~/skills/accounts-receivable-follow-up && python3 scripts/ar_aging.py \
        --invoices /home/user/in/invoices.csv --payments /home/user/in/payments.csv \
        --cutoff "2026-04-30 17:00" \
        [--disputes <state>/dispute-log.csv] [--contact-log <state>/contact-log.csv] \
        [--unapplied /home/user/work/unapplied.csv] \
        [--buckets 30,60,90] [--due-soon-days 7] --out /home/user/work/aging.csv

Invoices CSV columns: invoice, customer, currency, issue_date, due_date,
terms_days (optional), amount, credits (optional), billing_contact (optional).
Payments CSV: invoice, date, amount (method, reference optional). Dates ISO
(YYYY-MM-DD); convert other formats with normalize_export.py or ask.

Per invoice: paid and credited through the cutoff, open balance, due date and
where it came from, days past due, bucket (Current, 1-30, 31-60, 61-90, 90+ by
default [98]; edges are a default, confirm with the owner), group, last contact
stage, suggested next stage. Groups:
  due soon | past due, no known dispute | disputed or blocked |
  promised payment not yet due | status unconfirmed | paid | credit balance
- No due date: due_date = issue_date + terms_days when terms_days is given
  (source "terms"); with neither, the invoice is `status unconfirmed`. A
  ledger may show such an invoice as due on receipt [97]; confirm terms first.
- A payment dated after the cutoff is ignored and listed, never applied.
- An invoice listed in --unapplied (find_unapplied.py output) is `status
  unconfirmed`: a possible payment is not yet applied, so it is not chased.
- Bank coverage: --unapplied also reads find_unapplied.py's sidecar
  <unapplied>.coverage.json; --bank-coverage-end YYYY-MM-DD sets it by hand.
  When the bank export ends before the cutoff date, every chaseable row gets
  next_stage `hold: bank export ends <d>` (the planned stage is in notes)
  until the owner answers the gap: pass --coverage-confirmed "<the owner's
  words, verbatim>" (quoted in notes) or rerun with a newer bank export.
- An invoice number listed twice in the invoice export is bad input (exit 2,
  lines named): the balance would be counted twice.
- A payment whose invoice is not in the export is printed as an unmatched
  payment and never applied. When it looks like an invoice in the export
  (same number once punctuation is dropped, 'INV1039' for INV-1039, or the
  same digits), that invoice is `status unconfirmed` until the owner says
  where the payment belongs.
Money is exact decimal. Never edits an input. Exit 2 on bad input.
"""

import argparse
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bkio  # noqa: E402

STAGES = ["first reminder", "second reminder", "statement of account", "owner call", "escalate to owner"]
OUT_FIELDS = ["invoice", "customer", "currency", "issue_date", "due_date", "due_source", "amount", "credits",
              "paid_to_cutoff", "open_balance", "days_past_due", "bucket", "group", "dispute", "promised_date",
              "last_stage", "last_contact", "next_stage", "billing_contact", "notes"]


def parse_cutoff(text):
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text.strip(), fmt)
        except ValueError:
            continue
    raise bkio.InputError(f"--cutoff '{text}' must be 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD'")


def bucket_name(days, edges):
    if days is None:
        return ""
    if days <= 0:
        return "Current"
    lo = 1
    for e in edges:
        if days <= e:
            return f"{lo}-{e}"
        lo = e + 1
    return f"{edges[-1]}+"


def money(v, where):
    if v in (None, ""):
        return Decimal(0)
    val, _ = bkio.parse_amount(v)
    if val is None:
        raise bkio.InputError(f"{where}: empty amount")
    return val


def _squash(text):
    return re.sub(r"[^A-Z0-9]", "", (text or "").upper())


def near_invoices(number, invoices):
    """Invoices in the export that a payment's unknown invoice number probably
    means: equal once punctuation is dropped, or the same digits."""
    sq, digits = _squash(number), re.sub(r"\D", "", number or "")
    return sorted(i for i in invoices if (sq and _squash(i) == sq)
                  or (len(digits) >= 3 and re.sub(r"\D", "", i) == digits))


def read_coverage_end(unapplied_path):
    """bank_last from find_unapplied.py's sidecar next to the unapplied CSV, or None."""
    if not unapplied_path:
        return None
    import json
    side = (unapplied_path[:-4] if unapplied_path.lower().endswith(".csv") else unapplied_path) + ".coverage.json"
    if not os.path.exists(side):
        return None
    with open(side, encoding="utf-8") as fh:
        last = json.load(fh).get("bank_last")
    return bkio.parse_iso(last) if last else None


def age(invoices_path, payments_path=None, cutoff="", disputes_path=None, contact_path=None,
        unapplied_path=None, edges=(30, 60, 90), due_soon_days=7, bank_coverage_end=None,
        coverage_confirmed=None):
    cut = parse_cutoff(cutoff)
    cut_date = cut.date()
    cov_end = bkio.parse_iso(bank_coverage_end) if bank_coverage_end else read_coverage_end(unapplied_path)
    hold = cov_end is not None and cov_end < cut_date and not coverage_confirmed
    _, inv_rows = bkio.read_csv(invoices_path)
    need = {"invoice", "customer", "currency", "issue_date", "amount"}
    if inv_rows and not need <= set(inv_rows[0]):
        raise bkio.InputError(f"{invoices_path} needs columns {sorted(need)}; has {sorted(k for k in inv_rows[0] if k != '_row')}")
    seen_at = defaultdict(list)
    for r in inv_rows:
        seen_at[r["invoice"]].append(r["_row"])
    repeated = {i: rows for i, rows in seen_at.items() if len(rows) > 1}
    if repeated:
        raise bkio.InputError("invoice number repeated in the invoice export: " + "; ".join(
            f"{i} on lines {rows}" for i, rows in sorted(repeated.items()))
            + ". Ask which row is right before aging; the balance would be counted twice")
    paid, ignored, unmatched, near = defaultdict(Decimal), [], [], {}
    if payments_path:
        _, pay_rows = bkio.read_csv(payments_path)
        for p in pay_rows:
            d = bkio.parse_iso(p["date"])
            amt = money(p.get("amount"), f"{payments_path} line {p['_row']}")
            if d > cut_date:
                ignored.append(f"{p['invoice']} {amt} on {d} (after cutoff)")
                continue
            if p["invoice"] not in seen_at:
                close = near_invoices(p["invoice"], seen_at)
                unmatched.append(f"{p['invoice']} {amt} on {d} ({payments_path} line {p['_row']}): "
                                 f"no such invoice in the export"
                                 + (f"; possibly {', '.join(close)}" if close else ""))
                for c in close:
                    near.setdefault(c, []).append(f"{p['invoice']} {amt} on {d}")
                continue
            paid[p["invoice"]] += amt
    disputes = {}
    if disputes_path and os.path.exists(disputes_path):
        _, drows = bkio.read_csv(disputes_path)
        for d in drows:
            if (d.get("status") or "").lower() not in ("closed", "resolved"):
                disputes[d["invoice"]] = f"{d.get('stated_issue', '')} (raised {d.get('date_raised', '')}, owner {d.get('owner', '')})"
    contacts = {}
    if contact_path and os.path.exists(contact_path):
        _, crows = bkio.read_csv(contact_path)
        for c in crows:
            if (c.get("approval_state") or "").lower() in ("approved", "sent", "sent_per_owner"):
                contacts[c["invoice"]] = c          # last row wins: logs are append-only
    unapplied = set()
    if unapplied_path and os.path.exists(unapplied_path):
        _, urows = bkio.read_csv(unapplied_path)
        unapplied = {u["invoice"] for u in urows if u.get("invoice")}

    out = []
    for r in inv_rows:
        where = f"{invoices_path} line {r['_row']}"
        issue = bkio.parse_iso(r["issue_date"])
        amount = money(r.get("amount"), where)
        credits = money(r.get("credits"), where)
        pd = paid.get(r["invoice"], Decimal(0))
        open_bal = amount - credits - pd
        notes = []
        due, due_source = None, ""
        if r.get("due_date"):
            due, due_source = bkio.parse_iso(r["due_date"]), "invoice due date"
        elif r.get("terms_days"):
            due, due_source = issue + timedelta(days=int(r["terms_days"])), f"issue date + {r['terms_days']} days terms"
        days = (cut_date - due).days if due else None
        c = contacts.get(r["invoice"], {})
        promised = c.get("promised_date") or ""
        if open_bal == 0:
            group = "paid"
        elif open_bal < 0:
            group = "credit balance"
            notes.append("customer has a credit: owner to decide refund or allocation")
        elif r["invoice"] in unapplied:
            group = "status unconfirmed"
            notes.append("possible payment in bank not applied: confirm before any chase")
        elif r["invoice"] in near:
            group = "status unconfirmed"
            notes.append(f"payment recorded against an unknown invoice ({'; '.join(near[r['invoice']])}) "
                         "may belong here: confirm before any chase")
        elif due is None:
            group = "status unconfirmed"
            notes.append("no due date or terms on record: ask the account owner for the agreed terms")
        elif r["invoice"] in disputes:
            group = "disputed or blocked"
        elif promised and bkio.parse_iso(promised) >= cut_date:
            group = "promised payment not yet due"
        elif days is not None and days > 0:
            group = "past due, no known dispute"
        elif days is not None and -due_soon_days <= days <= 0:
            group = "due soon"
        else:
            group = "not yet due"
        if pd and open_bal > 0:
            notes.append(f"part-paid {pd} to cutoff")
        last = c.get("stage", "")
        nxt = ""
        if group == "past due, no known dispute":
            idx = STAGES.index(last) + 1 if last in STAGES else 0
            nxt = STAGES[min(idx, len(STAGES) - 1)]
            if hold:
                notes.append(f"planned stage: {nxt}; held until the owner answers the bank coverage gap")
                nxt = f"hold: bank export ends {cov_end.isoformat()}"
            elif cov_end is not None and cov_end < cut_date:
                notes.append(f"bank export ends {cov_end.isoformat()}; owner confirmed: \"{coverage_confirmed}\"")
        out.append({
            "invoice": r["invoice"], "customer": r["customer"], "currency": r["currency"],
            "issue_date": issue.isoformat(), "due_date": due.isoformat() if due else "", "due_source": due_source,
            "amount": str(amount), "credits": str(credits), "paid_to_cutoff": str(pd), "open_balance": str(open_bal),
            "days_past_due": "" if days is None else max(days, 0) if days > 0 else days,
            "bucket": bucket_name(days, list(edges)) if due else "unconfirmed",
            "group": group, "dispute": disputes.get(r["invoice"], ""), "promised_date": promised,
            "last_stage": last, "last_contact": c.get("sent_at", ""), "next_stage": nxt,
            "billing_contact": r.get("billing_contact", ""), "notes": "; ".join(notes),
        })
    order = {g: i for i, g in enumerate(["past due, no known dispute", "disputed or blocked", "status unconfirmed",
                                         "promised payment not yet due", "due soon", "not yet due",
                                         "credit balance", "paid"])}
    out.sort(key=lambda x: (order.get(x["group"], 99),
                            -(x["days_past_due"] if isinstance(x["days_past_due"], int) else -10**6),
                            -Decimal(x["open_balance"])))
    totals = defaultdict(Decimal)
    for x in out:
        if Decimal(x["open_balance"]) > 0:
            totals[(x["currency"], x["bucket"])] += Decimal(x["open_balance"])
    return out, totals, ignored, unmatched


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    ex = os.path.join(here, "..", "examples", "bramble-april-ar")
    out, totals, ignored, unmatched = age(os.path.join(ex, "invoices.csv"), os.path.join(ex, "payments.csv"),
                               "2026-04-30 17:00", os.path.join(ex, "dispute-log.csv"),
                               os.path.join(ex, "contact-log.csv"), os.path.join(ex, "unapplied-expected.csv"))
    by = {x["invoice"]: x for x in out}
    assert by["INV-1039"]["days_past_due"] == 61 and by["INV-1039"]["bucket"] == "61-90", by["INV-1039"]
    assert by["INV-1039"]["next_stage"] == "second reminder", by["INV-1039"]
    assert by["INV-1042"]["group"] == "status unconfirmed", by["INV-1042"]
    assert by["INV-1047"]["open_balance"] == "640.00" and by["INV-1047"]["days_past_due"] == 15
    assert by["INV-1049"]["group"] == "promised payment not yet due" and by["INV-1049"]["paid_to_cutoff"] == "0"
    assert by["INV-1051"]["group"] == "disputed or blocked"
    assert by["INV-1045"]["group"] == "due soon" and by["INV-1045"]["bucket"] == "Current"
    assert by["INV-1055"]["group"] == "status unconfirmed" and by["INV-1055"]["bucket"] == "unconfirmed"
    assert any("INV-1049" in i for i in ignored)
    assert out[0]["invoice"] == "INV-1039", [x["invoice"] for x in out]
    # a bank export that ends before the cutoff holds every chase
    held, _, _, _ = age(os.path.join(ex, "invoices.csv"), os.path.join(ex, "payments.csv"),
                     "2026-04-30 17:00", os.path.join(ex, "dispute-log.csv"),
                     os.path.join(ex, "contact-log.csv"), os.path.join(ex, "unapplied-expected.csv"),
                     bank_coverage_end="2026-04-12")
    hb = {x["invoice"]: x for x in held}
    assert hb["INV-1039"]["next_stage"] == "hold: bank export ends 2026-04-12", hb["INV-1039"]
    assert "planned stage: second reminder" in hb["INV-1039"]["notes"], hb["INV-1039"]
    assert hb["INV-1047"]["next_stage"].startswith("hold:"), hb["INV-1047"]
    ok, _, _, _ = age(os.path.join(ex, "invoices.csv"), os.path.join(ex, "payments.csv"),
                   "2026-04-30 17:00", os.path.join(ex, "dispute-log.csv"),
                   os.path.join(ex, "contact-log.csv"), os.path.join(ex, "unapplied-expected.csv"),
                   bank_coverage_end="2026-04-12", coverage_confirmed="Nothing else arrived")
    assert {x["invoice"]: x for x in ok}["INV-1039"]["next_stage"] == "second reminder"
    assert unmatched == [], unmatched
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        ip, pp = os.path.join(d, "i.csv"), os.path.join(d, "p.csv")
        f = ["invoice", "customer", "currency", "issue_date", "due_date", "amount"]
        rows = [dict(zip(f, ("INV-2007", "Delta Works", "GBP", "2026-03-01", "2026-03-31", "400.00")))]
        bkio.write_csv(ip, f, rows + rows)
        try:
            age(ip, None, "2026-04-30")
            raise AssertionError("a repeated invoice number must be refused")
        except bkio.InputError as e:
            assert "INV-2007 on lines [2, 3]" in str(e), e
        bkio.write_csv(ip, f, rows)
        bkio.write_csv(pp, ["invoice", "date", "amount"],
                       [{"invoice": "INV2007", "date": "2026-04-10", "amount": "400.00"}])
        o2, _, _, um = age(ip, pp, "2026-04-30")
        assert o2[0]["group"] == "status unconfirmed" and o2[0]["open_balance"] == "400.00", o2
        assert len(um) == 1 and "possibly INV-2007" in um[0], um
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--invoices")
    ap.add_argument("--payments")
    ap.add_argument("--cutoff")
    ap.add_argument("--disputes")
    ap.add_argument("--contact-log")
    ap.add_argument("--unapplied")
    ap.add_argument("--bank-coverage-end")
    ap.add_argument("--coverage-confirmed")
    ap.add_argument("--buckets", default="30,60,90")
    ap.add_argument("--due-soon-days", type=int, default=7)
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.invoices or not a.cutoff:
        bkio.die("--invoices and --cutoff are required",
                 "the cutoff is the date and time the payment records were exported; state it in the output")
    try:
        edges = tuple(int(x) for x in a.buckets.split(","))
        out, totals, ignored, unmatched = age(a.invoices, a.payments, a.cutoff, a.disputes, a.contact_log,
                                   a.unapplied, edges, a.due_soon_days, a.bank_coverage_end,
                                   a.coverage_confirmed)
    except (bkio.InputError, ValueError, KeyError) as e:
        bkio.die(str(e), "check column names and ISO dates; see the usage at the top of this file")
    bkio.write_csv(a.out, OUT_FIELDS, out)
    if a.out:
        print(f"aging written to {a.out} (cutoff {a.cutoff})")
        print("| Invoice | Customer | Due | Open | Days past due | Bucket | Group | Next stage |")
        print("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for x in out:
            print(f"| {x['invoice']} | {x['customer']} | {x['due_date'] or 'none on record'} | "
                  f"{x['open_balance']} {x['currency']} | {x['days_past_due']} | {x['bucket']} | {x['group']} | {x['next_stage']} |")
    print("Open balance by bucket: " + "; ".join(f"{c} {b}: {v}" for (c, b), v in sorted(totals.items())), file=sys.stderr)
    for i in ignored:
        print(f"ignored payment: {i}", file=sys.stderr)
    if unmatched:
        print("unmatched payments (not applied; ask the owner where each belongs): " + "; ".join(unmatched))


if __name__ == "__main__":
    main()
