#!/usr/bin/env python3
"""Keep the exception register and the missing-documents request list.

Python 3 standard library only. Appends and updates rows in the two CSVs you
name; never deletes a row, never sends anything.

    cd ~/skills/bookkeeping-exception-escalation
    R=~/workspace/bookkeeping/<entity>/exceptions.csv
    python3 scripts/register.py new --register $R --entity "Northgate Joinery Ltd" --account current-4411 \
        --period 2026-05 --class bank-detail-change --amount 4960.00 --currency GBP \
        --facts-ref "bills.csv:bill=8812; email 28 May" --decision "Confirm through a known contact or hold bill 8812" \
        --owner "Alex (finance owner)" --urgency "before payment run 5 Jun" --interim "bill 8812 left unapproved in the draft run"
    python3 scripts/register.py decide --register $R --id BX-7 --by "Alex" --verbatim "Hold it until I call Kestrel."
    python3 scripts/register.py close --register $R --id BX-7 --by "Alex" --verbatim "Called Kestrel on the old number: fraud. Close."
    python3 scripts/register.py list --register $R [--status open]

    Q=~/workspace/bookkeeping/<entity>/requests.csv
    python3 scripts/register.py request --requests $Q --owner Jo --item "Amex 12 Apr, 86.40, TFL" \
        --why "no receipt for a card line" --settles "receipt or journey record" --due 2026-05-08
    python3 scripts/register.py answer --requests $Q --id RQ-3 --verbatim "Uploading now"
    python3 scripts/register.py requests --requests $Q [--owner Jo] [--open]

Ids are never reused: the next id is one more than the highest ever issued.
Only the owner closes an exception: `close` needs the owner's words verbatim.
Exit codes: 0 ok; 2 bad input.
"""

import argparse
import csv
import datetime as dt
import os
import re
import sys
import tempfile

sys.dont_write_bytecode = True  # keep the package free of __pycache__
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_pack import mask  # noqa: E402  same masking as the exception pack

MASK_NOTE = " [verbatim, account numbers masked to last 4]"

EX_FIELDS = ["id", "raised_on", "entity", "account", "period", "class", "amount", "currency", "facts_ref",
             "decision_requested", "owner", "urgency", "interim_state", "status", "decision_verbatim",
             "decided_by", "decided_on", "evidence_path"]
RQ_FIELDS = ["id", "owner", "item", "why_needed", "settles_with", "asked_on", "due_on", "answered_on", "answer", "exception_id"]
CLASSES = [
    "missing-source", "duplicate-or-conflict", "unknown-party-or-purpose", "mismatch",
    "bank-detail-change", "unusual-payment", "tax-payroll-equity-loan-asset-policy",
    "suspected-error-fraud", "privacy-access", "payroll-tax-shortfall", "worker-classification",
    "receipt-without-payment-line", "payee-missing-w9-tin", "closed-period-change",
]
STATUSES = ["open", "decided", "closed_by_owner", "superseded"]


class InputError(Exception):
    pass


def read(path, fields):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as fh:
        rd = csv.DictReader(fh)
        missing = [f for f in fields if f not in (rd.fieldnames or [])]
        if missing:
            raise InputError(f"{path} is missing columns {missing}; compare with templates/")
        return list(rd)


def write(path, rows, fields):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, path)


def next_id(rows, prefix):
    nums = [int(m.group(1)) for r in rows for m in [re.fullmatch(prefix + r"-(\d+)", r["id"])] if m]
    return f"{prefix}-{max(nums, default=0) + 1}"


def no_long_numbers(*texts):
    for t in texts:
        cleaned = re.sub(r"\d{4}-\d{2}-\d{2}", "", t or "")
        cleaned = re.sub(r"(?<!\d)(?:19|20)\d{2}-\d{2}(?!\d)", "", cleaned)  # periods, e.g. main-4411-2026-04
        # Same shape as build_pack.LONG_DIGITS: space/dash groups count, trailing
        # punctuation does not hide a number, a decimal tail (an amount) is allowed.
        if re.search(r"(?<![\d.])(?<!\d,)\d(?:[ -]?\d){7,}(?!\d)(?![.,]\d)", cleaned):
            raise InputError("a field holds 8 or more consecutive digits (an account or card number?). "
                             "Store only the last 4 digits.")


def masked(text):
    """Owner's words and other free text as stored: account, card and IBAN numbers
    keep only their last 4 (dates and amounts stay), with a note when anything
    was masked, so shared state never holds a full number."""
    t = mask(text or "")
    return t + MASK_NOTE if t != (text or "") else t


