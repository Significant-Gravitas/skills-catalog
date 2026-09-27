"""Shared helpers for the resume-screening scripts (imported, not run).

Stdlib only. Keep file formats here so every script agrees:
  manifest.csv   id,source_file,format,pages,chars,parse_status,hidden_chars,injection_hits,name_hint,note
  criteria.json  {"rubric": {...}, "criteria": [{"id","text","must","resume_screenable"}]}
  records/<id>.json  {"id","rubric_version","rows":[{"criterion_id","result","quote","location","note"}],
                      "interview_questions":[...],"needs_a_look":false,"needs_a_look_reason":""}
  matrix.csv     candidate_id,criterion_id,criterion,must,result,sofia_label,quote,location,note,quote_check
"""

import csv
import json
import re
import unicodedata
from pathlib import Path

MANIFEST_FIELDS = ["id", "source_file", "format", "pages", "chars", "parse_status",
                   "hidden_chars", "injection_hits", "name_hint", "note"]
MATRIX_FIELDS = ["candidate_id", "criterion_id", "criterion", "must", "result", "sofia_label",
                 "quote", "location", "note", "quote_check"]
RESULTS = ("EVIDENCE FOUND", "EVIDENCE MISSING", "CONFIRM IN INTERVIEW")
# Sofia's labels for the same three states (see references/persona-vocabulary.md).
SOFIA_LABEL = {
    "EVIDENCE FOUND": "FACT",
    "EVIDENCE MISSING": "UNKNOWN (not stated)",
    "CONFIRM IN INTERVIEW": "UNKNOWN (confirm in interview)",
}

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+|any\s+|the\s+)?(previous|prior|above|earlier)\s+(instructions?|prompts?|rules)",
    r"disregard\s+(all\s+|any\s+|the\s+)?(previous|prior|above|earlier)",
    r"\byou\s+are\s+(now\s+)?(an?\s+)?(ai|assistant|language model|llm|screener|chatgpt|gpt|recruit\w* (bot|assistant))\b",
    r"\b(system|developer)\s+prompt\b",
    r"\b(rank|rate|score|mark|grade)\s+(this|the)\s+(candidate|applicant|resume|cv)\b",
    r"\b(highest|top|maximum|perfect)\s+(score|rank|rating|candidate)\b",
    r"\b(recommend|advance|shortlist|hire)\s+(this|the)\s+(candidate|applicant)\b",
    r"\bevidence\s+found\s+(for|on)\s+(all|every)\b",
    r"\bnote\s+to\s+(the\s+)?(ai|llm|chatgpt|model|screener|reviewer bot)s?\b",
    r"\bthis\s+candidate\s+(is|should\s+be)\s+(the\s+)?(best|perfect|ideal|top|strongest)\b",
    r"<\s*/?\s*(system|instructions?|prompt)\s*>",
]
_INJ = [re.compile(p, re.I) for p in INJECTION_PATTERNS]


def injection_hits(text: str) -> list[str]:
    return [m.group(0) for p in _INJ for m in [p.search(text)] if m]


# Role and business words that appear in ATS file names ("Billing_Operations_Lead.txt")
# and on the job-title line under a name; a line holding one is never a name.
ROLE_WORDS = {
    "billing", "operations", "operation", "ops", "lead", "leader", "manager", "management", "sales",
    "analyst", "finance", "financial", "engineer", "engineering", "developer", "designer", "director",
    "head", "senior", "junior", "principal", "staff", "associate", "assistant", "coordinator",
    "specialist", "consultant", "officer", "executive", "account", "accounts", "accounting",
    "accountant", "support", "customer", "success", "marketing", "product", "project", "program",
    "data", "software", "hr", "people", "recruiter", "recruiting", "candidate", "applicant",
    "role", "job", "position", "cover", "letter", "portfolio", "profile", "form", "submission",
    "admin", "administrator", "controller", "payroll", "revenue", "credit", "collections", "team",
    "remote", "hybrid", "onsite", "intern", "internship", "contract", "temp", "full", "time", "part",
    "clerk", "representative", "supervisor", "technician", "bookkeeper", "auditor", "agent",
    "experience", "education", "skills", "summary", "objective", "contact", "references",
}
# Lowercase particles inside names ("Ana de la Cruz", "Ludwig van Beethoven").
NAME_PARTICLES = {"de", "del", "della", "dela", "di", "da", "das", "do", "dos", "du", "la", "le", "van",
                  "von", "der", "den", "ter", "ten", "bin", "binti", "ibn", "al", "el", "y", "e", "st"}
# CV header words that are never a name ("BIO-DATA", "Personal Details", "About Me").
HEADER_WORDS = {"bio", "biodata", "bio-data", "personal", "details", "particulars", "information", "info",
                "about", "overview", "statement", "curriculum", "vitae", "résumé"}
HEADER_LINE = re.compile(r"(?i)\W*(curriculum\s+vitae|r[eé]sum[eé]|cv|profile|bio[- ]?data|"
                         r"personal\s+(details|information|data|profile|particulars|statement)|about(\s+me)?|"
                         r"contact\s+(details|information|info)|overview|summary|candidate\s+profile)[\s:.-]*")
