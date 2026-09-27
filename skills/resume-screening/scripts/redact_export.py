#!/usr/bin/env python3
"""Drop protected and identity columns from an ATS export before any screening.

Usage:
  python3 scripts/redact_export.py <export.csv|export.xlsx> <out_dir>
      [--drop-cols references/protected-columns.txt] [--id-col "Application ID"]
      [--name-cols "First Name,Last Name"] [--text-cols "Resume Text,Cover Letter"]
      [--prefix A]

Input:  a CSV (or XLSX, if openpyxl is installed) exported from Greenhouse,
        Lever, Ashby, Workday or similar. Pull it in first with
        read_workspace_file(file_id=..., save_to_path="/home/user/screen/<role>/in/export.csv").
Output: <out_dir>/export.redacted.csv  every column except protected ones and
          direct identifiers (name, email, phone, address, social URLs), with a
          candidate_id column (the export's id column if given, else A-001 ...).
        <out_dir>/export.identity.csv   candidate_id + the identity and proxy
          columns: FOR THE HUMAN OWNER ONLY; never read back into the screening
          context.
        With --text-cols: <out_dir>/<id>.txt per row (the named free-text
          columns, joined) plus <out_dir>/manifest.csv, so redact.py can run next.
        stdout: "Dropped columns: ...", "Identity columns moved: ..." and
          "Proxy columns moved: ..." for the notice to the owner. Never prints
          cell values.
Protected columns: listed in the --drop-cols file, plus any header matching
  gender, sex, race, ethnic, hispanic, latino/a/x, veteran, disab, dob, birth,
  age, marital, religion, nationality, citizen, eeo, self id, photo, avatar,
  pronoun, orientation, pregnan. Dropped from every output.
Proxy columns: any header matching graduat, school, universit, college,
  salary, compensation, pay, location, city, state, country, region, commute.
  Not evidence for the rubric (prestige, age, pay history, place); moved to
  the owner-only identity file, never kept in export.redacted.csv.
Exit:   0 done, 2 unreadable input or missing library.
No network.
"""

import argparse
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import screenio  # noqa: E402

DEFAULT_DROP = Path(__file__).resolve().parent.parent / "references" / "protected-columns.txt"
PROTECTED_RE = re.compile(r"gender|\bsex\b|hispanic|latin[oax]|\brace\b|ethnic|veteran|disab|\bdob\b|birth|\bage\b|marital|religio|nationality|citizen|\beeo|self[\s._-]?id|photo|avatar|headshot|pronoun|orientation|pregnan", re.I)
PROXY_RE = re.compile(r"graduat|school|universit|college|salary|compensation|\bpay\b|location|\bcity\b|\bstate\b|country|region|commute", re.I)
IDENTITY_RE = re.compile(r"\bname\b|first[\s_]?name|last[\s_]?name|full[\s_]?name|e-?mail|phone|mobile|address|street|\bzip\b|postcode|postal|linkedin|facebook|twitter|instagram|social", re.I)


def read_table(path: Path) -> tuple[list[str], list[list[str]]]:
    if path.suffix.lower() in (".xlsx", ".xlsm"):
        try:
            import openpyxl  # type: ignore
        except ImportError:
            raise RuntimeError("XLSX needs openpyxl: pip install --user openpyxl, or export the report as CSV")
        wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
        ws = wb.worksheets[0]
        rows = [["" if v is None else str(v) for v in r] for r in ws.iter_rows(values_only=True)]
    else:
        with path.open(encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.reader(fh))
    if not rows:
        raise RuntimeError("the export is empty")
    return [h.strip() for h in rows[0]], rows[1:]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("export")
    ap.add_argument("out_dir")
    ap.add_argument("--drop-cols", default=str(DEFAULT_DROP))
    ap.add_argument("--id-col")
    ap.add_argument("--name-cols", default="")
    ap.add_argument("--text-cols", default="")
    ap.add_argument("--prefix", default="A")
    args = ap.parse_args()

    try:
        header, rows = read_table(Path(args.export).expanduser())
    except (OSError, UnicodeDecodeError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    drop_list = set()
    dp = Path(args.drop_cols).expanduser()
    if dp.is_file():
        drop_list = {l.strip().lower() for l in dp.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")}

    protected = [h for h in header if h.lower() in drop_list or PROTECTED_RE.search(h)]
    name_cols = [c.strip() for c in args.name_cols.split(",") if c.strip()]
    identity = [h for h in header if h not in protected and (IDENTITY_RE.search(h) or h in name_cols)]
    text_cols = [c.strip() for c in args.text_cols.split(",") if c.strip()]
    proxy = [h for h in header if h not in protected and h not in identity and h not in text_cols
             and h != args.id_col and PROXY_RE.search(h)]
    missing = [c for c in text_cols + name_cols + ([args.id_col] if args.id_col else []) if c not in header]
    if missing:
        print(f"error: column(s) not in the export: {missing}. Headers are: {header}", file=sys.stderr)
        return 2
    keep = [h for h in header if h not in protected and h not in identity and h not in proxy and h not in text_cols]

    out = Path(args.out_dir).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    red_rows, ident_rows, manifest = [], [], []
    seen_ids: set[str] = set()
    for n, r in enumerate(rows, 1):
        rec = {h: (r[i] if i < len(r) else "") for i, h in enumerate(header)}
        cid = rec.get(args.id_col, "").strip() if args.id_col else ""
        cid = cid or f"{args.prefix}-{n:03d}"
        if cid in seen_ids:
            # The same id twice (someone applied twice): keep both applications apart.
            k = 2
            while f"{cid}-{k}" in seen_ids:
                k += 1
            print(f"WARN export row {n}: id {cid} already used; this row is {cid}-{k}")
            cid = f"{cid}-{k}"
        seen_ids.add(cid)
        red_rows.append({"candidate_id": cid} | {h: rec[h] for h in keep})
        ident_rows.append({"candidate_id": cid} | {h: rec[h] for h in identity + proxy})
        if text_cols:
            body = "\n\n".join(rec[c] for c in text_cols if rec.get(c, "").strip())
            hint = " ".join(rec[c] for c in name_cols if rec.get(c, "").strip())
            status = "ok" if len(body.strip()) >= 200 else ("low_text" if body.strip() else "error")
            if body.strip():
                (out / f"{cid}.txt").write_text(body.strip() + "\n", encoding="utf-8")
            manifest.append({"id": cid, "source_file": f"export row {n}", "format": "export", "pages": "",
                             "chars": len(body.strip()), "parse_status": status, "hidden_chars": 0,
                             "injection_hits": " | ".join(screenio.injection_hits(body)), "name_hint": hint,
                             "note": "" if body.strip() else "no text in the named columns"})

    screenio.write_csv(out / "export.redacted.csv", red_rows, ["candidate_id"] + [k for k in keep if k != "candidate_id"])
    screenio.write_csv(out / "export.identity.csv", ident_rows, ["candidate_id"] + identity + proxy)
    if text_cols:
        screenio.write_csv(out / "manifest.csv", manifest, screenio.MANIFEST_FIELDS)
    print(f"{len(rows)} row(s). Dropped columns: {', '.join(protected) or 'none'}")
    print(f"Identity columns moved to export.identity.csv (owner only): {', '.join(identity) or 'none'}")
    print(f"Proxy columns moved to export.identity.csv (owner only; not evidence): {', '.join(proxy) or 'none'}")
    if text_cols:
        print(f"Wrote {sum(1 for m in manifest if m['parse_status'] != 'error')} text file(s) and manifest.csv; run redact.py next")
    return 0


if __name__ == "__main__":
    sys.exit(main())
