#!/usr/bin/env python3
"""Validate offer terms before anything is filled, drafted or shown to an approver.

Usage (cd ~/skills/job-offer-and-close-plan first):

  python3 scripts/check_terms.py terms.json [--today 2026-10-12] \
      [--text letter-DRAFT.md --text email-DRAFT.txt] [--template company-template.md]

terms.json follows templates/offer-terms.json. Each entry under "terms" is
{"value", "source", "approver", "approved_on"}; dates are ISO (YYYY-MM-DD).

Checks (ERROR blocks the draft; WARN goes in front of the owner):
  - required terms present, each with a source and an approver;
  - no term sourced from or mentioning current / past / previous pay
    (salary-history bans, e.g. California Labor Code 432.3);
  - ISO dates; response_by not in the past; start_date after response_by;
  - base_pay has currency and pay_period;
  - base inside the approved band; above band needs above_band_approval with
    approver, approved_on and an amount at least base_pay;
  - sales: ote == base_pay + variable_target when all three are given, and the
    commission plan is carried as approved text;
  - contingencies: a background check needs a standalone FCRA disclosure on
    record before the report is procured; a medical exam must be post-offer
    and apply to everyone entering the job category (ADA, 29 CFR 1630.14);
  - with --text (.md, .txt or .docx): every money figure in the draft (a
    number with a currency sign/code next to it, a prefixed sign such as
    R$ / US$ / A$ / C$ / S$, a currency word after it such as "150.000
    euros" / "150.000 Euro" / "150,000 dollars" / "reais" / "libras", or a
    k suffix such as "EUR 110k") must match a term and be in the terms currency (catches an
    email that says 62,000 while the letter says 60,000). Any term whose
    value is a number counts as money (e.g. a derived "monthly_base" or a
    "meal_allowance_daily" term, each with source and approver); figures
    are compared to the cent. Thousands may be grouped with commas, dots,
    spaces or no-break spaces, and a trailing ",57" / ".57" is read as cents
    (EUR 104 000, 104.000 EUR, EUR 7.428,57, 9,60 EUR). Swiss apostrophe
    grouping (CHF 104'000) and Indian lakh grouping (INR 12,50,000) are read
    too. 401k / 401(k) / 403(b) / 457(b) are plan names, not money. Bare
    numbers grouped with commas, dots, apostrophes or no-break spaces that
    match no term are WARN (plain-space groups are not: phones, NIF); phone numbers, street numbers, postcodes
    and registration numbers carry no currency and are ignored. Dates that
    are neither start_date nor response_by are WARN.
  - with --template (the unfilled company template): a figure that appears
    verbatim in the template is the template's own binding wording (a fixed
    stipend or allowance). It is printed as INFO, not ERROR; the skill never
    edits it.

Exit: 0 no errors, 1 errors found, 2 unreadable input.
"""

import argparse
import datetime as dt
import html
import json
import re
import sys
import zipfile

from fill_offer_template import PARA, TEXT
from pay_history import HISTORY_RE

REQUIRED = ["entity", "title", "level", "start_date", "base_pay", "currency",
            "pay_period", "response_by", "signatory", "contact_for_questions"]
DATE_KEYS = ["start_date", "response_by"]
MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec"
CURRENCY = r"(?:R\$|US\$|A\$|C\$|S\$|[$€£]|USD|EUR|GBP|CAD|AUD|CHF|SGD|INR|BRL)"
# Spelled-out currencies, read after the number ("150.000 euros", "150.000 Euro",
# "150,000 dollars", "R$ 150.000,00" / "150.000 reais").
CURRENCY_WORD = r"(?:euros?|dollars?|pounds?|libras?|reais|francs?|rupees?)"
# A figure is money when a currency sign/code sits next to it or it has a k suffix.
# Numbers: grouped with one consistent separator (104,000 / 104.000 / 104 000 /
# 104<NBSP>000), optional 1-2 decimals after "." or "," (104,000.00, 7.428,57,
# 9,60), or plain digits (110 in "110k").
SEP = "[ \u00a0\u202f.,'\u2019]"
GROUPED_RE = rf"\d{{1,3}}(?P<sep>{SEP})\d{{3}}(?:(?P=sep)\d{{3}})*(?:[.,]\d{{1,2}})?"
# Indian lakh grouping: 12,50,000 / 1,04,00,000.
LAKH_RE = r"\d{1,2}(?:,\d{2})+,\d{3}(?:\.\d{1,2})?"
# Bare (no currency) numbers grouped this way that match no term are WARN.
# Plain spaces stay out: phone numbers, NIF and postcodes use them.
WARN_BARE_SEPS = {",", ".", "\u00a0", "\u202f", "'", "\u2019"}
MONEY_TOKEN = re.compile(
    rf"(?<![\w.,])(?:(?P<cur1>{CURRENCY})[ \u00a0]?)?"
    rf"(?P<num>{LAKH_RE}|{GROUPED_RE}|\d+(?:[.,]\d{{1,2}})?)"
    r"(?P<k>\s?[kK](?![A-Za-z]))?"
    rf"(?:[ \u00a0\u202f]?(?P<cur2>{CURRENCY}|{CURRENCY_WORD})(?![A-Za-z]))?"
    r"(?![\d%])", re.I)