def find(rows, rid):
    for r in rows:
        if r["id"] == rid:
            return r
    raise InputError(f"no row with id {rid}")


def cmd_new(a):
    if a.cls not in CLASSES:
        raise InputError(f"--class must be one of {CLASSES}")
    no_long_numbers(a.account, a.facts_ref, a.decision, a.interim)
    rows = read(a.register, EX_FIELDS)
    rid = next_id(rows, "BX")
    rows.append({"id": rid, "raised_on": str(dt.date.today()), "entity": a.entity, "account": a.account,
                 "period": a.period, "class": a.cls, "amount": a.amount, "currency": a.currency,
                 "facts_ref": a.facts_ref, "decision_requested": a.decision, "owner": mask(a.owner),
                 "urgency": mask(a.urgency), "interim_state": a.interim, "status": "open",
                 "decision_verbatim": "", "decided_by": "", "decided_on": "", "evidence_path": mask(a.evidence_path or "")})
    write(a.register, rows, EX_FIELDS)
    print(f"{rid} opened ({a.cls}), owner {a.owner}")
    return 0


def cmd_decide(a, closing=False):
    rows = read(a.register, EX_FIELDS)
    r = find(rows, a.id)
    if r["status"] in ("closed_by_owner", "superseded"):
        raise InputError(f"{a.id} is {r['status']}; open a new exception instead of reopening it")
    if not a.verbatim.strip():
        raise InputError("--verbatim is empty: record the owner's words exactly")
    r["status"] = "closed_by_owner" if closing else "decided"
    words = masked(a.verbatim)
    r["decision_verbatim"] = (r["decision_verbatim"] + " | " if r["decision_verbatim"] else "") + words
    r["decided_by"] = mask(a.by)
    r["decided_on"] = str(dt.date.today())
    write(a.register, rows, EX_FIELDS)
    print(f"{a.id} -> {r['status']} ({r['decided_by']}: \"{words}\")")
    return 0


def cmd_list(a):
    rows = read(a.register, EX_FIELDS)
    for r in rows:
        if a.status and r["status"] != a.status:
            continue
        print(f"{r['id']} [{r['status']}] {r['raised_on']} {r['class']} {r['amount']} {r['currency']} "
              f"owner {r['owner']}; ask: {r['decision_requested']}; urgency: {r['urgency']}")
    return 0


def cmd_request(a):
    no_long_numbers(a.item, a.why, a.settles)
    rows = read(a.requests, RQ_FIELDS)
    rid = next_id(rows, "RQ")
    rows.append({"id": rid, "owner": mask(a.owner), "item": a.item, "why_needed": a.why, "settles_with": a.settles,
                 "asked_on": str(dt.date.today()), "due_on": a.due or "", "answered_on": "", "answer": "",
                 "exception_id": a.exception or ""})
    write(a.requests, rows, RQ_FIELDS)
    print(f"{rid} for {a.owner}: {a.item}")
    return 0


def cmd_answer(a):
    rows = read(a.requests, RQ_FIELDS)
    r = find(rows, a.id)
    r["answered_on"] = str(dt.date.today())
    r["answer"] = masked(a.verbatim)
    write(a.requests, rows, RQ_FIELDS)
    print(f"{a.id} answered: {r['answer']}")
    return 0


def cmd_requests(a):
    rows = read(a.requests, RQ_FIELDS)
    by_owner = {}
    for r in rows:
        if (a.owner and r["owner"] != a.owner) or (a.open and r["answered_on"]):
            continue
        by_owner.setdefault(r["owner"], []).append(r)
    for owner, items in by_owner.items():
        print(f"{owner}: {len(items)} request(s)")
        for r in items:
            print(f"  {r['id']} {r['item']} | why: {r['why_needed']} | settles with: {r['settles_with']} | due {r['due_on'] or '-'}"
                  + (f" | answered {r['answered_on']}: {r['answer']}" if r["answered_on"] else ""))
    return 0


