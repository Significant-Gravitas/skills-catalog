#!/usr/bin/env python3
"""Turn a folder (or zip) of resumes into plain text, with a parse manifest and a hidden-text scan.

Usage:
  python3 scripts/extract_resumes.py <in_dir_or_zip> <out_dir> [--dnc <dnc.csv>] [--prefix A]

Input:  PDF, DOCX, TXT or MD files (a .zip is unpacked first). Hidden files
        and other types are listed as "unsupported".
Output: <out_dir>/<id>.txt      visible text only, one per readable resume
        <out_dir>/manifest.csv  id,source_file,format,pages,chars,parse_status,
                                hidden_chars,injection_hits,name_hint,note
        <out_dir>/hidden.json   per id: hidden character count, a 120-char
                                sample, and instruction-like patterns found
        stdout: a summary by id only (no file names, no candidate names).
        manifest.csv and hidden.json identify people: they are for the human
        owner. Do not print them into the conversation.
IDs:    A-001, A-002 ... in sorted file-name order. Re-running on the same
        out_dir keeps existing ids and numbers new files after them.
parse_status:
        ok | low_text (under 200 characters) | scanned (PDF under 100
        characters per page: no text layer) | unsupported | error |
        held (name matches the do-not-contact list; no text written).
        Defaults for both thresholds: confirm with the owner.
Hidden text: DOCX runs marked vanish, white (FFFFFF) or 2pt and smaller;
        PDF characters that are white or under 3pt when pdfplumber is
        installed (otherwise the check is marked unavailable). Hidden text is
        never written to <id>.txt; it is reported for the human.
Needs:  PDF: pdfplumber (preferred) or pypdf:
          python3 -c "import pdfplumber" || pip install --user pdfplumber pypdf
        DOCX, TXT, MD: stdlib only. No OCR and no network.
Exit:   0 done (even if some files need a look), 2 bad input.
"""

import argparse
import csv
import json
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
import screenio  # noqa: E402

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
LOW_TEXT_CHARS = 200        # default (confirm with the owner)
SCANNED_CHARS_PER_PAGE = 100  # default (confirm with the owner)
HIDDEN_DOCX_HALF_POINTS = 4   # 2pt and smaller counts as hidden
HIDDEN_PDF_POINTS = 3.0
SUPPORTED = {".pdf", ".docx", ".txt", ".md"}


def name_hint(text: str) -> str:
    """Name line near the top (see screenio.name_hint): capitalised or ALL-CAPS, 1-6 words,
    particles such as 'de la' allowed, pronoun tags and credentials stripped, never a line
    with a role word or a '|'. '' when none is found: that record goes on "needs a look"."""
    return screenio.name_hint(text)


def docx_extract(path: Path) -> tuple[str, str, int]:
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    visible, hidden = [], []
    for p in root.iter(W + "p"):
        vis_parts, hid_parts = [], []
        for r in p.iter(W + "r"):
            rpr = r.find(W + "rPr")
            is_hidden = False
            if rpr is not None:
                if rpr.find(W + "vanish") is not None or rpr.find(W + "webHidden") is not None:
                    is_hidden = True
                color = rpr.find(W + "color")
                if color is not None and (color.get(W + "val") or "").upper() in ("FFFFFF", "FEFEFE", "FDFDFD"):
                    is_hidden = True
                sz = rpr.find(W + "sz")
                if sz is not None and (sz.get(W + "val") or "99").isdigit() and int(sz.get(W + "val")) <= HIDDEN_DOCX_HALF_POINTS:
                    is_hidden = True
            text = "".join((t.text or "") for t in r.iter(W + "t"))
            (hid_parts if is_hidden else vis_parts).append(text)
        if "".join(vis_parts).strip():
            visible.append("".join(vis_parts).strip())
        if "".join(hid_parts).strip():
            hidden.append("".join(hid_parts).strip())
    return "\n".join(visible), "\n".join(hidden), 1


def _is_white(color) -> bool:
    if color is None:
        return False
    vals = color if isinstance(color, (list, tuple)) else [color]
    try:
        vals = [float(v) for v in vals]
    except (TypeError, ValueError):
        return False
    if len(vals) == 4:  # CMYK white
        return all(v <= 0.02 for v in vals)
    return all(v >= 0.95 for v in vals)


