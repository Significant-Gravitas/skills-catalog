#!/usr/bin/env python3
"""Render a markdown posting to paste-ready HTML and plain text.

Usage (cd ~/skills/job-description-drafting first):
    python3 scripts/render_posting.py <posting-vN.md> [--draft]

Output: writes <posting-vN>.html (basic tags only: h1, h2, h3, p, ul, li,
        strong, em, a) and <posting-vN>.txt next to the input, then prints
        both paths. ATS rich-text editors lose markdown, so paste the HTML
        into rich-text fields and the TXT into plain fields.
        HTML comments and lines starting with "Cut for language:",
        "Still UNKNOWN:" or "Internal:" are internal notes and are left out.
Paste-ready check: unresolved "[OWNER TO CONFIRM ...]" fields, "<...>"
        template placeholders and a "draft pending calibration" banner are
        counted. If there are any, it prints
        "WARNING: <n> unresolved fields; not paste-ready" with each one, and
        writes nothing (exit 1). With --draft it writes both files anyway,
        stamped "DRAFT - NOT PASTE-READY (<n> unresolved fields)" at the top,
        and exits 0; deliver those only labelled as a draft.
        A markdown autolink ("<jobs@acme.example>", "<https://acme.example/jobs>")
        is a link, not a placeholder: it renders as a mailto/http link.
Exit:   0 written; 1 unresolved fields and no --draft; 2 unreadable or empty
        input (nothing to render).
Stdlib only, no network.
"""

import html
import re
import sys
from pathlib import Path

INTERNAL = ("cut for language:", "still unknown:", "internal:", "not posted anywhere")
AUTOLINK = r"(?:https?://[^<>\s]+|mailto:[^<>\s]+|[\w.+-]+@[\w-]+(?:\.[\w-]+)+)"


def _autolink(m):
    target = html.unescape(m.group(1))
    href = target if re.match(r"^(https?|mailto):", target) else "mailto:" + target
    return f'<a href="{html.escape(href)}">{html.escape(target.replace("mailto:", "", 1), quote=False)}</a>'


def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    s = re.sub(r"&lt;(" + AUTOLINK + r")&gt;", _autolink, s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", s)
    return s


def plain(s: str) -> str:
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r"\1 (\2)", s)
    s = re.sub(r"<(" + AUTOLINK + r")>", lambda m: m.group(1).replace("mailto:", "", 1), s)
    return s.replace("**", "").replace("*", "").replace("`", "")


UNRESOLVED = re.compile(r"\[OWNER TO CONFIRM[^\]]*\]|<(?!" + AUTOLINK + r">)[^<>\n]{1,80}>|draft pending calibration", re.I)


def main(argv):
    draft = "--draft" in argv
    argv = [a for a in argv if a != "--draft"]
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    src = Path(argv[1]).expanduser()
    try:
        text = src.read_text(encoding="utf-8").replace("\r\n", "\n")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: cannot read {src}: {exc}", file=sys.stderr)
        return 2
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    public = [ln for ln in text.splitlines()
              if not any(ln.strip().lstrip(">").strip().lower().startswith(p) for p in INTERNAL)]
    if not any(ln.strip().lstrip(">").strip() for ln in public):
        print(f"error: {src} has no posting text to render (empty, or only comments and internal notes)", file=sys.stderr)
        return 2
    unresolved = [m.group(0) for ln in public for m in UNRESOLVED.finditer(ln)]
    if unresolved:
        print(f"WARNING: {len(unresolved)} unresolved fields; not paste-ready")
        for u in unresolved:
            print(f"  {u}")
        if not draft:
            print("nothing written; resolve them, or rerun with --draft for a stamped draft copy")
            return 1
    out_html, out_txt, in_list, para = [], [], False, []

    def flush_para():
        if para:
            joined = " ".join(para)
            out_html.append(f"<p>{inline(joined)}</p>")
            out_txt.append(plain(joined))
            out_txt.append("")
            para.clear()

    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith(">"):
            line = line.lstrip(">").strip()
        if any(line.lower().startswith(p) for p in INTERNAL):
            continue
        bullet = re.match(r"^[-*]\s+(.*)$", line)
        if not bullet and in_list:
            out_html.append("</ul>")
            out_txt.append("")
            in_list = False
        if not line:
            flush_para()
            continue
        head = re.match(r"^(#{1,3})\s+(.*)$", line)
        if head:
            flush_para()
            level = len(head.group(1))
            out_html.append(f"<h{level}>{inline(head.group(2))}</h{level}>")
            out_txt.append(plain(head.group(2)).upper() if level == 1 else plain(head.group(2)))
            out_txt.append("")
            continue
        if bullet:
            flush_para()
            if not in_list:
                out_html.append("<ul>")
                in_list = True
            out_html.append(f"<li>{inline(bullet.group(1))}</li>")
            out_txt.append(f"- {plain(bullet.group(1))}")
            continue
        para.append(line)
    flush_para()
    if in_list:
        out_html.append("</ul>")
    html_path = src.with_suffix(".html")
    txt_path = src.with_suffix(".txt")
    if unresolved:
        stamp = f"DRAFT - NOT PASTE-READY ({len(unresolved)} unresolved fields)"
        out_html.insert(0, f"<p><strong>{stamp}</strong></p>")
        out_txt[:0] = [stamp, ""]
    html_path.write_text("\n".join(out_html) + "\n", encoding="utf-8")
    txt_path.write_text("\n".join(out_txt).strip() + "\n", encoding="utf-8")
    print(html_path)
    print(txt_path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
