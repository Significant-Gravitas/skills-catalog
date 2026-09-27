#!/usr/bin/env python3
"""Track month-end control status and enforce the dependency rule.

Python 3 standard library only. Reads templates/close-controls.csv and a period
status file; writes only the status file you name. Never posts, locks or sends.

    cd ~/skills/month-end-close-checklist
    # open the close (optionally carrying last month's still-open controls as notes)
    python3 scripts/close_status.py init --period 2026-04 \
        --out ~/workspace/bookkeeping/<entity>/close/2026-04/status.csv [--prior <last month status.csv>]
    # change one control
    python3 scripts/close_status.py set --status-file <status.csv> --id 1 --status ready_for_review \
        --evidence "main-4411 workpaper, unexplained 0.00" --owner Jo
    # what can start now, what is blocked, is the period prepared for review?
    python3 scripts/close_status.py report --status-file <status.csv> [--todo] [--markdown report-table.md]

Statuses: not_started, in_progress, ready_for_review, approved, blocked, not_applicable.
Rules enforced:
  - ready_for_review needs evidence, and every dependency ready_for_review, approved or not_applicable;
  - approved needs --approval-ref (the approvals.csv timestamp, or several joined by ;),
    --approvals <approvals.csv> and --artefact <file> (repeatable): each timestamp must
    be an approving row, and each artefact needs one whose SHA-256 equals the file now.
    Control 14 needs every <state>/recs/*-<YYYY-MM>/workpaper.md named, so the status
    file must sit at <state>/close/<YYYY-MM>/status.csv; every dependency must be done;
  - blocked needs --blocker; not_applicable needs --reason;
  - moving a control back reopens every downstream control that was ready or approved.
The period is "prepared for review" when every control except the post-approval
ones (15, lock date) is done. The lock follows the owner's and accountant's review,
so it is never asked for before the close report is approved. Nothing here can
mark it closed: the owner closes the period in their own system.
Exit codes: 0 ok; 2 refused or bad input (the message names the blocking control).
"""

import argparse
import csv
import datetime as dt
import glob
import hashlib
import json
import os
import re
import sys
import tempfile

STATUSES = ["not_started", "in_progress", "ready_for_review", "approved", "blocked", "not_applicable"]
DONE = {"ready_for_review", "approved", "not_applicable"}
FIELDS = ["id", "control", "level", "depends_on", "skill_to_load", "status", "evidence", "blocker",
          "owner", "updated_on", "approval_ref", "reason"]
# Controls recorded only after the close report is approved; they do not gate "prepared for review".
POST_APPROVAL = {"15"}
HERE = os.path.dirname(os.path.abspath(__file__))
CONTROLS = os.path.join(os.path.dirname(HERE), "templates", "close-controls.csv")


class Refused(Exception):
    pass


def read(path):
    if not os.path.isfile(path):
        raise Refused(f"file not found: {path}")
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write(path, rows):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, path)


def deps(row):
    return [d for d in (row.get("depends_on") or "").split(";") if d]


def index(rows):
    return {r["id"]: r for r in rows}


def downstream(rows, cid):
    out, frontier = set(), {cid}
    while frontier:
        nxt = {r["id"] for r in rows if set(deps(r)) & frontier} - out
        out |= nxt
        frontier = nxt
    return out


def cmd_init(a):
    if os.path.exists(a.out) and not a.force:
        raise Refused(f"{a.out} exists. Use 'set' to change it, or --force to start over (the old file is kept as .bak).")
    if os.path.exists(a.out):
        os.replace(a.out, a.out + ".bak")
    controls = read(a.controls)
    prior = index(read(a.prior)) if a.prior else {}
    rows = []
    for c in controls:
        r = {k: c.get(k, "") for k in FIELDS}
        r.update(status="not_started", updated_on=str(dt.date.today()))
        p = prior.get(c["id"])
        if p and p["status"] not in DONE:
            r["blocker"] = f"carried from prior period: was {p['status']}" + (f" ({p['blocker']})" if p.get("blocker") else "")
        rows.append(r)
    write(a.out, rows)
    print(f"opened close {a.period}: {len(rows)} controls in {a.out}")
    carried = [r for r in rows if r["blocker"].startswith("carried")]
    for r in carried:
        print(f"  carried: {r['id']} {r['control']} - {r['blocker']}")
    return 0


