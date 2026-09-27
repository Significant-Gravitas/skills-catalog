#!/usr/bin/env python3
"""Match hiring locations and process facts to jurisdiction flags.

Usage:
  python3 scripts/policy_flags.py --locations "Denver, CO; Remote (UK)" \
      [--ai-screening yes|no|unknown] [--video-interviews yes|no|unknown] \
      [--background-check yes|no|unknown] [--talent-pool yes|no|unknown] \
      [--federal-contractor yes|no|unknown] [--json]

Input:  free-text locations (cities, US state names or ", XX" codes,
        countries, "US", "Remote (US)"), plus yes/no/unknown answers from the
        hiring plan. The list is split into places on ';', newline, '/', '&',
        ' and ', ' or ' and on commas (not inside brackets); a comma followed
        by a US state code or name or a country keeps it with the place before
        it. So "Chicago, London" is two places, while "Boston, MA", "London,
        Ontario" and "Paris, France" are one. Each place is judged on its own.
        A city name counts only when its own place names no other US
        state or country: "Birmingham, AL", "Manchester, NH", "Dublin, OH"
        and "Paris, TX" are US only (with a NOTE to confirm the country);
        "Brooklyn Park, MN" is not New York City; "Sydney, New South Wales"
        and "London, Ontario" are not recognised; "Tbilisi, Georgia" is not
        the US, and "Georgia" alone gets the US flags plus a NOTE asking
        which Georgia. Whenever a city match is dropped this way, a NOTE
        asks the owner to confirm the place.
Data:   references/jurisdiction-triggers.csv (dated rows, each with sources).
Output: one flag per line, ready to paste into the plan's "Jurisdiction
        flags" section; every flag ends "may apply; confirm with counsel".
        --json prints the same as a list of objects.
Exit:   0 flags printed (or none matched), 2 bad input or missing data file.

The flags are prompts for the people lead, never legal advice. Stdlib only,
no network.
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "references" / "jurisdiction-triggers.csv"

US_STATES = (
    "AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO "
    "MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC"
).split()

# Region detectors. Case-insensitive name patterns plus case-sensitive
# ", XX" state codes so "Denver, CO" matches but "co-located" does not.
# Country, state and region names: always count.
REGIONS = {
    "NYC": [r"\bnew york city\b", r"\bnyc\b", r"\bnew york,\s*ny\b"],
    "IL": [r"\billinois\b"],
    "CA": [r"\bcalifornia\b", r"\bbay area\b"],
    "CO": [r"\bcolorado\b"],
    "US": [r"\bunited states\b", r"\busa\b", r"\bu\.s\.a?\.?", r"\(us\)", r"\bus[- ]based\b",
           r"\bremote \(us\)"],
    "UK": [r"\buk\b", r"\bu\.k\.", r"\bunited kingdom\b", r"\bengland\b", r"\bscotland\b",
           r"(?<!new south )\bwales\b", r"\bnorthern ireland\b"],
    "EU": [r"\beu\b", r"\beea\b", r"\beuropean union\b", r"\baustria\b", r"\bbelgium\b",
           r"\bbulgaria\b", r"\bcroatia\b", r"\bcyprus\b", r"\bczech", r"\bdenmark\b",
           r"\bestonia\b", r"\bfinland\b", r"\bfrance\b", r"\bgermany\b", r"\bgreece\b",
           r"\bhungary\b", r"\bireland\b", r"\bitaly\b", r"\blatvia\b", r"\blithuania\b",
           r"\bluxembourg\b", r"\bmalta\b", r"\bnetherlands\b", r"\bpoland\b", r"\bportugal\b",
           r"\bromania\b", r"\bslovakia\b", r"\bslovenia\b", r"\bspain\b", r"\bsweden\b"],
}
# City names: count only when the location names no other country or US state, because the
# same names exist elsewhere ("Birmingham, AL", "Dublin, OH", "Paris, TX", "London, Ontario",
# "Brooklyn Park, MN"). The value is the US state a US city is in (None outside the US).
CITIES = {
    "NYC": ("NY", [r"\bmanhattan\b", r"\bbrooklyn\b(?!\s+(?:park|center|centre)\b)", r"\bqueens\b",
                   r"\bbronx\b", r"\bstaten island\b"]),
    "IL": ("IL", [r"\bchicago\b"]),
    "CA": ("CA", [r"\bsan francisco\b", r"\blos angeles\b", r"\bsan diego\b", r"\bsan jose\b",
                  r"\boakland\b", r"\bsacramento\b", r"\bpalo alto\b"]),
    "CO": ("CO", [r"\bdenver\b", r"\bboulder\b"]),
    "UK": (None, [r"\blondon\b", r"\bmanchester\b", r"\bedinburgh\b", r"\bglasgow\b", r"\bbirmingham\b",
                  r"\bbristol\b", r"\bleeds\b", r"\bcardiff\b", r"\bbelfast\b"]),
    "EU": (None, [r"\bberlin\b", r"\bparis\b", r"\bamsterdam\b", r"\bdublin\b", r"\bmadrid\b",
                  r"\blisbon\b", r"\bmunich\b", r"\bwarsaw\b", r"\bstockholm\b"]),
}
# Countries and regions this checklist has no rows for. Naming one turns off city matches
# ("London, Ontario", "Sydney, New South Wales"); the location then gets a "not recognised" note.
OTHER_PLACES = (r"\b(canada|ontario|quebec|british columbia|alberta|australia|new south wales|victoria, au|queensland|"
                r"new zealand|india|singapore|south africa|mexico|brazil|japan|china|philippines|nigeria|kenya|"
                r"switzerland|norway|iceland|turkey|israel|uae|united arab emirates|tbilisi|batumi|kutaisi|"
                r"georgia \(country\))\b")
STATE_CODE = {"NY": None, "IL": "IL", "CA": "CA", "CO": "CO"}
# Full US state names. Any match adds US; the value adds a state region where
# this checklist has one. "New York" is handled separately (city or state?).
STATE_NAMES = {
    "alabama": None, "alaska": None, "arizona": None, "arkansas": None,
    "california": "CA", "colorado": "CO", "connecticut": None, "delaware": None,
    "florida": None, "georgia": None, "hawaii": None, "idaho": None,
    "illinois": "IL", "indiana": None, "iowa": None, "kansas": None,
    "kentucky": None, "louisiana": None, "maine": None, "maryland": None,
    "massachusetts": None, "michigan": None, "minnesota": None,
    "mississippi": None, "missouri": None, "montana": None, "nebraska": None,
    "nevada": None, "new hampshire": None, "new jersey": None,
    "new mexico": None, "north carolina": None, "north dakota": None,
    "ohio": None, "oklahoma": None, "oregon": None, "pennsylvania": None,
    "rhode island": None, "south carolina": None, "south dakota": None,
    "tennessee": None, "texas": None, "utah": None, "vermont": None,
    "virginia": None, "washington": None, "west virginia": None,
    "wisconsin": None, "wyoming": None, "district of columbia": None,
}
# Case-sensitive country codes, checked on the original string so the letters
# "us" inside ordinary words never match.
US_CASED = [r"\bUS\b", r"\bU\.S\.", r"\bUSA\b"]
NY_STATE = r"\bnew york state\b|\bstate of new york\b|\bnew york \(state\)"
ANSWERS = {"yes", "no", "unknown"}
CONDITION_LABEL = {
    "ai_screening": "If an AI tool screens or ranks applicants",
    "video_interviews": "If AI analyses video interviews",
    "background_check": "If background checks are run",
    "talent_pool": "If unsuccessful candidates are kept in a talent pool",
    "federal_contractor": "If the company is a US federal contractor",
}


SEPARATOR = re.compile(r"[;\n/&,]|\s+(?:and|or)\s+", re.I)


def is_qualifier(segment: str) -> bool:
    """True when a comma segment starts with a US state code or name, or a country or region."""
    seg = segment.strip()
    m = re.match(r"([A-Z]{2})\b", seg)
    if (m and m.group(1) in US_STATES) or any(re.match(p, seg) for p in US_CASED):
        return True
    low = seg.lower()
    pats = [r"\b" + n + r"\b" for n in STATE_NAMES] + [r"\bnew york\b", OTHER_PLACES]
    for region in ("US", "UK", "EU"):
        pats += REGIONS[region]
    return any(re.match(p, low) for p in pats)


def split_places(text: str) -> list[str]:
    """Split a free-text location list into places, one jurisdiction each.

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


