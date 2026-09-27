#!/usr/bin/env python3
"""Validate a Sofia role scorecard, stamp approval, or start a new version.

Usage (cd ~/skills/role-intake-and-scorecard first):
    python3 scripts/scorecard_check.py <scorecard.md> [--companies <target-companies.csv>]
    python3 scripts/scorecard_check.py <scorecard.md> --approve "<HM name>" "<their words>"
    python3 scripts/scorecard_check.py <scorecard.md> --revise

Input:  a scorecard filled from templates/role-scorecard.md.
Output: one line per finding, "ERROR <where>: <what to fix>" or "WARN ...",
        then a summary. --approve and --revise rewrite the header in place.
Exit:   0 no errors; 1 errors found (or approval refused); 2 usage/unreadable.

Checks (stdlib only, no network):
  * header has role, role_slug, version, status (draft | draft-pending-calibration | approved)
  * 3 to 6 must-haves (M1..), each with evidence_method, agree_test, what_fails_without_it
  * must-haves carry no years-of-experience or degree floor unless the line says "HM defended:"
  * no protected-trait proxy anywhere in the bar (lexicon below); location is not a postcode
  * disqualifiers each have a fairness_check; short tenures ("no job-hoppers") are never kept
  * benchmark traits that name a school or employer brand are WARN (incidental)
  * target companies (if --companies): each row has a link and link_status ok|blocked;
    'dead' or missing links are errors (drop the row)
The lexicon flags; a human decides. Physical-demand words are WARN, not ERROR,
because they can be job-related when written "with or without reasonable accommodation".

Job words that trip the lexicon. "Under/over NN" is an age only when it reads as
one ("candidates over 50", "be over 18", "under 35 years old", "... over 40."); a
count ("over 10 direct reports", "payroll for over 50 employees") is not flagged.
The same pattern is the age row in job-description-drafting's lint-terms.csv.
Some listed terms are plain job words in some roles: a preschool teacher leads
"children aged 3 to 5", a clinic keeps "medical history" records, a midwife
works a "maternity ward". For these terms only (children, kids, childcare,
pregnancy, maternity, disability, medical history, photo), record why the use
is job-related with a child line under that item:
    - M1: Has led a room of children aged 3 to 5 in a licensed setting.
      - lint_ok: children - the job is caring for children; not a family-status test
The term is then a WARN ("kept as job-related: <why>") that you show the HM,
and approval can proceed. lint_ok never clears the other terms (digital native,
native speaker, culture fit, young, age limits, graduation year, postcode,
married/marital, health issues, able-bodied, religion, sex/gender, employment gaps, job-hopping): rewrite or cut those.
"man-hours"/"man-days" are units, not a sex term, and are not flagged.
--approve warns when the approver is not the header's hiring_manager.
"""

from __future__ import annotations

import csv
import datetime as dt
import re
import shutil
import sys
import unicodedata
from pathlib import Path

STATUSES = {"draft", "draft-pending-calibration", "approved"}
MIN_MUST, MAX_MUST = 3, 6  # persona day_one: "three to six checkable must-haves"
MUST_FIELDS = ("evidence_method", "agree_test", "what_fails_without_it")

# Age limit, not a count: a person word before, or "years old"/end of clause after.
# Keep in step with the age row of job-description-drafting/references/lint-terms.csv.
_AGE_N = r"(?:1[6-9]|[2-7]\d)"
AGE_LIMIT = (r"\b(?:age[ds]?|candidates?|applicants?|someone|anyone|people|persons?|individuals?|workers?|staff|"
             r"nobody|no one|those|be|is|are|you're|you are)\s+(?:under|over|below|above|aged?)\s+" + _AGE_N + r"\b"
             r"|\bage[ds]?\s+" + _AGE_N + r"\s*(?:to|-|\u2013|and)\s*" + _AGE_N + r"\b"
             r"|\b(?:under|over|below|above|aged?)\s+" + _AGE_N +
             r"(?:\s*(?:years? old|years of age|yrs? old|y/?o)\b|\s*(?:years?|yrs)?(?=\s*(?:$|[.,;:!?)])))")
