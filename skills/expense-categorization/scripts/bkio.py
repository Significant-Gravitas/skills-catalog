"""Shared helpers for the bookkeeping scripts. Python 3 standard library only.

Imported by the other scripts in this folder; not run on its own. The same
file ships in every bookkeeping package because packages cannot share files.

Conventions
- Money is decimal.Decimal, never float. Values are kept exactly as parsed;
  quantize only at presentation, to the currency's minor unit (ISO 4217).
- Canonical transaction columns (what normalize_export.py writes):
  source_file, source_row, date (ISO YYYY-MM-DD), description,
  amount (signed: money into the account positive, money out negative),
  currency, reference, balance.
- Errors exit with code 2 and say what to fix. Nothing here edits an input.
"""

import csv
import io
import re
import sys
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CANONICAL = ["source_file", "source_row", "date", "description", "amount",
             "currency", "reference", "balance"]

# ISO 4217 minor units for currencies that are not 2 decimal places.
# Anything not listed is treated as 2. Source: ISO 4217 currency code list.
MINOR_UNITS = {"JPY": 0, "KRW": 0, "VND": 0, "CLP": 0, "ISK": 0, "UGX": 0,
               "BHD": 3, "KWD": 3, "OMR": 3, "JOD": 3, "TND": 3, "LYD": 3, "IQD": 3}

DATE_FORMATS = ["%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y", "%d/%m/%y",
                "%m/%d/%y", "%d-%m-%Y", "%m-%d-%Y", "%d.%m.%Y", "%d %b %Y",
                "%d-%b-%Y", "%d %B %Y", "%b %d, %Y", "%d-%b-%y", "%Y%m%d"]
# Pairs that read the same text two ways; if both parse every value the
# format is ambiguous and a person must choose.
AMBIGUOUS_PAIRS = [("%d/%m/%Y", "%m/%d/%Y"), ("%d/%m/%y", "%m/%d/%y"),
                   ("%d-%m-%Y", "%m-%d-%Y")]

COLUMN_HINTS = {
    "date": ["date", "transaction date", "txn date", "posted date", "posting date",
             "value date", "trans date", "booking date", "created", "invoice date"],
    "description": ["description", "details", "narrative", "memo", "payee", "name",
                    "merchant", "transaction description", "reference description"],
    "amount": ["amount", "value", "net amount", "transaction amount", "amount (gbp)",
               "amount (usd)", "gross"],
    "debit": ["debit", "debits", "paid out", "money out", "withdrawal", "withdrawals",
              "debit amount", "out"],
    "credit": ["credit", "credits", "paid in", "money in", "deposit", "deposits",
               "credit amount", "in"],
    "balance": ["balance", "running balance", "closing balance", "balance after"],
    "currency": ["currency", "ccy", "currency code"],
    "reference": ["fitid", "transaction id", "id", "reference", "ref", "bank reference",
                  "transaction reference", "check number", "cheque number"],
}


class InputError(Exception):
    """Bad input the user can fix. Message says what to fix."""


def die(message, fix=None, code=2):
    print(f"error: {message}", file=sys.stderr)
    if fix:
        print(f"fix: {fix}", file=sys.stderr)
    sys.exit(code)


def minor_unit(currency):
    return MINOR_UNITS.get((currency or "").upper(), 2)


def quantize(value, currency, rounding=ROUND_HALF_UP):
    places = minor_unit(currency)
    exp = Decimal(1).scaleb(-places)
    return value.quantize(exp, rounding=rounding)


def fmt_money(value, currency=""):
    if value is None:
        return ""
    q = quantize(value, currency) if currency else value
    return f"{q:,}" + (f" {currency}" if currency else "")


_CCY_SYMBOLS = "£$€¥₹"