def bare_new_york(location: str) -> bool:
    """True when 'New York' appears with no sign of whether it is the city or the state."""
    low = location.lower()
    if not re.search(r"\bnew york\b", low):
        return False
    return not re.search(r"\bnew york city\b|\bnew york,\s*ny\b|" + NY_STATE, low)


def us_states_named(location: str) -> set[str]:
    """US state codes the location names (", XX" codes and full state names)."""
    low = location.lower()
    out = {c for c in re.findall(r",\s*([A-Z]{2})\b", location) if c in US_STATES}
    names = {v: k for k, v in {"AL": "alabama", "AK": "alaska", "AZ": "arizona", "AR": "arkansas", "CA": "california",
             "CO": "colorado", "CT": "connecticut", "DE": "delaware", "FL": "florida", "GA": "georgia", "HI": "hawaii",
             "ID": "idaho", "IL": "illinois", "IN": "indiana", "IA": "iowa", "KS": "kansas", "KY": "kentucky",
             "LA": "louisiana", "ME": "maine", "MD": "maryland", "MA": "massachusetts", "MI": "michigan",
             "MN": "minnesota", "MS": "mississippi", "MO": "missouri", "MT": "montana", "NE": "nebraska",
             "NV": "nevada", "NH": "new hampshire", "NJ": "new jersey", "NM": "new mexico", "NC": "north carolina",
             "ND": "north dakota", "OH": "ohio", "OK": "oklahoma", "OR": "oregon", "PA": "pennsylvania",
             "RI": "rhode island", "SC": "south carolina", "SD": "south dakota", "TN": "tennessee", "TX": "texas",
             "UT": "utah", "VT": "vermont", "VA": "virginia", "WA": "washington", "WV": "west virginia",
             "WI": "wisconsin", "WY": "wyoming", "DC": "district of columbia"}.items()}
    for name, code in names.items():
        if re.search(r"\b" + name + r"\b", low) and not (code == "GA" and georgia_country(location)):
            out.add(code)
    if re.search(r"\bnew york\b", low):
        out.add("NY")
    return out