# Categories a recorded "lint_ok: <term> - <why>" may turn from ERROR into WARN.
OVERRIDABLE = {"family", "health", "photo"}
# (regex, message[, category]). ERROR unless the category is OVERRIDABLE and a lint_ok line covers the term.
PROXY_ERRORS = [
    (r"\bdigital natives?\b", "age proxy; name the actual skill (e.g. 'ships features in <tool>')"),
    (r"\bnative (english )?speakers?\b|\bnative[- ]level\b", "national-origin proxy; write the language task (e.g. 'writes customer docs in English')"),
    (r"\bculture fit\b|\bfits? (our|the) culture\b", "class/demographic proxy; name the job behaviour or cut it"),
    (r"\b(young|youthful)\b", "age term (29 CFR 1625.4)"),
    (r"\brecent (college )?grad(uate)?s?\b|\bcollege students?\b", "age term (29 CFR 1625.4)"),
    (AGE_LIMIT, "age limit (29 CFR 1625.4)"),
    (r"\b(graduat\w+|class of) (19|20)\d{2}\b|\bgraduation year\b", "graduation year used as an age filter"),
    (r"\b(post ?code|zip ?code)\b|\bwithin \d+ ?(miles|km)\b|\bcommut\w+ (distance|radius)\b|\blocal candidates only\b", "location proxy; write work terms (hours, on-site days) instead"),
    (r"\b(married|marital|single parents?|family plans?)\b", "family-status term; write the work requirement (e.g. travel days) instead"),
    (r"\b(children|kids|childcare|pregnan\w*|maternity)\b", "family-status term; write the work requirement (e.g. travel days) instead", "family"),
    (r"\b(religio\w+|church|christian|muslim|jewish|hindu)\b", "religion term"),
    (r"\b(man|woman|male|female|guys?|girls?|boys?)\b(?!-(hours?|days?|months?|years?)\b)", "sex/gender term"),
    (r"\b(health (issues|problems|conditions)|able[- ]bodied)\b", "health/disability term; use 'with or without reasonable accommodation'"),
    (r"\b(disabilit\w+|medical history)\b", "health/disability term; use 'with or without reasonable accommodation'", "health"),
    (r"\bno (employment )?gaps?\b|\bgaps? in employment\b|\bcontinuous employment\b", "employment-gap filter (gap proxies; see Mobley allegations)"),
    (r"\bphoto\b|\bheadshot\b", "photo request", "photo"),
    (r"\bjob[- ]?hopp\w*|\bshort tenures?\b|\btoo many (jobs|employers)\b", "short tenures are never a disqualifier; note the pattern on the candidate card for the interviewer instead"),
]
# Benchmark traits must transfer; school and employer brand are incidental.
BENCH_WARN = re.compile(r"\b(school|university|college|alma mater|ivy( league)?|stanford|harvard|mit|oxford|cambridge|"
                        r"faang|big tech|ex-\w+|went to|graduated from|prestig\w+|top[- ]tier)\b", re.I)
PROXY_WARNS = [
    (r"\b(lift(ing)?|carry(ing)?)\s+(up to\s+)?\d+|\bstand(ing)? for\b|\bon (your|their) feet\b|\bwalk(ing)? for\b", "physical demand: keep only if essential and phrase 'with or without reasonable accommodation'"),
    (r"\bcitizens?(hip)?\b", "citizenship: usually a work-authorisation question; confirm wording with counsel"),
    (r"\b(energetic|high[- ]energy)\b", "can read as an age proxy; describe the pace of the work instead"),
    (r"\b(rockstar|ninja|guru|wizard)\b", "label, not a requirement"),
]
FLOOR_RE = re.compile(r"\b\d+\s*\+?\s*(years?|yrs)\b|\b(bachelor'?s?|master'?s?|ph\.?d|mba|(?<![\d-])(?<!\d )degree|b\.?s\.?|b\.?a\.?)\b", re.I)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        sys.exit(2)


def split_header(text: str):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text.replace("\r\n", "\n"), re.S)
    if not m:
        return None, text
    header = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            header[k.strip()] = v.strip()
    return header, m.group(2)


def section(body: str, title: str) -> str:
    m = re.search(r"^## " + re.escape(title) + r"\s*$(.*?)(?=^## |\Z)", body, re.M | re.S)
    return m.group(1) if m else ""


def items(block: str, prefix: str):
    """Return {id: {"text": str, field: value}} for '- M1: text' items with '  - field: value' children."""
    out, current = {}, None
    for line in block.splitlines():
        m = re.match(r"^- (%s\d+):\s*(.*)$" % prefix, line)
        if m:
            current = m.group(1)
            out[current] = {"text": m.group(2).strip()}
            continue
        f = re.match(r"^\s+- ([a-z_]+):\s*(.*)$", line)
        if f and current:
            if f.group(1) == "lint_ok":
                out[current].setdefault("lint_ok", []).append(f.group(2).strip())
            else:
                out[current][f.group(1)] = f.group(2).strip()
    return out


def fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return " ".join("".join(c for c in s if not unicodedata.combining(c)).casefold().split())


