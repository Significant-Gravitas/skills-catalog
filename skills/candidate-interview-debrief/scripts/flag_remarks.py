#!/usr/bin/env python3
"""Propose exclusions for panel remarks that are labels, affect or protected-trait proxies.

Usage:
  cd ~/skills/candidate-interview-debrief && \
  python3 scripts/flag_remarks.py <debrief.json | notes.txt | notes.md | notes.csv> \
      [--lexicon scripts/remark_flags.csv] [--json]

Input
  * debrief.json from collate_scorecards.py (scans every evidence quote), or
  * any text, markdown or CSV file of panel notes (scans every line / cell).
Lexicon: scripts/remark_flags.csv, columns pattern,category,action,ask_or_note.
  action "exclude"            -> goes to the Excluded list with the note
  action "ask-for-behaviour"  -> ask the interviewer the question; exclude if
                                 no approved criterion and observed behaviour

It only proposes. It never deletes or edits a note. A person confirms each
exclusion so legitimate job evidence is not dropped (for example "confident
SQL" may be a job-related claim about a query, not affect; judge in context).
Sources: "fit" encodes evaluator similarity (Rivera, dossier [79]); affect is
not a rubric criterion, and an AI system inferring emotions in hiring is
prohibited in the EU (dossier [73]), so Harper never infers it either.

  python3 scripts/flag_remarks.py --selftest
runs known panel remarks against the lexicon and exits 1 if any expected
category fails to fire (or a clean remark fires), so a dead pattern is caught.
Exit 0 = no hits, 1 = hits to review, 2 = bad input (missing or non-UTF-8
file, malformed JSON or CSV, or a JSON file that is not a debrief.json).
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load_lexicon(path: Path) -> list[tuple]:
    rules = []
    for row in csv.DictReader(path.read_text(encoding="utf-8").splitlines()):
        try:
            rules.append((re.compile(row["pattern"], re.I), row["category"], row["action"], row["ask_or_note"]))
        except re.error as exc:
            print(f"error: bad pattern {row['pattern']!r}: {exc}", file=sys.stderr)
            sys.exit(2)
    return rules


class BadInput(Exception):
    pass


def remarks(path: Path) -> list[tuple[str, str]]:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        raise BadInput(f"{path} is not UTF-8 text; save it as UTF-8 and re-run")
    return remarks_from_text(text, path.suffix.lower())


def remarks_from_text(text: str, suffix: str) -> list[tuple[str, str]]:
    if suffix == ".json":
        try:
            data = json.loads(text)
        except ValueError as exc:
            raise BadInput(f"not valid JSON ({exc}); pass the debrief.json written by collate_scorecards.py")
        if not isinstance(data, dict) or not isinstance(data.get("cells", {}), dict):
            raise BadInput("not a debrief.json from collate_scorecards.py (no 'cells' object)")
        out = []
        for cid, cells in data.get("cells", {}).items():
            if not isinstance(cells, dict):
                raise BadInput(f"cells.{cid} is not an object; pass the debrief.json from collate_scorecards.py")
            for who, cell in cells.items():
                if not isinstance(cell, dict):
                    continue
                if cell.get("quote"):
                    out.append((f"{who} / {cid}", cell["quote"]))
                for other in cell.get("also", []):
                    if other.get("quote"):
                        out.append((f"{who} / {cid} ({other.get('file', 'second filing')})", other["quote"]))
        return out
    if suffix == ".csv":
        out = []
        try:
            for n, row in enumerate(csv.DictReader(text.splitlines()), start=2):
                for k, v in row.items():
                    if isinstance(v, list):
                        v = ", ".join(x for x in v if x)
                    if v and len(v) > 3:
                        out.append((f"row {n} / {k}", v))
        except csv.Error as exc:
            raise BadInput(f"cannot read the CSV ({exc})")
        return out
    return [(f"line {n}", ln.strip()) for n, ln in enumerate(text.splitlines(), start=1) if ln.strip()]


SELFTEST_POSITIVE = [
    ("fit", "not sure she'd gel with the team"), ("fit", "Luis: not a culture fit."),
    ("fit", "Tom: great vibe."), ("label-no-behaviour", "great energy, very polished"),
    ("affect", "seemed nervous throughout"), ("affect", "Priya: seemed anxious and fidgety."),
    ("affect", "Tom: lacked confidence when explaining joins."), ("affect", "poor eye contact"),
    ("age", "Maya: probably too old to learn our stack."),
    ("age", "Priya: he is overqualified, might get bored."),
    ("family", "Tom: she has young kids so evenings could be hard."),
    ("family", "Maya: is she pregnant? she mentioned leave."),
    ("origin", "Priya: very articulate for someone whose English is a second language."),
    ("origin", "English isn't her first language"), ("origin", "strong accent"),
    ("religion", "Maya: wears a headscarf, might not fit client meetings."),
    ("religion", "needs breaks for prayers"), ("religion", "wears a turban"),
    ("religion", "wears a kippah"), ("religion", "very observant, leaves early Fridays"),
    ("appearance", "scruffy for an interview"), ("health", "mentioned her medication"),
    ("gap", "gap in her CV"), ("prestige", "big-name school"),
    ("automated", "the AI score said 62"),
    # review-2-r3 notes3.txt phrasings
    ("family", "Maya: she's a mum of three, worried about evenings."), ("family", "single dad"),
    ("fit", "Luis: seemed like a good cultural match."), ("fit", "strong culture add"),
    ("label-no-behaviour", "Zoe: I didn't love her attitude."),
    ("honesty", "Tom: wasn't sure he was being straight with us."), ("honesty", "not trustworthy"),
    ("origin", "Priya: his English was hard to follow."),
    ("age", "Tom: she's in her fifties."), ("age", "Maya: he's a recent grad."),
    ("religion", "Luis: she wears a hijab, clients might react."),
]
SELFTEST_CLEAN = [
    "Query ran and totals matched for 40 of 43 invoices but missed the duplicate invoices in the sample.",
    "Rewrote the escalation guide used by the 12-person support team.",
]


def selftest(rules) -> int:
    bad = 0
    for cat, text in SELFTEST_POSITIVE:
        fired = {c for rx, c, _, _ in rules if rx.search(text)}
        if cat not in fired:
            print(f"FAIL {cat} did not fire on: {text}")
            bad += 1
    for text in SELFTEST_CLEAN:
        fired = {c for rx, c, _, _ in rules if rx.search(text)}
        if fired:
            print(f"FAIL clean remark hit {sorted(fired)}: {text}")
            bad += 1
    for bad_input in ("{not json", "[1, 2]"):
        try:
            remarks_from_text(bad_input, ".json")
            print(f"FAIL malformed debrief.json accepted: {bad_input!r}")
            bad += 1
        except BadInput:
            pass
    print("selftest OK" if not bad else f"selftest: {bad} failure(s)")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?")
    ap.add_argument("--lexicon", default=str(HERE / "remark_flags.csv"))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest(load_lexicon(Path(a.lexicon)))
    if not a.input:
        ap.error("input is required unless --selftest is given")
    p = Path(a.input).expanduser()
    if not p.is_file():
        print(f"error: not found: {p}", file=sys.stderr)
        return 2
    rules = load_lexicon(Path(a.lexicon))
    try:
        items = remarks(p)
    except BadInput as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    hits = []
    for where, text in items:
        for rx, cat, action, note in rules:
            m = rx.search(text)
            if m:
                hits.append({"where": where, "text": text, "match": m.group(0),
                             "category": cat, "action": action, "note": note})
    if a.json:
        print(json.dumps(hits, indent=2))
    else:
        for h in hits:
            print(f"[{h['action']}] {h['category']} '{h['match']}' at {h['where']}\n"
                  f"    \"{h['text']}\"\n    -> {h['note']}")
        print(f"{len(hits)} proposal(s). A person confirms each; nothing was removed."
              if hits else "No lexicon hits. Still read every remark against the rubric.")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