def georgia_country(location: str) -> bool:
    """'Georgia' with a sign of the country (Tbilisi, Batumi, 'Georgia (country)')."""
    return bool(re.search(r"\b(tbilisi|batumi|kutaisi|georgia \(country\))\b", location, re.I))


def georgia_unclear(location: str) -> bool:
    """'Georgia' alone: the US state or the country?"""
    low = location.lower()
    if not re.search(r"\bgeorgia\b", low) or georgia_country(location):
        return False
    us_context = (re.search(r",\s*GA\b", location) or any(re.search(p, location) for p in US_CASED)
                  or re.search(r"\b(united states|atlanta|savannah|augusta|athens, ga|macon|columbus, ga)\b", low)
                  or len(us_states_named(location) - {"GA"}) > 0)
    return not us_context


def detect_regions(location: str) -> set[str]:
    found: set[str] = set()
    low = location.lower()
    for region, patterns in REGIONS.items():
        if any(re.search(p, low) for p in patterns):
            found.add(region)
    states = us_states_named(location)
    other_country = bool(re.search(OTHER_PLACES, low))
    for region, (home, patterns) in CITIES.items():
        if not any(re.search(p, low) for p in patterns):
            continue
        if home is None:
            # A UK or EU city counts only when no US state or other country is named with it.
            if not states and not other_country and not (found & {"US"}):
                found.add(region)
        elif not other_country and (not states or home in states) and not (found & {"UK", "EU"}):
            found.add(region)
    if any(re.search(p, location) for p in US_CASED):
        found.add("US")
    for name, code in STATE_NAMES.items():
        if re.search(r"\b" + name + r"\b", low):
            if name == "georgia" and georgia_country(location):
                continue
            found.add("US")
            if code:
                found.add(code)
    if re.search(NY_STATE, low):
        found.add("US")
    if bare_new_york(location):
        # City or state is unclear: flag NYC too, and main() asks which.
        found |= {"NYC", "US"}
    for code in re.findall(r",\s*([A-Z]{2})\b", location):
        if code in US_STATES:
            found.add("US")
            if code in STATE_CODE and STATE_CODE[code]:
                found.add(STATE_CODE[code])
    # Northern Ireland also contains "ireland"; do not treat it as the EU.
    if "northern ireland" in low and not re.search(r"(?<!northern )ireland", low):
        found.discard("EU")
    if found & {"NYC", "IL", "CA", "CO"}:
        found.add("US")
    return found