def file_sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def rec_workpapers(status_file):
    """Every reconciliation workpaper of the period, found from <state>/close/<YYYY-MM>/status.csv."""
    close_dir = os.path.dirname(os.path.abspath(status_file))
    period = os.path.basename(close_dir)
    state = os.path.dirname(os.path.dirname(close_dir))
    if not re.fullmatch(r"\d{4}-\d{2}", period) or os.path.basename(os.path.dirname(close_dir)) != "close":
        raise Refused("control 14 needs the status file at <state>/close/<YYYY-MM>/status.csv so every "
                      "reconciliation workpaper of the period can be found.")
    found = sorted(glob.glob(os.path.join(state, "recs", f"*-{period}", "workpaper.md")))
    if not found:
        raise Refused(f"control 14: no workpaper under {os.path.join(state, 'recs', '*-' + period)}/. "
                      "Store each reconciliation (statement-reconciliation step 11) first.")
    return found


def check_approval(path, refs, artefacts, cid, status_file):
    """Each named artefact needs an approving row, among the given timestamps, whose
    logged SHA-256 equals the file as it is now. Control 14 needs every workpaper."""
    if not path:
        raise Refused("approved needs --approvals <state>/approvals.csv so the reference can be checked.")
    if not os.path.isfile(path):
        raise Refused(f"approvals file not found: {path}")
    if not artefacts:
        raise Refused("approved needs --artefact <file> for each approved file (for example the workpaper or brief), "
                      "so the approval is checked against that exact file.")
    sys.dont_write_bytecode = True  # keep the package free of __pycache__
    sys.path.insert(0, HERE)
    from log_approval import is_approval  # same rule the approval log uses
    refs = [x.strip() for x in refs.split(";") if x.strip()]
    with open(path, newline="", encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r.get("timestamp") in refs]
    for ref in refs:
        mine = [r for r in rows if r.get("timestamp") == ref]
        if not mine:
            raise Refused(f"no row in {os.path.basename(path)} has timestamp {ref}. Record the reply with log_approval.py record first.")
        if not any(is_approval(r.get("verbatim_reply", "")) for r in mine):
            raise Refused(f"the approvals.csv row {ref} is not an approval (reply: {mine[0].get('verbatim_reply', '')!r}).")
    for art in artefacts:
        if not os.path.isfile(art):
            raise Refused(f"artefact not found: {art}")
    if cid == "14":
        have = {os.path.realpath(x) for x in artefacts}
        missing = [w for w in rec_workpapers(status_file) if os.path.realpath(w) not in have]
        if missing:
            raise Refused("control 14 needs an approval for every reconciliation workpaper of the period; not named: "
                          + ", ".join(missing))
    for art in artefacts:
        sha = file_sha(art)
        if not any(r.get("artefact_sha256") == sha and is_approval(r.get("verbatim_reply", "")) for r in rows):
            raise Refused(f"{art}: none of the approvals {', '.join(refs)} was given for this exact file (SHA-256 {sha[:12]}...). "
                          "It changed since it was shown, or the approval is for another artefact. Show it again and re-ask.")


