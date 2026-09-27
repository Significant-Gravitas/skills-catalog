#!/usr/bin/env python3
"""Remove one candidate from the hiring folder, in the same reply the owner asks.

    cd ~/skills/interview-coordination && python3 scripts/forget_candidate.py --name "<Full Name>" \
        [--role "<role>"] [--keep-dnc | --drop-dnc] [--dry-run] [--hiring ~/workspace/hiring]

What it touches (everything under --hiring, default ~/workspace/hiring):
- CSV files: deletes every row whose name/candidate column matches the person
  (case, accents, punctuation and spacing folded). With --role, only rows whose
  role column matches too (rows with no role column still match on name).
- Files about the person (their full name slug in the file or folder name, on
  word boundaries, e.g. packets, briefs, their debrief folder, screens):
  deleted. "Jo Park" never matches "jo-parker". With --role, only when the
  path also names that role (again on word boundaries). A scorecard file named after an
  interviewer (debriefs/<role>/<other-candidate>/scorecards/<name>.md) sits
  under another candidate's folder: it is never deleted or redacted, only
  listed as "skipped" so the owner can check it is a different person.
- Other text files (.md .txt .json notes) that merely mention them, such as a
  weekly report: each mention is replaced with "[removed]", except on a line
  where the name sits in an interviewer context ("interviewer:", "interviewers",
  "rated by", "panel", "speakers", or a brief's roll-call or rating line such as
  "- Dev Rao (M3): filed" or "- Dev Rao, 4:"): that mention may be a colleague with the same name, so
  it is left untouched and listed as "check with owner".
- CSV files are never text-redacted: only rows whose name/candidate column
  matches are deleted. A CSV that still mentions the name in another column
  (for example an interviewers column in loops.csv) is listed as "check with
  owner".
- dnc.csv: an existing do-not-contact row for them is ALWAYS kept, normalised
  to "name,do-not-contact" (persona: for a do-not-contact person, the name and
  the flag are all you keep), so no later batch re-sources them.
- --keep-dnc: also adds that row when there was none (use it when the removal
  request comes from the candidate, or is a do-not-contact request).
- --drop-dnc: removes the do-not-contact row too. Only on the owner's explicit
  order to lift the flag; never on a candidate's own request.
Name matching folds accents and case everywhere (rows and text mentions):
removing "Zoë Müller" also removes "Zoe Muller". The whole plan is walked
read-only first, so an unreadable file stops the run before anything is
deleted. CSV rows are read as raw lists: a ragged row (an unquoted comma in
someone else's notes) is kept as it was and listed as "needs a look".
It never prints removed content: only file paths and counts.

Run --dry-run first to see the list and read every path in it for another
person's name. If the dry run shows rows for the same name under two different
roles and the owner named one role, ask which person they mean (it may be two
people); otherwise apply at once.

Not covered (the procedure does these): memory facts (memory_forget), copies
delivered to the cloud workspace (list_workspace_files + delete_workspace_file),
Gmail/Calendar/Sheets content, and the ATS itself.
Record-retention rules may require keeping hiring records (US: at least one year,
29 CFR 1602.14); the procedure adds that one line.

Exit 0 on success (or nothing found), 2 on bad input. --selftest uses a temp folder.
"""

import argparse
import csv
import io
import os
import re
import shutil
import sys
import tempfile
import unicodedata

NAME_COLS = ("name", "candidate", "full_name", "candidate_name")
TEXT_EXT = (".md", ".txt", ".json", ".csv")


