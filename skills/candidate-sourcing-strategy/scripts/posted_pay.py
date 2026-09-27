#!/usr/bin/env python3
"""Extract pay ranges printed in saved job postings. Never estimates.

Usage (cd ~/skills/candidate-sourcing-strategy first):
    python3 scripts/posted_pay.py <posting1.txt> [<posting2.txt> ...] [--csv]

Input:  text files you saved from web_fetch results, one posting per file.
        First lines may carry metadata the script copies to the output:
          url: <posting url>
          company: <company as printed>
          title: <job title as printed>
Forms read: currency before the numbers ("$150,000 - $185,000", "EUR 95.000-110.000",
        "£45k to £55k"), currency after them ("60 000 € – 75 000 €",
        "150,000 to 185,000 USD per year"), and per-unit suffixes on each bound
        ("$40/hr - $55/hr").
Skipped: figures in funding or company-size context ("Raised $20 - 30 million",
        "$5-10M ARR", "valuation", "revenue"); each skip is printed as
        "skipped (not pay): <text>" so you can check it.
        A 3-letter code also works before unseparated digits ("USD 140000-160000").
        Also read: a "k" on the upper bound only ("$120-150K", "140-170k USD"):
        the lower bound is multiplied too and `check` says "k applied to both
        bounds"; an apostrophe thousands separator ("CHF 120'000 - 140'000");
        a decimal comma after dot thousands ("EUR 95.000,00 - 110.000,00");
        and the yen/yuan sign ("¥8,000,000 - ¥11,000,000", currency "¥ (JPY or CNY)").
        A funding figure in an earlier sentence ("We raised $40M Series B.
        Salary $140k-$170k.") no longer hides the salary after it.
Output: a markdown table (or CSV with --csv): url, company, title, min, max,
        currency, period, kind, check, and the exact matched text. `kind` is
        "OTE/variable (<word>)" when OTE, commission, bonus, equity or total
        comp is named just before or after the range, else "base?" (read the
        matched text to confirm). Never mix OTE rows with base rows in one read. `check` says
        "CHECK: implausible for <period>" when a bound is below a floor
        (hour < 5, month < 100, year < 1000, or no period and < 1000); such a
        row is a lead, not a fact, until you read the posting. Postings where no
        range parsed are listed as "no range parsed - read the posting" (a single
        figure, or a form this script does not read, may still be there).
        The summary gives n only. No average, median or band is computed, on
        purpose: a handful of postings is a small, non-random sample, and the
        persona never estimates a band.
This is a reader's aid, not the fact check: read the matched text of every row
and drop any that is not pay before the table is shown.
Exit:   0 at least one file read; 2 no readable input.
Stdlib only, no network (fetch with web_fetch first, then save the text).
"""

import csv
import re
import sys
from pathlib import Path

CODES = r"USD|EUR|GBP|CAD|AUD|CHF|SEK|NOK|DKK|PLN|CZK|HUF|RON|INR|SGD|JPY"
CUR = r"(?:US\$|CA\$|A\$|\$|€|£|¥|" + CODES + r")"
# "140000", "140,000", "120'000", "95.000,00"
NUM = r"(?:\d{4,7}|\d{1,3}(?:[,.   '’]\d{3})*)(?:\.\d+|,\d{2}(?!\d))?\s?[kK]?(?![\w])"
UNIT = r"(?:\s*(?:/|per\s+|an\s+|a\s+)\s*(?:year|yr|annum|hour|hr|h|month|mo)\b|\s*(?:annually|yearly|hourly|monthly|p\.?a\.?|jährlich)\b)"
SEP = r"\s*(?:-|–|—|to|bis|à)\s*"

# Currency before each number: "$40/hr - $55/hr", "£45k to £55k", "USD 120,000-140,000 annually".
PREFIX = re.compile(
    r"(?P<cur>" + CUR + r")\s?(?P<lo>" + NUM + r")(?P<u1>" + UNIT + r")?" + SEP
    + r"(?:" + CUR + r"\s?)?(?P<hi>" + NUM + r")(?:\s*(?P<cur3>" + CODES + r")\b)?(?P<u2>" + UNIT + r")?",
    re.I,
)
# Currency after the numbers: "60 000 € – 75 000 €", "150,000 to 185,000 USD per year".
SUFFIX = re.compile(
    r"(?<![\w$€£])(?P<lo>" + NUM + r")\s?(?:" + CUR + r")?(?P<u1>" + UNIT + r")?" + SEP
    + r"(?P<hi>" + NUM + r")\s?(?P<cur>" + CUR + r")(?![\w])(?P<u2>" + UNIT + r")?",
    re.I,
)
FUNDING_AFTER = re.compile(r"^\s*(?:million|billion|mn|mm|m|bn|b)\b|^\s*(?:in )?(?:series|seed|funding|arr|revenue|valuation)", re.I)
FUNDING_BEFORE = re.compile(r"(raised|raising|funding|funded|valuation|valued|revenue|arr|series [a-e]|investment|round)\W*(\w+\W+){0,4}$", re.I)
# Words that mark a range as OTE/variable pay, not base. Before the range any of
# them counts; after it only an OTE/total-comp label does ("... plus equity" is base).
VARIABLE_BEFORE = re.compile(r"\b(OTE|on[- ]target|commission\w*|bonus\w*|variable|incentive|equity|stock|RSUs?|total comp\w*|TC)\W*(\w+\W+){0,3}$", re.I)
VARIABLE_AFTER = re.compile(r"^[ \t]*\(?(OTE|on[- ]target\w*|total comp\w*|TC|including commission|incl\.? commission)\b", re.I)
SYMBOL = {"$": "$ (unspecified)", "US$": "USD", "CA$": "CAD", "A$": "AUD", "€": "EUR", "£": "GBP", "¥": "¥ (JPY or CNY)"}
FLOOR = {"hour": 5, "month": 100, "year": 1000, "not stated": 1000}