def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        R, Q = os.path.join(tmp, "exceptions.csv"), os.path.join(tmp, "requests.csv")
        base = dict(register=R, entity="T Ltd", account="main-4411", period="2026-05", cls="bank-detail-change",
                    amount="4960.00", currency="GBP", facts_ref="bills.csv:bill=8812", decision="confirm or hold",
                    owner="Alex", urgency="5 Jun", interim="unapproved", evidence_path="")
        cmd_new(argparse.Namespace(**base))
        cmd_new(argparse.Namespace(**base))
        rows = read(R, EX_FIELDS)
        rows[1]["status"] = "superseded"
        write(R, rows, EX_FIELDS)
        cmd_new(argparse.Namespace(**base))
        assert [r["id"] for r in read(R, EX_FIELDS)] == ["BX-1", "BX-2", "BX-3"]
        try:
            cmd_new(argparse.Namespace(**dict(base, account="acct 12340937")))
        except InputError:
            pass
        else:
            raise AssertionError("unmasked account accepted")
        for leak in ("email: new acct 12340937.", "card 4111 1111 1111 1111, used", "acct 1234-5678-9012"):
            try:
                cmd_new(argparse.Namespace(**dict(base, facts_ref=leak)))
            except InputError:
                pass
            else:
                raise AssertionError(f"unmasked number accepted: {leak}")
        no_long_numbers("bill 8812 for 4,960.00.", "email of 2026-05-28, acct ****0937.",
                        "recs/main-4411-2026-04/workpaper.md", "12,340,937.00")
        cmd_decide(argparse.Namespace(register=R, id="BX-1", by="Alex", verbatim="Hold it"))
        cmd_decide(argparse.Namespace(register=R, id="BX-1", by="Alex", verbatim="Confirmed genuine. Close."), closing=True)
        assert find(read(R, EX_FIELDS), "BX-1")["status"] == "closed_by_owner"
        cmd_request(argparse.Namespace(requests=Q, owner="Jo", item="Amex 12 Apr 86.40", why="no receipt",
                                       settles="receipt", due="2026-05-08", exception="BX-3"))
        cmd_answer(argparse.Namespace(requests=Q, id="RQ-1", verbatim="Uploading now"))
        assert read(Q, RQ_FIELDS)[0]["answer"] == "Uploading now"
        # An owner's decision that quotes the new account number is stored masked,
        # so the register never holds a full number (and build_binder can ship it).
        cmd_new(argparse.Namespace(**base))
        cmd_decide(argparse.Namespace(register=R, id="BX-4", by="Alex",
                                      verbatim="Kestrel confirmed on the old number that 12340937 is not theirs. Hold."))
        got = find(read(R, EX_FIELDS), "BX-4")["decision_verbatim"]
        assert "12340937" not in got and "****0937" in got and got.endswith(MASK_NOTE), got
        cmd_answer(argparse.Namespace(requests=Q, id="RQ-1", verbatim="Paid from card 4111 1111 1111 1111 on 2026-05-02"))
        got = read(Q, RQ_FIELDS)[0]["answer"]
        assert "4111 1111" not in got and "****1111" in got and "2026-05-02" in got, got
        assert masked("Hold it until I call.") == "Hold it until I call."
    print("selftest ok")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--selftest", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    n = sub.add_parser("new")
    n.add_argument("--register", required=True)
    for k in ("entity", "account", "period", "amount", "currency", "owner", "urgency"):
        n.add_argument(f"--{k}", required=True)
    n.add_argument("--class", dest="cls", required=True)
    n.add_argument("--facts-ref", required=True)
    n.add_argument("--decision", required=True, help="the one decision requested")
    n.add_argument("--interim", required=True, help="the safe interim state")
    n.add_argument("--evidence-path")
    for name in ("decide", "close"):
        d = sub.add_parser(name)
        d.add_argument("--register", required=True)
        d.add_argument("--id", required=True)
        d.add_argument("--by", required=True, help="the decider as the user stated it")
        d.add_argument("--verbatim", required=True)
    ls = sub.add_parser("list")
    ls.add_argument("--register", required=True)
    ls.add_argument("--status", choices=STATUSES)
    rq = sub.add_parser("request")
    rq.add_argument("--requests", required=True)
    rq.add_argument("--owner", required=True)
    rq.add_argument("--item", required=True)
    rq.add_argument("--why", required=True)
    rq.add_argument("--settles", required=True, help="the document that would settle it")
    rq.add_argument("--due")
    rq.add_argument("--exception")
    an = sub.add_parser("answer")
    an.add_argument("--requests", required=True)
    an.add_argument("--id", required=True)
    an.add_argument("--verbatim", required=True)
    rl = sub.add_parser("requests")
    rl.add_argument("--requests", required=True)
    rl.add_argument("--owner")
    rl.add_argument("--open", action="store_true")
    a = p.parse_args()
    try:
        if a.selftest:
            return selftest()
        handler = {"new": cmd_new, "decide": cmd_decide, "close": lambda x: cmd_decide(x, closing=True),
                   "list": cmd_list, "request": cmd_request, "answer": cmd_answer, "requests": cmd_requests}.get(a.cmd)
        if handler:
            return handler(a)
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
