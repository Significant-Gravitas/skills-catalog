#!/usr/bin/env python3
"""Check a hiring plan against the template contract.

Usage:
  python3 scripts/plan_check.py <hiring-plan.md> [--json]

Input:  a plan made from templates/hiring-plan.md.
Checks: every heading and "- Field:" line the other Harper skills read is
        present; the role_slug line is set; every policy row has "stated by"
        and a date unless it is OPEN; pay is OPEN or carries "APPROVED by";
        no field is left blank; no leftover <placeholder> text.
Output: ERROR lines (must fix), WARN lines (should fix), then the list of
        OPEN items, each of which needs an owner in "Open approvals" or
        "Open questions".
Exit:   0 no errors, 1 errors, 2 unreadable file.
Stdlib only, no network.
"""

import json
import re
import sys
from pathlib import Path

HEADINGS = [
    "Role", "Owners and decision rights", "Terms", "Policies", "Existing materials",
    "Stages", "Jurisdiction flags (for the people lead; not legal advice)",
    "Open approvals", "Open questions", "Change log",
]
FIELDS = {
    "Role": ["Title", "Outcome (what is different six months after the start)",
             "Work the person must deliver", "Reason for the hire"],
    "Owners and decision rights": ["Hiring manager", "Final decision-maker", "Headcount approver",
                                   "JD approver", "Rubric approver", "Candidate-message approver",
                                   "Default sender", "Offer approver", "Coordinator", "Interviewers"],
    "Terms": ["Start window", "Location and work terms", "Hiring jurisdictions", "Level", "Pay range"],
}
POLICIES = ["Accommodation route", "Data retention and talent pool", "Required posting text",
            "Candidates' AI use", "Background checks", "AI tools used in screening or interviews",
            "US federal contractor"]
# Rows added after plans already existed: a missing one is an OPEN item, not an error.
LATER_POLICIES = {"US federal contractor"}
PROXY_WORDS = re.compile(r"\b(zip|postcode|post code|commute|within \d+ (miles|km)|culture fit|young|digital native)\b", re.I)


def sections(text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            current = m.group(1)
            out[current] = []
        elif current is not None:
            out[current].append(line)
    return out


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    if len(args) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    path = Path(args[0]).expanduser()
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: cannot read {path}: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []
    warns: list[str] = []
    open_items: list[str] = []

    slug = re.search(r"^role_slug:\s*(\S+)", text, re.M)
    if not slug or slug.group(1).startswith("<"):
        errors.append("role_slug line missing or not filled")
    if re.search(r"<(Role title|role-slug|YYYY-MM-DD)>", text):
        errors.append("template placeholder left in the file (<Role title>, <role-slug> or <YYYY-MM-DD>)")

    secs = sections(text)
    for h in HEADINGS:
        if h not in secs:
            errors.append(f"heading missing: '## {h}'")

    for sec, names in FIELDS.items():
        lines = secs.get(sec, [])
        for name in names:
            hit = [l for l in lines if l.strip().startswith(f"- {name}:")]
            if not hit:
                errors.append(f"field missing under '{sec}': '- {name}:'")
                continue
            value = hit[0].split(":", 1)[1].strip()
            if not value:
                errors.append(f"'{name}' is blank; write a value or OPEN")
            elif value.upper().startswith("OPEN"):
                open_items.append(name)
            if name == "Pay range" and value and not value.upper().startswith("OPEN") and "APPROVED BY" not in value.upper():
                errors.append("Pay range must be OPEN or '<range> (APPROVED by <name>, <date>)'")
            if name == "Location and work terms" and PROXY_WORDS.search(value):
                warns.append("Location uses a postcode, commute or proxy term; write work terms (country or state, hours, onsite days, travel)")

    policy_lines = [l for l in secs.get("Policies", []) if l.strip().startswith("|")]
    for name in POLICIES:
        row = [l for l in policy_lines if l.strip().startswith(f"| {name} |")]
        if not row:
            if name in LATER_POLICIES:
                open_items.append(f"policy: {name} (row missing; add it)")
            else:
                errors.append(f"policy row missing: '{name}'")
            continue
        cells = [c.strip() for c in row[0].strip().strip("|").split("|")]
        while len(cells) < 4:
            cells.append("")
        stated, by, date = cells[1], cells[2], cells[3]
        if not stated or stated.upper().startswith("OPEN"):
            open_items.append(f"policy: {name}")
        elif not by or not date:
            errors.append(f"policy '{name}' needs 'stated by' and a date")

    for sec in ("Open approvals", "Open questions"):
        body = [l for l in secs.get(sec, []) if l.strip().startswith("-")]
        if open_items and all("none yet" in l for l in body) and sec == "Open questions":
            warns.append("OPEN items exist but 'Open questions' says none yet; add one line per item with who can settle it")

    result = {"file": str(path), "errors": errors, "warnings": warns, "open": open_items}
    if as_json:
        print(json.dumps(result, indent=2))
    else:
        for e in errors:
            print(f"ERROR {e}")
        for w in warns:
            print(f"WARN  {w}")
        print(f"OPEN  {len(open_items)} item(s): " + ("; ".join(open_items) if open_items else "none"))
        print("OK" if not errors else f"{len(errors)} error(s); fix them before delivering the plan")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
