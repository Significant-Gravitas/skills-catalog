#!/usr/bin/env python3
"""Dedupe a sourcing batch against the shortlist, the pipeline and do-not-contact.

Usage (cd ~/skills/candidate-sourcing-strategy first):
    python3 scripts/dedupe_names.py <batch.json> [--shortlist PATH] [--pipeline PATH]
        [--dnc PATH] [--out kept.json]

Defaults (the hiring folder, override with HIRING_DIR):
    --shortlist ~/workspace/hiring/shortlist.csv        (name, company, ...)
    --pipeline  ~/workspace/hiring/tracker/candidates.csv (name, role, ...; company optional)
    --dnc       ~/workspace/hiring/dnc.csv              (name, flag)
Batch:  a JSON list of cards, each with at least "name" and "company"
        (templates/batch-card.json shows the full card).

Matching rule (the skill's rule, made deterministic):
  normalise = accents folded (NFKD), lower case, punctuation stripped,
              first name mapped through references/nicknames.csv,
              company suffixes stripped (inc, ltd, gmbh, llc, ...).
  EXACT       same normalised full name AND same normalised company  -> dropped
  CHECK THESE same full name, different/missing company; or same surname with a
              close first name (similarity >= 0.8)                    -> held back, listed
  DNC         any of these                                            -> dropped silently
              - same normalised first and last name;
              - same last name, first-name similarity >= 0.85;
              - every name token of one is among the other's tokens, in
                either direction (catches compound or extra surnames,
                initials and "Surname, First" order: DNC "Marta Silva"
                excludes "Marta Silva Pereira", "Marta P. Silva" and
                "Silva, Marta");
              - same first name and any DNC surname token in the card name
                (DNC "Marta Silva Pereira" excludes "Marta Pereira").
              The DNC test errs toward excluding: a wrong exclusion costs one
              card, a wrong inclusion contacts someone who asked not to be.
  Never merges anything. Fuzzy results are never dropped as duplicates; they
  are held for a human to confirm.

Output: JSON report on stdout:
  {"kept": n, "exact": [{"name","company","matched_in"}], "check_these": [...],
   "dnc_excluded": n, "files_missing": ["DNC: <path>", ...]}
  A shortlist, pipeline or DNC file that does not exist is read as empty, but
  never silently: stderr gets "WARN <file> not found; <list> not checked" and
  the JSON lists it under files_missing. Files are read BOM-tolerant (Excel's
  "CSV UTF-8") with header names folded to lower case ("Name,Flag" works). A
  file with rows but no name column gets "WARN <file> has no name column;
  <list> not checked" and is listed under files_missing too. A missing DNC file means the batch
  was NOT checked against do-not-contact: say so in the batch header, and in
  an unattended run hold the batch instead of showing it.
  DNC names are never echoed (count only). Kept cards go to --out (default
  kept.json in the current directory).
Exit:   0 ok; 2 unreadable input.
Stdlib only, no network.
"""

import csv
import difflib
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

HIRING_DIR = Path(os.environ.get("HIRING_DIR", str(Path.home() / "workspace" / "hiring")))
NICKNAMES = Path(__file__).resolve().parent.parent / "references" / "nicknames.csv"
SUFFIXES = {"inc", "incorporated", "ltd", "limited", "llc", "llp", "plc", "gmbh", "ag", "sa", "sas",
            "sarl", "bv", "nv", "co", "corp", "corporation", "company", "oy", "ab", "as", "srl",
            "spa", "pty", "kk", "the"}
CHECK_MIN = 0.8   # first-name similarity for "check these" (default; tune with the owner)
HONORIFICS = {"dr", "mr", "mrs", "ms", "mx", "prof", "jr", "sr", "ii", "iii", "phd"}
PARTICLES = {"da", "de", "do", "dos", "das", "del", "della", "di", "du", "la", "le", "van", "von", "der",
             "den", "ter", "e", "y", "bin", "binti", "al", "el"}
DNC_MIN = 0.85    # first-name similarity for a DNC exclusion (errs toward excluding)


def fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^\w\s]", " ", s)
    return " ".join(s.split())


