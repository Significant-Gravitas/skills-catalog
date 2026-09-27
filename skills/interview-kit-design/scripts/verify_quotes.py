#!/usr/bin/env python3
"""Check that a prep packet's candidate summary is quotes, and that each quote
is really in its source.

    cd ~/skills/interview-kit-design && python3 scripts/verify_quotes.py <packet.md> \
        [--base ~/workspace/hiring] [--source-map URL=/home/user/src/page.txt ...] [--json]

Reads the "## Candidate summary" section only. Each line must be either
    - "exact words" — source: <path or URL>
    - <topic>: not stated
Line checks:
    FAIL  more than 5 lines (skill limit), a line with no quote (paraphrase),
          a quote with no source, or a quote not found in its source.
          Every quoted span on the line is checked; one bad span fails the
          line. Outside the quotes only a short '<topic>:' label (at most 6
          words) before the first quote, joiners (and ; , ...) between quotes
          and the dash before 'source:' are allowed; any other words are
          paraphrase and FAIL. A quote that starts just after 'not', 'never',
          'no' or a "n't" word in the source FAILs (it drops a negation).
          Any changed letter or digit is a FAIL: "I was the lead" for "I was not
          the lead", "4GB" for "4TB", "some downtime" for "zero downtime". There
          is no "approximate" band; the near-match ratio is only shown to help
          find the real words, and a changed number is named in the FAIL line.
    SKIP  a URL source with no local copy. Fetch it with web_fetch, save the text
          to a file, and rerun with --source-map URL=path. Until then the line is
          UNVERIFIED and must say so in the packet.
    OK    exact match after normalising case, spacing, quote marks and dashes,
          or once every run of punctuation/spacing is treated as one space
          ("on call" for "on-call", a dropped comma or full stop).
Relative source paths resolve against --base (default ~/workspace/hiring).

Exit 0 when nothing FAILs (SKIPs allowed but listed), 1 on any FAIL, 2 on bad input.
Every summary line in a packet must end OK (a quote or "not stated"); a SKIP
line is marked UNVERIFIED in the packet.
--selftest checks itself.
"""

import argparse
import difflib
import json
import os
import re
import sys
import tempfile

MAX_LINES = 5
MINIMUM = 0.92      # near-match ratio at or above which the FAIL says "near match" (a hint only)
QUOTE = re.compile(r"[\"“”](.+?)[\"“”]")
SOURCE = re.compile(r"source:\s*(\S.*?)\s*(\((FACT|INFERENCE|UNKNOWN)\))?\s*$", re.I)


def norm(t):
    t = t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    t = re.sub(r"[–—-]+", "-", t)
    return re.sub(r"\s+", " ", t).strip().lower()


def bare(t):
    """Letters and digits only, every other run collapsed to one space."""
    return " ".join(re.sub(r"[^a-z0-9]+", " ", t.lower()).split())


def summary_lines(text):
    out, grab = [], False
    for line in text.splitlines():
        if re.match(r"^##\s+candidate summary", line, re.I):
            grab = True
            continue
        if grab and re.match(r"^##\s", line):
            break
        if grab and re.match(r"^\s*[-*]\s+", line):
            out.append(line.strip()[1:].strip())
    return out


NUMBER_WORDS = {
    "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen",
    "nineteen", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety",
    "hundred", "thousand", "million", "billion", "half", "quarter", "dozen", "once", "twice",
    "double", "triple", "single"}
DIGITS = re.compile(r"\d+(?:[.,]\d+)*")


def numbers(text):
    """Digit groups and number words, as a multiset-free set of tokens."""
    toks = set(DIGITS.findall(text))
    toks |= {w for w in re.findall(r"[a-z]+", text.lower()) if w in NUMBER_WORDS}
    return toks


