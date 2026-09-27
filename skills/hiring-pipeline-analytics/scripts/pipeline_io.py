"""Shared helpers for the hiring-pipeline-analytics scripts (imported, not run).

- read_text(): UTF-8 first; a Windows-1252 / Latin-1 file is read with a
  one-line note on stderr instead of a UnicodeDecodeError traceback.
- read_csv(): comma, semicolon or tab delimited; header names are normalised (lower case, non-alphanumerics -> "_"),
  protected columns are dropped and reported, rows keep their line number.
- parse_date(): ISO first; a few unambiguous written forms; ambiguous numeric
  dates (03/04/2026) are refused unless dayfirst/monthfirst is given.
- funnel_level(): maps the owner's stage wording to the funnel ladder using
  DEFAULT_STAGES plus an optional stage map; unmapped stages return None and
  are listed for the owner - never guessed.
"""

import csv
import datetime as dt
import io as _io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROTECTED_LIST = os.path.join(HERE, "..", "references", "protected-columns.txt")
PROTECTED_RE = re.compile(
    r"gender|sex\b|^sex|race|racial|ethnic|veteran|disab|dob\b|birth|^age$|_age$|^age_|marital|religio|"
    r"nationality|citizenship_country|eeo|self_?id|pronoun|photo|pregnan|orientation|health|medical|"
    r"salary_history|current_salary|current_pay|previous_salary|prior_salary",
    re.I)

LADDER = ["entered", "screened", "in_loop", "offer", "hired"]
LEVEL = {name: i for i, name in enumerate(LADDER)}
TERMINAL = {"rejected", "withdrew", "declined_offer"}
DEFAULT_STAGES = {
    "entered": ["sourced", "applied", "new", "lead", "contacted", "application review", "inbound",
                "referred", "referral", "replied", "application", "new applicant"],
    "prospect": ["prospect", "prospects", "sourcing"],
    "screened": ["screen", "screened", "screening", "phone screen", "recruiter screen", "hm screen",
                 "hiring manager screen", "phone interview", "intro call"],
    "in_loop": ["interview", "interviewing", "onsite", "on-site", "loop", "in loop", "panel", "final",
                "final round", "technical interview", "take-home", "take home", "assessment",
                "face to face", "debrief"],
    "offer": ["offer", "offer out", "offer extended", "offer sent", "verbal offer", "offer stage", "verbal"],
    "hired": ["hired", "accepted", "offer accepted", "signed", "closed won", "closed - hired"],
    "rejected": ["rejected", "archived", "not a fit", "declined by us", "pass", "passed", "not selected"],
    "withdrew": ["withdrew", "withdrawn", "candidate withdrew", "dropped out", "not interested", "ghosted"],
    "declined_offer": ["offer declined", "declined offer", "declined", "offer rejected"],
}
TRUTHY = {"1", "true", "yes", "y", "x", "prospect"}


def norm_header(name):
    return re.sub(r"[^a-z0-9]+", "_", (name or "").strip().lower()).strip("_")