NAME_LABEL = re.compile(r"(?i)^\W*(?:full\s+name|candidate(?:['’]?s)?\s+name|applicant(?:['’]?s)?\s+name|name)\s*[:\-–]\s*(.+?)\s*$")
PRONOUN_TAG = re.compile(r"\(\s*(she|he|they|ze|xe)\s*/\s*\w+(\s*/\s*\w+)?\s*\)", re.I)
CREDENTIALS = re.compile(r"(?:,\s*(?:CPA|MBA|ACCA|ACA|CIMA|CMA|CFA|CIA|CISA|PMP|PhD|Ph\.D\.?|MSc|BSc|BA|MA|JD|SHRM-\w+|PHR|SPHR|FCCA|CA)|,?\s+(?:Jr|Sr|II|III|IV))\.?\s*$")


# Letters that carry no combining mark in Unicode but are read as a base letter with an accent.
_FOLD_EXTRA = str.maketrans("ŁłØøĐđĦħıŦŧĿŀ", "LlOoDdHhiTtLl")


def fold(s: str) -> str:
    """Strip accents: 'García' -> 'Garcia', 'Nguyễn' -> 'Nguyen', 'Łukasz' -> 'Lukasz'."""
    s = "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c))
    return s.translate(_FOLD_EXTRA)


def name_key(s: str) -> str:
    """Accent-free, lower-case, punctuation-free form of a name: 'Pérez, José' -> 'perez jose'."""
    s = fold(unicodedata.normalize("NFKC", s or "")).lower()
    return re.sub(r"[\W_]+", " ", s).strip()


def same_name(a: str, b: str) -> bool:
    """True when two names are the same words, ignoring accents, case, punctuation and order
    ('Jose Perez' == 'José Pérez' == 'PEREZ, Jose'). 'Ann Lee' != 'Joann Leeds'."""
    ka, kb = name_key(a), name_key(b)
    return bool(ka) and (ka == kb or sorted(ka.split()) == sorted(kb.split()))


def name_in_lines(name: str, lines: list[str]) -> bool:
    """Do-not-contact test: the listed name appears as whole words (accents and case ignored)
    in one of the lines, or a line holds exactly the same words in another order
    ('WONG, CHRIS'). A longer name that only contains it ('Joann Leeds' for 'Ann Lee',
    'Chris Wongsakul' for 'Chris Wong') does not match."""
    k = name_key(name)
    if not k:
        return False
    want = sorted(k.split())
    pat = re.compile(r"(?<!\w)" + re.escape(k) + r"(?!\w)")
    for line in lines:
        lk = name_key(line)
        if pat.search(lk) or (len(want) > 1 and sorted(lk.split()) == want):
            return True
    return False


def clean_name_line(line: str) -> str:
    """Drop a pronoun tag and trailing credentials from a name line."""
    line = PRONOUN_TAG.sub("", line or "").strip()
    for _ in range(4):
        new = CREDENTIALS.sub("", line).strip().rstrip(",").strip()
        if new == line:
            break
        line = new
    return line


def looks_like_name(line: str, allow_single: bool = False) -> bool:
    """A 1-6 word personal name: capitalised or ALL-CAPS words, lowercase particles allowed,
    no digits, no separators, no role words ("Billing Analyst" is never a name)."""
    line = clean_name_line(line)
    if not line or re.search(r"[\d|@:/•;]", line):
        return False
    words = line.split()
    if not (2 if not allow_single else 1) <= len(words) <= 6:
        return False
    caps = 0
    for w in words:
        wl = fold(w).lower().strip(".,")
        if wl in ROLE_WORDS or wl in {"resume", "curriculum", "vitae", "cv", "page"} or wl in HEADER_WORDS:
            return False
        if w in NAME_PARTICLES:
            continue
        if not (w[0].isupper() and all(c.isalpha() or c in "'’.-" for c in w)):
            return False
        caps += 1
    return caps >= 1 and words[0] not in NAME_PARTICLES


def name_hint(text: str) -> str:
    """The name line near the top, cleaned. A labelled line ('Name: ...', 'Full name: ...')
    in the first 10 lines wins. Header words ('Resume', 'CURRICULUM VITAE', 'BIO-DATA',
    'Personal Details', 'About Me') and lines ending in ':' are skipped. A single word counts
    only on the first real line. Returns '' when none is found."""
    lines = [l.strip() for l in (text or "").splitlines() if l.strip()]
    for line in lines[:10]:
        m = NAME_LABEL.match(line)
        if m and looks_like_name(m.group(1), allow_single=True):
            return clean_name_line(m.group(1))
    seen = 0
    for line in lines[:5]:
        if HEADER_LINE.fullmatch(line) or line.endswith(":"):
            continue
        if looks_like_name(line, allow_single=(seen == 0)):
            return clean_name_line(line)
        seen += 1
        if seen >= 3:
            break
    return ""


def norm_text(s: str) -> str:
    """Normalise for quote matching: unicode, quotes, dashes, whitespace, case."""
    s = unicodedata.normalize("NFKC", s or "")
    s = (s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
          .replace("–", "-").replace("—", "-").replace("…", "..."))
    s = re.sub(r"[•●▪‣⁃]", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def read_csv(path) -> tuple[list[dict], list[str]]:
    with Path(path).expanduser().open(encoding="utf-8-sig", newline="") as fh:
        r = csv.DictReader(fh)
        return list(r), list(r.fieldnames or [])


def write_csv(path, rows: list[dict], fields: list[str]) -> None:
    p = Path(path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def load_criteria(path) -> dict:
    data = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    if "criteria" not in data or not data["criteria"]:
        raise ValueError("criteria.json has no criteria; re-run find_rubric.py --emit-criteria")
    return data


def id_key(cid: str) -> tuple:
    m = re.match(r"([A-Za-z]*)-?(\d+)$", cid or "")
    return (m.group(1), int(m.group(2))) if m else (cid, 0)
