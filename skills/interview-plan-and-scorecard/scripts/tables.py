"""Small shared reader for the CSV / markdown-table inputs this skill uses.

Imported by check_loop.py, make_scorecards.py and question_lint.py. Standard
library only, so it runs in the sandbox without installs.

A table can be:
  * a .csv file with a header row, or
  * a .md / .txt file holding a pipe table (the first table with a header row
    and a |---| separator is used).

Header names are normalised: lower case, spaces and hyphens become "_", so
"Criterion ID" and "criterion-id" both read as "criterion_id".
"""

import csv
import hashlib
import re
import unicodedata
import sys
from pathlib import Path


def norm(name: str) -> str:
    return re.sub(r"[\s\-]+", "_", str(name).strip().lower())


def read_table(path: str) -> list[dict]:
    p = Path(path)
    if not p.is_file():
        fail(f"file not found: {path}")
    text = p.read_text(encoding="utf-8-sig")
    if p.suffix.lower() == ".csv":
        rows = list(csv.DictReader(text.splitlines()))
        rows = [{norm(k): (v or "").strip() for k, v in r.items() if k} for r in rows]
        # A sheet export often ends in ",,,,,," rows; drop rows with every cell blank.
        return [r for r in rows if any(r.values())]
    return [r for r in _pipe_table(text, path) if any(r.values())]


def _pipe_table(text: str, path: str) -> list[dict]:
    lines = [ln.strip() for ln in text.splitlines()]
    for i in range(len(lines) - 1):
        if lines[i].startswith("|") and re.match(r"^\|?\s*:?-{3,}", lines[i + 1]):
            header = [norm(c) for c in _cells(lines[i])]
            rows = []
            for ln in lines[i + 2:]:
                if not ln.startswith("|"):
                    break
                cells = _cells(ln)
                cells += [""] * (len(header) - len(cells))
                rows.append(dict(zip(header, (c.strip() for c in cells))))
            return rows
    fail(f"no pipe table with a header row found in {path}")
    return []


def _cells(line: str) -> list[str]:
    line = line.strip().strip("|")
    return [c.strip() for c in re.split(r"(?<!\\)\|", line)]


def split_ids(value: str) -> list[str]:
    return [v.strip() for v in re.split(r"[;,]", value or "") if v.strip()]


def slug(value: str) -> str:
    """ASCII file-name slug. Accents are folded (José Núñez -> jose-nunez).
    A name with no Latin letters (李明) gets a stable id from a short hash of
    the name ("id-<8 hex>"), so two such names never share a slug. Callers
    that write one file per person must still check for collisions."""
    value = str(value).strip()
    folded = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^a-z0-9]+", "-", folded.lower()).strip("-")
    if s:
        return s
    if value:
        return "id-" + hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
    return "unnamed"


def fail(message: str, code: int = 2) -> None:
    print(f"error: {message}", file=sys.stderr)
    sys.exit(code)