def lint_oks(where: str, item: dict, errors: list) -> dict:
    """Parse 'lint_ok: <term> - <why>' lines into {folded term: why}."""
    oks = {}
    for raw in item.get("lint_ok", []):
        m = re.match(r"^(.+?)\s+[-\u2013\u2014]\s+(.+)$", raw)
        if not m or m.group(2).strip().startswith("<"):
            errors.append(f"{where}: lint_ok '{raw}' needs '<term> - <why it is job-related>'")
            continue
        oks[fold(m.group(1).strip(" '\""))] = m.group(2).strip()
    return oks


def item_text(item: dict) -> str:
    return " ".join(v for k, v in item.items() if k != "lint_ok" and isinstance(v, str))


def strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def lint_line(where: str, text: str, errors: list, warns: list, oks: dict | None = None) -> None:
    low = text.lower()
    oks = oks or {}
    used = set()
    for entry in PROXY_ERRORS:
        rx, msg = entry[0], entry[1]
        cat = entry[2] if len(entry) > 2 else None
        for m in re.finditer(rx, low):
            term = fold(m.group(0))
            if cat in OVERRIDABLE and term in oks:
                if term not in used:
                    warns.append(f"{where}: '{m.group(0)}' kept as job-related: {oks[term]} "
                                 f"(show the HM; the lexicon reads it as a {msg.split(';')[0]})")
                used.add(term)
                continue
            if cat in OVERRIDABLE:
                hint = f" (if the use is job-related, record '  - lint_ok: {m.group(0)} - <why>' under this item)"
            elif term in oks:
                hint = " (lint_ok cannot clear this term; rewrite or cut it)"
                used.add(term)
            else:
                hint = ""
            errors.append(f"{where}: '{m.group(0)}' - {msg}{hint}")
            break
    for term in oks:
        if term not in used:
            warns.append(f"{where}: lint_ok '{term}' matched nothing on this item; remove it")
    for rx, msg in PROXY_WARNS:
        m = re.search(rx, low)
        if m and "accommodation" not in low:
            warns.append(f"{where}: '{m.group(0)}' - {msg}")


def check(path: Path, companies: Path | None) -> int:
    text = read(path)
    header, body = split_header(text)
    body = strip_comments(body)
    errors, warns = [], []
    if header is None:
        errors.append("header: missing '---' block; start from templates/role-scorecard.md")
        header = {}
    for key in ("role", "role_slug", "version", "status"):
        if not header.get(key) or header[key].startswith("<"):
            errors.append(f"header: '{key}' is empty")
    if header.get("status") and header["status"] not in STATUSES:
        errors.append(f"header: status '{header['status']}' must be one of {sorted(STATUSES)}")
    lint_line("header location_terms", header.get("location_terms", ""), errors, warns)

    musts = items(section(body, "Must-haves"), "M")
    if not MIN_MUST <= len(musts) <= MAX_MUST:
        errors.append(f"must-haves: {len(musts)} found, need {MIN_MUST}-{MAX_MUST} (persona day-one bar)")
    for mid, m in musts.items():
        if not m["text"] or m["text"].startswith("<"):
            errors.append(f"{mid}: empty statement")
        for field in MUST_FIELDS:
            if not m.get(field) or m[field].startswith("<"):
                errors.append(f"{mid}: missing {field}")
        if FLOOR_RE.search(m["text"]) and "hm defended:" not in m["text"].lower():
            errors.append(f"{mid}: years/degree floor; replace with the outcome behind it, or record 'HM defended: <quote>'")
        if re.search(r"\b(the best|top \d+ ?%|strongest|better than|among the)\b", m["text"], re.I):
            errors.append(f"{mid}: comparative wording; a must-have is met or not, without comparing candidates")
        lint_line(mid, item_text(m), errors, warns, lint_oks(mid, m, errors))

    for nid, n in items(section(body, "Nice-to-haves"), "N").items():
        lint_line(nid, n["text"], errors, warns, lint_oks(nid, n, errors))
    for did, d in items(section(body, "Disqualifiers"), "D").items():
        if not d.get("fairness_check") or d["fairness_check"].startswith("<"):
            errors.append(f"{did}: missing fairness_check")
        if "kept" in d.get("fairness_check", "").lower():
            lint_line(did, d["text"], errors, warns, lint_oks(did, d, errors))
    for bid, b in items(section(body, "Benchmark"), "B").items():
        lint_line(bid, b["text"], errors, warns, lint_oks(bid, b, errors))
        hit = BENCH_WARN.search(b["text"])
        if hit:
            warns.append(f"{bid}: '{hit.group(0)}' reads as pedigree (school or employer brand); keep only a checkable trait that transfers, and list the rest under dropped_as_incidental")
    for oid, o in items(section(body, "Year-one outcomes"), "O").items():
        if not o.get("source") or o["source"].startswith("<"):
            errors.append(f"{oid}: no source; quote the HM (FACT) or label INFERENCE")

    if companies:
        if not companies.exists():
            errors.append(f"companies: {companies} not found")
        else:
            with companies.open(encoding="utf-8", newline="") as fh:
                rows = list(csv.DictReader(fh))
            if not rows:
                warns.append("companies: file has no rows yet")
            blocked = 0
            for i, row in enumerate(rows, start=2):
                name = (row.get("company") or "").strip() or f"row {i}"
                link = (row.get("link") or "").strip()
                status = (row.get("link_status") or "").strip().lower()
                if not link.startswith(("http://", "https://")):
                    errors.append(f"companies {name}: no link; a company with no working link is dropped")
                elif status == "dead" or status not in ("ok", "blocked"):
                    errors.append(f"companies {name}: link_status '{status or 'empty'}'; fetch it and set ok/blocked, or drop the row")
                elif status == "blocked":
                    blocked += 1
                lint_line(f"companies {name}", row.get("why", ""), errors, warns)
            if blocked:
                warns.append(f"companies: {blocked} link(s) blocked (403/login wall): check manually")

    for e in errors:
        print(f"ERROR {e}")
    for w in warns:
        print(f"WARN  {w}")
    print(f"summary: {len(musts)} must-haves, {len(errors)} errors, {len(warns)} warnings, status={header.get('status', '?')}, version={header.get('version', '?')}")
    return 1 if errors else 0