def cmd_set(a):
    rows = read(a.status_file)
    by = index(rows)
    if a.id not in by:
        raise Refused(f"no control '{a.id}'. Ids: {', '.join(by)}")
    if a.status not in STATUSES:
        raise Refused(f"status must be one of {STATUSES}")
    r = by[a.id]
    if a.id == "14" and a.status == "ready_for_review":
        # Control 14 is the owner's sign-off itself: it is done only when approvals.csv
        # proves it (approved, with the artefact check), never on free-text evidence.
        raise Refused("control 14 cannot be ready_for_review: owner sign-off is either recorded or not. Use approved "
                      "with --approval-ref, --approvals and an --artefact per rec workpaper, or blocked / not_applicable.")
    open_deps = [d for d in deps(r) if by.get(d, {}).get("status") not in DONE]
    if a.status in ("ready_for_review", "approved"):
        if open_deps:
            names = "; ".join(f"{d} {by[d]['control']} ({by[d]['status']})" for d in open_deps if d in by)
            raise Refused(f"control {a.id} cannot be {a.status}: it depends on {names}. Finish or block those first; do not work around them.")
        if not (a.evidence or r["evidence"]):
            raise Refused(f"control {a.id}: {a.status} needs --evidence (what was checked, and the file or workpaper).")
    if a.status == "approved":
        if not a.approval_ref:
            raise Refused("approved needs --approval-ref: the approvals.csv timestamp of the owner's or accountant's reply.")
        check_approval(getattr(a, "approvals", None), a.approval_ref, getattr(a, "artefact", None) or [], a.id, a.status_file)
    if a.status == "blocked" and not (a.blocker or r["blocker"]):
        raise Refused("blocked needs --blocker (what is missing, who owes it, expected date).")
    if a.status == "not_applicable" and not a.reason:
        raise Refused("not_applicable needs --reason (for example: no payroll this entity).")
    was_done = r["status"] in DONE
    r["status"] = a.status
    for k in ("evidence", "blocker", "owner", "reason"):
        v = getattr(a, k)
        if v is not None:
            r[k] = v
    if a.status == "approved":
        r["approval_ref"] = a.approval_ref
    else:
        r["approval_ref"] = ""  # a row that leaves approved no longer carries an approval
    if a.status in DONE and a.blocker is None:
        r["blocker"] = ""
    r["updated_on"] = str(dt.date.today())
    reopened = []
    if was_done and a.status not in DONE:
        for d in downstream(rows, a.id):
            if by[d]["status"] in ("ready_for_review", "approved"):
                by[d]["status"] = "in_progress"
                by[d]["blocker"] = f"dependency {a.id} reopened on {r['updated_on']}"
                by[d]["approval_ref"] = ""
                reopened.append(d)
    write(a.status_file, rows)
    print(f"{a.id} -> {a.status}")
    if reopened:
        print(f"  reopened downstream: {', '.join(reopened)} (their review must be redone)")
    return 0


def critical_path(rows):
    by = index(rows)
    memo = {}

    def longest(cid):
        if cid in memo:
            return memo[cid]
        r = by[cid]
        if r["status"] in DONE:
            memo[cid] = []
            return []
        best = []
        for d in deps(r):
            if d in by:
                p = longest(d)
                if len(p) > len(best):
                    best = p
        memo[cid] = best + [cid]
        return memo[cid]

    paths = [longest(r["id"]) for r in rows]
    return max(paths, key=len) if paths else []


def is_done(r):
    # Control 14 counts only when approved (or not applicable): an older status file
    # that holds 14 at ready_for_review has no recorded sign-off behind it.
    if r.get("id") == "14" and r.get("status") == "ready_for_review":
        return False
    return r.get("status") in DONE


def summarise(rows):
    by = index(rows)
    eligible, waiting, blocked = [], [], []
    for r in rows:
        if is_done(r):
            continue
        open_deps = [d for d in deps(r) if not is_done(by.get(d, {}))]
        if r["status"] == "blocked":
            blocked.append(r)
        elif open_deps:
            waiting.append((r, open_deps))
        else:
            eligible.append(r)
    not_done = [r for r in rows if not is_done(r) and r["id"] not in POST_APPROVAL]
    post_open = [r["id"] for r in rows if not is_done(r) and r["id"] in POST_APPROVAL]
    if not_done:
        state = f"not prepared for review ({len(not_done)} controls open)"
    elif post_open:
        state = ("prepared for review (after the close report is approved, record the lock date "
                 f"as the owner states it: control {', '.join(post_open)})")
    else:
        state = "prepared for review; lock date recorded"
    return {"state": state, "eligible": eligible, "waiting": waiting, "blocked": blocked,
            "critical_path": critical_path(rows), "counts": {s: sum(r["status"] == s for r in rows) for s in STATUSES}}