def protected_names():
    names = set()
    if os.path.exists(PROTECTED_LIST):
        with open(PROTECTED_LIST, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    names.add(norm_header(line))
    return names


def is_protected(header):
    h = norm_header(header)
    return h in protected_names() or bool(PROTECTED_RE.search(h))


NOT_UTF8_WARNED = set()


def read_text(path):
    """File text as UTF-8 (BOM allowed). A file that is not UTF-8 (an Excel
    "CSV (Comma delimited)" save on Windows is Windows-1252) is read as
    Windows-1252, falling back to Latin-1, with one line on stderr - never a
    traceback."""
    with open(path, "rb") as fh:
        data = fh.read()
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        pass
    try:
        text, enc = data.decode("cp1252"), "Windows-1252"
    except UnicodeDecodeError:
        text, enc = data.decode("latin-1"), "Latin-1"
    if path not in NOT_UTF8_WARNED:
        NOT_UTF8_WARNED.add(path)
        print(f"note: {os.path.basename(path)} was not UTF-8; read as {enc} - check accented names, "
              "and next time save the export as 'CSV UTF-8'", file=sys.stderr)
    return text


def sniff_delimiter(sample, ext=""):
    """Tab, semicolon (Excel in pt-PT / de-DE locales) or comma, from the header line."""
    if ext == ".tsv":
        return "\t"
    head = sample.splitlines()[0] if sample.splitlines() else sample
    counts = {d: head.count(d) for d in ("\t", ";", ",")}
    best = max(counts, key=lambda d: counts[d])
    return best if counts[best] > counts[","] else ","


def csv_rows(text, delimiter=","):
    """All rows of CSV text (quoted multi-line fields kept)."""
    return list(csv.reader(_io.StringIO(text, newline=""), delimiter=delimiter))


def read_csv(path, dropped=None):
    """Return rows (dicts with normalised keys + '_line'). Protected columns are removed."""
    if not path or not os.path.exists(path):
        return []
    text = read_text(path)
    reader = iter(csv_rows(text, sniff_delimiter(text[:4096])))
    try:
        header = next(reader)
    except StopIteration:
        return []
    keys = [norm_header(h) for h in header]
    drop = {i for i, h in enumerate(header) if is_protected(h)}
    if dropped is not None:
        for i in sorted(drop):
            dropped.append(f"{os.path.basename(path)}:{header[i]}")
    rows = []
    for n, raw in enumerate(reader, start=2):
        if not any(c.strip() for c in raw):
            continue
        row = {keys[i]: (raw[i].strip() if i < len(raw) else "") for i in range(len(keys)) if i not in drop}
        row["_line"] = n
        rows.append(row)
    return rows


def first(row, *names):
    for name in names:
        value = row.get(name)
        if value not in (None, ""):
            return value
    return ""


MONTHS = {m: i for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep",
                                      "oct", "nov", "dec"], start=1)}


def parse_date(value, order=None):
    """-> date or None. order: None (refuse ambiguous), 'dayfirst', 'monthfirst'."""
    s = (value or "").strip()
    if not s:
        return None
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})", s)
    if m:
        try:
            return dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return None
    m = re.match(r"^(\d{1,2}) ([A-Za-z]{3})[a-z]*\.?,? (\d{4})$", s)
    if m and m.group(2).lower() in MONTHS:
        return _safe(int(m.group(3)), MONTHS[m.group(2).lower()], int(m.group(1)))
    m = re.match(r"^([A-Za-z]{3})[a-z]*\.? (\d{1,2}),? (\d{4})$", s)
    if m and m.group(1).lower() in MONTHS:
        return _safe(int(m.group(3)), MONTHS[m.group(1).lower()], int(m.group(2)))
    m = re.match(r"^(\d{1,2})[/.](\d{1,2})[/.](\d{4})", s)
    if m:
        a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if a > 12 >= b:
            return _safe(y, b, a)
        if b > 12 >= a:
            return _safe(y, a, b)
        if order == "dayfirst":
            return _safe(y, b, a)
        if order == "monthfirst":
            return _safe(y, a, b)
    return None


def _safe(y, mth, d):
    try:
        return dt.date(y, mth, d)
    except ValueError:
        return None


def business_days(start, end):
    """Weekdays after start up to and including end (0 if end <= start)."""
    if not start or not end or end <= start:
        return 0
    days, cur = 0, start
    while cur < end:
        cur += dt.timedelta(days=1)
        if cur.weekday() < 5:
            days += 1
    return days


def load_stage_map(path):
    mapping = {}
    for row in read_csv(path):
        user, funnel = first(row, "user_stage", "stage"), first(row, "funnel_stage", "maps_to")
        if user and funnel:
            mapping[user.strip().lower()] = funnel.strip().lower()
    return mapping


def classify_stage(stage, stage_map=None):
    """-> one of LADDER, 'prospect', TERMINAL member, or None (unmapped)."""
    s = (stage or "").strip().lower()
    if not s:
        return None
    if stage_map and s in stage_map:
        return stage_map[s]
    for bucket, words in DEFAULT_STAGES.items():
        if s in words:
            return bucket
    return None


def truthy(value):
    return (value or "").strip().lower() in TRUTHY


def read_prefs(path):
    prefs = {}
    if path and os.path.exists(path):
        for line in read_text(path).splitlines():
            if ":" in line and not line.lstrip().startswith("#"):
                k, v = line.split(":", 1)
                prefs[k.strip().lower()] = v.strip()
    return prefs


def parse_stalled_bar(text, default=(5, "business")):
    """'2 business days' -> (2, 'business'); '7 days' -> (7, 'calendar')."""
    m = re.match(r"\s*(\d+)\s*(business|working)?", text or "")
    if not m:
        return default
    return int(m.group(1)), "business" if m.group(2) else "calendar"
