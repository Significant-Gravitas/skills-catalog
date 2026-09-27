#!/usr/bin/env python3
"""Collect one entity's month-end files into a review binder (zip + index + SHA-256 manifest).

Python 3 standard library only. Reads the state root, writes one zip. Never sends it.

    cd ~/skills/month-end-close-checklist && python3 scripts/build_binder.py \
        --state-root ~/workspace/bookkeeping/<entity-slug> --period 2026-04 \
        --out /home/user/out/<entity-slug>-2026-04-close-binder.zip

Included when present (paths relative to the state root):
  close/<period>/*                 status.csv, report.md
  recs/*-<period>.json, recs/*-<period>/workpaper.md and its CSVs
  pl/<period>.csv, pl/<period>-brief.md
  expenses/<period>-review.csv
  open-items.csv, exceptions.csv, requests.csv, approvals.csv, filtered to rows
  for this period or still open (--all-registers keeps every row), minus any
  exception named with --exclude-exception (repeatable) and its requests
Refuses (exit 2): a path outside the state root, a symlink, or any text file
holding 8 or more digits, alone or grouped by spaces or dashes, with or without
trailing punctuation (an unmasked account or card number). The refusal names
each file and the skill that wrote it: re-run that skill (its outputs mask long
numbers) and rebuild. Never hand-edit an approved file: its SHA-256 approval
would no longer match. The binder never masks silently.
"""

import argparse
import csv
import datetime as dt
import io
import glob
import hashlib
import os
import re
import sys
import tempfile
import zipfile

# Same shape as the escalation kit's check: digits optionally grouped by spaces or
# dashes; trailing punctuation does not hide a number; a decimal tail (an amount)
# and a thousands comma do not count.
LONG_NUMBER = re.compile(r"(?<![\d.])(?<!\d,)\d(?:[ -]?\d){7,}(?!\d)(?![.,]\d)")
PERIOD = re.compile(r"(?<!\d)(?:19|20)\d{2}-\d{2}(?!\d)")
CLOSED = {"closed", "closed_by_owner", "superseded"}
TEXT_EXT = {".csv", ".md", ".json", ".txt"}
SHARED = ["open-items.csv", "exceptions.csv", "requests.csv", "approvals.csv"]


class Refused(Exception):
    pass


def collect(root, period):
    pats = [f"close/{period}/*", f"recs/*-{period}.json", f"recs/*-{period}/*", f"pl/{period}.csv",
            f"pl/{period}-brief.md", f"expenses/{period}-review.csv"] + SHARED
    files = []
    real_root = os.path.realpath(root)
    for pat in pats:
        for path in sorted(glob.glob(os.path.join(root, pat))):
            if not os.path.isfile(path):
                continue
            if os.path.islink(path):
                raise Refused(f"{path} is a symlink; copy the real file into the state root")
            if not os.path.realpath(path).startswith(real_root + os.sep):
                raise Refused(f"{path} is outside the state root")
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            if rel not in [f[0] for f in files]:
                files.append((rel, path))
    return files


def next_month(period):
    y, m = int(period[:4]), int(period[5:])
    return f"{y + (m == 12)}-{1 if m == 12 else m + 1:02d}"


def keep_row(name, r, period, excluded):
    """Rows of a shared register that belong in this period's binder."""
    if name == "exceptions.csv":
        if r.get("id") in excluded:
            return False
        return r.get("period") == period or r.get("status", "").lower() not in CLOSED
    if name == "open-items.csv":
        return r.get("period") == period or r.get("status", "").lower() == "open"
    if name == "requests.csv":
        if r.get("exception_id") in excluded:
            return False
        return not r.get("answered_on") or period in (r.get("asked_on", "")[:7], r.get("answered_on", "")[:7])
    if name == "approvals.csv":
        return period in r.get("artefact_path", "") or r.get("timestamp", "")[:7] in (period, next_month(period))
    return True


def filtered(path, period, excluded):
    """Return the register's bytes, cut to this period and still-open rows."""
    name = os.path.basename(path)
    with open(path, newline="", encoding="utf-8") as fh:
        rd = csv.DictReader(fh)
        fields = rd.fieldnames or []
        rows = [r for r in rd if keep_row(name, r, period, excluded)]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


