#!/usr/bin/env python3
"""Build an exception evidence pack: only the cited rows, only the needed columns, numbers masked.

Python 3 standard library only. Reads source CSVs and your pack.md; writes
packs/<id>/ and a zip. Never edits a source, never sends anything.

    cd ~/skills/bookkeeping-exception-escalation && python3 scripts/build_pack.py \
        --id BX-7 --pack-md /home/user/out/pack-BX-7.md \
        --cite "/home/user/in/bills.csv:bill=8812" --cite "/home/user/in/vendor-master.csv:vendor=Kestrel Timber" \
        --cite "/home/user/in/bank.csv:3" \
        [--keep-columns date,payee,amount,reference,bank_account] \
        --out ~/workspace/bookkeeping/<entity>/packs

    python3 scripts/build_pack.py --selftest

--cite FILE:N takes data row N (1 = first row under the header); FILE:col=value
takes every row where that column equals the value. --keep-columns limits the
columns copied (data minimisation); the columns left out are listed under
"Fields withheld". Masking: runs of 6 or more digits (spaces and dashes allowed
inside) keep only the last 4; IBANs keep country code and last 4; sort codes
become **-**-**. Dates and decimal amounts are not masked. pack.md is refused if
it contains an unmasked number: mask it in the text and run again.
"""

import argparse
import csv
import hashlib
import os
import re
import sys
import tempfile
import zipfile

IBAN = re.compile(r"\b([A-Z]{2})\d{2}[A-Z0-9 ]{11,30}?(\d{4})\b")
SORT_CODE = re.compile(r"\b\d{2}-\d{2}-\d{2}\b")
ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
# 6+ digits, optionally grouped by spaces or dashes ("4111 1111 1111 1111").
# Trailing punctuation is allowed ("account 12340937."); a decimal tail is not,
# so amounts such as 4,960.00 or 125000.00 are left alone.
LONG_DIGITS = re.compile(r"(?<![\d.])(?<!\d,)\d(?:[ -]?\d){5,}(?!\d)(?![.,]\d)")
PERIOD = re.compile(r"(?<!\d)(?:19|20)\d{2}-\d{2}(?!\d)")  # YYYY-MM, as in recs/main-4411-2026-04


def mask(text):
    if not text:
        return text
    dates = {}

    def keep_date(m):
        key = f"\x00{len(dates)}\x00"
        dates[key] = m.group(0)
        return key

    t = ISO_DATE.sub(keep_date, text)
    t = PERIOD.sub(keep_date, t)
    t = IBAN.sub(lambda m: f"{m.group(1)}** **** {m.group(2)}", t)
    t = SORT_CODE.sub("**-**-**", t)
    t = LONG_DIGITS.sub(lambda m: "****" + re.sub(r"\D", "", m.group(0))[-4:], t)
    for k, v in dates.items():
        t = t.replace(k, v)
    return t


def unmasked(text):
    t = ISO_DATE.sub("", text)
    t = PERIOD.sub("", t)
    t = re.sub(r"\*{2,}\d{4}", "", t)
    return bool(LONG_DIGITS.search(t) or IBAN.search(t) or SORT_CODE.search(t))


class InputError(Exception):
    pass


def select(cite):
    path, _, sel = cite.rpartition(":")
    if not path or not sel:
        raise InputError(f"--cite '{cite}' must be FILE:N or FILE:column=value")
    if not os.path.isfile(path):
        raise InputError(f"cited file not found: {path}")
    with open(path, newline="", encoding="utf-8-sig") as fh:
        rd = csv.DictReader(fh)
        rows = [{k.strip(): (v or "").strip() for k, v in r.items() if k} for r in rd]
        header = [h.strip() for h in rd.fieldnames or []]
    if sel.isdigit():
        n = int(sel)
        if not 1 <= n <= len(rows):
            raise InputError(f"{path} has {len(rows)} data rows; row {n} does not exist")
        picked = [(n, rows[n - 1])]
    else:
        col, _, val = sel.partition("=")
        if col not in header:
            raise InputError(f"{path}: no column '{col}'; columns are {header}")
        picked = [(i, r) for i, r in enumerate(rows, 1) if r.get(col) == val]
        if not picked:
            raise InputError(f"{path}: no row where {col} = {val}")
    return os.path.basename(path), header, picked