def load_nicknames() -> dict:
    """Map every name in the table to one group key (union-find), so
    Alex/Alexander/Aleksandr/Sasha all normalise alike. Over-grouping only
    makes a match more likely to be flagged, which is the safe direction."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    if NICKNAMES.exists():
        with NICKNAMES.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                a, b = find(fold(row["canonical"])), find(fold(row["variant"]))
                if a != b:
                    parent[max(a, b)] = min(a, b)
    return {name: find(name) for name in parent}


NICK = load_nicknames()


def norm_name(name: str):
    parts = fold(name).split()
    parts = [p for p in parts if p not in HONORIFICS]
    if not parts:
        return "", ""
    first = NICK.get(parts[0], parts[0])
    last = parts[-1] if len(parts) > 1 else ""
    return first, last


def name_tokens(name: str):
    """Folded, nickname-mapped tokens, in order. Particles (da, de, dos, van,
    von, ...) are kept; they only make a DNC subset match more likely."""
    parts = [p for p in fold(name).split() if p not in HONORIFICS]
    return [NICK.get(p, p) for p in parts]


def dnc_hit(card_name: str, dnc_entries) -> bool:
    f, l = norm_name(card_name)
    toks = set(name_tokens(card_name))
    for (df, dl), dtoks in dnc_entries:
        if (f, l) == (df, dl):
            return True
        if l and l == dl and difflib.SequenceMatcher(None, f, df).ratio() >= DNC_MIN:
            return True
        full = {t for t in dtoks if len(t) > 1}
        mine = {t for t in toks if len(t) > 1}
        if full and mine and (full <= mine or mine <= full):
            return True
        if f and f == df and (set(dtoks[1:]) - PARTICLES) & toks:
            return True
    return False


def norm_company(company: str) -> str:
    return " ".join(w for w in fold(company).split() if w not in SUFFIXES)


MISSING = []  # (label, path) of list files that were not found


def read_csv(path: Path, label: str = ""):
    if not path.exists():
        MISSING.append((label or path.name, str(path)))
        print(f"WARN {path} not found; {label or path.name} not checked", file=sys.stderr)
        return []
    try:
        with path.open(encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            reader.fieldnames = [(f or "").strip().lower() for f in (reader.fieldnames or [])]
            rows = list(reader)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        sys.exit(2)
    if rows and "name" not in rows[0]:
        MISSING.append((label or path.name, f"{path} (no name column)"))
        print(f"WARN {path} has no name column; {label or path.name} not checked", file=sys.stderr)
        return []
    return rows


def arg(args, flag, default):
    if flag in args:
        i = args.index(flag)
        if i + 1 < len(args):
            return Path(args[i + 1]).expanduser()
    return default


def main(argv):
    args = argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__, file=sys.stderr)
        return 2
    try:
        batch = json.loads(Path(args[0]).expanduser().read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"error: cannot read batch {args[0]}: {exc}. It must be a JSON list of cards.", file=sys.stderr)
        return 2
    if not isinstance(batch, list):
        print("error: batch must be a JSON list of cards", file=sys.stderr)
        return 2
    shortlist = read_csv(arg(args, "--shortlist", HIRING_DIR / "shortlist.csv"), "shortlist")
    pipeline = read_csv(arg(args, "--pipeline", HIRING_DIR / "tracker" / "candidates.csv"), "pipeline")
    dnc = read_csv(arg(args, "--dnc", HIRING_DIR / "dnc.csv"), "DNC")
    out_path = arg(args, "--out", Path("kept.json"))

    known = []  # (first, last, company_or_None, list_name, display)
    for row in shortlist:
        f, l = norm_name(row.get("name", ""))
        known.append((f, l, norm_company(row.get("company", "")) or None, "shortlist", row.get("name", "")))
    for row in pipeline:
        f, l = norm_name(row.get("name", ""))
        known.append((f, l, norm_company(row.get("company", "")) or None, "pipeline", row.get("name", "")))
    dnc_names = [(norm_name(r["name"]), name_tokens(r["name"])) for r in dnc if r.get("name")]

    kept, exact, check, dnc_count, seen = [], [], [], 0, []
    for card in batch:
        f, l = norm_name(card.get("name", ""))
        comp = norm_company(card.get("company", ""))
        if not f:
            check.append({"name": card.get("name", ""), "company": card.get("company", ""), "why": "no usable name"})
            continue
        # Do-not-contact first; err toward excluding.
        if dnc_hit(card.get("name", ""), dnc_names):
            dnc_count += 1
            continue
        # Duplicates inside the same batch.
        if any((f, l, comp) == s for s in seen):
            exact.append({"name": card.get("name"), "company": card.get("company"), "matched_in": "this batch"})
            continue
        hit = None
        for kf, kl, kc, where, disp in known:
            if (kf, kl) == (f, l) and kc is not None and kc == comp:
                hit = ("exact", where, disp)
                break
            if (kf, kl) == (f, l):
                hit = hit or ("check", where, disp, "same name, company differs or unknown")
            elif l and kl == l and difflib.SequenceMatcher(None, f, kf).ratio() >= CHECK_MIN:
                hit = hit or ("check", where, disp, "same surname, similar first name")
        if hit and hit[0] == "exact":
            exact.append({"name": card.get("name"), "company": card.get("company"), "matched_in": hit[1]})
            continue
        if hit:
            check.append({"name": card.get("name"), "company": card.get("company"),
                          "maybe": hit[2], "in": hit[1], "why": hit[3]})
            continue
        seen.append((f, l, comp))
        kept.append(card)

    out_path.write_text(json.dumps(kept, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"kept": len(kept), "kept_file": str(out_path), "exact": exact,
                      "check_these": check, "dnc_excluded": dnc_count,
                      "files_missing": [f"{label}: {p}" for label, p in MISSING]}, indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