def parse_amount(text):
    """Parse a money string to Decimal. Returns (value or None, flags list).

    Handles currency symbols, thousands separators, (1.00) and 1.00- negatives,
    'CR'/'DR' suffixes and decimal commas when unambiguous. Raises InputError
    when the text cannot be read as money.
    """
    flags = []
    if text is None:
        return None, flags
    s = str(text).strip()
    if s == "" or s in {"-", "--"}:
        return None, flags
    neg = False
    upper = s.upper()
    if upper.endswith("CR"):
        s = s[:-2].strip()
        flags.append("cr_suffix")
    elif upper.endswith("DR"):
        s = s[:-2].strip()
        neg = True
        flags.append("dr_suffix")
    if s.startswith("(") and s.endswith(")"):
        neg, s = True, s[1:-1].strip()
        flags.append("parenthesis_negative")
    if s.endswith("-"):
        neg, s = True, s[:-1].strip()
        flags.append("trailing_minus")
    s = re.sub(r"^[A-Z]{3}\s*", "", s)          # leading ISO code
    s = re.sub(r"\s*[A-Z]{3}$", "", s)          # trailing ISO code
    s = s.strip(_CCY_SYMBOLS + " ")
    if s.startswith("-"):
        neg, s = (not neg), s[1:]
    if s.startswith("+"):
        s = s[1:]
    s = s.strip(_CCY_SYMBOLS + " ")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):          # 1.234,56
            s = s.replace(".", "").replace(",", ".")
            flags.append("decimal_comma")
        else:                                   # 1,234.56
            s = s.replace(",", "")
            flags.append("thousands_separator")
    elif "," in s:
        if re.fullmatch(r"\d{1,3}(,\d{3})+", s):
            s = s.replace(",", "")
            flags.append("thousands_separator")
        elif re.fullmatch(r"\d+,\d{1,2}", s):
            s = s.replace(",", ".")
            flags.append("decimal_comma")
        else:
            raise InputError(f"cannot read '{text}' as money")
    s = s.replace(" ", "").replace(" ", "")
    try:
        value = Decimal(s)
    except InvalidOperation:
        raise InputError(f"cannot read '{text}' as money") from None
    return (-value if neg else value), flags


def detect_date_formats(values):
    """Return (formats that parse every non-empty value, ambiguous flag)."""
    vals = [v.strip() for v in values if v and v.strip()]
    if not vals:
        return [], False
    fits = []
    for fmt in DATE_FORMATS:
        try:
            for v in vals:
                datetime.strptime(_date_part(v), fmt)
            fits.append(fmt)
        except ValueError:
            continue
    ambiguous = any(a in fits and b in fits for a, b in AMBIGUOUS_PAIRS)
    return fits, ambiguous


def _date_part(text):
    t = text.strip()
    # drop a time part: "2026-04-03 14:22:01" or "03/04/2026 14:22" or ISO "T"
    t = re.split(r"[T ](?=\d{1,2}:\d{2})", t)[0]
    return t


def parse_date(text, fmt):
    try:
        return datetime.strptime(_date_part(text), fmt).date()
    except (ValueError, AttributeError):
        raise InputError(f"date '{text}' does not match format {fmt}") from None


def parse_iso(text):
    try:
        return date.fromisoformat(str(text).strip()[:10])
    except ValueError:
        raise InputError(f"'{text}' is not an ISO date (YYYY-MM-DD)") from None


def read_csv(path, allow_ragged=False, header_line=None):
    """Read a CSV export. Returns (header list, rows list of dicts).

    Each row dict gets '_row' = the 1-based line number in the file, so every
    output can cite the source row. Tries UTF-8 (with or without BOM), then
    cp1252. Skips leading blank lines and bank preamble lines (account name,
    sort code, account number ...): the header is the first row that names a
    date column and an amount or debit/credit column; failing that, the first
    row as wide as most rows. header_line (1-based) forces the header row.

    A data row with more cells than the file's normal row width, or a non-empty
    cell beyond the header's width (usually an unquoted comma inside a
    description), would shift every later column, so it raises InputError
    naming the lines. Pass allow_ragged=True only to report such rows
    (profile_sources.py) or to copy them unchanged (redact.py); use
    read_csv_report() to get the list.
    """
    header, rows, ragged = read_csv_report(path, header_line=header_line)
    if ragged and not allow_ragged:
        raise InputError(
            f"{path}: RAGGED_ROWS on lines {ragged[:10]}{'...' if len(ragged) > 10 else ''}: "
            f"more cells than the {len(header)} header columns or the normal row width (usually "
            "an unquoted comma in a description), so later columns would shift. Ask the owner "
            "for a properly quoted export; do not guess which cell is the amount")
    return header, rows


def _is_header_row(cells):
    names = {c.strip().lower() for c in cells if c.strip()}
    has_date = any(h in names for h in COLUMN_HINTS["date"])
    has_money = any(h in names for role in ("amount", "debit", "credit") for h in COLUMN_HINTS[role])
    return has_date and has_money


