#!/usr/bin/env python3
"""Turn a markdown job description into a .docx the owner can review in Word or Docs.

Usage:
  python3 scripts/to_docx.py <jd.md> <out.docx>

Input:  markdown with #/##/### headings, "- " or "* " bullets, **bold**,
        plain paragraphs and simple | tables |.
Output: a .docx. Every "[OWNER TO CONFIRM]" and "OWNER TO CONFIRM" run is
        highlighted yellow so open items stay visible. Tables become one
        paragraph per row with cells separated by " | ".
Exit:   0 written, 2 unreadable input or unwritable output.
Stdlib only (zipfile + XML), no pandoc or python-docx needed, no network.
"""

import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
DOC_HEAD = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>')
DOC_TAIL = '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1134" w:right="1134" w:bottom="1134" w:left="1134" w:header="0" w:footer="0" w:gutter="0"/></w:sectPr></w:body></w:document>'
SIZES = {1: 32, 2: 28, 3: 24}  # half-points: 16pt, 14pt, 12pt
OPEN_RE = re.compile(r"(\[?OWNER TO CONFIRM\]?)")


def runs(text: str, bold: bool = False, size: int | None = None) -> str:
    out = []
    for chunk in re.split(r"(\*\*.+?\*\*)", text):
        if not chunk:
            continue
        b = bold
        if chunk.startswith("**") and chunk.endswith("**"):
            chunk, b = chunk[2:-2], True
        chunk = chunk.replace("`", "")
        for piece in OPEN_RE.split(chunk):
            if not piece:
                continue
            props = []
            if b:
                props.append("<w:b/>")
            if size:
                props.append(f'<w:sz w:val="{size}"/>')
            if OPEN_RE.fullmatch(piece):
                props.append('<w:highlight w:val="yellow"/>')
            rpr = f"<w:rPr>{''.join(props)}</w:rPr>" if props else ""
            out.append(f'<w:r>{rpr}<w:t xml:space="preserve">{escape(piece)}</w:t></w:r>')
    return "".join(out)


def para(inner: str, indent: bool = False) -> str:
    ppr = '<w:pPr><w:ind w:left="360" w:hanging="360"/></w:pPr>' if indent else ""
    return f"<w:p>{ppr}{inner}</w:p>"


def convert(md: str) -> str:
    body = []
    for raw in md.splitlines():
        line = raw.rstrip()
        if not line.strip() or re.fullmatch(r"\s*\|?\s*:?-{3,}.*", line) or line.strip().startswith("<!--"):
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", line)
        if m:
            body.append(para(runs(m.group(2), bold=True, size=SIZES[len(m.group(1))])))
            continue
        m = re.match(r"^\s*[-*]\s+(\[[ xX]\]\s+)?(.*)$", line)
        if m:
            box = "☐ " if m.group(1) and m.group(1).strip() == "[ ]" else ("☑ " if m.group(1) else "• ")
            body.append(para(runs(box + m.group(2)), indent=True))
            continue
        if line.lstrip().startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            body.append(para(runs(" | ".join(cells))))
            continue
        body.append(para(runs(line.strip())))
    return DOC_HEAD + "".join(body) + DOC_TAIL


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    src, dst = Path(sys.argv[1]).expanduser(), Path(sys.argv[2]).expanduser()
    try:
        md = src.read_text(encoding="utf-8")
        dst.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", CONTENT_TYPES)
            zf.writestr("_rels/.rels", RELS)
            zf.writestr("word/document.xml", convert(md))
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"wrote {dst} ({dst.stat().st_size} bytes); open items highlighted: {len(OPEN_RE.findall(md))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