def fold(t):
    t = unicodedata.normalize("NFKD", t or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", t).split())


def slug(t):
    return fold(t).replace(" ", "-")


def names(s, text):
    """True when slug s appears in slug(text) as whole words ('jo-park' not in 'jo-parker')."""
    return bool(s) and re.search(rf"(^|[-_]){re.escape(s)}([-_]|$)", slug(text)) is not None


INTERVIEWER_CTX = re.compile(r"\binterviewers?\b|\brated by\b|\bpanel(ists?)?\b|\bscored by\b|"
                             r"\bspeakers?\b|\broll-call\b", re.I)
# a brief's roll-call or rating line: "- Dev Rao (M3): filed", "- Dev Rao, 4: ..."
RATER_AFTER = r"\s*(\(M\d+|,\s*[1-5]\b|,\s*not assessed|:\s*(hire|no hire|no decision|filed|not filed)\b)"


def fold_map(text):
    """Accent-fold and lower-case text one character at a time. Returns the
    folded string and, for each folded character, the index of the original
    character it came from, so a match on the folded copy maps back."""
    out, idx = [], []
    for i, c in enumerate(text):
        f = "".join(x for x in unicodedata.normalize("NFKD", c) if not unicodedata.combining(x)).lower()
        for x in f or c:
            out.append(x)
            idx.append(i)
    return "".join(out), idx


class NameMatcher:
    """Finds the name in text regardless of accents and case: removing
    'Zoë Müller' also finds 'Zoe Muller' and 'ZOË MÜLLER'."""

    def __init__(self, name):
        parts = [re.escape(p) for p in fold(name).split()]
        self.pattern = r"\b" + r"[\s.\-_'’]+".join(parts) + r"\b"
        self.rx = re.compile(self.pattern, re.I)

    def spans(self, text):
        folded, idx = fold_map(text or "")
        return [(idx[m.start()], idx[m.end() - 1] + 1) for m in self.rx.finditer(folded)]

    def search(self, text):
        return bool(self.spans(text))

    def findall(self, text):
        return self.spans(text)

    def sub(self, repl, text):
        for a, b in reversed(self.spans(text)):
            text = text[:a] + repl + text[b:]
        return text

    def rater_line(self, line):
        return re.search(self.pattern + RATER_AFTER, fold_map(line)[0], re.I) is not None


def name_regex(name):
    return NameMatcher(name)


def read_rows(path):
    """Raw CSV rows (lists), so a ragged row is kept exactly as it was."""
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.reader(fh))


def other_candidates_scorecard(rel, s):
    """True for .../<candidate-slug>/scorecards/<file> when that candidate is not this person."""
    parts = rel.replace("\\", "/").split("/")
    if "scorecards" in parts[:-1]:
        i = parts.index("scorecards")
        return i == 0 or parts[i - 1] != s
    return False


def dnc_listed(hiring, target):
    path = os.path.join(hiring, "dnc.csv")
    if not os.path.exists(path):
        return False
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return any(fold(r.get("name") or r.get("candidate")) == target for r in csv.DictReader(fh))