def build(a):
    if not re.fullmatch(r"BX-\d+", a.id):
        raise InputError("--id must be an exception id like BX-7 from register.py")
    with open(a.pack_md, encoding="utf-8") as fh:
        md = fh.read()
    if unmasked(md):
        raise InputError("pack.md contains an unmasked account, card, IBAN or sort-code number. "
                         "Write only the last 4 digits (e.g. 'ending 0937') and run again.")
    keep = [c.strip() for c in a.keep_columns.split(",")] if a.keep_columns else None
    out_rows, withheld = [], set()
    for cite in a.cite:
        name, header, picked = select(cite)
        cols = [c for c in header if keep is None or c in keep]
        withheld |= {f"{name}:{c}" for c in header if c not in cols}
        for n, r in picked:
            out_rows.append({"source": name, "row": str(n),
                             "fields": "; ".join(f"{c}={mask(r.get(c, ''))}" for c in cols)})
    folder = os.path.join(a.out, a.id)
    os.makedirs(folder, exist_ok=True)
    ev = os.path.join(folder, "evidence.csv")
    with open(ev, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["source", "row", "fields"])
        w.writeheader()
        w.writerows(out_rows)
    note = "\n\n**Fields withheld (not needed for this decision):** " + (", ".join(sorted(withheld)) if withheld else "none") + "\n"
    note += "**Masking:** account, card and IBAN numbers show the last 4 digits only.\n"
    pk = os.path.join(folder, "pack.md")
    with open(pk, "w", encoding="utf-8") as fh:
        fh.write(md.rstrip() + note)
    zpath = os.path.join(a.out, f"{a.id}-pack.zip")
    manifest = []
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for f in (pk, ev):
            data = open(f, "rb").read()
            manifest.append(f"{hashlib.sha256(data).hexdigest()}  {os.path.basename(f)}")
            z.writestr(os.path.basename(f), data)
        z.writestr("manifest.sha256", "\n".join(manifest) + "\n")
    return folder, zpath, len(out_rows), sorted(withheld)


def selftest():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    d = os.path.join(here, "examples", "bank-detail-change")
    assert mask("acct 12340937 sort 40-11-22 on 2026-05-28 for 4,960.00") == "acct ****0937 sort **-**-** on 2026-05-28 for 4,960.00"
    assert mask("GB29NWBK60161331926819") .startswith("GB** **** 6819"), mask("GB29NWBK60161331926819")
    assert mask("gives new account 12340937.") == "gives new account ****0937.", mask("gives new account 12340937.")
    assert mask("card 4111 1111 1111 1111, then") == "card ****1111, then", mask("card 4111 1111 1111 1111, then")
    for text in ("Kestrel email of 28 May gives new account 12340937.", "card 4111 1111 1111 1111, used",
                 "acct 12340937, sort 40-11-22"):
        assert unmasked(text), text
    assert unmasked("acct,12340937,x")
    for text in ("bill 8812 for 4,960.00.", "total 125000.00, due 2026-06-05.", "account ****0937.",
                 "see recs/main-4411-2026-04/workpaper.md"):
        assert not unmasked(text), text
    with tempfile.TemporaryDirectory() as tmp:
        ns = argparse.Namespace(id="BX-7", pack_md=os.path.join(d, "pack-BX-7.md"),
                                cite=[os.path.join(d, "bills.csv") + ":bill=8812", os.path.join(d, "bank.csv") + ":3"],
                                keep_columns="date,bill,payee,amount,due,bank_account,reference,description",
                                out=tmp)
        folder, zpath, n, withheld = build(ns)
        ev = open(os.path.join(folder, "evidence.csv"), encoding="utf-8").read()
        assert n == 2 and "12340937" not in ev and "****0937" in ev, ev
        assert any(w.endswith(":approver_email") for w in withheld), withheld
        bad = os.path.join(tmp, "bad.md")
        with open(bad, "w", encoding="utf-8") as fh:
            fh.write("Kestrel email of 28 May gives new account 12340937.")
        try:
            build(argparse.Namespace(**dict(vars(ns), pack_md=bad)))
        except InputError:
            pass
        else:
            raise AssertionError("unmasked pack.md accepted")
    print("selftest ok")
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--id")
    p.add_argument("--pack-md")
    p.add_argument("--cite", action="append", default=[])
    p.add_argument("--keep-columns")
    p.add_argument("--out")
    p.add_argument("--selftest", action="store_true")
    a = p.parse_args()
    if a.selftest:
        return selftest()
    if not (a.id and a.pack_md and a.cite and a.out):
        p.error("--id, --pack-md, at least one --cite, and --out are required")
    try:
        folder, zpath, n, withheld = build(a)
    except InputError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"pack {a.id}: {n} evidence rows, {len(withheld)} fields withheld -> {folder}/ and {zpath}. "
          "Draft only: sending needs the owner's yes naming the recipient.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
