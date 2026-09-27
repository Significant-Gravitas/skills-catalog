#!/usr/bin/env python3
"""Check that a posting's must-haves mirror the approved scorecard word for word.

Usage (cd ~/skills/job-description-drafting first):
    python3 scripts/mirror_check.py <scorecard.md> <posting.md>

Scorecard: Sofia's role scorecard (role-intake-and-scorecard), must-haves as
           "- M1: <text>" lines under "## Must-haves". Without M-ids, every
           top-level bullet in that section is used.
           A trailing "HM defended: <quote>" on a must-have line (how
           role-intake-and-scorecard records a defended years or degree floor)
           is internal and is stripped before comparing, so the posting carries
           the floor without the HM's note.
Posting:   the bullets under the first heading (## or **bold** line) whose text
           contains "you have", "you'll need", "what you need", "must-have",
           "requirements", "qualifications", "about you" or "what you bring",
           and that does not read as optional ("Preferred qualifications" is a
           nice-to-have heading, never the must-have one).
           Pass --heading "<text>" to name another heading.
Output:    MATCH / CHANGED (with both texts) / MISSING (in scorecard, not in
           posting) / ADDED (in posting, not in scorecard), then a summary.
           Nice-to-haves: under every posting heading that reads as optional
           ("nice", "bonus points", "preferred", "a plus", "pluses", "even
           better", "would be great", "great/good to have"), every
           posting nice-to-have must match a bullet under the scorecard's
           "## Nice-to-haves" ("- N1: ..." or a plain "- ..." bullet); one that
           does not is ADDED (a new nice-to-have goes through a scorecard
           revision too). Placeholders ("- none agreed", "UNSET", "<...>") and a
           missing or empty section allow zero lines, so then EVERY posting
           nice-to-have is ADDED. Scorecard nice-to-haves left out of the
           posting are fine.
           Example: scorecard "## Nice-to-haves / - none agreed" + posting
           "## Nice to have / - Kubernetes expert" -> "ADDED nice-to-have:
           Kubernetes expert (the scorecard has no agreed nice-to-haves ...)",
           exit 1.
Exit:      0 all must-haves match and nothing added; 1 any difference;
           2 unreadable input or no must-have section found.

Normalisation before comparing: case, punctuation, whitespace, and a leading
"has"/"have"/"you have"/"you've" are ignored, so "Has run on-call..." in the
scorecard matches "run on-call...;" in a "You have" list. Stdlib only.
"""

import difflib
import re
import sys
from pathlib import Path

CHANGED_MIN = 0.6  # below this similarity a line counts as MISSING/ADDED, not CHANGED
POSTING_HEAD_RE = re.compile(r"(you have|you've|you'll need|you will need|what you need|you need|must[- ]haves?|requirements|qualifications|about you|what you bring)", re.I)
NICE_HEAD_RE = re.compile(r"\bnice\b|\bbonus points?\b|\bpreferred\b|\bpluses\b|\ba plus\b|even better|would be great|(great|good) to have", re.I)
DEFENDED_RE = re.compile(r"[\s;,.(\-–—]*\bHM defended:.*$", re.I)


def read(p: str) -> str:
    try:
        return Path(p).expanduser().read_text(encoding="utf-8").replace("\r\n", "\n")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: cannot read {p}: {exc}", file=sys.stderr)
        sys.exit(2)


def norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"\*\*|__|`", "", s)
    s = re.sub(r"^(you have|you've|you|has|have)\s+", "", s.strip())
    s = re.sub(r"[^\w\s+#/-]", " ", s)
    return " ".join(s.split())