def pdf_extract(path: Path) -> tuple[str, str | None, int]:
    try:
        import pdfplumber  # type: ignore
        visible, hidden_chars = [], []
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                def hidden(obj, page=page):
                    if obj.get("object_type") != "char":
                        return False
                    off = obj["x1"] < 0 or obj["x0"] > page.width or obj["bottom"] < 0 or obj["top"] > page.height
                    return _is_white(obj.get("non_stroking_color")) or float(obj.get("size", 12)) < HIDDEN_PDF_POINTS or off
                hidden_chars.extend(c["text"] for c in page.chars if hidden(c))
                visible.append(page.filter(lambda o: not hidden(o)).extract_text() or "")
            return "\n".join(visible), "".join(hidden_chars), len(pdf.pages)
    except ImportError:
        pass
    try:
        import pypdf  # type: ignore
    except ImportError:
        raise RuntimeError("no PDF library: pip install --user pdfplumber pypdf, then re-run")
    reader = pypdf.PdfReader(str(path))
    pages = [(pg.extract_text() or "") for pg in reader.pages]
    return "\n".join(pages), None, len(pages)


def load_dnc(path: str | None) -> list[str]:
    if not path:
        return []
    p = Path(path).expanduser()
    if not p.is_file():
        print(f"warning: do-not-contact file {p} not found; no one held back", file=sys.stderr)
        return []
    with p.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        return []
    col = 0
    if any(h.strip().lower() == "name" for h in rows[0]):
        col = [h.strip().lower() for h in rows[0]].index("name")
        rows = rows[1:]
    return [r[col].strip() for r in rows if len(r) > col and r[col].strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("out_dir")
    ap.add_argument("--dnc")
    ap.add_argument("--prefix", default="A")
    args = ap.parse_args()

    src = Path(args.source).expanduser()
    out = Path(args.out_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    tmp, zip_name = None, ""
    if src.is_file() and src.suffix.lower() == ".zip":
        tmp = Path(tempfile.mkdtemp())
        with zipfile.ZipFile(src) as zf:
            for member in zf.namelist():
                target = (tmp / member).resolve()
                if not str(target).startswith(str(tmp.resolve())) or member.endswith("/"):
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zf.read(member))
        zip_name = Path(args.source).name
        src = tmp
    if not src.is_dir():
        print(f"error: {src} is not a folder or .zip; save uploads with read_workspace_file(..., save_to_path=...) first", file=sys.stderr)
        return 2

    files = sorted(p for p in src.rglob("*") if p.is_file() and not any(part.startswith((".", "__MACOSX")) for part in p.relative_to(src).parts))
    manifest_path = out / "manifest.csv"
    existing: dict[str, dict] = {}
    if manifest_path.is_file():
        rows, _ = screenio.read_csv(manifest_path)
        existing = {r["source_file"]: r for r in rows}
    used = [int(r["id"].split("-")[-1]) for r in existing.values() if re.fullmatch(r"[A-Za-z]+-\d+", r["id"])]
    next_n = max(used, default=0) + 1
    dnc = load_dnc(args.dnc)
    hidden_report = {}
    if (out / "hidden.json").is_file():
        hidden_report = json.loads((out / "hidden.json").read_text(encoding="utf-8"))

    rows_out = dict(existing)
    for f in files:
        rel = str(f.relative_to(src))
        if rel in existing:
            continue
        cid = f"{args.prefix}-{next_n:03d}"
        next_n += 1
        row = {"id": cid, "source_file": rel, "format": f.suffix.lower().lstrip("."), "pages": "",
               "chars": 0, "parse_status": "ok", "hidden_chars": 0, "injection_hits": "", "name_hint": "", "note": ""}
        visible, hidden = "", ""
        try:
            ext = f.suffix.lower()
            if ext not in SUPPORTED:
                row["parse_status"], row["note"] = "unsupported", "ask for PDF, DOCX or text"
            elif ext == ".docx":
                visible, hidden, row["pages"] = docx_extract(f)
            elif ext == ".pdf":
                visible, hidden, row["pages"] = pdf_extract(f)
                if hidden is None:
                    hidden, row["note"] = "", "hidden-text check unavailable (pip install --user pdfplumber)"
            else:
                visible = f.read_text(encoding="utf-8", errors="replace")
        except (zipfile.BadZipFile, KeyError, ET.ParseError, OSError, RuntimeError, ValueError) as exc:
            row["parse_status"], row["note"] = "error", str(exc)[:200]
        except Exception as exc:  # a malformed PDF can raise library-specific errors
            row["parse_status"], row["note"] = "error", f"{type(exc).__name__}: {str(exc)[:160]}"

        if row["parse_status"] == "ok":
            chars = len(visible.strip())
            row["chars"] = chars
            pages = int(row["pages"] or 1)
            if row["format"] == "pdf" and chars < SCANNED_CHARS_PER_PAGE * pages:
                row["parse_status"], row["note"] = "scanned", "no text layer; needs a look (no OCR run)"
            elif chars < LOW_TEXT_CHARS:
                row["parse_status"], row["note"] = "low_text", "very little text; needs a look"
            row["name_hint"] = name_hint(visible)
            if not row["name_hint"] and not row["note"]:
                row["note"] = "no name line found; owner to confirm the name in idmap.csv before screening"
            # Whole words, accents and case ignored, any order on one line ("Perez, Jose"):
            # "Ann Lee" never holds "Joann Leeds", and "Jose Perez" holds "José Pérez".
            head = [l for l in visible.splitlines() if l.strip()][:5] + [re.sub(r"[_\-.]+", " ", f.stem)]
            if any(screenio.name_in_lines(d, head) for d in dnc):
                row["parse_status"], row["note"], visible = "held", "on the do-not-contact list; not screened", ""
            hits = screenio.injection_hits(visible + "\n" + (hidden or ""))
            row["hidden_chars"] = len((hidden or "").strip())
            row["injection_hits"] = " | ".join(hits)
            if row["hidden_chars"] or hits:
                hidden_report[cid] = {"hidden_chars": row["hidden_chars"],
                                      "sample": (hidden or "").strip()[:120],
                                      "patterns": hits,
                                      "in_visible_text": bool(screenio.injection_hits(visible))}
            if row["parse_status"] in ("ok", "low_text"):
                (out / f"{cid}.txt").write_text(visible.strip() + "\n", encoding="utf-8")
        if zip_name:
            # forget_candidate.py reads this: the original upload still holds the file.
            row["note"] = (row["note"] + "; " if row["note"] else "") + f"from zip {zip_name}"
        rows_out[rel] = row

    ordered = sorted(rows_out.values(), key=lambda r: screenio.id_key(r["id"]))
    screenio.write_csv(manifest_path, ordered, screenio.MANIFEST_FIELDS)
    (out / "hidden.json").write_text(json.dumps(hidden_report, indent=2), encoding="utf-8")
    if tmp:
        shutil.rmtree(tmp, ignore_errors=True)

    counts: dict[str, list[str]] = {}
    for r in ordered:
        counts.setdefault(r["parse_status"], []).append(r["id"])
    print(f"{len(ordered)} file(s): " + ", ".join(f"{k} {len(v)}" for k, v in sorted(counts.items())))
    for status in ("scanned", "low_text", "unsupported", "error"):
        if counts.get(status):
            print(f"needs a look ({status}): {', '.join(counts[status])}")
    no_name = [r["id"] for r in ordered if r["parse_status"] in ("ok", "low_text") and not r.get("name_hint")]
    if no_name:
        print(f"needs a look (no name line found): {', '.join(no_name)}; do not screen these until the owner "
              "fills name_hint for them in idmap.csv and redact.py is re-run")
    if counts.get("held"):
        print(f"held back (do-not-contact list): {len(counts['held'])} record(s); the owner sees which in manifest.csv")
    for cid, info in sorted(hidden_report.items(), key=lambda kv: screenio.id_key(kv[0])):
        bits = []
        if info["hidden_chars"]:
            bits.append(f"{info['hidden_chars']} hidden characters")
        if info["patterns"]:
            bits.append("instruction-like text: " + "; ".join(f'"{p}"' for p in info["patterns"][:3]))
        print(f"FACT {cid}: " + ", ".join(bits))
    return 0


if __name__ == "__main__":
    sys.exit(main())
