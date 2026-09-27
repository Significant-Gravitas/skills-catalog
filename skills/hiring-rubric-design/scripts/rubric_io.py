"""Shared parsing for rubric files made from templates/rubric.md.

Imported by validate_rubric.py and approve_rubric.py (same folder).
Stdlib only.
"""

import re

HEADER = ["criterion_id", "criterion", "outcome_supported", "requirement_ids", "evidence_sources",
          "anchor_1", "anchor_2", "anchor_3", "anchor_4", "not_assessed_rule", "confirm_method",
          "scorer", "weight"]
META_KEYS = ["role_slug", "version", "status", "approved_by", "approved_on", "approval_quote",
             "scale", "weighting", "loop_methods", "loop_reason", "allowed_terms"]
META_RE = re.compile(r"^([a-z_]+):[ \t]*(.*)$")


def split_row(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", s)]


def parse(text: str) -> dict:
    """Return {'meta': {...}, 'header': [...] or None, 'rows': [dict], 'table_line': int}."""
    meta: dict[str, str] = {}
    lines = text.splitlines()
    in_comment = False
    for line in lines:
        if line.startswith("## "):
            break
        if "<!--" in line:
            in_comment = True
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue
        m = META_RE.match(line)
        if m and m.group(1) in META_KEYS:
            meta[m.group(1)] = m.group(2).strip()

    header = None
    rows: list[dict] = []
    table_line = 0
    for i, line in enumerate(lines):
        if header is None:
            if line.strip().startswith("|"):
                cells = [c.lower() for c in split_row(line)]
                if "criterion_id" in cells:
                    header = cells
                    table_line = i + 1
            continue
        if not line.strip().startswith("|"):
            break
        cells = split_row(line)
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells if c):
            continue
        row = {h: (cells[k] if k < len(cells) else "") for k, h in enumerate(header)}
        row["_line"] = i + 1
        rows.append(row)
    return {"meta": meta, "header": header, "rows": rows, "table_line": table_line}


def set_meta(text: str, key: str, value: str) -> str:
    pattern = re.compile(rf"^{key}:[ \t]*.*$", re.M)
    if pattern.search(text):
        line = f"{key}: {value}".rstrip()
        # A function replacement, so a backslash in the owner's words is kept as written.
        return pattern.sub(lambda _: line, text, count=1)
    # insert after the first line (the title)
    first, _, rest = text.partition("\n")
    return f"{first}\n{key}: {value}\n{rest}"


def req_ids(cell: str) -> list[str]:
    return [x.strip() for x in re.split(r"[;,\s]+", cell or "") if x.strip()]