def producer(rel):
    """The kit skill that writes a state file, so a refusal can say what to re-run."""
    rel = rel.replace("\\", "/")
    for prefix, skill in (("recs/", "statement-reconciliation"), ("pl/", "monthly-profit-and-loss-summary"),
                          ("expenses/", "expense-categorization"), ("close/", "month-end-close-checklist"),
                          ("exceptions.csv", "bookkeeping-exception-escalation"),
                          ("requests.csv", "bookkeeping-exception-escalation")):
        if rel.startswith(prefix):
            return skill
    return "the skill that wrote it"


def scan_text(rel, text):
    hits = []
    for n, line in enumerate(text.splitlines(), start=1):
        # ISO timestamps, periods (YYYY-MM) and hashes are not account numbers
        cleaned = re.sub(r"\b[0-9a-f]{64}\b", "", line)
        cleaned = re.sub(r"\d{4}-\d{2}-\d{2}(T[\d:+.]+)?", "", cleaned)
        cleaned = PERIOD.sub("", cleaned)
        if LONG_NUMBER.search(cleaned):
            hits.append(f"{rel} line {n}")
    return hits


def scan(files):
    hits = []
    for rel, path in files:
        if os.path.splitext(path)[1].lower() not in TEXT_EXT:
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            hits += scan_text(rel, fh.read())
    return hits


def describe(rel):
    table = [("close/", "close status and report"), ("recs/", "reconciliation"), ("pl/", "P&L draft"),
             ("expenses/", "expense review table"), ("open-items", "open items register"),
             ("exceptions", "exception register"), ("requests", "missing-document requests"),
             ("approvals", "approval log (who approved which file, by SHA-256)")]
    for k, v in table:
        if rel.startswith(k):
            return v
    return "supporting file"


def build(root, period, out, excluded=(), all_registers=False):
    if not re.fullmatch(r"\d{4}-\d{2}", period):
        raise Refused("--period must be YYYY-MM")
    if not os.path.isdir(root):
        raise Refused(f"state root not found: {root}")
    files = collect(root, period)
    if not files:
        raise Refused(f"no files for {period} under {root}; run the close first")
    excluded = set(excluded)
    payload = {}
    for rel, path in files:
        if rel in SHARED and not all_registers:
            payload[rel] = filtered(path, period, excluded)
        else:
            with open(path, "rb") as fh:
                payload[rel] = fh.read()
    hits = []
    for rel, _ in files:
        if os.path.splitext(rel)[1].lower() in TEXT_EXT:
            hits += scan_text(rel, payload[rel].decode("utf-8", errors="replace"))
    if hits:
        files_hit = sorted({h.rsplit(" line ", 1)[0] for h in hits})
        # Working registers are indexes, not approved artefacts: the fix is to mask
        # the field in the row itself. Produced outputs are re-run, never hand-edited.
        registers = [f for f in files_hit if f in ("exceptions.csv", "requests.csv", "open-items.csv")]
        outputs = [f for f in files_hit if f not in registers]
        advice = []
        if registers:
            advice.append("In " + ", ".join(registers) + " (a working register, not an approved artefact), edit the named "
                          "row so the number keeps only its last 4 digits (for example ****0937), note that it was masked, "
                          "and keep every other field as it is; register.py now masks new decisions and answers itself. "
                          "Do not leave an open exception out of the binder to get round this")
        if outputs:
            advice.append("Re-run the skill that produced " + ", ".join(f"{f} ({producer(f)})" for f in outputs)
                          + " so its output is masked. Do not hand-edit an approved file: "
                          "its SHA-256 approval would no longer match")
        raise Refused("unmasked long number(s) found, binder not built: " + "; ".join(hits[:10])
                      + ". " + ". ".join(advice) + ". Then rebuild.")
    manifest, index = [], [f"# Close binder: {os.path.basename(os.path.normpath(root))}, {period}", "",
                           f"Built {dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')} by build_binder.py. "
                           "DRAFT for owner and accountant review; nothing here has been posted.", "",
                           ("Shared registers: every row (--all-registers)." if all_registers else
                            f"Shared registers: rows for {period} or still open only."
                            + (f" {len(excluded)} exception(s) left out at the owner's direction." if excluded else "")), "",
                           "| File | What it is | SHA-256 |", "| --- | --- | --- |"]
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for rel, path in files:
            data = payload[rel]
            h = hashlib.sha256(data).hexdigest()
            manifest.append(f"{h}  {rel}")
            index.append(f"| {rel} | {describe(rel)} | {h[:16]}... |")
            z.writestr(rel, data)
        z.writestr("index.md", "\n".join(index) + "\n")
        z.writestr("manifest.sha256", "\n".join(manifest) + "\n")
    return files


