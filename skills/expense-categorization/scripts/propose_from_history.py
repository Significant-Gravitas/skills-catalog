#!/usr/bin/env python3
"""Propose accounts from the owner's approved coding rules and past approved
review tables, so the model reasons only over rows with no basis or a conflict.

    cd ~/skills/expense-categorization && python3 scripts/propose_from_history.py \
        --tx /home/user/work/amex.canonical.csv \
        --rules ~/workspace/bookkeeping/<entity>/coding-rules.csv \
        --history ~/workspace/bookkeeping/<entity>/expenses/ \
        [--checks /home/user/work/checks.json] [--chart chart.csv] \
        --out /home/user/work/proposals.csv

Rules CSV: rule_id, pattern, account, dimension, rule_source, approved_by,
approved_on, status. `pattern` is a case-insensitive substring of the
description, or a regular expression when it starts with `re:`.
History: every *.csv in the folder with columns vendor (or description),
final_account and status; only rows with status `approved` count.

Per row the output gives proposed_account, proposed_dimension, basis and
confidence_cap:
- one approved rule matches               -> basis "rule <id>", cap high
- several rules with different accounts   -> no account, basis "conflict: ...", cap medium
- a matching rule that is not approved    -> basis "unapproved rule <id>", cap medium
- history only, all months agree          -> basis "history: n approved rows", cap medium
  (history can repeat an old miscoding; the owner confirms before it is high)
- history disagrees                       -> no account, basis "history conflict", cap low
- special line in checks.json (transfer, loan, tax, payroll, owner, refund,
  card payment, money in)                 -> no proposal, basis "special line: <kinds>"
- nothing                                 -> basis "none", no cap (reason from evidence)
- a row in a duplicate pair (checks.json) -> cap medium (likely, unless its own
                                             receipt ties) or low (exact),
                                             basis gains "duplicate: ask before coding"
A proposed account that is not in --chart is dropped and reported.
Never posts, never edits an input. Exit 2 on bad input.
"""

import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bkio  # noqa: E402

BLOCKING_SPECIALS = {"transfer", "loan", "tax", "payroll", "owner", "refund", "card_payment", "money_in"}
OUT_FIELDS = ["source_file", "source_row", "date", "description", "amount", "currency",
              "proposed_account", "proposed_dimension", "basis", "confidence_cap"]


def load_rules(path):
    if not path or not os.path.exists(path):
        return []
    _, rows = bkio.read_csv(path)
    rules = []
    for r in rows:
        pat = r.get("pattern", "")
        if not pat or not r.get("account"):
            raise bkio.InputError(f"{path} line {r['_row']}: pattern and account are required")
        rx = re.compile(pat[3:], re.I) if pat.startswith("re:") else re.compile(re.escape(pat), re.I)
        rules.append({**r, "rx": rx})
    return rules


def load_history(folder):
    hist = {}
    if not folder:
        return hist
    files = [folder] if os.path.isfile(folder) else glob.glob(os.path.join(folder, "*.csv"))
    for f in files:
        _, rows = bkio.read_csv(f)
        for r in rows:
            if (r.get("status") or "").lower() != "approved" or not r.get("final_account"):
                continue
            key = bkio.norm_text(r.get("vendor") or r.get("description"))
            if key:
                hist.setdefault(key, []).append(r["final_account"])
    return hist