def process(hiring, name, role, keep_dnc, dry, drop_dnc=False):
    target, s = fold(name), slug(name)
    rx = name_regex(name)
    report = {"rows_deleted": {}, "files_deleted": [], "files_redacted": {}, "roles_seen": set(),
              "skipped": [], "check_with_owner": {}, "dnc_kept": False}
    # an existing do-not-contact flag survives unless the owner explicitly drops it
    keep_dnc = (keep_dnc or dnc_listed(hiring, target)) and not drop_dnc
    report["dnc_kept"] = keep_dnc
    rs = slug(role) if role else ""

    def role_ok(path):
        # with --role, a file or folder is removed only if its path names that role too
        return not rs or names(rs, os.path.relpath(path, hiring))
    for root, dirs, files in os.walk(hiring, topdown=False):
        for d in dirs:
            p = os.path.join(root, d)
            if names(s, d) and os.path.isdir(p) and role_ok(p):
                report["files_deleted"].append(os.path.relpath(p, hiring).replace("\\", "/") + "/")
                if not dry:
                    shutil.rmtree(p, ignore_errors=True)
        for f in files:
            p = os.path.join(root, f)
            if not os.path.exists(p):
                continue
            rel = os.path.relpath(p, hiring).replace("\\", "/")
            if rel == "dnc.csv" and keep_dnc:
                continue
            if other_candidates_scorecard(rel, s):
                if names(s, os.path.splitext(f)[0]) or f.endswith(TEXT_EXT) and _mentions(p, rx):
                    report["skipped"].append(rel)
                continue
            if f.endswith(".csv"):
                raw = read_rows(p)
                fields = [c.strip().lower() for c in raw[0]] if raw else []
                if len(raw) > 1:
                    ncol = next((i for i, c in enumerate(fields) if c in NAME_COLS), None)
                    rcol = next((i for i, c in enumerate(fields) if c == "role"), None)
                    if ncol is not None:
                        keep, gone, ragged = [raw[0]], 0, 0
                        for r in raw[1:]:
                            if len(r) != len(fields):
                                ragged += 1
                            cell = lambda i: r[i] if i is not None and i < len(r) else ""  # noqa: E731
                            hit = fold(cell(ncol)) == target
                            if hit and rcol is not None:
                                report["roles_seen"].add(cell(rcol))
                            if hit and role and rcol is not None and fold(cell(rcol)) != fold(role):
                                hit = False
                            if hit:
                                gone += 1
                            else:
                                keep.append(r)
                        if ragged:
                            report.setdefault("ragged", {})[rel] = ragged
                        if gone:
                            report["rows_deleted"][rel] = gone
                            if not dry:
                                buf = io.StringIO()
                                csv.writer(buf, lineterminator="\n").writerows(keep)
                                with open(p, "w", newline="", encoding="utf-8") as fh:
                                    fh.write(buf.getvalue())
                        left = sum(1 for r in keep[1:] for v in r if rx.search(v))
                        if left:
                            report["check_with_owner"][rel] = left
                        continue
            if names(s, os.path.splitext(f)[0]) and role_ok(p):
                report["files_deleted"].append(rel)
                if not dry:
                    os.remove(p)
                continue
            if f.endswith(".csv"):
                # never text-redact a CSV: a name in another column may be a colleague's
                if _mentions(p, rx):
                    with open(p, encoding="utf-8", errors="replace") as fh:
                        report["check_with_owner"][rel] = len(rx.findall(fh.read()))
                continue
            if f.endswith(TEXT_EXT):
                with open(p, encoding="utf-8", errors="replace") as fh:
                    lines = fh.read().split("\n")
                n, held = 0, 0
                for i, line in enumerate(lines):
                    k = len(rx.findall(line))
                    if not k:
                        continue
                    if INTERVIEWER_CTX.search(line) or rx.rater_line(line):
                        held += k          # maybe a colleague with the same name
                    else:
                        n += k
                        lines[i] = rx.sub("[removed]", line)
                if held:
                    report["check_with_owner"][rel] = held
                if n:
                    report["files_redacted"][rel] = n
                    if not dry:
                        with open(p, "w", encoding="utf-8") as fh:
                            fh.write("\n".join(lines))
    if keep_dnc and not dry:
        path = os.path.join(hiring, "dnc.csv")
        rows = []
        if os.path.exists(path):
            with open(path, newline="", encoding="utf-8-sig") as fh:
                rows = [r for r in csv.DictReader(fh) if fold(r.get("name")) != target]
        rows.append({"name": name.strip(), "flag": "do-not-contact"})
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["name", "flag"], extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
    report["roles_seen"] = sorted(x for x in report["roles_seen"] if x)
    return report


def _mentions(path, rx):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return bool(rx.search(fh.read()))


def show(report, dry, keep_dnc):
    tag = "would delete" if dry else "deleted"
    total = sum(report["rows_deleted"].values())
    print(f"{'DRY RUN: ' if dry else ''}{total} row(s) {tag} across {len(report['rows_deleted'])} file(s); "
          f"{len(report['files_deleted'])} file(s)/folder(s) {tag}; "
          f"{sum(report['files_redacted'].values())} mention(s) in {len(report['files_redacted'])} file(s) "
          f"{'would be ' if dry else ''}replaced with [removed]")
    for f, n in sorted(report["rows_deleted"].items()):
        print(f"  rows: {f}: {n}")
    for f in sorted(report["files_deleted"]):
        print(f"  file: {f}")
    for f, n in sorted(report["files_redacted"].items()):
        print(f"  redacted: {f}: {n}")
    if len(report["roles_seen"]) > 1:
        print(f"  NOTE: rows under {len(report['roles_seen'])} roles: {', '.join(report['roles_seen'])}. "
              "If the owner meant one role, confirm it is the same person before applying.")
    for f, n in sorted(report.get("check_with_owner", {}).items()):
        print(f"  check with owner: {f}: {n} mention(s) left untouched (a CSV column other than the "
              "candidate's, or an interviewer context: may be another person with the same name)")
    for f, n in sorted(report.get("ragged", {}).items()):
        print(f"  needs a look: {f}: {n} row(s) with the wrong number of columns (an unquoted comma?); "
              "kept exactly as they were")
    for f in sorted(report["skipped"]):
        print(f"  skipped: {f} (another candidate's scorecard; the name may be an interviewer's. "
              "Check with the owner; not touched)")
    if report.get("dnc_kept", keep_dnc):
        print("  dnc.csv keeps: name + do-not-contact flag only")


