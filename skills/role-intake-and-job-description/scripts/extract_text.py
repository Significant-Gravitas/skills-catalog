#!/usr/bin/env python3
"""Extract plain text from an old posting (DOCX, PDF, HTML, TXT or MD).

Usage:
  python3 scripts/extract_text.py <file> > /home/user/old.md

Input:  one file brought into the sandbox with
        read_workspace_file(file_id=..., save_to_path="/home/user/in/<name>").
Output: text on stdout, one paragraph per line; list items start with "- ";
        headings from DOCX heading styles start with "## ".
        Diagnostics go to stderr.
Needs:  nothing for DOCX, HTML, TXT and MD (stdlib). PDF needs pypdf
        (pre-flight: python3 -c "import pypdf" || pip install --user pypdf);
        if pypdf is missing it tries the pdftotext command.
Exit:   0 ok; 2 unreadable, unsupported, or a PDF with no text layer
        (scanned): ask the owner for a paste instead of guessing.
No network.
"""

import html.parser
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
MIN_CHARS_PER_PAGE = 100  # default (confirm with the owner): below this average a PDF is treated as scanned


def docx_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as zf:
            xml = zf.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError) as exc:
        raise ValueError(f"not a readable .docx ({exc})")
    root = ET.fromstring(xml)
    lines = []
    for p in root.iter(W + "p"):
        ppr = p.find(W + "pPr")
        style = ""
        is_list = False
        if ppr is not None:
            ps = ppr.find(W + "pStyle")
            if ps is not None:
                style = ps.get(W + "val", "")
            is_list = ppr.find(W + "numPr") is not None
        parts = []
        for node in p.iter():
            if node.tag == W + "t" and node.text:
                parts.append(node.text)
            elif node.tag == W + "tab":
                parts.append("\t")
            elif node.tag in (W + "br", W + "cr"):
                parts.append("\n")
        text = "".join(parts).strip()
        if not text:
            continue
        if style.lower().startswith("heading") or style.lower() == "title":
            text = "## " + text
        elif is_list or style.lower().startswith("list"):
            text = "- " + text
        lines.append(text)
    return "\n".join(lines)


class _HTML(html.parser.HTMLParser):
    BLOCK = {"p", "div", "li", "br", "h1", "h2", "h3", "h4", "tr", "section", "article", "ul", "ol"}

    def __init__(self):
        super().__init__()
        self.out: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript", "template"):
            self.skip += 1
        elif tag in self.BLOCK:
            self.out.append("\n")
            if tag == "li":
                self.out.append("- ")
            elif tag in ("h1", "h2", "h3", "h4"):
                self.out.append("## ")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript", "template") and self.skip:
            self.skip -= 1
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def html_text(path: Path) -> str:
    parser = _HTML()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    text = "".join(parser.out)
    lines = [re.sub(r"[ \t]+", " ", l).strip() for l in text.splitlines()]
    return "\n".join(l for l in lines if l and l not in ("-", "##"))


def pdf_text(path: Path) -> tuple[str, int]:
    try:
        import pypdf  # type: ignore
        reader = pypdf.PdfReader(str(path))
        pages = [(pg.extract_text() or "") for pg in reader.pages]
        return "\n".join(pages), len(pages)
    except ImportError:
        pass
    if shutil.which("pdftotext"):
        out = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True, timeout=60)
        if out.returncode == 0:
            pages = out.stdout.split("\f")
            return out.stdout, max(1, len([p for p in pages if p.strip()]) or len(pages))
    raise ValueError("PDF support missing: run  pip install --user pypdf  then retry, or ask for a paste")


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__, file=sys.stderr)
        return 2
    path = Path(sys.argv[1]).expanduser()
    if not path.is_file():
        print(f"error: {path} not found; save the upload with read_workspace_file(..., save_to_path=...) first", file=sys.stderr)
        return 2
    ext = path.suffix.lower()
    try:
        if ext == ".docx":
            text = docx_text(path)
        elif ext in (".html", ".htm"):
            text = html_text(path)
        elif ext in (".txt", ".md", ".markdown"):
            text = path.read_text(encoding="utf-8", errors="replace")
        elif ext == ".pdf":
            text, pages = pdf_text(path)
            if len(text.strip()) < MIN_CHARS_PER_PAGE * max(1, pages):
                print(f"error: scanned PDF, little or no text layer ({len(text.strip())} chars over {pages} page(s)); ask the owner for a paste", file=sys.stderr)
                return 2
        elif ext == ".doc":
            print("error: old .doc format; ask the owner to save as .docx or paste the text", file=sys.stderr)
            return 2
        else:
            print(f"error: unsupported file type '{ext}'; ask for .docx, .pdf, .html, .txt or a paste", file=sys.stderr)
            return 2
    except (ValueError, OSError, ET.ParseError, subprocess.SubprocessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    sys.stdout.write(text.strip() + "\n")
    print(f"extracted {len(text.strip())} chars from {path.name}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
