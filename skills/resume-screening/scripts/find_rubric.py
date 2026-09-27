#!/usr/bin/env python3
"""Find the approved rubric (Harper) or role scorecard (Sofia) for a role.

Usage:
  python3 scripts/find_rubric.py <role-slug> [--root ~/workspace/hiring]
                                 [--file <path>] [--emit-criteria <criteria.json>]

Looks for, in order:
  Harper  <root>/<role-slug>/rubric-v<N>.md   (highest approved N; checksum
          <file>.sha256 from hiring-rubric-design's approve_rubric.py)
  Sofia   <root>/roles/<role-slug>/scorecard.md or scorecard-v<N>.md
  --file  an explicit path (for example a rubric the owner pasted, saved with
          "status: approved", "approved_by:" and "approval_quote:" lines)
A file counts as approved only if its header says "status: approved" and
names approved_by. Criteria are read from the rubric's criteria table
(criterion_id column) or from Sofia's M1../N1.. must-have and nice-to-have lines.
Also reads the hiring jurisdictions (Harper plan "- Hiring jurisdictions:" line,
or "hiring_jurisdictions:" in <root>/preferences.md; UNSET, OPEN, TBD or
empty count as "not recorded") and lists which references/ai-hiring-law-watch.md
regions they touch. The list is split into places on ';', newline, '/', '&',
' and ', ' or ' and on commas (not inside brackets); a comma followed by a US
state code or name or a country stays with the place before it, so "Chicago,
London" and "Portugal, Spain (EU)" are two places while "Boston, MA" is one.
Each place is read with the state or country beside it: "Dublin, OH" and
"Birmingham, AL" are US only, "Sydney, New South Wales" is not the UK,
"Brooklyn Park, MN" is not New York City.

Output: JSON on stdout: path, format, version, status, approved_by, approved_on,
        checksum (ok | missing | mismatch), newer_drafts, jurisdictions, law_watch,
        criteria. When a city name was not counted because of the state or
        country beside it, law_watch_confirm lists "<place>: <region> city not
        counted; confirm the country" lines (the key is present only then).
        --emit-criteria also writes criteria.json for the other scripts.
A Harper rubric (rubric-v<N>.md in the role folder) with an approved header
but no .sha256 was never frozen by approve_rubric.py: it counts as not
approved (exit 3). "checksum: missing" is accepted only for Sofia's scorecard
and for a --file rubric the owner approved in chat.
Exit:   0 approved rubric found; 3 none approved (screening must not start);
        4 approved file changed after approval (stop; ask the owner); 2 bad input.
Stdlib only, no network.
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import screenio  # noqa: E402

META_RE = re.compile(r"^([a-z_]+):[ \t]*(.*)$")
SCREENABLE = re.compile(r"\b(resume|cv|application|cover letter|portfolio|profile|work history)\b", re.I)
REGIONS = {
    "NYC": r"\b(new york city|nyc|new york,\s*ny|manhattan|brooklyn(?!\s+(?:park|center|centre)\b)|queens|bronx|staten island)\b",
    "Illinois": r"\b(illinois|chicago|,\s*il\b)",
    "California": r"\b(california|san francisco|los angeles|san diego|san jose|oakland|,\s*ca\b)",
    "Colorado": r"\b(colorado|denver|boulder|colorado springs|aurora,\s*co|,\s*co\b)",
    "US (federal)": (r"\b(us|u\.s\.a?\.?|usa|united states|alabama|alaska|arizona|arkansas|california|colorado|"
                     r"connecticut|delaware|florida|georgia|hawaii|idaho|illinois|indiana|iowa|kansas|kentucky|"
                     r"louisiana|maine|maryland|massachusetts|michigan|minnesota|mississippi|missouri|montana|"
                     r"nebraska|nevada|new hampshire|new jersey|new mexico|new york|north carolina|north dakota|ohio|"
                     r"oklahoma|oregon|pennsylvania|rhode island|south carolina|south dakota|tennessee|texas|utah|"
                     r"vermont|virginia|washington|west virginia|wisconsin|wyoming|district of columbia|nyc|"
                     r"new york city|chicago|san francisco|los angeles|denver|austin|seattle|boston)\b"
                     r"|,\s*(a[klrz]|c[aot]|d[ce]|fl|ga|hi|i[adln]|k[sy]|la|m[adeinost]|n[cdehjmvy]|o[hkr]|pa|ri|s[cd]|"
                     r"t[nx]|ut|v[at]|w[aivy])\b"),
    "UK": r"\b(uk|u\.k\.|united kingdom|great britain|england|scotland|(?<!new south )wales|northern ireland)\b",
    "EU": r"\b(eu|eea|european union|germany|france|netherlands|(?<!northern )ireland|spain|italy|poland|sweden|belgium|austria|denmark|finland|portugal)\b",
}
# City names shared with other countries ("Birmingham, AL", "Dublin, OH", "Paris, TX",
# "London, Ontario"): they count only when the same place names no US state and no other
# country. US cities count only when no other state is named ("Brooklyn Park, MN").
CITY_REGIONS = {
    "UK": (None, r"\b(london|manchester|edinburgh|glasgow|belfast|cardiff|birmingham|bristol|leeds)\b"),
    "EU": (None, r"\b(berlin|paris|amsterdam|dublin|madrid|lisbon|munich|warsaw|stockholm)\b"),
    "NYC": ("ny", r"\b(manhattan|brooklyn(?!\s+(?:park|center|centre)\b)|queens|bronx|staten island)\b"),
    "Illinois": ("il", r"\bchicago\b"),
    "California": ("ca", r"\b(san francisco|los angeles|san diego|san jose|oakland)\b"),
    "Colorado": ("co", r"\b(denver|boulder|colorado springs)\b"),
}
US_STATE_HINT = re.compile(r",\s*(a[klrz]|c[aot]|d[ce]|fl|ga|hi|i[adln]|k[sy]|la|m[adeinost]|n[cdehjmvy]|o[hkr]|pa|ri|"
                           r"s[cd]|t[nx]|ut|v[at]|w[aivy])\b|\b(alabama|alaska|arizona|arkansas|california|colorado|"
                           r"connecticut|delaware|florida|hawaii|idaho|illinois|indiana|iowa|kansas|kentucky|louisiana|"
                           r"maine|maryland|massachusetts|michigan|minnesota|mississippi|missouri|montana|nebraska|"
                           r"nevada|new hampshire|new jersey|new mexico|new york|north carolina|north dakota|ohio|"
                           r"oklahoma|oregon|pennsylvania|rhode island|south carolina|south dakota|tennessee|texas|utah|"
                           r"vermont|virginia|washington|west virginia|wisconsin|wyoming|georgia)\b", re.I)
OTHER_COUNTRY = re.compile(r"\b(canada|ontario|quebec|australia|new south wales|queensland|new zealand|india|singapore|"
                           r"south africa|mexico|tbilisi|batumi|kutaisi)\b", re.I)
UNSET_VALUES = {"", "unset", "open", "tbd", "todo", "n/a", "none", "unknown", "?"}


US_CODES = set(("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM "
                 "NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC").split())
US_MARKER = re.compile(r"(?:us|usa|united states)\b|u\.s\.", re.I)
SEPARATOR = re.compile(r"[;\n/&,]|\s+(?:and|or)\s+", re.I)


def is_qualifier(segment: str) -> bool:
    """True when a comma segment starts with a US state code or name, or a country or region."""
    seg = segment.strip()
    m = re.match(r"([A-Z]{2})\b", seg)
    if m and m.group(1) in US_CODES:
        return True
    return bool(US_MARKER.match(seg) or US_STATE_HINT.match(seg) or OTHER_COUNTRY.match(seg)
                or re.match(REGIONS["UK"], seg, re.I) or re.match(REGIONS["EU"], seg, re.I))


def split_places(text: str) -> list[str]:
    """Split a free-text jurisdiction list into places, one jurisdiction each.

    Breaks on ';', newline, '/', '&', ' and ', ' or ' and ',' outside brackets. A comma
    segment that is a US state code or name or a country stays with the place before it
    ("Boston, MA", "London, Ontario", "Tbilisi, Georgia"). A place takes one such qualifier;
    a further one ("Chicago, IL, USA") becomes its own place, which names the same country
    anyway. Two countries ("Portugal, Spain") may share a place: country names always count.
    """
    pieces: list[tuple[str, str]] = []  # (separator before the piece, text)
    depth, start, sep, i = 0, 0, ";", 0
    while i < len(text):
        ch = text[i]
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        elif depth == 0:
            m = SEPARATOR.match(text, i)
            if m:
                pieces.append((sep, text[start:i]))
                sep = "," if m.group(0) == "," else ";"
                start = i = m.end()
                continue
        i += 1
    pieces.append((sep, text[start:]))
    places: list[list] = []  # [text, already took a qualifier after a comma]
    for sep, piece in pieces:
        piece = piece.strip()
        if not piece:
            continue
        if sep == "," and places and not places[-1][1] and is_qualifier(piece):
            places[-1] = [places[-1][0] + ", " + piece, True]
        else:
            places.append([piece, False])
    return [p for p, _ in places]


def law_watch(juris: str) -> list[str]:
    """Regions of references/ai-hiring-law-watch.md that the jurisdictions touch."""
    return law_watch_detail(juris)[0]


def law_watch_detail(juris: str) -> tuple[list[str], list[str]]:
    """(regions, confirm lines). Each place from split_places() is read on its own, so a city
    name is judged only by the state or country beside it. A city that is not counted for
    that reason gets a confirm line, so the drop is never silent."""
    found: list[str] = []
    confirm: list[str] = []
    for place in split_places(juris or ""):
        other = bool(OTHER_COUNTRY.search(place))
        here = set()
        for name, pat in REGIONS.items():
            if name == "US (federal)" and other:
                continue
            if re.search(pat, place, re.I):
                here.add(name)
        states = {m.group(1).lower() if m.group(1) else m.group(2).lower() for m in US_STATE_HINT.finditer(place)}
        for name, (home, pat) in CITY_REGIONS.items():
            if not re.search(pat, place, re.I):
                continue
            if other:
                counted = False
            elif home is None:
                counted = not states and "US (federal)" not in here
            else:
                counted = (not states or home in states or
                           {"ny": "new york", "il": "illinois", "ca": "california", "co": "colorado"}[home] in states)
            if counted:
                here.add(name)
            elif name not in here:
                confirm.append(f"{place}: {name} city name not counted because of the state or country named "
                               f"with it; confirm the country with the owner")
        found += [n for n in REGIONS if n in here and n not in found]
    return found, confirm


def meta_of(text: str) -> dict:
    meta = {}
    for line in text.splitlines():
        if line.startswith("## "):
            break
        m = META_RE.match(line.strip())
        if m:
            meta.setdefault(m.group(1), m.group(2).strip().strip('"'))
    return meta


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def criteria_harper(text: str, reqs: dict[str, str]) -> list[dict]:
    lines = text.splitlines()
    header, out = None, []
    for line in lines:
        if not line.strip().startswith("|"):
            if header is not None and out:
                break
            continue
        cells = split_row(line)
        if header is None:
            if "criterion_id" in [c.lower() for c in cells]:
                header = [c.lower() for c in cells]
            continue
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells if c):
            continue
        row = dict(zip(header, cells))
        ids = [x for x in re.split(r"[;,\s]+", row.get("requirement_ids", "")) if x]
        sources = row.get("evidence_sources", "")
        if reqs:
            must = any(reqs.get(i) == "must-show" for i in ids)
        else:
            must = bool(SCREENABLE.search(sources))
        out.append({"id": row.get("criterion_id", ""), "text": row.get("criterion", ""), "must": must,
                    "resume_screenable": bool(SCREENABLE.search(sources)), "evidence_sources": sources})
    return out


def criteria_sofia(text: str) -> list[dict]:
    out = []
    pat = re.compile(r"^\s*(?:[-*]\s*|\|\s*)?\**\s*([MN]\d+)\s*\**\s*[:.)|\-–]\s*(.+?)\s*\|?\s*$")
    for line in text.splitlines():
        m = pat.match(line)
        if not m:
            continue
        cid, body = m.group(1), m.group(2)
        body = body.split("|")[0].strip().strip("*").strip()
        if cid in {c["id"] for c in out} or not body:
            continue
        out.append({"id": cid, "text": body, "must": cid.startswith("M"), "resume_screenable": True,
                    "evidence_sources": ""})
    return out


def jurisdictions(root: Path, slug: str) -> str:
    for plan in (root / slug / "hiring-plan.md", root / "roles" / slug / "hiring-plan.md"):
        if plan.is_file():
            m = re.search(r"^- Hiring jurisdictions:\s*(.+)$", plan.read_text(encoding="utf-8"), re.M)
            if m:
                return m.group(1).strip()
    prefs = root / "preferences.md"
    if prefs.is_file():
        m = re.search(r"^hiring_jurisdictions:[ \t]*(.*)$", prefs.read_text(encoding="utf-8"), re.M)
        # Sofia stores unset keys as UNSET: that is "not recorded", not a place.
        if m and m.group(1).strip().strip('"').lower() not in UNSET_VALUES:
            return m.group(1).strip()
    return ""


def version_of(path: Path, meta: dict) -> int:
    try:
        return int(meta.get("version", ""))
    except ValueError:
        m = re.search(r"-v(\d+)\.md$", path.name)
        return int(m.group(1)) if m else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("role_slug")
    ap.add_argument("--root", default="~/workspace/hiring")
    ap.add_argument("--file")
    ap.add_argument("--emit-criteria")
    args = ap.parse_args()
    root = Path(args.root).expanduser()
    slug = args.role_slug

    candidates: list[tuple[Path, str]] = []
    if args.file:
        candidates.append((Path(args.file).expanduser(), "pasted"))
    else:
        candidates += [(p, "harper") for p in sorted((root / slug).glob("rubric-v*.md"))]
        candidates += [(p, "sofia") for p in sorted((root / "roles" / slug).glob("scorecard*.md"))]
    if not candidates:
        print(json.dumps({"error": f"no rubric or scorecard found for '{slug}' under {root}",
                          "next": "Harper: role-intake-and-job-description, then hiring-rubric-design. Sofia: role-intake-and-scorecard."}, indent=2))
        return 3

    approved, drafts = [], []
    for path, fmt in candidates:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(f"error: cannot read {path}: {exc}", file=sys.stderr)
            return 2
        meta = meta_of(text)
        item = (version_of(path, meta), path, fmt, meta, text)
        if meta.get("status", "").lower() == "approved" and meta.get("approved_by"):
            approved.append(item)
        else:
            drafts.append(item)

    if not approved:
        print(json.dumps({"error": "no approved rubric or scorecard",
                          "drafts": [str(d[1]) for d in drafts],
                          "next": "Ask the owner to approve it (hiring-rubric-design / role-intake-and-scorecard). Do not screen against a draft or a job description."}, indent=2))
        return 3

    ver, path, fmt, meta, text = max(approved, key=lambda x: (x[0], str(x[1])))
    sha_file = path.with_name(path.name + ".sha256")
    checksum = "missing"
    if sha_file.is_file():
        expected = sha_file.read_text(encoding="utf-8").split()[0]
        checksum = "ok" if hashlib.sha256(path.read_bytes()).hexdigest() == expected else "mismatch"

    reqs = {}
    req_file = path.parent / "requirements.csv"
    if req_file.is_file():
        rows, _ = screenio.read_csv(req_file)
        reqs = {r.get("req_id", "").strip(): r.get("group", "").strip() for r in rows}
    crit = criteria_harper(text, reqs) or criteria_sofia(text)

    juris = jurisdictions(root, slug)
    watch, confirm = law_watch_detail(juris)
    newer = [str(d[1]) for d in drafts if d[0] > ver]
    result = {
        "path": str(path), "format": fmt, "version": ver, "status": "approved",
        "approved_by": meta.get("approved_by", ""), "approved_on": meta.get("approved_on", ""),
        "approval_quote": meta.get("approval_quote", ""), "checksum": checksum,
        "newer_drafts": newer, "jurisdictions": juris or "not recorded", "law_watch": watch,
        "criteria": crit,
    }
    if confirm:
        result = {k: v for k, v in result.items() if k != "criteria"} | {"law_watch_confirm": confirm, "criteria": crit}
    if fmt == "harper" and checksum == "missing":
        result["error"] = ("approved header but not frozen: no .sha256 next to the rubric; run hiring-rubric-design's "
                           "approve_rubric.py with the owner's approval quote, then screen")
        print(json.dumps(result, indent=2))
        return 3
    if checksum == "mismatch":
        result["error"] = "the approved file changed after approval; stop and ask the owner to re-approve or create a new version"
        print(json.dumps(result, indent=2))
        return 4
    if not crit:
        print(json.dumps(result | {"error": "no criteria could be read; check the table header or M1/N1 lines"}, indent=2))
        return 2
    if args.emit_criteria:
        out = Path(args.emit_criteria).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"rubric": {k: result[k] for k in ("path", "format", "version", "approved_by", "approved_on", "checksum")},
                                   "criteria": crit}, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