def amount(s: str) -> float:
    s = re.sub(r"[\s  '’]", "", s)
    k = s.lower().endswith("k")
    s = s.rstrip("kK")
    if re.match(r"^\d{1,3}(\.\d{3})+,\d{2}$", s):  # 95.000,00: dot thousands, decimal comma
        s = s.replace(".", "").replace(",", ".")
    if re.match(r"^\d{1,3}(\.\d{3})+$", s):  # 95.000 style thousands
        s = s.replace(".", "")
    s = s.replace(",", "")
    try:
        v = float(s)
    except ValueError:
        return float("nan")
    return v * 1000 if k else v


def period(*units) -> str:
    p = " ".join(u or "" for u in units).lower()
    if not p.strip():
        return "not stated"
    if "mo" in p:
        return "month"
    if re.search(r"year|yr|annum|annual|p\.?a\.?|jährlich", p):
        return "year"
    if re.search(r"h(ou)?r|\bh\b|hourly", p):
        return "hour"
    return "year"


def parse(path: Path):
    text = path.read_text(encoding="utf-8", errors="replace")
    meta = {"url": "", "company": "", "title": ""}
    for line in text.splitlines()[:5]:
        m = re.match(r"^(url|company|title):\s*(.+)$", line.strip(), re.I)
        if m:
            meta[m.group(1).lower()] = m.group(2).strip()
    found, skipped, taken = [], [], []
    for rx in (PREFIX, SUFFIX):
        for m in rx.finditer(text):
            if any(m.start() < e and s < m.end() for s, e in taken):
                continue
            matched = " ".join(m.group(0).split())
            before = re.split(r"[.;!?](?=\s)|\n", text[max(0, m.start() - 60):m.start()])[-1]  # this sentence only
            if FUNDING_AFTER.search(text[m.end():m.end() + 25]) or FUNDING_BEFORE.search(before):
                skipped.append(matched)
                taken.append((m.start(), m.end()))
                continue
            cur = m.group("cur")
            cur = SYMBOL.get(cur, cur.upper())
            if "cur3" in rx.groupindex and m.group("cur3"):
                cur = m.group("cur3").upper()
            lo, hi = amount(m.group("lo")), amount(m.group("hi"))
            k_note = ""
            if (lo == lo and hi == hi and m.group("hi").strip().lower().endswith("k")
                    and not m.group("lo").strip().lower().endswith("k") and lo < 1000 <= hi):
                lo, k_note = lo * 1000, "k applied to both bounds"
            if not (lo == lo and hi == hi) or lo <= 0 or hi < lo:
                continue
            per = period(m.group("u1"), m.group("u2"))
            check = f"CHECK: implausible for {per}" if lo < FLOOR[per] else ""
            check = "; ".join(x for x in (check, k_note) if x)
            taken.append((m.start(), m.end()))
            vb = VARIABLE_BEFORE.search(text[max(0, m.start() - 40):m.start()])
            va = VARIABLE_AFTER.search(text[m.end():m.end() + 30])
            kind = f"OTE/variable ({(vb or va).group(1)})" if (vb or va) else "base?"
            found.append({**meta, "min": f"{lo:,.0f}", "max": f"{hi:,.0f}", "currency": cur,
                          "period": per, "kind": kind, "check": check, "matched": matched})
    return meta, found, skipped


def main(argv):
    files = [a for a in argv[1:] if not a.startswith("--")]
    as_csv = "--csv" in argv
    if not files:
        print(__doc__, file=sys.stderr)
        return 2
    rows, none, skips, read = [], [], [], 0
    for f in files:
        p = Path(f).expanduser()
        try:
            meta, found, skipped = parse(p)
        except OSError as exc:
            print(f"warning: cannot read {p}: {exc}", file=sys.stderr)
            continue
        read += 1
        skips.extend((meta.get("url") or str(p), s) for s in skipped)
        if found:
            rows.extend(found)
        else:
            none.append(meta.get("url") or str(p))
    if not read:
        return 2
    cols = ["url", "company", "title", "min", "max", "currency", "period", "kind", "check", "matched"]
    if as_csv:
        w = csv.DictWriter(sys.stdout, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    else:
        print("| " + " | ".join(cols) + " |")
        print("|" + "---|" * len(cols))
        for r in rows:
            print("| " + " | ".join(str(r[c]).replace("|", "/") for c in cols) + " |")
    for u, s in skips:
        print(f"skipped (not pay): {u}: {s}")
    for u in none:
        print(f"no range parsed - read the posting: {u}")
    print(f"summary: n={read} postings read, {len({r['url'] or r['matched'] for r in rows})} with a parsed range, "
          f"{len(none)} without. No average or band computed (small, non-random sample). "
          f"Read each row's matched text before showing the table.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