# Retirement-plan names that look like "401k" money.
PLAN_NAMES = re.compile(r"\b(?:401|403|457)\s?(?:\(\s?[kb]\s?\)|[kb])(?![A-Za-z])", re.I)
DOLLARS = {"USD", "CAD", "AUD", "SGD"}
CURRENCY_OF_SIGN = {"$": DOLLARS, "€": {"EUR"}, "£": {"GBP"}, "R$": {"BRL"}, "US$": {"USD"},
                    "A$": {"AUD"}, "C$": {"CAD"}, "S$": {"SGD"},
                    "euro": {"EUR"}, "euros": {"EUR"}, "dollar": DOLLARS, "dollars": DOLLARS,
                    "pound": {"GBP"}, "pounds": {"GBP"}, "libra": {"GBP"}, "libras": {"GBP"},
                    "reais": {"BRL"}, "franc": {"CHF"}, "francs": {"CHF"},
                    "rupee": {"INR"}, "rupees": {"INR"}}
DATE_TOKENS = [
    (re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"), "%Y-%m-%d"),
    (re.compile(rf"\b(\d{{1,2}} (?:{MONTHS})[a-z]* \d{{4}})\b", re.I), "%d %b %Y"),
    (re.compile(rf"\b((?:{MONTHS})[a-z]* \d{{1,2}},? \d{{4}})\b", re.I), "%b %d %Y"),
]


def currencies_of(cur):
    """The currency codes a sign, code or word can stand for."""
    key = cur.upper() if cur.upper() in CURRENCY_OF_SIGN else cur.lower()
    return CURRENCY_OF_SIGN.get(key, CURRENCY_OF_SIGN.get(cur, {cur.upper()}))


def parse_iso(value):
    try:
        return dt.date.fromisoformat(str(value))
    except ValueError:
        return None


def to_number(value):
    try:
        return float(str(value).replace(",", "").replace(" ", ""))
    except ValueError:
        return None


def parse_amount(raw):
    """Parse a figure as written: 104,000 / 104.000 / 104 000 / 104,000.00 /
    7.428,57 / 9,60 / 110 -> float rounded to cents. A last separator followed
    by one or two digits is the decimal mark; every other separator groups
    thousands."""
    raw = raw.strip()
    m = re.search(r"[.,](\d{1,2})$", raw)
    cents = ""
    if m:
        cents, raw = m.group(1), raw[:m.start()]
    digits = re.sub(r"[ \u00a0\u202f.,'\u2019]", "", raw)
    if not digits.isdigit():
        return None
    return round(float(digits + ("." + cents if cents else "")), 2)


def term_amount(value):
    """A term value as money when it is a number (104000, "104000", "7428.57",
    "EUR 7.428,57"); None for text, dates and levels."""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return round(float(value), 2)
    s = str(value).strip()
    s = re.sub(rf"^{CURRENCY}\s*|\s*{CURRENCY}$", "", s, flags=re.I).strip()
    if not re.fullmatch(rf"{LAKH_RE}|{GROUPED_RE}|\d+(?:[.,]\d{{1,2}})?", s):
        return None
    return parse_amount(s)


def money_tokens(text):
    """Yield (match, token) for money-like figures, with plan names blanked."""
    text = PLAN_NAMES.sub(lambda m: " " * len(m.group(0)), text)
    for m in MONEY_TOKEN.finditer(text):
        yield m, re.sub(r"\s+", " ", m.group(0).strip())


def parse_loose_date(text, fmt):
    cleaned = re.sub(r",", "", text)
    cleaned = re.sub(r"(?i)\b(sept)\b", "Sep", cleaned)
    parts = cleaned.split()
    if fmt != "%Y-%m-%d":
        idx = 1 if fmt == "%d %b %Y" else 0
        parts[idx] = parts[idx][:3]
        cleaned = " ".join(parts)
    try:
        return dt.datetime.strptime(cleaned, fmt).date()
    except ValueError:
        return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("terms")
    ap.add_argument("--today", help="ISO date; defaults to the system date")
    ap.add_argument("--text", action="append", default=[], help="draft email/letter text to cross-check")
    ap.add_argument("--template", help="the unfilled company template: its own fixed figures are INFO, not ERROR")
    a = ap.parse_args(argv)
    try:
        with open(a.terms, encoding="utf-8") as fh:
            doc = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read {a.terms}: {exc}", file=sys.stderr)
        return 2
    shape = None
    if not isinstance(doc, dict):
        shape = "the file must be a JSON object with a \"terms\" object (see templates/offer-terms.json)"
    elif not isinstance(doc.get("terms", {}), dict):
        shape = "\"terms\" must be an object keyed by term name, each {value, source, approver, approved_on}"
    elif not isinstance(doc.get("contingencies", []), list) or not all(
            isinstance(c, dict) for c in doc.get("contingencies", [])):
        shape = "\"contingencies\" must be a list of objects, each {name, source, ...}"
    elif not isinstance(doc.get("band") or {}, dict) or not isinstance(doc.get("above_band_approval") or {}, dict):
        shape = "\"band\" and \"above_band_approval\" must be objects"
    if shape:
        print(f"error: {a.terms}: {shape}", file=sys.stderr)
        return 2
    today = parse_iso(a.today) if a.today else dt.date.today()
    if today is None:
        print(f"error: --today '{a.today}' is not an ISO date (YYYY-MM-DD)", file=sys.stderr)
        return 2
    terms = doc.get("terms", {})
    errors, warns, infos = [], [], []

    def val(key):
        entry = terms.get(key) or {}
        return entry.get("value") if isinstance(entry, dict) else None

    for key in REQUIRED:
        entry = terms.get(key)
        if not isinstance(entry, dict) or str(entry.get("value", "")).strip() in ("", "[OWNER TO CONFIRM]"):
            errors.append(f"{key}: missing - mark [OWNER TO CONFIRM] in the draft and ask the owner")
    for key, entry in terms.items():
        if not isinstance(entry, dict):
            errors.append(f"{key}: must be an object with value, source, approver")
            continue
        if str(entry.get("value", "")).strip() and not (str(entry.get("source", "")).strip() and str(entry.get("approver", "")).strip()):
            errors.append(f"{key}: has a value but no source or approver")
        blob = " ".join(str(entry.get(f, "")) for f in ("value", "source", "notes"))
        if HISTORY_RE.search(blob):
            errors.append(f"{key}: references current/past pay ('{HISTORY_RE.search(blob).group(0)}'). "
                          "Salary history may not be asked for or used; remove it and re-source from the band")
    for key in DATE_KEYS:
        if val(key) and not parse_iso(val(key)):
            errors.append(f"{key}: '{val(key)}' is not an ISO date (YYYY-MM-DD)")
    rb, sd = parse_iso(val("response_by") or ""), parse_iso(val("start_date") or "")
    if rb and rb < today:
        errors.append(f"response_by {rb} is already past (today {today})")
    if rb and sd and sd <= rb:
        errors.append(f"start_date {sd} is not after response_by {rb}")
    if sd and notice_check(doc, sd, today):
        warns.append(notice_check(doc, sd, today))

    base = to_number(val("base_pay") or "")
    band = doc.get("band") or {}
    if base is not None and band:
        lo, hi = to_number(band.get("min", "")), to_number(band.get("max", ""))
        if lo is None or hi is None or not band.get("approver"):
            errors.append("band: needs min, max and approver")
        elif base > hi:
            aba = doc.get("above_band_approval") or {}
            amount = to_number(aba.get("amount", "") or "")
            missing = [f for f in ("approver", "approved_on") if not str(aba.get(f, "")).strip()]
            if amount is None:
                missing.append("amount")
            if missing:
                errors.append(f"base_pay {base:,.0f} is above band max {hi:,.0f}: above_band_approval needs "
                              + ", ".join(missing) + " (escalate to the band approver; never counter above band)")
            elif base > amount:
                errors.append(f"base_pay {base:,.0f} is above the approved above-band amount {amount:,.0f} "
                              f"({aba.get('approver')}, {aba.get('approved_on')})")
            elif not parse_iso(aba.get("approved_on")):
                errors.append(f"above_band_approval.approved_on '{aba.get('approved_on')}' is not an ISO date")
        elif base < lo:
            warns.append(f"base_pay {base:,.0f} is below band min {lo:,.0f}")
    elif base is not None:
        warns.append("no band block in terms.json: the base cannot be checked against the approved band")

    var, ote = to_number(val("variable_target") or ""), to_number(val("ote") or "")
    if ote is not None:
        if base is None or var is None:
            errors.append("ote given without base_pay and variable_target")
        elif abs(base + var - ote) > 0.5:
            errors.append(f"ote {ote:,.0f} != base {base:,.0f} + variable {var:,.0f} = {base + var:,.0f}")
        if not val("commission_plan_text"):
            warns.append("sales offer with OTE but no commission_plan_text: carry the approved plan wording, do not summarise it")

    for i, c in enumerate(doc.get("contingencies", [])):
        name = str(c.get("name", "")).lower()
        if not c.get("source"):
            errors.append(f"contingency[{i}] '{c.get('name')}': no template source; contingency wording comes only from the template")
        if "background" in name or "credit" in name or "consumer report" in name:
            if not c.get("fcra_disclosure_on_record"):
                warns.append(f"contingency[{i}] background check: no standalone FCRA disclosure/authorisation on record. "
                             "It must precede procuring the report; flag to the owner")
        if "medical" in name or "health" in name or "physical exam" in name:
            if not c.get("post_offer") or not c.get("all_entrants_in_category"):
                errors.append(f"contingency[{i}] medical exam: must be post-offer and required of all entrants in the job category")

    currency = str(val("currency") or band.get("currency") or "").strip().upper()
    # Every numeric term is known money, not only MONEY_KEYS: a derived
    # monthly_base or an allowance term with source and approver clears it.
    known_money = {term_amount(e.get("value")) for e in terms.values() if isinstance(e, dict)} - {None}
    template_tokens = set()
    if a.template:
        try:
            template_tokens = {tok for _, tok in money_tokens(read_text(a.template))}
        except (OSError, zipfile.BadZipFile, KeyError, UnicodeDecodeError) as exc:
            print(f"error: cannot read template {a.template}: {exc}", file=sys.stderr)
            return 2
    known_dates = {parse_iso(val(k) or "") for k in DATE_KEYS} - {None}
    for path in a.text:
        try:
            text = read_text(path)
        except (OSError, zipfile.BadZipFile, KeyError) as exc:
            print(f"error: cannot read {path}: {exc}", file=sys.stderr)
            return 2
        except UnicodeDecodeError:
            print(f"error: {path} is not UTF-8 text. Pass the .docx itself (read from word/document.xml) "
                  "or a UTF-8 .md/.txt copy of the letter", file=sys.stderr)
            return 2
        for m, token in money_tokens(text):
            raw = m.group("num")
            cur = m.group("cur1") or m.group("cur2")
            is_k = bool(m.group("k"))
            if not cur and not is_k:
                if m.group("sep") not in WARN_BARE_SEPS:
                    continue  # bare number: phone, street, postcode, year, percentage
                n = parse_amount(raw)
                if n is not None and n not in known_money and token not in template_tokens:
                    warns.append(f"{path}: number '{token}' has no currency and matches no approved term - check it")
                continue
            n = parse_amount(raw)
            if n is None:
                continue
            if is_k:
                n = round(n * 1000, 2)
            if token in template_tokens:
                infos.append(f"{path}: figure '{token}' is fixed wording in the company template "
                             "(binding; not a term, not edited)")
                continue
            if cur and currency:
                allowed = currencies_of(cur)
                if currency not in allowed:
                    errors.append(f"{path}: figure '{token}' is in {'/'.join(sorted(allowed))}, "
                                  f"but the offer currency is {currency}")
                    continue
            if n not in known_money:
                errors.append(f"{path}: figure '{token}' does not match any approved term")
        for rx, fmt in DATE_TOKENS:
            for m in rx.finditer(text):
                d = parse_loose_date(m.group(1), fmt)
                if d and d not in known_dates:
                    warns.append(f"{path}: date '{m.group(1)}' is not start_date or response_by - check it is intended")

    for e in errors:
        print(f"ERROR {e}")
    for w in warns:
        print(f"WARN  {w}")
    for i in infos:
        print(f"INFO  {i}")
    print(f"{len(errors)} errors, {len(warns)} warnings")
    return 1 if errors else 0


def read_text(path):
    """Plain text for .md/.txt; for .docx the paragraph text of the body, headers and footers."""
    if not path.lower().endswith(".docx"):
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    lines = []
    with zipfile.ZipFile(path) as z:
        parts = sorted(n for n in z.namelist() if re.match(r"word/(document|header\d*|footer\d*)\.xml$", n))
        if "word/document.xml" not in parts:
            raise KeyError("word/document.xml not found: not a Word document")
        for name in parts:
            xml = z.read(name).decode("utf-8")
            for para in PARA.finditer(xml):
                lines.append("".join(html.unescape(t.group(2)) for t in TEXT.finditer(para.group(0))))
    return "\n".join(lines)


def notice_check(doc, start, today):
    notice_days = doc.get("notice_days")
    if isinstance(notice_days, (int, float)) and (start - today).days < notice_days:
        return (f"start_date {start} is {(start - today).days} days out but the candidate's stated notice is "
                f"{notice_days} days: the start date is not realistic")
    return None


if __name__ == "__main__":
    sys.exit(main())
