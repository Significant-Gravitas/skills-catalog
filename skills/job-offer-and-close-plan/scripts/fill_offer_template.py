#!/usr/bin/env python3
"""Fill the company's offer-letter template from approved terms. Touches placeholders only.

Usage (cd ~/skills/job-offer-and-close-plan first):

  python3 scripts/fill_offer_template.py <template.docx|.md|.txt> terms.json <out>

  - Placeholders are {{key}} (spaces inside the braces are allowed). Keys are
    the names under "terms" in terms.json (see templates/offer-terms.json).
  - A key that is missing, empty, or lacks a source or approver is written as
    "[OWNER TO CONFIRM: key]" and reported. It is never guessed.
  - A term whose value, source or notes mention current or past pay is refused
    (scripts/pay_history.py catches common phrasings; the rule is yours to apply).
  - Text outside placeholders is not edited: binding clauses survive
    byte-for-byte. In .docx, placeholders split across Word runs are merged
    into the first run of the placeholder; formatting of that run is kept.
  - The output name must contain DRAFT; if it does not, "-DRAFT" is added.

Pure standard library (zipfile + regex), so no install is needed.
Exit: 0 all placeholders filled, 1 some left [OWNER TO CONFIRM], 2 bad input,
4 template has no placeholders (ask for the placeholder version or fill by hand
with the owner).
"""

import html
import json
import os
import re
import sys
import zipfile

from pay_history import HISTORY_RE

PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}")
PARA = re.compile(r"<w:p[ >].*?</w:p>", re.S)
TEXT = re.compile(r"(<w:t(?: [^>]*)?>)(.*?)(</w:t>)", re.S)


def resolve(terms):
    """Map key -> (text or None, reason)."""
    out = {}
    for key, entry in terms.items():
        if not isinstance(entry, dict):
            out[key] = (None, "not an object")
            continue
        value = str(entry.get("value", "")).strip()
        if not value or value.upper().startswith("[OWNER TO CONFIRM"):
            out[key] = (None, "no value")
        elif not str(entry.get("source", "")).strip() or not str(entry.get("approver", "")).strip():
            out[key] = (None, "no source or approver")
        elif HISTORY_RE.search(" ".join([value, str(entry.get("source", "")), str(entry.get("notes", ""))])):
            out[key] = (None, "refers to current/past pay - refused")
        else:
            out[key] = (value, "ok")
    return out


def substitute(text, resolved, report):
    def repl(m):
        key = m.group(1)
        value, reason = resolved.get(key, (None, "not in terms.json"))
        report.append((key, "filled" if value is not None else reason))
        return value if value is not None else f"[OWNER TO CONFIRM: {key}]"
    return PLACEHOLDER.sub(repl, text)


def fill_paragraph_xml(para, resolved, report):
    nodes = list(TEXT.finditer(para))
    if not nodes:
        return para
    texts = [html.unescape(n.group(2)) for n in nodes]
    joined = "".join(texts)
    if not PLACEHOLDER.search(joined):
        return para
    # character offset -> node index
    owner = []
    for i, t in enumerate(texts):
        owner.extend([i] * len(t))
    new_texts = list(texts)
    # walk placeholders right-to-left so offsets stay valid
    for m in reversed(list(PLACEHOLDER.finditer(joined))):
        start, end = m.start(), m.end()
        first, last = owner[start], owner[end - 1]
        offsets = [sum(len(t) for t in texts[:i]) for i in range(len(texts))]
        replacement = substitute(m.group(0), resolved, report)
        if first == last:
            s0 = start - offsets[first]
            e0 = end - offsets[first]
            new_texts[first] = new_texts[first][:s0] + replacement + new_texts[first][e0:]
        else:
            s0 = start - offsets[first]
            new_texts[first] = new_texts[first][:s0] + replacement
            for mid in range(first + 1, last):
                new_texts[mid] = ""
            e0 = end - offsets[last]
            new_texts[last] = new_texts[last][e0:]
    pieces, pos = [], 0
    for n, t in zip(nodes, new_texts):
        pieces.append(para[pos:n.start()])
        open_tag = n.group(1)
        if 'xml:space="preserve"' not in open_tag and (t[:1].isspace() or t[-1:].isspace()):
            open_tag = open_tag[:-1] + ' xml:space="preserve">'
        pieces.append(open_tag + html.escape(t, quote=False) + n.group(3))
        pos = n.end()
    pieces.append(para[pos:])
    return "".join(pieces)


def fill_docx(src, dst, resolved, report):
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if re.match(r"word/(document|header\d*|footer\d*)\.xml$", item.filename):
                xml = data.decode("utf-8")
                xml = PARA.sub(lambda m: fill_paragraph_xml(m.group(0), resolved, report), xml)
                data = xml.encode("utf-8")
            zout.writestr(item, data)


def main(argv):
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    template, terms_path, out = argv
    try:
        with open(terms_path, encoding="utf-8") as fh:
            resolved = resolve(json.load(fh).get("terms", {}))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: cannot read {terms_path}: {exc}", file=sys.stderr)
        return 2
    base, ext = os.path.splitext(out)
    if "DRAFT" not in os.path.basename(out):
        out = f"{base}-DRAFT{ext}"
    report = []
    try:
        if template.lower().endswith(".docx"):
            fill_docx(template, out, resolved, report)
        else:
            with open(template, encoding="utf-8") as fh:
                text = fh.read()
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(substitute(text, resolved, report))
    except (OSError, zipfile.BadZipFile, UnicodeDecodeError) as exc:
        print(f"error: cannot process template {template}: {exc}. Ask for the .docx or a text copy.", file=sys.stderr)
        return 2
    if not report:
        os.remove(out)
        print("STOP: the template has no {{placeholders}}. Ask the owner for the placeholder "
              "version; do not retype binding clauses.", file=sys.stderr)
        return 4
    missing = [(k, r) for k, r in report if r != "filled"]
    print(f"wrote {out}")
    print(f"placeholders: {len(report)} found, {len(report) - len(missing)} filled, {len(missing)} left for the owner")
    for key, reason in missing:
        print(f"  [OWNER TO CONFIRM: {key}] - {reason}")
    unused = sorted(set(k for k, (v, _) in resolved.items() if v is not None) - {k for k, _ in report})
    if unused:
        print("approved terms with no placeholder in the template (check nothing is missing from the letter): "
              + ", ".join(unused))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
