#!/usr/bin/env python3
"""Turn a rec_match.py output folder into the reconciliation workpaper and the state record.

Standard library only; writes an .xlsx as well if openpyxl happens to be importable.
Reads only the rec_match output folder. Never edits it, never sends anything.

    cd ~/skills/statement-reconciliation && python3 scripts/write_workpaper.py \
        --rec /home/user/out/rec/main-4411-2026-04 \
        --entity "Bramble Design Ltd" --preparer "Mina (AI bookkeeper)" \
        [--owners /home/user/in/owners.csv]     # side,id,owner,next_step
        [--xlsx]

Writes into the same folder:
  workpaper.md     the bank-rec layout, item classes, aging, diagnostics, sign-off block
  rec-state.json   what the next period needs (copy to recs/<account>-<YYYY-MM>.json)
  carried-next.csv open items to pass as --carried next month
  workpaper.xlsx   only with --xlsx and openpyxl installed
"""

import argparse
import csv
import datetime as dt
import json
import os
import sys
from decimal import Decimal

sys.dont_write_bytecode = True  # keep the package free of __pycache__
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rec_match import mask  # noqa: E402  same masking as the matcher's outputs

# Aging buckets in days. Illustrative defaults from references/bank-rec-layout.md;
# default — confirm the buckets and actions with the owner.
BUCKETS = [(30, "current", "monitor"), (60, "aging", "ask the owner why it has not cleared"),
           (90, "overdue", "escalate to the finance owner"), (10 ** 6, "stale", "escalate; accountant decides on any correction")]