def load_rows() -> list[dict]:
    if not DATA.is_file():
        sys.exit(f"error: data file missing at {DATA}; re-run read_skill to re-sync the package")
    with DATA.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--locations", required=True)
    for name in CONDITION_LABEL:
        ap.add_argument("--" + name.replace("_", "-"), default="unknown")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    answers = {}
    for name in CONDITION_LABEL:
        value = getattr(args, name).strip().lower()
        if value not in ANSWERS:
            print(f"error: --{name.replace('_', '-')} must be yes, no or unknown, got '{value}'", file=sys.stderr)
            return 2
        answers[name] = value

    locations = split_places(args.locations)
    if not locations:
        print("error: --locations is empty; list where the role is posted and hired", file=sys.stderr)
        return 2

    rows = load_rows()
    flags: list[dict] = []
    notes: list[str] = []
    regions: set[str] = set()
    per_location: list[tuple[str, set[str]]] = []
    for loc in locations:
        found = detect_regions(loc)
        per_location.append((loc, found))
        if re.search(r"\bremote\b", loc, re.I):
            notes.append(f"'{loc}': remote roles follow where candidates live and work; name the countries or states you will hire in.")
        if not found:
            notes.append(f"'{loc}': location not recognised by this checklist; restate it as a country, US state or city, and ask the people lead which posting and screening rules apply there.")
        for region, (home, patterns) in CITIES.items():
            if region in found or not any(re.search(p, loc.lower()) for p in patterns):
                continue
            if home is None:
                notes.append(f"'{loc}': the city name also exists in the {region}; it was read with the state or country named, so no {region} rules are flagged. Confirm the country with the owner.")
            else:
                notes.append(f"'{loc}': names a city this checklist reads as {region}, but it was read with the other state or country named with it, so no {region} rules are flagged for the city. Confirm the place with the owner.")
        if georgia_unclear(loc):
            notes.append(f"'{loc}': 'Georgia' could be the US state or the country; US flags are shown in case it is the state. Ask the owner which one.")
        if re.search(OTHER_PLACES, loc.lower()) and found:
            notes.append(f"'{loc}': names a country or region this checklist does not cover; the flags above come from the other places named. Ask the people lead which rules apply there.")
        if bare_new_york(loc):
            notes.append(f"'{loc}': 'New York' could mean the city or the state; New York City rules are flagged in case it is the city. Ask the owner which one.")
        regions |= found

    seen: set[str] = set()
    for row in rows:
        if row["region"] not in regions or row["id"] in seen:
            continue
        cond = row["condition"].strip()
        prefix = ""
        if cond:
            answer = answers.get(cond, "unknown")
            if answer == "no":
                continue
            if answer == "unknown":
                prefix = CONDITION_LABEL[cond] + ": "
        seen.add(row["id"])
        flags.append({
            "id": row["id"],
            "region": row["region"],
            "text": f"{prefix}{row['flag']} May apply; confirm with counsel.",
            "sources": row["sources"],
            "checked_on": row["checked_on"],
        })

    flagged_regions = {f["region"] for f in flags}
    for loc, found in per_location:
        if found and not (found & flagged_regions):
            notes.append(f"'{loc}': recognised as {', '.join(sorted(found))}, but no row in this checklist applies there with these answers; ask the people lead which posting and screening rules apply.")

    if args.json:
        print(json.dumps({"regions": sorted(regions), "flags": flags, "notes": notes}, indent=2))
        return 0
    print(f"Regions matched: {', '.join(sorted(regions)) or 'none'}")
    for f in flags:
        print(f"- [{f['region']}] {f['text']} Sources: {f['sources']}. Checked {f['checked_on']}.")
    for n in notes:
        print(f"- NOTE {n}")
    if not flags and not notes:
        print("- No flags. Still ask the people lead to confirm posting text and retention.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