def set_header(path: Path, updates: dict) -> None:
    text = read(path).replace("\r\n", "\n")
    header, _ = split_header(text)
    if header is None:
        print("error: no header block to update", file=sys.stderr)
        sys.exit(2)
    head, rest = text.split("\n---\n", 1)
    lines = head.splitlines()
    for key, value in updates.items():
        for i, line in enumerate(lines):
            if line.startswith(f"{key}:"):
                lines[i] = f"{key}: {value}"
                break
        else:
            lines.append(f"{key}: {value}")
    path.write_text("\n".join(lines) + "\n---\n" + rest, encoding="utf-8")


def append_log(path: Path, line: str) -> None:
    text = read(path)
    if "## Change log" not in text:
        text = text.rstrip("\n") + "\n\n## Change log\n"
    path.write_text(text.rstrip("\n") + f"\n- {line}\n", encoding="utf-8")


def main(argv: list) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    path = Path(argv[1]).expanduser()
    args = argv[2:]
    today = dt.date.today().isoformat()
    if args[:1] == ["--approve"]:
        if len(args) != 3 or not args[1].strip() or not args[2].strip():
            print('usage: --approve "<HM name>" "<their words>"', file=sys.stderr)
            return 2
        if check(path, None):
            print("approval refused: fix the errors above first")
            return 1
        header, _ = split_header(read(path))
        hm = (header or {}).get("hiring_manager", "")
        if not hm or hm.startswith("<") or fold(hm) != fold(args[1].strip()):
            print(f"WARN  approver is not the hiring_manager ({hm or 'not set'}); confirm they own the bar")
        set_header(path, {"status": "approved", "approved_by": args[1].strip(),
                          "approved_on": today, "approval_quote": '"' + args[2].strip().replace('"', "'") + '"'})
        append_log(path, f"v{header.get('version', '?')} {today}: approved by {args[1].strip()}.")
        print(f"approved: v{header.get('version')} by {args[1].strip()} on {today}")
        return 0
    if args[:1] == ["--revise"]:
        header, _ = split_header(read(path))
        try:
            version = int(header.get("version", "1"))
        except ValueError:
            print("error: version is not a number", file=sys.stderr)
            return 2
        keep = path.with_name(f"{path.stem}-v{version}{path.suffix}")
        shutil.copyfile(path, keep)
        set_header(path, {"version": str(version + 1), "status": "draft", "approved_by": "UNSET",
                          "approved_on": "UNSET", "approval_quote": "UNSET"})
        append_log(path, f"v{version + 1} {today}: revision opened; v{version} kept as {keep.name}. Needs HM approval.")
        print(f"revised: v{version} kept as {keep.name}; now v{version + 1}, status draft")
        return 0
    companies = None
    if args[:1] == ["--companies"]:
        if len(args) != 2:
            print("usage: --companies <target-companies.csv>", file=sys.stderr)
            return 2
        companies = Path(args[1]).expanduser()
    elif args:
        print(f"unknown option {args[0]}", file=sys.stderr)
        return 2
    return check(path, companies)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