def selftest():
    h = tempfile.mkdtemp()
    os.makedirs(os.path.join(h, "tracker"))
    os.makedirs(os.path.join(h, "packets"))
    os.makedirs(os.path.join(h, "debriefs", "sbe", "priya-nair", "scorecards"))
    with open(os.path.join(h, "tracker", "candidates.csv"), "w", encoding="utf-8") as fh:
        fh.write("name,role,stage\nPriya Nair,SBE,Onsite\nTom Becker,SBE,Screen\n")
    with open(os.path.join(h, "outreach-log.csv"), "w", encoding="utf-8") as fh:
        fh.write("candidate,role,touch\nPRIYA  NAIR,SBE,1\n")
    with open(os.path.join(h, "packets", "2026-10-29-sbe-priya-nair-1000-slot2.md"), "w", encoding="utf-8") as fh:
        fh.write("x")
    with open(os.path.join(h, "debriefs", "sbe", "priya-nair", "scorecards", "ana.md"), "w", encoding="utf-8") as fh:
        fh.write("x")
    with open(os.path.join(h, "weekly.md"), "w", encoding="utf-8") as fh:
        fh.write("New: Priya Nair and Tom Becker.\n")
    r = process(h, "Priya Nair", None, True, True)
    assert sum(r["rows_deleted"].values()) == 2 and os.path.exists(os.path.join(h, "weekly.md"))
    r = process(h, "Priya Nair", None, True, False)
    with open(os.path.join(h, "weekly.md"), encoding="utf-8") as fh:
        assert fh.read() == "New: [removed] and Tom Becker.\n"
    assert not os.path.exists(os.path.join(h, "debriefs", "sbe", "priya-nair"))
    assert not os.listdir(os.path.join(h, "packets"))
    with open(os.path.join(h, "tracker", "candidates.csv"), encoding="utf-8") as fh:
        assert "Priya" not in fh.read()
    with open(os.path.join(h, "dnc.csv"), encoding="utf-8") as fh:
        assert fh.read().strip().splitlines() == ["name,flag", "Priya Nair,do-not-contact"]
    # an existing DNC flag survives a removal run without --keep-dnc
    h2 = tempfile.mkdtemp()
    os.makedirs(os.path.join(h2, "tracker"))
    os.makedirs(os.path.join(h2, "debriefs", "sbe", "tom-becker", "scorecards"))
    with open(os.path.join(h2, "dnc.csv"), "w", encoding="utf-8") as fh:
        fh.write("name,flag\nSara Lind,dnc\n")
    with open(os.path.join(h2, "tracker", "candidates.csv"), "w", encoding="utf-8") as fh:
        fh.write("name,role,stage\nSara Lind,SBE,Screen\nTom Becker,SBE,Onsite\n")
    card = os.path.join(h2, "debriefs", "sbe", "tom-becker", "scorecards", "sara-lind.md")
    with open(card, "w", encoding="utf-8") as fh:
        fh.write("interviewer: Sara Lind\n")
    r = process(h2, "Sara Lind", None, False, False)
    with open(os.path.join(h2, "dnc.csv"), encoding="utf-8") as fh:
        assert fh.read().strip().splitlines() == ["name,flag", "Sara Lind,do-not-contact"]
    assert os.path.exists(card) and r["skipped"], r
    with open(card, encoding="utf-8") as fh:
        assert "Sara Lind" in fh.read()
    # --drop-dnc (owner's explicit order) removes the flag
    process(h2, "Sara Lind", None, False, False, drop_dnc=True)
    with open(os.path.join(h2, "dnc.csv"), encoding="utf-8") as fh:
        assert "Sara" not in fh.read()
    # "Jo Park" never takes Jo Parker's files
    h3 = tempfile.mkdtemp()
    os.makedirs(os.path.join(h3, "debriefs", "designer", "jo-parker", "scorecards"))
    os.makedirs(os.path.join(h3, "debriefs", "designer", "jo-park", "scorecards"))
    os.makedirs(os.path.join(h3, "packets"))
    for rel in ("packets/2026-10-29-designer-jo-parker-1000-slot1.md", "jo-parker-resume.txt",
                "packets/2026-10-29-designer-jo-park-1000-slot1.md"):
        with open(os.path.join(h3, rel), "w", encoding="utf-8") as fh:
            fh.write("x")
    r = process(h3, "Jo Park", None, False, True)
    assert all("parker" not in f for f in r["files_deleted"]), r
    assert len(r["files_deleted"]) == 2, r
    # a candidate named like an interviewer: other candidates' loop rows and briefs keep the interviewer
    h4 = tempfile.mkdtemp()
    os.makedirs(os.path.join(h4, "tracker"))
    os.makedirs(os.path.join(h4, "debriefs", "sbe"))
    with open(os.path.join(h4, "tracker", "loops.csv"), "w", encoding="utf-8") as fh:
        fh.write("candidate,role,interviewers,coverage\nDev Rao,Designer,Ana Silva,M1\n"
                 "Priya Nair,SBE,Dev Rao,M3\nTom Becker,SBE,Dev Rao; Ana Silva,M1\n")
    brief = os.path.join(h4, "debriefs", "sbe", "2026-10-30-priya-nair-brief.md")
    with open(brief, "w", encoding="utf-8") as fh:
        fh.write("- Dev Rao (M3): filed\ninterviewer: Dev Rao\nNote: Dev Rao, the Designer candidate, withdrew.\n")
    r = process(h4, "Dev Rao", "Designer", False, False)
    with open(os.path.join(h4, "tracker", "loops.csv"), encoding="utf-8") as fh:
        loops = fh.read()
    assert "Designer" not in loops and loops.count("Dev Rao") == 2 and "[removed]" not in loops, loops
    assert r["check_with_owner"].get("tracker/loops.csv") == 2, r
    with open(brief, encoding="utf-8") as fh:
        text = fh.read()
    assert "interviewer: Dev Rao" in text and "- Dev Rao (M3): filed" in text, text
    assert "Note: [removed], the Designer" in text and r["check_with_owner"].get(
        "debriefs/sbe/2026-10-30-priya-nair-brief.md") == 2, (text, r)
    # a ragged CSV row (unquoted comma in someone else's notes) is kept as-is, no crash;
    # accent variants of the name are found and removed
    h5 = tempfile.mkdtemp()
    os.makedirs(os.path.join(h5, "tracker"))
    os.makedirs(os.path.join(h5, "debriefs", "sbe", "zoe-muller"))
    with open(os.path.join(h5, "tracker", "candidates.csv"), "w", encoding="utf-8") as fh:
        fh.write("name,role,notes\nZoë Müller,SBE,ok\nTom Becker,SBE,likes Go, Rust\n")
    with open(os.path.join(h5, "weekly.md"), "w", encoding="utf-8") as fh:
        fh.write("Zoë Müller moved on. ZOË MÜLLER again. Zoe Muller in plain letters.\n")
    r = process(h5, "Zoë Müller", None, False, True)
    assert r["files_redacted"].get("weekly.md") == 3 and r.get("ragged"), r
    process(h5, "Zoë Müller", None, False, False)
    with open(os.path.join(h5, "weekly.md"), encoding="utf-8") as fh:
        assert fh.read() == "[removed] moved on. [removed] again. [removed] in plain letters.\n"
    with open(os.path.join(h5, "tracker", "candidates.csv"), encoding="utf-8") as fh:
        assert fh.read() == "name,role,notes\nTom Becker,SBE,likes Go, Rust\n"
    assert not os.path.exists(os.path.join(h5, "debriefs", "sbe", "zoe-muller"))
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name")
    ap.add_argument("--role")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--keep-dnc", action="store_true",
                   help="keep (or add) name + do-not-contact flag; default when the candidate asked")
    g.add_argument("--drop-dnc", action="store_true",
                   help="owner's explicit order only: also remove an existing do-not-contact row")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--hiring", default=os.path.expanduser("~/workspace/hiring"))
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.name or len(fold(a.name).split()) < 2:
        print("bad input: give the full name as the tracker holds it (at least two words), "
              "so no one else is matched", file=sys.stderr)
        return 2
    if not os.path.isdir(a.hiring):
        print(f"nothing to remove: {a.hiring} does not exist")
        return 0
    # always walk the whole plan read-only first, so an unreadable file stops
    # the run before anything is deleted (no partial removal)
    try:
        report = process(a.hiring, a.name, a.role, a.keep_dnc, True, a.drop_dnc)
    except (OSError, csv.Error, UnicodeDecodeError, ValueError) as exc:
        print(f"bad input: {exc}. Nothing was removed; fix or move that file and run again.", file=sys.stderr)
        return 2
    if not a.dry_run:
        report = process(a.hiring, a.name, a.role, a.keep_dnc, False, a.drop_dnc)
    show(report, a.dry_run, a.keep_dnc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