def cmd_report(a):
    rows = read(a.status_file)
    s = summarise(rows)
    by = index(rows)
    print(f"Period state: {s['state']}")
    print("Counts: " + ", ".join(f"{k} {v}" for k, v in s["counts"].items() if v))
    print("Can start or continue now:")
    for r in s["eligible"]:
        print(f"  {r['id']} {r['control']} [{r['status']}]" + (f" -> load skill:{r['skill_to_load']}" if r["skill_to_load"] else ""))
    print("Blocked:")
    for r in s["blocked"]:
        print(f"  {r['id']} {r['control']}: {r['blocker']}")
    print("Waiting on dependencies:")
    for r, od in s["waiting"]:
        print(f"  {r['id']} {r['control']} <- {', '.join(od)}")
    if s["critical_path"]:
        print("Critical path (longest open chain): " + " -> ".join(f"{c} {by[c]['control'][:40]}" for c in s["critical_path"]))
    if a.markdown:
        lines = ["| # | Control | Status | Evidence / blocker | Owner |", "| --- | --- | --- | --- | --- |"]
        for r in sorted(rows, key=lambda r: (int(r["level"]), r["id"])):
            eb = r["blocker"] if r["status"] in ("blocked",) or (r["blocker"] and r["status"] not in DONE) else r["evidence"] or r["reason"]
            lines.append(f"| {r['id']} | {r['control']} | {r['status'].replace('_', ' ')} | {eb} | {r['owner']} |")
        lines += ["", f"Period state: **{s['state']}** (from close_status.py)."]
        with open(a.markdown, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print(f"wrote {a.markdown}")
    if a.todo:
        # TodoWrite shows one item in progress at a time: the first in_progress control.
        todo, active = [], False
        for r in sorted(rows, key=lambda r: (int(r["level"]), r["id"])):
            if r["status"] in DONE:
                st = "completed"
            elif r["status"] == "in_progress" and not active:
                st, active = "in_progress", True
            else:
                st = "pending"
            note = f" (blocked: {r['blocker']})" if r["status"] == "blocked" else ""
            todo.append({"content": f"{r['id']} {r['control']}{note}", "status": st})
        print("TODO_JSON " + json.dumps(todo))
    return 0


def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        st = os.path.join(tmp, "close", "2026-04", "status.csv")
        cmd_init(argparse.Namespace(out=st, controls=CONTROLS, prior=None, period="2026-04", force=False))
        S = lambda i, s, **k: cmd_set(argparse.Namespace(status_file=st, id=i, status=s, evidence=k.get("e"),
                                                          blocker=k.get("b"), owner=k.get("o"), reason=k.get("r"),
                                                          approval_ref=k.get("ref"), approvals=k.get("ap"),
                                                          artefact=k.get("art")))
        wp = {}
        for acct in ("main-4411", "amex-1009"):
            os.makedirs(os.path.join(tmp, "recs", f"{acct}-2026-04"))
            wp[acct] = os.path.join(tmp, "recs", f"{acct}-2026-04", "workpaper.md")
            with open(wp[acct], "w", encoding="utf-8") as fh:
                fh.write(f"# workpaper {acct}\n")
        brief = os.path.join(tmp, "brief.md")
        with open(brief, "w", encoding="utf-8") as fh:
            fh.write("# P&L brief\n")
        sha = {k: file_sha(v) for k, v in dict(wp, brief=brief).items()}
        def refused(fn):
            try:
                fn()
            except Refused:
                return True
            return False
        assert refused(lambda: S("1", "ready_for_review", e="rec")), "rec ready before statements received"
        S("S1", "ready_for_review", e="Main and Amex statements")
        S("1", "ready_for_review", e="main-4411 0.00; amex-1009 0.00")
        assert refused(lambda: S("14", "approved", e="x")), "approved without approval ref"
        assert refused(lambda: S("14", "ready_for_review", e="owner said ok")), "control 14 done without an approval"
        legacy = [dict(r, status="ready_for_review") if r["id"] == "14" else dict(r, status="approved") for r in read(st)]
        assert summarise(legacy)["state"].startswith("not prepared"), "legacy 14 ready_for_review counted as signed off"
        ap = os.path.join(tmp, "approvals.csv")
        with open(ap, "w", newline="", encoding="utf-8") as fh:
            fh.write("timestamp,artefact_path,artefact_sha256,action,approver_as_stated,verbatim_reply\n"
                     f"2026-05-04T10:00:00+00:00,recs/main-4411-2026-04/workpaper.md,{sha['main-4411']},sign off rec,Jo,Signed off\n"
                     f"2026-05-04T11:00:00+00:00,recs/amex-1009-2026-04/workpaper.md,{sha['amex-1009']},sign off rec,Jo,Not yet: I have questions\n"
                     f"2026-05-04T12:00:00+00:00,pl/2026-04-brief.md,{sha['brief']},approve P&L brief,Jo,Approved\n"
                     f"2026-05-04T13:00:00+00:00,recs/amex-1009-2026-04/workpaper.md,{sha['amex-1009']},sign off rec,Jo,Signed off\n")
        both = [wp["main-4411"], wp["amex-1009"]]
        assert refused(lambda: S("14", "approved", e="x", ref="whatever", ap=ap, art=both)), "made-up approval ref accepted"
        assert refused(lambda: S("14", "approved", e="x", ref="2026-05-04T11:00:00+00:00", ap=ap, art=both)), "non-approval accepted"
        assert refused(lambda: S("14", "approved", e="x", ref="2026-05-04T10:00:00+00:00", art=both)), "approval not checked"
        assert refused(lambda: S("14", "approved", e="x", ref="2026-05-04T10:00:00+00:00", ap=ap)), "approval without artefact"
        assert refused(lambda: S("14", "approved", e="x", ref="2026-05-04T10:00:00+00:00", ap=ap, art=[wp["main-4411"]])), \
            "control 14 approved with one of two workpapers"
        assert refused(lambda: S("14", "approved", e="x", ref="2026-05-04T10:00:00+00:00;2026-05-04T12:00:00+00:00", ap=ap, art=both)), \
            "a P&L-brief approval accepted for a reconciliation workpaper"
        with open(wp["amex-1009"], "a", encoding="utf-8") as fh:
            fh.write("edited after sign-off\n")
        assert refused(lambda: S("14", "approved", e="x", ref="2026-05-04T10:00:00+00:00;2026-05-04T13:00:00+00:00", ap=ap, art=both)), \
            "workpaper changed after approval accepted"
        with open(wp["amex-1009"], "w", encoding="utf-8") as fh:
            fh.write("# workpaper amex-1009\n")
        S("14", "approved", e="approvals.csv", ref="2026-05-04T10:00:00+00:00;2026-05-04T13:00:00+00:00", ap=ap, art=both)
        S("S1", "blocked", b="Amex statement reissued by the bank")
        rows = index(read(st))
        assert rows["1"]["status"] == "in_progress" and rows["14"]["status"] == "in_progress", "downstream not reopened"
        S("S1", "ready_for_review", e="Amex statement reissued and received")
        S("1", "ready_for_review", e="main-4411 0.00; amex-1009 0.00")
        S("14", "approved", e="approvals.csv", ref="2026-05-04T10:00:00+00:00;2026-05-04T13:00:00+00:00", ap=ap, art=both)
        S("14", "blocked", b="owner withdrew the Amex sign-off")
        assert index(read(st))["14"]["approval_ref"] == "", "approval_ref kept after leaving approved"
        S("S1", "blocked", b="Amex statement reissued by the bank")
        assert rows["14"]["approval_ref"] == ""
        assert refused(lambda: S("8", "ready_for_review", e="draft P&L")), "P&L ready while rec open"
        assert summarise(read(st))["state"].startswith("not prepared")
        # fixture: the worked example's status file must report the expected blockers
        fx = os.path.join(os.path.dirname(HERE), "examples", "close-2026-04", "status.csv")
        s = summarise(read(fx))
        assert s["state"].startswith("not prepared"), s["state"]
        assert {r["id"] for r in s["blocked"]} == {"S4", "S1"}, [r["id"] for r in s["blocked"]]
        # the lock date (15) never gates "prepared for review"
        done = [dict(r, status="not_started") if r["id"] == "15" else dict(r, status="approved") if r["id"] == "14"
                else dict(r, status="ready_for_review") for r in read(st)]
        assert summarise(done)["state"].startswith("prepared for review (after"), summarise(done)["state"]
    print("selftest ok")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--selftest", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    i = sub.add_parser("init")
    i.add_argument("--period", required=True)
    i.add_argument("--out", required=True)
    i.add_argument("--controls", default=CONTROLS)
    i.add_argument("--prior")
    i.add_argument("--force", action="store_true")
    s = sub.add_parser("set")
    s.add_argument("--status-file", required=True)
    s.add_argument("--id", required=True)
    s.add_argument("--status", required=True)
    for k in ("evidence", "blocker", "owner", "reason", "approval-ref"):
        s.add_argument(f"--{k}")
    s.add_argument("--approvals", help="approvals.csv; required with --status approved")
    s.add_argument("--artefact", action="append", help="approved file; repeat per file (control 14: every rec workpaper)")
    r = sub.add_parser("report")
    r.add_argument("--status-file", required=True)
    r.add_argument("--markdown")
    r.add_argument("--todo", action="store_true")
    a = p.parse_args()
    try:
        if a.selftest:
            return selftest()
        if a.cmd == "init":
            return cmd_init(a)
        if a.cmd == "set":
            return cmd_set(a)
        if a.cmd == "report":
            return cmd_report(a)
    except Refused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