def selftest():
    with tempfile.TemporaryDirectory() as tmp:
        root = os.path.join(tmp, "bramble-design-ltd")
        os.makedirs(os.path.join(root, "close", "2026-04"))
        os.makedirs(os.path.join(root, "close", "2026-03"))
        with open(os.path.join(root, "close", "2026-04", "report.md"), "w") as fh:
            fh.write("April close, main-4411, 2026-05-06T10:00:00+00:00\n")
        with open(os.path.join(root, "close", "2026-03", "report.md"), "w") as fh:
            fh.write("March\n")
        with open(os.path.join(root, "approvals.csv"), "w") as fh:
            fh.write("timestamp,artefact_path,artefact_sha256\n"
                     "2026-05-06T10:00:00+00:00,recs/main-4411-2026-04/workpaper.md," + "a" * 64 + "\n"
                     "2026-02-03T10:00:00+00:00,recs/main-4411-2026-01/workpaper.md," + "b" * 64 + "\n")
        with open(os.path.join(root, "exceptions.csv"), "w") as fh:
            fh.write("id,period,status,owner,amount\nBX-1,2026-02,closed_by_owner,Jo,4,960.00\n"
                     "BX-2,2026-04,open,Jo,120.00\nBX-3,2026-04,open,Sam,95.00\n")
        out = os.path.join(tmp, "b.zip")
        files = build(root, "2026-04", out, excluded=["BX-3"])
        with zipfile.ZipFile(out) as z:
            names = z.namelist()
            ex = z.read("exceptions.csv").decode()
            ap = z.read("approvals.csv").decode()
        assert "close/2026-04/report.md" in names and "close/2026-03/report.md" not in names, names
        assert "index.md" in names and "manifest.sha256" in names
        assert "BX-2" in ex and "BX-1" not in ex and "BX-3" not in ex, ex
        assert "2026-04" in ap and "2026-01" not in ap, ap
        for leak in ("Payee card 4111 1111 1111 1111 used", "new account 12340937.", "acct,12340937,x"):
            assert scan_text("t", leak), leak
        for fine in ("recs/main-4411-2026-04/workpaper.md", "total 4,960.00.", "12,340,937.00", "2026-05-06T10:00:00+00:00"):
            assert not scan_text("t", fine), fine
        with open(os.path.join(root, "close", "2026-04", "report.md"), "a") as fh:
            fh.write("payee account 12340937 sort 401122\n")
        try:
            build(root, "2026-04", out)
        except Refused as exc:
            assert "unmasked" in str(exc)
        else:
            raise AssertionError("unmasked number not refused")
    print("selftest ok")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--state-root")
    p.add_argument("--period")
    p.add_argument("--out")
    p.add_argument("--exclude-exception", action="append", default=[],
                   help="exception id to leave out (with its requests), only at the owner's direction; repeatable")
    p.add_argument("--all-registers", action="store_true", help="include every row of the shared registers")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    if a.selftest:
        return selftest()
    if not (a.state_root and a.period and a.out):
        p.error("--state-root, --period and --out are required")
    try:
        files = build(os.path.expanduser(a.state_root), a.period, a.out, a.exclude_exception, a.all_registers)
    except Refused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {a.out}: {len(files)} files + index.md + manifest.sha256. Not sent: sending needs the owner's yes naming the recipient.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