def propose(tx_path, rules_path=None, history=None, checks_path=None, chart_path=None):
    tx = bkio.read_canonical(tx_path)
    rules = load_rules(rules_path)
    hist = load_history(history)
    specials, exact_dups, likely_dups = {}, set(), set()
    if checks_path:
        with open(checks_path, encoding="utf-8") as fh:
            checks = json.load(fh)
        specials = dict(checks.get("special_rows", {}))
        exact_dups = set(checks.get("exact_duplicate_rows", []))
        # a likely-duplicate row whose own receipt ties is the genuine one; cap only the other
        receipted = {r["id"] for r in checks.get("rows", []) if r.get("receipt")}
        likely_dups = set(checks.get("likely_duplicate_rows", [])) - receipted
    chart = None
    if chart_path:
        _, crows = bkio.read_csv(chart_path)
        chart = {r["account"] for r in crows}
    out, dropped = [], []
    for t in tx:
        row = int(t["source_row"])
        rec = {"source_file": t["source_file"], "source_row": row, "date": t["date"].isoformat(),
               "description": t["description"], "amount": str(t["amount"]), "currency": t["currency"],
               "proposed_account": "", "proposed_dimension": "", "basis": "none", "confidence_cap": ""}
        kinds = set(specials.get(f"{t['source_file']}:{row}", []))
        if kinds & BLOCKING_SPECIALS:
            rec["basis"] = "special line: " + ", ".join(sorted(kinds))
            rec["confidence_cap"] = "low"
            out.append(rec)
            continue
        hits = [r for r in rules if r["rx"].search(t["description"] or "")]
        accounts = {h["account"] for h in hits}
        if len(accounts) > 1:
            rec["basis"] = "conflict: " + " vs ".join(f"{h['rule_id']}={h['account']}" for h in hits)
            rec["confidence_cap"] = "medium"
        elif hits:
            h = hits[0]
            rec["proposed_account"] = h["account"]
            rec["proposed_dimension"] = h.get("dimension", "")
            approved = all((x.get("status") or "").lower() == "approved" for x in hits)
            rec["basis"] = f"rule {h['rule_id']}" if approved else f"unapproved rule {h['rule_id']}"
            rec["confidence_cap"] = "high" if approved else "medium"
        else:
            past = hist.get(bkio.norm_text(t["description"]), [])
            if past and len(set(past)) == 1:
                rec["proposed_account"] = past[0]
                rec["basis"] = f"history: {len(past)} approved rows"
                rec["confidence_cap"] = "medium"
            elif past:
                rec["basis"] = "history conflict: " + ", ".join(sorted(set(past)))
                rec["confidence_cap"] = "low"
        if kinds - BLOCKING_SPECIALS and rec["confidence_cap"] == "high":
            rec["confidence_cap"] = "medium"
            rec["basis"] += "; check " + ", ".join(sorted(kinds - BLOCKING_SPECIALS))
        rid = f"{t['source_file']}:{row}"
        if rid in exact_dups or rid in likely_dups:
            cap = "low" if rid in exact_dups else "medium"
            if rec["confidence_cap"] in ("", "high") or (cap == "low" and rec["confidence_cap"] == "medium"):
                rec["confidence_cap"] = cap
            rec["basis"] += "; " + ("exact" if rid in exact_dups else "likely") + " duplicate: ask before coding"
        if chart is not None and rec["proposed_account"] and rec["proposed_account"] not in chart:
            dropped.append((row, rec["proposed_account"]))
            rec["basis"] += f"; dropped '{rec['proposed_account']}' (not in chart)"
            rec["proposed_account"] = ""
            rec["confidence_cap"] = "low"
        out.append(rec)
    return out, dropped


def selftest():
    import tempfile
    here = os.path.dirname(os.path.abspath(__file__))
    import normalize_export
    import expense_checks
    ex = os.path.join(here, "..", "examples", "bramble-april-card")
    rows = normalize_export.normalize(os.path.join(ex, "amex-2026-04.csv"), "%Y-%m-%d", flip=True)
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "amex.csv")
        bkio.write_csv(p, bkio.CANONICAL, rows)
        chk = expense_checks.run(p, os.path.join(ex, "receipts.csv"))
        cp = os.path.join(d, "checks.json")
        with open(cp, "w", encoding="utf-8") as fh:
            json.dump(chk, fh)
        out, dropped = propose(p, os.path.join(ex, "coding-rules.csv"), os.path.join(ex, "history"),
                               cp, os.path.join(ex, "chart.csv"))
    by = {r["source_row"]: r for r in out}
    assert by[2]["basis"] == "rule R1" and by[2]["confidence_cap"] == "high", by[2]
    assert by[5]["confidence_cap"] == "medium" and "likely duplicate" in by[5]["basis"], by[5]
    assert by[7]["confidence_cap"] == "low" and "exact duplicate" in by[7]["basis"], by[7]
    assert by[3]["basis"].startswith("conflict") and not by[3]["proposed_account"], by[3]
    assert by[4]["basis"] == "unapproved rule R7" and by[4]["confidence_cap"] == "medium", by[4]
    assert by[6]["basis"].startswith("history") and by[6]["proposed_account"] == "Meals and subsistence", by[6]
    assert by[8]["basis"].startswith("special line"), by[8]
    assert by[9]["basis"] == "none" or "check" in by[9]["basis"], by[9]
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tx")
    ap.add_argument("--rules")
    ap.add_argument("--history")
    ap.add_argument("--checks")
    ap.add_argument("--chart")
    ap.add_argument("--out")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.tx:
        bkio.die("--tx is required", "pass the canonical CSV from normalize_export.py")
    try:
        out, dropped = propose(a.tx, a.rules, a.history, a.checks, a.chart)
    except (bkio.InputError, re.error) as e:
        bkio.die(str(e), "fix the rules or history file; a pattern starting 're:' must be a valid regex")
    bkio.write_csv(a.out, OUT_FIELDS, out)
    counts = {}
    for r in out:
        k = r["basis"].split(":")[0].split(" ")[0]
        counts[k] = counts.get(k, 0) + 1
    print(f"{len(out)} rows: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())), file=sys.stderr)
    for row, acct in dropped:
        print(f"row {row}: proposed '{acct}' is not in the chart; left unresolved", file=sys.stderr)


if __name__ == "__main__":
    main()