def read_csv(path):
    if not os.path.isfile(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def bucket(days):
    for limit, label, action in BUCKETS:
        if days <= limit:
            return label, action
    return BUCKETS[-1][1], BUCKETS[-1][2]


def fmt(x):
    d = Decimal(x)
    s = f"{abs(d):,.2f}"
    return f"({s})" if d < 0 else s


def build(rec, entity, preparer, owners):
    with open(os.path.join(rec, "summary.json"), encoding="utf-8") as fh:
        s = json.load(fh)
    uns = read_csv(os.path.join(rec, "unmatched_statement.csv"))
    unl = read_csv(os.path.join(rec, "unmatched_ledger.csv"))
    pairs = read_csv(os.path.join(rec, "ledger_errors.csv"))
    matches = read_csv(os.path.join(rec, "matches.csv"))
    as_of = dt.date.fromisoformat(s["period"].split(" to ")[1])
    for p in pairs:
        p["note"] = mask(p.get("note", ""))
    for r in uns + unl:
        # Masked again here so an older rec folder cannot put a full number into
        # the workpaper before it is hashed for approval.
        r["description"] = mask(r.get("description", ""))
        r["reference"] = mask(r.get("reference", ""))
        o = owners.get((r["side"], r["id"]), {})
        r["owner"] = o.get("owner") or r.get("owner") or "UNASSIGNED"
        r["next_step"] = o.get("next_step") or r.get("next_step") or "UNASSIGNED"
        age = (as_of - dt.date.fromisoformat(r["date"])).days
        r["age"] = age
        r["bucket"], r["action"] = bucket(age)

    timing = [r for r in unl if r["class"] == "timing"]
    dit = [r for r in timing if Decimal(r["amount"]) > 0]
    op = [r for r in timing if Decimal(r["amount"]) < 0]
    bank_err = [r for r in uns if r["class"] == "bank-error"]
    corr_s = [r for r in uns if r["class"] == "correction"]
    corr_l = [r for r in unl if r["class"] == "correction"]
    inv = [r for r in uns + unl if r["class"] == "investigate"]
    period = s["period"]
    L = []
    L.append(f"# Reconciliation workpaper: {entity}, {s['account']}, {period} ({s['currency']})")
    L.append("")
    L.append(f"Status: **{s['status']}**. Prepared by {preparer}. Figures from `rec_match.py` (script-verified).")
    L.append(f"Matching window: {s['window_days']} days ({s['window_days_note']}).")
    L.append("")
    L.append("## Prior-period tie")
    L.append("")
    pac = s.get("prior_approved_closing")
    L.append(f"Prior approved closing: {fmt(pac) if pac else 'none on file (first period or not approved): open item'}; "
             f"statement opening: {fmt(s['statement_opening'])}.")
    L.append("")
    L.append("## Layout")
    L.append("")
    L.append("```")
    w = 44
    L.append(f"{'Balance per statement at ' + str(as_of) + ':':<{w}}{fmt(s['statement_closing']):>14}")
    L.append(f"{'Add: deposits in transit (' + str(len(dit)) + ')':<{w}}{fmt(sum((Decimal(r['amount']) for r in dit), Decimal(0))):>14}")
    L.append(f"{'Less: outstanding payments (' + str(len(op)) + ')':<{w}}{fmt(sum((Decimal(r['amount']) for r in op), Decimal(0))):>14}")
    L.append(f"{'Add/less: statement errors, proved (' + str(len(bank_err)) + ')':<{w}}{fmt(-sum((Decimal(r['amount']) for r in bank_err), Decimal(0))):>14}")
    L.append(f"{'Adjusted statement balance:':<{w}}{fmt(s['adjusted_statement_balance']):>14}")
    L.append("")
    L.append(f"{'Balance per ledger at ' + str(as_of) + ':':<{w}}{fmt(s['ledger_closing']):>14}")
    L.append(f"{'Add/less: items not in the ledger (' + str(len(corr_s)) + ')':<{w}}{fmt(sum((Decimal(r['amount']) for r in corr_s), Decimal(0))):>14}")
    L.append(f"{'Add/less: ledger errors, proved (' + str(len(corr_l) + len(pairs)) + ')':<{w}}"
             f"{fmt(-sum((Decimal(r['amount']) for r in corr_l), Decimal(0)) + sum((Decimal(p['correction']) for p in pairs), Decimal(0))):>14}")
    L.append(f"{'Adjusted ledger balance:':<{w}}{fmt(s['adjusted_ledger_balance']):>14}")
    L.append("")
    L.append(f"{'Unexplained difference:':<{w}}{fmt(s['unexplained_difference']):>14}")
    L.append("```")
    L.append("")
    L.append(f"Matched: {s['matched_groups']} groups, value {fmt(s['matched_value'])}. "
             f"Statement lines in period: {s['statement_lines_in_period']}; ledger rows: {s['ledger_rows_in_period']}.")
    L.append("")
    L.append(f"Movements: statement money in {fmt(s['statement_credits'])}, out {fmt(s['statement_debits'])}; "
             f"ledger money in {fmt(s['ledger_credits'])}, out {fmt(s['ledger_debits'])}. "
             f"Openings: statement {fmt(s['statement_opening'])}, ledger {fmt(s['ledger_opening'])}.")
    L.append("")
    L.append("Ledger-side items are proposals for the accountant, not entries. Nothing has been posted, matched in the ledger, or deleted.")
    L.append("")
    L.append("## Reconciling items and aging")
    L.append("")
    L.append("Aging buckets: 0-30 current, 31-60 aging, 61-90 overdue, over 90 stale (default — confirm with the owner).")
    L.append("")
    L.append("| Side | Id | Date | Description | Amount | Class | Age | Bucket | Owner | Next step |")
    L.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in sorted(uns + unl, key=lambda r: (r["class"] != "investigate", -r["age"])):
        L.append(f"| {r['side']} | {r['id']} | {r['date']} | {r['description']} | {fmt(r['amount'])} | {r['class']}"
                 f"{' (' + r['why'] + ')' if r['why'].startswith(('default', 'cleared', 'late')) else ''} | {r['age']} | {r['bucket']} | {r['owner']} | {r['next_step']} |")
    for p in pairs:
        L.append(f"| pair | {p['statement_id']}/{p['ledger_id']} | | ledger error: {p['note']} | {fmt(p['correction'])} | correction | | | | draft for accountant |")
    L.append("")
    if s["stops"] or s["notes"] or s["diagnostics"]:
        L.append("## Controls and diagnostics")
        L.append("")
        for x in s["stops"] + s["notes"] + s["diagnostics"]:
            L.append(f"- {x}")
        L.append("")
    unowned = [r for r in inv if r["owner"] == "UNASSIGNED"]
    unowned_all = [r for r in uns + unl if r["owner"] == "UNASSIGNED" or r["next_step"] == "UNASSIGNED"]
    L.append("## Sign-off")
    L.append("")
    if s["status"] == "RECONCILED" and unowned_all:
        L.append(f"Not ready for sign-off. The figures tie, but {len(unowned_all)} open item(s) have no owner or next step "
                 f"({', '.join(r['side'] + ' ' + r['id'] for r in unowned_all)}). Assign each one (--owners) and rebuild this workpaper "
                 "before asking the owner to sign.")
    elif s["status"] == "RECONCILED":
        L.append("Ready for owner sign-off. Signing off confirms review of this workpaper; it does not post any correction.")
    else:
        L.append(f"Not reconciled. {len(inv)} item(s) to investigate"
                 + (f", {len(unowned)} without an owner: assign before review." if unowned else ", each with an owner and next step.")
                 + " The owner may record this as *reviewed*, never as *reconciled*.")
    L.append("")
    L.append("Reviewer: ____________  Date: ________  (recorded in approvals.csv with this file's SHA-256)")
    md = "\n".join(L) + "\n"

    # Ledger corrections (confirmed ledger-error pairs and ledger 'correction'
    # rows) are carried as statement-side corrections, never dropped.
    corrections = correction_items(pairs, corr_l, owners)
    unl_next = [r for r in unl if r["class"] != "correction"]

    state = {"entity": entity, "account": s["account"], "currency": s["currency"], "period": period,
             "status": s["status"], "statement_closing": s["statement_closing"], "ledger_closing": s["ledger_closing"],
             "unexplained_difference": s["unexplained_difference"],
             "open_items": [{k: r[k] for k in ("side", "id", "date", "amount", "description", "class", "owner", "next_step")}
                            for r in uns + unl_next + corrections],
             "approval_ref": None, "note": "approval_ref is filled only from approvals.csv; until then this closing is NOT an approved closing"}
    carried = [dict(r, originated=r.get("originated") or r["date"][:7]) for r in uns + unl_next + corrections]
    return md, state, carried, (s, uns, unl, matches)


def bare(rid):
    """The id without its carried:<YYYY-MM>: namespace."""
    return str(rid).split(":")[-1]


def correction_items(pairs, corr_l, owners):
    """Drafted ledger corrections that stay open until the accountant posts them.

    Each one is carried as a statement-side 'correction' row for the amount the
    ledger still needs. Next month it adjusts the ledger side while unposted, and
    it matches the posted correcting entry (same amount) once it is posted. So a
    month that truly reconciles says RECONCILED, and an unposted correction stays
    an owned open item, not an unexplained difference.
      ledger-error pair                        -> amount = statement_amount - ledger_amount
      ledger 'correction' row (e.g. duplicate) -> amount = -(ledger amount), its reversal
    """
    out = []
    for p in pairs:
        out.append({"side": "statement", "id": f"{bare(p['statement_id'])}/{bare(p['ledger_id'])}",
                    "date": p["statement_date"], "amount": p["correction"],
                    "description": f"ledger correction to post: {p['note'] or 'ledger error'}", "reference": "",
                    "originated": p["statement_date"][:7], "class": "correction"})
    for r in corr_l:
        out.append({"side": "statement", "id": f"ledger-{bare(r['id'])}", "date": r["date"],
                    "amount": str(-Decimal(r["amount"])),
                    "description": f"ledger correction to post: reverse ledger {bare(r['id'])} ({r['description']})",
                    "reference": "", "originated": r.get("originated") or r["date"][:7], "class": "correction"})
    for c in out:
        o = owners.get(("statement", c["id"]), {})
        c["owner"] = o.get("owner") or "accountant"
        c["next_step"] = o.get("next_step") or "post the drafted correction; it clears when the correcting entry is in the ledger"
    return out


def write_xlsx(path, data):
    try:
        import openpyxl  # type: ignore
    except ImportError:
        print("openpyxl not installed: skipped workpaper.xlsx (the .md and CSV files are complete)")
        return
    s, uns, unl, matches = data
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Summary"
    for k, v in s.items():
        ws.append([k, json.dumps(v) if isinstance(v, (list, dict)) else v])
    for title, rows in (("Matched", matches), ("Statement only", uns), ("Ledger only", unl)):
        sh = wb.create_sheet(title)
        if rows:
            sh.append(list(rows[0].keys()))
            for r in rows:
                sh.append([str(v) for v in r.values()])
    wb.save(path)
    print(f"wrote {path}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--rec", required=False)
    p.add_argument("--entity", default="(entity not stated)")
    p.add_argument("--preparer", default="Mina (AI bookkeeper)")
    p.add_argument("--owners")
    p.add_argument("--xlsx", action="store_true")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    if a.selftest:
        return selftest()
    if not a.rec or not os.path.isfile(os.path.join(a.rec, "summary.json")):
        print("error: --rec must be a rec_match.py output folder (it holds summary.json). Run rec_match.py first.", file=sys.stderr)
        return 2
    owners = {}
    if a.owners:
        for r in read_csv(a.owners):
            owners[(r["side"], r["id"])] = r
    md, state, carried, data = build(a.rec, a.entity, a.preparer, owners)
    with open(os.path.join(a.rec, "workpaper.md"), "w", encoding="utf-8") as fh:
        fh.write(md)
    with open(os.path.join(a.rec, "rec-state.json"), "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2)
    fields = ["side", "id", "date", "amount", "description", "reference", "originated", "class", "owner", "next_step"]
    with open(os.path.join(a.rec, "carried-next.csv"), "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        wr.writeheader()
        wr.writerows(carried)
    if a.xlsx:
        write_xlsx(os.path.join(a.rec, "workpaper.xlsx"), data)
    print(f"wrote {a.rec}/workpaper.md, rec-state.json, carried-next.csv ({state['status']}, unexplained {state['unexplained_difference']})")
    return 0


def selftest():
    import subprocess
    import tempfile
    here = os.path.dirname(os.path.abspath(__file__))
    d = os.path.join(os.path.dirname(here), "examples", "scenarios", "c-plug-temptation")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, os.path.join(here, "rec_match.py"), "--statement", os.path.join(d, "statement.csv"),
                        "--ledger", os.path.join(d, "ledger.csv"), "--balances", os.path.join(d, "balances.json"),
                        "--classify", os.path.join(d, "classify.csv"), "--out", tmp], check=True, capture_output=True)
        md, state, carried, _ = build(tmp, "Test Ltd", "selftest", {})
        assert "NOT RECONCILED" in md and "never as *reconciled*" in md, md
        assert state["approval_ref"] is None
        assert any(c["id"] == "194" for c in carried)
    # A reconciled run whose open items have no owner must not say "Ready for owner sign-off".
    d = os.path.join(os.path.dirname(here), "examples", "scenarios", "a-clean-tie")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([sys.executable, os.path.join(here, "rec_match.py"), "--statement", os.path.join(d, "statement.csv"),
                        "--ledger", os.path.join(d, "ledger.csv"), "--balances", os.path.join(d, "balances.json"),
                        "--classify", os.path.join(d, "classify.csv"), "--next-statement", os.path.join(d, "next-statement.csv"),
                        "--out", tmp], check=True, capture_output=True)
        md, _, _, _ = build(tmp, "Test Ltd", "selftest", {})
        assert "Ready for owner sign-off" not in md and "Not ready for sign-off" in md, md
        owners = {(side, i): {"owner": "Sam", "next_step": "confirm on May statement"}
                  for side, i in (("ledger", "L7"), ("ledger", "L8"), ("statement", "S6"))}
        md, _, _, _ = build(tmp, "Test Ltd", "selftest", owners)
        assert "Ready for owner sign-off" in md, md
    # Long numbers in bank text (card, mandate, trace references) never reach an output.
    d = os.path.join(os.path.dirname(here), "examples", "scenarios", "a-clean-tie")
    with tempfile.TemporaryDirectory() as tmp:
        st = os.path.join(tmp, "statement.csv")
        with open(os.path.join(d, "statement.csv"), encoding="utf-8") as fh:
            body = fh.read().replace("ACCOUNT FEE APR,,", "CARD 4111 1111 1111 1111 FEE REF 123456789012,99887766554,")
        with open(st, "w", encoding="utf-8") as fh:
            fh.write(body)
        out = os.path.join(tmp, "rec")
        subprocess.run([sys.executable, os.path.join(here, "rec_match.py"), "--statement", st,
                        "--ledger", os.path.join(d, "ledger.csv"), "--balances", os.path.join(d, "balances.json"),
                        "--out", out], check=True, capture_output=True)
        subprocess.run([sys.executable, os.path.abspath(__file__), "--rec", out], check=True, capture_output=True)
        for name in os.listdir(out):
            with open(os.path.join(out, name), encoding="utf-8") as fh:
                text = fh.read()
            for raw in ("4111 1111 1111 1111", "123456789012", "99887766554"):
                assert raw not in text, (name, raw)
        with open(os.path.join(out, "workpaper.md"), encoding="utf-8") as fh:
            assert "****1111" in fh.read()
    two_month_corrections(here)
    print("selftest ok")
    return 0


def two_month_corrections(here):
    """April b-transposition (95.00 keyed as 59.00, confirmed ledger-error) plus a
    duplicate ledger row classed 'correction'; then May with and without the
    accountant's correcting entries. Posted: RECONCILED, 0 investigate, nothing
    carried. Unposted: RECONCILED only because both corrections are carried as
    owned open items, and they are carried again."""
    import subprocess
    import tempfile
    d = os.path.join(os.path.dirname(here), "examples", "scenarios", "b-transposition")
    rm = os.path.join(here, "rec_match.py")

    def w(path, text):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)

    def run(args):
        r = subprocess.run([sys.executable, "-B", rm] + args, capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
        with open(os.path.join(args[args.index("--out") + 1], "summary.json"), encoding="utf-8") as fh:
            return json.load(fh)

    with tempfile.TemporaryDirectory() as tmp:
        j = lambda f: os.path.join(tmp, f)
        with open(os.path.join(d, "ledger.csv"), encoding="utf-8") as fh:
            w(j("apr-lg.csv"), fh.read().rstrip("\n") + "\nL9,2026-04-12,-100.00,Stationery (keyed twice),,\n")
        with open(os.path.join(d, "classify.csv"), encoding="utf-8") as fh:
            w(j("apr-cl.csv"), fh.read().rstrip("\n") + "\nledger,L9,correction,,duplicate of the stationery bill\n")
        with open(os.path.join(d, "balances.json"), encoding="utf-8") as fh:
            b = json.load(fh)
        b["ledger_closing"] = "22991.00"
        w(j("apr-bal.json"), json.dumps(b))
        s = run(["--statement", os.path.join(d, "statement.csv"), "--ledger", j("apr-lg.csv"), "--balances", j("apr-bal.json"),
                 "--classify", j("apr-cl.csv"), "--out", j("apr")])
        assert s["status"] == "RECONCILED", s
        _, state, carried, _ = build(j("apr"), "Test Ltd", "selftest", {})
        corr = {c["id"]: c["amount"] for c in carried if c["side"] == "statement" and c["class"] == "correction"}
        assert corr.get("S3/L3") == "-36.00" and corr.get("ledger-L9") == "100.00", carried
        assert {"S3/L3", "ledger-L9"} <= {o["id"] for o in state["open_items"]}, state["open_items"]
        assert not any(c["side"] == "ledger" and c["id"] == "L9" for c in carried), carried
        fields = ["side", "id", "date", "amount", "description", "reference", "originated", "class", "owner", "next_step"]
        with open(j("carried.csv"), "w", newline="", encoding="utf-8") as fh:
            wr = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
            wr.writeheader()
            wr.writerows(carried)
        w(j("may-st.csv"), "id,date,amount,description,reference,fitid\nS1,2026-05-01,900.00,FPS WORKSHOP INV-1050,INV-1050,F1101\n"
                           "S2,2026-05-03,-1250.00,BACS KESTREL STUDIO 553,553,F1102\nS3,2026-05-28,-12.50,ACCOUNT FEE MAY,,F1103\n")
        base = {"account": "main-4411", "currency": "GBP", "period_start": "2026-05-01", "period_end": "2026-05-31",
                "statement_opening": "23392.50", "statement_closing": "23030.00", "ledger_opening": "22991.00",
                "prior_approved_closing": "23392.50"}
        head = "id,date,amount,description,reference,fitid\nL1,2026-05-02,-12.50,Bank fee April (per rec),,\n"
        # Posted: the Adobe correction and the duplicate's reversal are in the May ledger.
        w(j("may-lg.csv"), head + "L2,2026-05-02,-36.00,Correct Adobe April keyed 59 not 95,,\n"
                                  "L4,2026-05-02,100.00,Reverse duplicate stationery,,\nL3,2026-05-28,-12.50,Bank fee May,,\n")
        w(j("may-bal.json"), json.dumps(dict(base, ledger_closing="23030.00")))
        s = run(["--statement", j("may-st.csv"), "--ledger", j("may-lg.csv"), "--balances", j("may-bal.json"),
                 "--carried", j("carried.csv"), "--out", j("may")])
        assert s["status"] == "RECONCILED" and s["investigate_items"] == 0 and s["unexplained_difference"] == "0.00", s
        _, state, carried2, _ = build(j("may"), "Test Ltd", "selftest", {})
        assert carried2 == [], carried2
        # Unposted: no correcting entries; both stay as owned corrections.
        w(j("may-lg2.csv"), head + "L3,2026-05-28,-12.50,Bank fee May,,\n")
        w(j("may-bal2.json"), json.dumps(dict(base, ledger_closing="22966.00")))
        s = run(["--statement", j("may-st.csv"), "--ledger", j("may-lg2.csv"), "--balances", j("may-bal2.json"),
                 "--carried", j("carried.csv"), "--out", j("may2")])
        assert s["status"] == "RECONCILED" and s["investigate_items"] == 0, s
        md, state, carried3, _ = build(j("may2"), "Test Ltd", "selftest", {})
        ids = sorted(c["id"] for c in carried3)
        assert ids == ["carried:2026-04:S3/L3", "carried:2026-04:ledger-L9"], ids
        assert all(c["class"] == "correction" and c["owner"] == "accountant" for c in carried3), carried3


if __name__ == "__main__":
    sys.exit(main())