def scorecard_musts(text: str):
    m = re.search(r"^## Must-haves\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m:
        return None
    block = re.sub(r"<!--.*?-->", "", m.group(1), flags=re.S)
    ided = re.findall(r"^- (M\d+):\s*(.+)$", block, re.M)
    if ided:
        return [(i, DEFENDED_RE.sub("", t).strip()) for i, t in ided]
    plain = re.findall(r"^- (.+)$", block, re.M)
    return [(f"#{n}", DEFENDED_RE.sub("", t).strip()) for n, t in enumerate(plain, 1)]


NICE_PLACEHOLDER_RE = re.compile(r"^(none( .*)?|n/?a|unset|tbd|<[^>]*>|\.\.\.|-)$", re.I)


def scorecard_nices(text: str):
    """Agreed nice-to-haves, with or without N-ids. Placeholders ('none agreed',
    'UNSET', '<...>') are ignored, so an empty or missing section allows zero."""
    m = re.search(r"^## Nice-to-haves\s*$(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m:
        return []
    block = re.sub(r"<!--.*?-->", "", m.group(1), flags=re.S)
    out = []
    for n, t in enumerate(re.findall(r"^- (.+)$", block, re.M), 1):
        ided = re.match(r"(N\d+):\s*(.*)$", t.strip())
        nid, body = (ided.group(1), ided.group(2)) if ided else (f"#{n}", t)
        body = body.strip()
        if not body or NICE_PLACEHOLDER_RE.match(body.rstrip(".").strip()):
            continue
        out.append((nid, body))
    return out


def posting_musts(text: str, head_re=POSTING_HEAD_RE, nice=False):
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        stripped = line.strip().lstrip(">").strip()
        is_head = stripped.startswith("#") or (stripped.startswith("**") and stripped.count("**") >= 2)
        if is_head and head_re.search(stripped) and (head_re is not POSTING_HEAD_RE or bool(NICE_HEAD_RE.search(stripped)) == nice):
            start = i + 1
            break
    if start is None:
        return None
    return bullets_from(lines, start)


def bullets_from(lines, start):
    out = []
    for line in lines[start:]:
        stripped = line.strip().lstrip(">").strip()
        if stripped.startswith(("- ", "* ")):
            out.append(stripped[2:].strip().rstrip(";.").strip())
        elif stripped.startswith("#") or stripped.startswith("**"):
            break
        elif stripped and out:
            break
    return out


def posting_nices(text: str):
    """Bullets under every heading that reads as optional (nice/bonus/preferred/...)."""
    lines, out = text.splitlines(), []
    for i, line in enumerate(lines):
        stripped = line.strip().lstrip(">").strip()
        is_head = stripped.startswith("#") or (stripped.startswith("**") and stripped.count("**") >= 2)
        if is_head and NICE_HEAD_RE.search(stripped):
            out.extend(bullets_from(lines, i + 1))
    return out


def main(argv):
    head_re = POSTING_HEAD_RE
    if "--heading" in argv:
        i = argv.index("--heading")
        if i + 1 >= len(argv):
            print(__doc__, file=sys.stderr)
            return 2
        head_re = re.compile(re.escape(argv[i + 1]), re.I)
        argv = argv[:i] + argv[i + 2:]
    if len(argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    sc_text = read(argv[1])
    sc = scorecard_musts(sc_text)
    if not sc:
        print("error: no '## Must-haves' section with bullets in the scorecard", file=sys.stderr)
        return 2
    po_text = read(argv[2])
    po = posting_musts(po_text, head_re)
    if po is None:
        print("error: no must-have heading in the posting (e.g. '**You have**' or '## What you have done')", file=sys.stderr)
        return 2
    remaining = list(po)
    diffs = 0
    for mid, text in sc:
        best, score = None, 0.0
        for cand in remaining:
            r = difflib.SequenceMatcher(None, norm(text), norm(cand)).ratio()
            if r > score:
                best, score = cand, r
        if best is not None and score == 1.0:
            print(f"MATCH   {mid}: {text}")
            remaining.remove(best)
        elif best is not None and score >= CHANGED_MIN:
            print(f"CHANGED {mid}: scorecard: {text}\n        posting:   {best}  (similarity {score:.2f})")
            remaining.remove(best)
            diffs += 1
        else:
            print(f"MISSING {mid}: {text}")
            diffs += 1
    for extra in remaining:
        print(f"ADDED   {extra}  (not on the scorecard; cut it, or revise the scorecard first)")
        diffs += 1
    nices = scorecard_nices(sc_text)
    po_nice = posting_nices(po_text)
    # Always checked: with no agreed nice-to-haves on the scorecard, every
    # posting nice-to-have is ADDED (the posting never sets the bar).
    for line in po_nice:
        if not any(norm(line) == norm(t) for _, t in nices):
            why = "no matching scorecard nice-to-have" if nices else "the scorecard has no agreed nice-to-haves"
            print(f"ADDED   nice-to-have: {line}  ({why}; revise the scorecard first or cut it)")
            diffs += 1
    print(f"summary: {len(sc)} scorecard must-haves, {len(po)} posting lines, {len(po_nice)} nice-to-haves, {diffs} differences")
    return 1 if diffs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