def read_csv_report(path, header_line=None):
    """Like read_csv, but never refuses ragged rows. Returns (header, rows,
    ragged_lines): the 1-based line numbers of rows that have more cells than
    the normal row width (the most common cell count, counting empty cells, so
    an unquoted comma is caught even when the last column is empty) or a
    non-empty cell beyond the header's width. Exports that end every line with
    a comma are not ragged. Extra cells are kept as 'colN' keys."""
    raw = None
    for enc in ("utf-8-sig", "cp1252"):
        try:
            with open(path, encoding=enc, newline="") as fh:
                raw = fh.read()
            break
        except UnicodeDecodeError:
            continue
        except FileNotFoundError:
            raise InputError(f"file not found: {path}") from None
    if raw is None:
        raise InputError(f"{path}: not UTF-8 or cp1252 text; export it again as CSV")
    if not raw.strip():
        raise InputError(f"{path}: file is empty")
    sample = raw[:4096]
    # Take only the delimiter from the sniffer; keep standard quoting ("" inside
    # a quoted field), which the sniffer can misjudge and so split a field.
    try:
        delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t|").delimiter
    except csv.Error:
        delimiter = ","
    lines = list(csv.reader(io.StringIO(raw), csv.excel, delimiter=delimiter))
    widths = [len([c for c in r if c.strip()]) for r in lines]
    if not any(widths):
        raise InputError(f"{path}: no data rows")
    if header_line is not None:
        header_idx = int(header_line) - 1
        if not 0 <= header_idx < len(lines) or not widths[header_idx]:
            raise InputError(f"{path}: --header-line {header_line} is not a non-empty line of the file")
    else:
        header_idx = next((i for i, r in enumerate(lines) if _is_header_row(r)), None)
        if header_idx is None:
            # fall back: first row whose width equals the most common width
            target = max(set(widths), key=widths.count)
            header_idx = next(i for i, w in enumerate(widths) if w >= target and w > 0)
    header = [h.strip() for h in lines[header_idx]]
    data = [(i, lines[i]) for i in range(header_idx + 1, len(lines)) if any(c.strip() for c in lines[i])]
    counts = [len(c) for _, c in data]
    normal = max(set(counts), key=counts.count) if counts else len(header)
    # a trailing comma on every line is a normal width, not a shifted column
    width = max(len(header), normal) if normal > len(header) and all(
        not any(c.strip() for c in cells[len(header):]) for _, cells in data if len(cells) == normal
    ) else len(header)
    rows, ragged = [], []
    for i, cells in data:
        if len(cells) > width or any(c.strip() for c in cells[len(header):]):
            ragged.append(i + 1)
        row = {header[j] if j < len(header) and header[j] else f"col{j+1}": (cells[j].strip() if j < len(cells) else "")
               for j in range(max(len(header), len(cells)))}
        row["_row"] = i + 1
        rows.append(row)
    return header, rows, ragged


def find_column(header, role, mapping=None):
    """Find the header for a role (date, amount, ...). mapping overrides."""
    if mapping and role in mapping:
        name = mapping[role]
        if name not in header:
            raise InputError(f"--map {role}={name}: no such column; columns are {header}")
        return name
    lowered = {h.lower().strip(): h for h in header}
    for hint in COLUMN_HINTS.get(role, []):
        if hint in lowered:
            return lowered[hint]
    return None


def parse_mapping(items):
    mapping = {}
    for item in items or []:
        for part in item.split(","):
            if not part.strip():
                continue
            if "=" not in part:
                raise InputError(f"--map expects role=Column, got '{part}'")
            k, v = part.split("=", 1)
            mapping[k.strip()] = v.strip()
    return mapping


def read_canonical(path):
    """Read a canonical CSV written by normalize_export.py."""
    header, rows = read_csv(path)
    missing = [c for c in ("source_file", "source_row", "date", "description", "amount", "currency")
               if c not in header]
    if missing:
        raise InputError(f"{path} is not a canonical export (missing {missing}); "
                         "run normalize_export.py on the raw file first")
    out = []
    for r in rows:
        amt, _ = parse_amount(r["amount"])
        if amt is None:
            raise InputError(f"{path} line {r['_row']}: empty amount")
        out.append({**r, "amount": amt, "date": parse_iso(r["date"])})
    return out


def write_csv(path, fieldnames, rows):
    target = sys.stdout if path in (None, "-") else open(path, "w", encoding="utf-8", newline="")
    try:
        w = csv.DictWriter(target, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})
    finally:
        if target is not sys.stdout:
            target.close()


def norm_text(text):
    """Lower-case, strip digits and punctuation: a vendor key for fuzzy grouping."""
    t = re.sub(r"[^a-z ]+", " ", (text or "").lower())
    t = re.sub(r"\b(ltd|limited|inc|llc|plc|co|the|www|com|uk|gb|us|card|pos|ref)\b", " ", t)
    return " ".join(t.split())
