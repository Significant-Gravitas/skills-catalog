#!/usr/bin/env python3
"""Hash an artefact before it is shown, and log the owner's reply against that hash.

Python 3 standard library only. Never edits the artefact, never sends anything.

    # 1. Before asking: print the SHA-256 of exactly what the owner will see.
    python3 scripts/log_approval.py hash /home/user/out/rec/main-4411-2026-04/report.md

    # 2. After the owner answers: append one row to approvals.csv.
    python3 scripts/log_approval.py record \
        --approvals ~/workspace/bookkeeping/<entity>/approvals.csv \
        --artefact /home/user/out/rec/main-4411-2026-04/report.md \
        --expect-sha <sha printed in step 1> \
        --action "sign off main-4411 2026-04 reconciliation" \
        --approver "Jo (as stated in chat)" \
        --reply "Signed off"

    # 3. Later: is this exact file approved?
    python3 scripts/log_approval.py check --approvals <csv> --artefact <file>

Aliases, so the kit's other copies of this script read the same way:
--log = --approvals, --shown-sha = --expect-sha, verify = check. The CSV
columns are identical across the kit.

Exit codes: 0 ok; 2 bad input or the artefact changed since it was shown
(show it again and re-ask); 3 `check` found no approval for this exact file.
"""

import argparse
import csv
import datetime as dt
import hashlib
import os
import sys
import tempfile

FIELDS = [
    "timestamp",
    "artefact_path",
    "artefact_sha256",
    "action",
    "approver_as_stated",
    "verbatim_reply",
]
# Replies that count as approval of the exact file shown. "Reviewed" counts as a
# recorded review (for example of a reconciliation that is still open); the
# artefact's own status field still says whether it is reconciled or final.
# Anything else ("Not yet", questions) is logged as a reply only.
APPROVING_PREFIXES = ("approve", "approved", "signed off", "sign off", "yes", "reviewed")


def fail(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(2)


def sha256(path: str) -> str:
    if not os.path.isfile(path):
        fail(f"artefact not found: {path}. Write the file first, then hash it.")
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def is_approval(reply: str) -> bool:
    return reply.strip().lower().startswith(APPROVING_PREFIXES)


def cmd_hash(args) -> int:
    print(sha256(args.artefact))
    return 0


def cmd_record(args) -> int:
    actual = sha256(args.artefact)
    if args.expect_sha and args.expect_sha != actual:
        fail(
            "the artefact changed after it was shown to the owner "
            f"(shown {args.expect_sha[:12]}..., now {actual[:12]}...). "
            "Show the current file again and ask again; an approval covers one exact file."
        )
    if not args.reply.strip():
        fail("--reply is empty. Record the owner's words verbatim.")
    new = not os.path.exists(args.approvals)
    os.makedirs(os.path.dirname(os.path.abspath(args.approvals)), exist_ok=True)
    with open(args.approvals, "a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(
            {
                "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                "artefact_path": args.artefact,
                "artefact_sha256": actual,
                "action": args.action,
                "approver_as_stated": args.approver,
                "verbatim_reply": args.reply,
            }
        )
    verdict = "APPROVAL" if is_approval(args.reply) else "NOT AN APPROVAL (logged as a reply only)"
    print(f"logged {verdict}: {args.action} sha256={actual}")
    return 0


def cmd_check(args) -> int:
    actual = sha256(args.artefact)
    if not os.path.exists(args.approvals):
        print(f"NOT APPROVED: {args.approvals} does not exist")
        return 3
    with open(args.approvals, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row.get("artefact_sha256") == actual and is_approval(row.get("verbatim_reply", "")):
                print(f"APPROVED {row['timestamp']} by {row['approver_as_stated']}: {row['action']}")
                return 0
    print("NOT APPROVED: no approving row carries this file's SHA-256 (it may have been edited since)")
    return 3


def selftest() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        art = os.path.join(tmp, "a.md")
        with open(art, "w", encoding="utf-8") as fh:
            fh.write("report v1\n")
        appr = os.path.join(tmp, "state", "approvals.csv")
        s1 = sha256(art)
        ns = argparse.Namespace(approvals=appr, artefact=art, expect_sha=s1,
                                action="test", approver="Jo", reply="Signed off")
        assert cmd_record(ns) == 0
        assert cmd_check(argparse.Namespace(approvals=appr, artefact=art)) == 0
        with open(art, "a", encoding="utf-8") as fh:
            fh.write("edited\n")
        assert cmd_check(argparse.Namespace(approvals=appr, artefact=art)) == 3
        try:
            cmd_record(ns)  # stale expect-sha must be refused
        except SystemExit as exc:
            assert exc.code == 2
        else:
            raise AssertionError("stale hash accepted")
    print("selftest ok")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--selftest", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    h = sub.add_parser("hash")
    h.add_argument("artefact")
    r = sub.add_parser("record")
    r.add_argument("--approvals", "--log", dest="approvals", required=True)
    r.add_argument("--artefact", required=True)
    r.add_argument("--expect-sha", "--shown-sha", dest="expect_sha", default="")
    r.add_argument("--action", required=True)
    r.add_argument("--approver", required=True, help="the approver as the user stated it; never inferred")
    r.add_argument("--reply", required=True, help="the owner's reply, verbatim")
    c = sub.add_parser("check", aliases=["verify"])
    c.add_argument("--approvals", "--log", dest="approvals", required=True)
    c.add_argument("--artefact", required=True)
    args = p.parse_args()
    if args.selftest:
        return selftest()
    if args.cmd == "hash":
        return cmd_hash(args)
    if args.cmd == "record":
        return cmd_record(args)
    if args.cmd in ("check", "verify"):
        return cmd_check(args)
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