def best_ratio(quote, source):
    """Best fuzzy ratio of quote against any same-length window, and that window."""
    if quote in source:
        return 1.0, quote
    n = len(quote)
    if n == 0 or len(source) < n // 2:
        return 0.0, ""
    best, span = 0.0, ""
    step = max(1, n // 8)
    for i in range(0, max(1, len(source) - n + 1), step):
        r = difflib.SequenceMatcher(None, quote, source[i:i + n]).ratio()
        if r > best:
            pad = max(8, n // 8)
            best, span = r, source[max(0, i - pad):i + n + pad]
    return best, span


NEGATION = {"not", "never", "no", "nor", "without", "neither", "hardly", "barely"}
TOPIC = re.compile(r"^\s*([\w'’/&()-]+(\s+[\w'’/&()-]+){0,5})?\s*:?\s*$")
JOINER = re.compile(r"^\s*(and|;|,|\.\.\.|…|,\s*and|;\s*and)?\s*$", re.I)
TAIL = re.compile(r"^\s*[–—-]*\s*$")


def outside_text(line, spans, src_start):
    """Return a reason when words outside the quotes carry a claim, else None.
    Allowed: an optional '<topic>:' label (at most 6 words) before the first
    quote, joiners ('and', ';', ',', '...') between quotes, and a dash before
    'source:'."""
    head = line[:spans[0].start()]
    if head.strip() and not (TOPIC.match(head) and head.rstrip().endswith(":")):
        return f"text outside the quotes is paraphrase: '{head.strip()[:60]}'"
    for a, b in zip(spans, spans[1:]):
        mid = line[a.end():b.start()]
        if not JOINER.match(mid):
            return f"text outside the quotes is paraphrase: '{mid.strip()[:60]}'"
    tail = line[spans[-1].end():src_start]
    if not TAIL.match(tail):
        return f"text outside the quotes is paraphrase: '{tail.strip()[:60]}'"
    return None


def check(lines, base, source_map):
    results = []
    if len(lines) > MAX_LINES:
        results.append({"line": "(section)", "status": "FAIL",
                        "why": f"{len(lines)} lines; the summary is at most {MAX_LINES}"})
    for line in lines:
        if re.search(r":\s*not stated\s*$", line, re.I):
            results.append({"line": line, "status": "OK", "why": "gap marked not stated"})
            continue
        s = SOURCE.search(line)
        qs = list(QUOTE.finditer(line[:s.start()] if s else line))
        if not qs:
            results.append({"line": line, "status": "FAIL", "why": "no direct quote: paraphrase is not allowed"})
            continue
        if not s:
            results.append({"line": line, "status": "FAIL", "why": "quote has no 'source:'"})
            continue
        extra = outside_text(line, qs, s.start())
        if extra:
            results.append({"line": line, "status": "FAIL", "why": extra})
            continue
        src = s.group(1).strip()
        path = source_map.get(src)
        if not path and re.match(r"https?://", src):
            results.append({"line": line, "status": "SKIP",
                            "why": "URL source with no local copy: web_fetch it, save, rerun with --source-map"})
            continue
        path = path or (src if os.path.isabs(os.path.expanduser(src)) else os.path.join(base, src))
        path = os.path.expanduser(path)
        if not os.path.exists(path):
            results.append({"line": line, "status": "FAIL", "why": f"source file not found: {path}"})
            continue
        with open(path, encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
        verdicts = [one_quote(q.group(1), raw) for q in qs]
        bad = [(i, v) for i, v in enumerate(verdicts, 1) if v[0] == "FAIL"]
        if bad:
            i, (_, why) = bad[0]
            label = f"quote {i} of {len(qs)}: " if len(qs) > 1 else ""
            results.append({"line": line, "status": "FAIL", "why": label + why})
        else:
            results.append({"line": line, "status": "OK", "why": "; ".join(v[1] for v in verdicts)})
    return results


def one_quote(text, raw):
    quote = norm(text)
    ratio, span = best_ratio(quote, norm(raw))
    changed = numbers(quote) - numbers(span)
    if ratio >= 1.0:
        src = norm(raw)
        for mm in re.finditer(re.escape(quote), src):
            before = re.findall(r"[a-z']+", src[max(0, mm.start() - 40):mm.start()])[-2:]
            if any(w in NEGATION or w.endswith("n't") for w in before):
                return "FAIL", (f"the source puts '{' '.join(before)}' just before these words; the "
                                "quote drops a negation and reverses the claim. Quote the whole phrase")
        return "OK", "exact"
    if bare(quote) and f" {bare(quote)} " in f" {bare(raw)} ":
        return "OK", "exact apart from punctuation or spacing"
    if ratio >= MINIMUM and changed:
        return "FAIL", (f"near match ({ratio:.2f}) but the number(s) {', '.join(sorted(changed))} are not "
                        "in the source; a changed figure is not a quote, do not use")
    if ratio >= MINIMUM:
        return "FAIL", (f"near match ({ratio:.2f}) with changed words; a quote is the exact "
                        "words, so copy them from the source or drop the line")
    return "FAIL", f"not found in source (best {ratio:.2f}); do not use"


def selftest():
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "resume.txt"), "w", encoding="utf-8") as fh:
        fh.write("Led the migration of a 4TB Postgres table with zero downtime.\nOwned billing on-call.\n"
                 "Cut unmatched items from 2.1% to 0.3%. On-call one week in four.")
    packet = """## Candidate summary (max 5 lines; direct quotes only)

- "Led the migration of a 4TB Postgres table with zero downtime" — source: resume.txt
- "Owned billing on call" — source: resume.txt
- "Built the whole platform alone" — source: resume.txt
- Strong Postgres background — source: resume.txt
- "Talk on retries" — source: https://example.org/talk
- Management experience: not stated

## Your questions
"""
    res = check(summary_lines(packet), d, {})
    st = [r["status"] for r in res]
    assert st == ["FAIL", "OK", "OK", "FAIL", "FAIL", "SKIP", "OK"], res
    changed = """## Candidate summary

- "Led the migration of a 40TB Postgres table with zero downtime" — source: resume.txt
- "Cut unmatched items from 2.1% to 0.03%" — source: resume.txt
- "On-call one week in two" — source: resume.txt
- "Cut unmatched items from 2.1% to 0.3%" — source: resume.txt
"""
    st = [r["status"] for r in check(summary_lines(changed), d, {})]
    assert st == ["FAIL", "FAIL", "FAIL", "OK"], st
    with open(os.path.join(d, "resume2.txt"), "w", encoding="utf-8") as fh:
        fh.write("I was not the lead on the billing migration project, but I wrote the backfill.\n"
                 "Moved 4TB of ledger rows with zero downtime.")
    reversed_ = """## Candidate summary

- "I was the lead on the billing migration project" — source: resume2.txt
- "Moved 4GB of ledger rows with zero downtime" — source: resume2.txt
- "Moved 4TB of ledger rows with some downtime" — source: resume2.txt
- "I was not the lead on the billing migration project but I wrote the backfill" — source: resume2.txt
"""
    st = [r["status"] for r in check(summary_lines(reversed_), d, {})]
    assert st == ["FAIL", "FAIL", "FAIL", "OK"], st
    # every quote on a line is checked, and words outside the quotes are paraphrase
    multi = """## Candidate summary

- "Led the migration of a 4TB Postgres table" and "led the billing rewrite" — source: resume.txt
- Managed a team of 12; "Owned billing on-call" — source: resume.txt
- Postgres: "Led the migration of a 4TB Postgres table"; "Owned billing on-call" — source: resume.txt
- "Owned billing on-call" (she was the lead) — source: resume.txt
- "the lead on the billing migration project" — source: resume2.txt
"""
    st = [r["status"] for r in check(summary_lines(multi), d, {})]
    assert st == ["FAIL", "FAIL", "OK", "FAIL", "FAIL"], st
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("packet", nargs="?")
    ap.add_argument("--base", default=os.path.expanduser("~/workspace/hiring"))
    ap.add_argument("--source-map", action="append", default=[])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.packet:
        ap.error("give the packet path")
    try:
        smap = dict(x.split("=", 1) for x in a.source_map)
        with open(a.packet, encoding="utf-8") as fh:
            lines = summary_lines(fh.read())
    except (OSError, ValueError) as exc:
        print(f"bad input: {exc}", file=sys.stderr)
        return 2
    if not lines:
        print("FAIL\tno '## Candidate summary' lines found; fill the summary first")
        return 1
    res = check(lines, a.base, smap)
    if a.json:
        print(json.dumps(res, indent=1))
    else:
        for r in res:
            print(f"{r['status']}\t{r['why']}\n\t{r['line'][:140]}")
    return 1 if any(r["status"] == "FAIL" for r in res) else 0


if __name__ == "__main__":
    sys.exit(main())
