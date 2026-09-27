#!/usr/bin/env python3
"""Create, import into and refresh the hiring tracker (roles, candidates, loops).

    cd ~/skills/interview-coordination && python3 scripts/merge_tracker.py init [--hiring ~/workspace/hiring]
    python3 scripts/merge_tracker.py import --list candidates|roles|loops --incoming /home/user/in/export.csv \
        [--date-order dmy|mdy] [--today YYYY-MM-DD] [--dry-run] [--hiring DIR]
    python3 scripts/merge_tracker.py refresh [--today YYYY-MM-DD]     # recompute days_in_stage

Files: <hiring>/tracker/{roles,candidates,loops}.csv. Column names are fixed
(templates/tracker-headers/); other skills read them. init also creates
packets/, debriefs/, flags/, roles/ and reports/, and adds any missing optional
column to an existing file without touching its rows.

import rules (from the skill):
- Vendor columns are mapped to the fixed names (aliases for Greenhouse, Lever,
  Ashby, Workday and hand-made sheets). Unmapped columns are listed, not imported.
- Protected-attribute and self-ID columns are dropped before anything is read
  (gender, race, ethnicity, veteran, disability, date of birth, age, marital,
  religion, nationality, EEO, self-ID, photo...). Printed as "Dropped: ...",
  for the one-line notice to the owner.
- Dates are normalised to ISO. A date that reads both ways (03/04/2026) with
  no --date-order goes to needs-a-look; it is never guessed.
- Keys: candidates on name + role, loops on candidate + date + start, roles on
  role (case, accents and spacing folded). When both copies hold a row, the
  newer wins: for candidates the later last_contact; for roles and loops the
  incoming copy. Every changed field is printed old -> new.
- Stage names, titles and notes keep the owner's wording; only dates and
  times are normalised.
- Never merge on a guess: a name that is close to an existing one for the
  same role (same surname and first initial, or one name inside the other) is
  not merged; it goes to needs-a-look as "possible duplicate". ATS merges drop
  source and referral credit and auto-merge is narrow, so duplicates are
  common and must be resolved by a human.
- Prospects are not applicants: a row marked prospect (a prospect column,
  candidate type, or stage "Prospect") keeps is_prospect=yes.
- Rows with no name or no role (no candidate + date for loops) go to
  tracker/needs-a-look.csv with the reason.

Exit 0 on success, 1 when rows went to needs-a-look, 2 on bad input.
--selftest runs in a temporary folder.
"""

import argparse
import csv
import datetime as dt
import os
import re
import sys
import tempfile
import unicodedata

HEADERS = {
    "roles": ["role", "level", "hiring_manager", "target_start", "panel", "stage", "notes"],
    "candidates": ["name", "role", "stage", "source", "owner", "last_contact", "next_step", "waiting_on",
                   "days_in_stage", "notes", "stage_since", "due_by", "tz", "is_prospect", "verification_step"],
    "loops": ["candidate", "role", "date", "start", "end", "tz", "interviewers", "coverage", "status",
              "scorecards", "candidate_tz", "location"],
}
DATE_COLS = {"last_contact", "stage_since", "due_by", "target_start", "date"}
ALIASES = {
    "name": ["name", "candidate name", "full name", "candidate", "applicant", "applicant name", "contact name"],
    "first_name": ["first name", "given name"],
    "last_name": ["last name", "surname", "family name"],
    "role": ["role", "job", "job name", "job title applied", "requisition", "req", "posting", "opening",
             "position", "job posting", "posting title", "opportunity"],
    "stage": ["stage", "current stage", "status", "pipeline stage", "application status", "step"],
    "source": ["source", "origin", "source name", "candidate source", "referrer source"],
    "owner": ["owner", "recruiter", "coordinator", "candidate owner", "opportunity owner"],
    "last_contact": ["last contact", "last activity", "last activity date", "last updated", "updated at",
                     "last contacted", "last interaction"],
    "next_step": ["next step", "next action"],
    "waiting_on": ["waiting on", "blocked by", "pending with"],
    "notes": ["notes", "note", "comments"],
    "stage_since": ["stage since", "date entered stage", "moved to stage", "stage entered", "in stage since"],
    "due_by": ["due by", "answer by", "offer expires", "offer deadline", "expiry", "reply by"],
    "tz": ["tz", "timezone", "time zone", "candidate timezone"],
    "is_prospect": ["is prospect", "prospect", "candidate type", "type"],
    "verification_step": ["verification step", "verification"],
    "level": ["level", "grade", "band level"],
    "hiring_manager": ["hiring manager", "hm", "manager"],
    "target_start": ["target start", "start date target", "target start date"],
    "panel": ["panel", "interviewers", "interview panel"],
    "candidate": ["candidate", "candidate name", "name", "full name", "applicant"],
    "date": ["date", "interview date", "scheduled date", "day"],
    "start": ["start", "start time", "from", "scheduled start"],
    "end": ["end", "end time", "to", "scheduled end"],
    "interviewers": ["interviewers", "interviewer", "panelists", "panel"],
    "coverage": ["coverage", "competency", "focus", "interview type", "interview name"],
    "scorecards": ["scorecards", "scorecard", "feedback", "scorecard status"],
    "candidate_tz": ["candidate tz", "candidate timezone", "candidate time zone"],
    "location": ["location", "room", "video link", "meeting link", "link"],
}
PROTECTED = re.compile(
    r"(gender|\bsex\b|\brace\b|ethnic|veteran|disab|date of birth|\bdob\b|birth|\bage\b|marital|religio|"
    r"nationality|citizenship|\beeo|eeoc|self.?id|photo|picture|pronoun|sexual|pregnan|national origin|"
    r"health|medical|genetic|criminal|arrest|conviction|visa|immigration|\bfamily\b|children)",
    re.I)
FORMATS = ["%Y-%m-%d", "%Y/%m/%d", "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y", "%b %d %Y", "%d-%b-%Y"]


def fold(t):
    t = unicodedata.normalize("NFKD", t or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", t).split())


def norm_date(v, order):
    """Return (iso, time_or_None, problem_or_None)."""
    v = (v or "").strip()
    if not v:
        return "", None, None
    m = re.match(r"^(\S+?)[T ](\d{1,2}:\d{2})", v)
    time = None
    if m and re.match(r"\d", m.group(1)):
        v, time = m.group(1), m.group(2)
    for f in FORMATS:
        try:
            return dt.datetime.strptime(v, f).date().isoformat(), time, None
        except ValueError:
            pass
    m = re.match(r"^(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})$", v)
    if m:
        a, b, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        y = y + 2000 if y < 100 else y
        options = []
        if a <= 12 and b <= 31:
            options.append(("mdy", a, b))
        if b <= 12 and a <= 31:
            options.append(("dmy", b, a))
        if order:
            options = [o for o in options if o[0] == order]
        dates = set()
        for _, mo, d in options:
            try:
                dates.add(dt.date(y, mo, d).isoformat())
            except ValueError:
                pass
        if len(dates) == 1:
            return dates.pop(), time, None
        if len(dates) > 1:
            return "", None, f"date '{v}' reads both day/month and month/day; pass --date-order"
    return "", None, f"unreadable date '{v}'"


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        r = csv.reader(fh)
        rows = list(r)
    if not rows:
        return [], []
    return rows[0], rows[1:]


def load(path, header):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return [{h: (row.get(h) or "").strip() for h in header} for row in csv.DictReader(fh)]


def save(path, header, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, path)


def key_of(lst, row):
    if lst == "candidates":
        return (fold(row["name"]), fold(row["role"]))
    if lst == "loops":
        return (fold(row["candidate"]), row["date"], row["start"])
    return (fold(row["role"]),)


def near(a, b):
    ta, tb = a.split(), b.split()
    if not ta or not tb or a == b:
        return False
    if ta[-1] == tb[-1] and ta[0][0] == tb[0][0]:
        return True
    return set(ta) < set(tb) or set(tb) < set(ta)


def cmd_init(hiring):
    for d in ("tracker", "packets", "debriefs", "flags", "roles", "reports"):
        os.makedirs(os.path.join(hiring, d), exist_ok=True)
    for lst, header in HEADERS.items():
        path = os.path.join(hiring, "tracker", f"{lst}.csv")
        if not os.path.exists(path):
            save(path, header, [])
            print(f"created tracker/{lst}.csv")
            continue
        existing, _ = read_csv(path)
        missing = [h for h in header if h not in existing]
        if missing:
            with open(path, newline="", encoding="utf-8-sig") as fh:
                rows = list(csv.DictReader(fh))
            save(path, existing + missing, rows)
            print(f"tracker/{lst}.csv: added optional column(s) {', '.join(missing)}")
        else:
            print(f"tracker/{lst}.csv: ok")
    return 0


def cmd_import(a):
    lst = a.list
    header = HEADERS[lst]
    raw_header, raw_rows = read_csv(a.incoming)
    if not raw_header:
        print("bad input: the incoming file is empty", file=sys.stderr)
        return 2
    dropped, unmapped, colmap = [], [], {}
    exact = {n for field, names in ALIASES.items()
             if field in header or field in ("first_name", "last_name") for n in names}
    for i, h in enumerate(raw_header):
        # an exact tracker alias ("Family Name" = last name) is mapped, never
        # dropped as protected; every other protected-looking header is dropped
        if fold(h) not in exact and PROTECTED.search(h):
            dropped.append(h)
            continue
        fh = fold(h)
        target = None
        for field, names in ALIASES.items():
            if fh in names and (field in header or field in ("first_name", "last_name")):
                target = field
                break
        if target and target not in colmap.values():
            colmap[i] = target
        else:
            unmapped.append(h)
    print("Dropped (protected or self-ID): " + (", ".join(dropped) if dropped else "none"))
    if unmapped:
        print("Not imported (no matching tracker column): " + ", ".join(unmapped))
    path = os.path.join(a.hiring, "tracker", f"{lst}.csv")
    existing_header, _ = read_csv(path) if os.path.exists(path) else ([], [])
    out_header = list(existing_header) + [h for h in header if h not in existing_header]
    current = load(path, out_header)   # keeps any extra columns the owner added
    index = {key_of(lst, r): r for r in current}
    needs, added, updated, unchanged, changes = [], 0, 0, 0, []
    for n, raw in enumerate(raw_rows, 2):
        row = {h: "" for h in header}
        for i, field in colmap.items():
            if i < len(raw):
                row.setdefault(field, "")
                row[field] = raw[i].strip()
        if lst == "candidates" and not row.get("name") and (row.get("first_name") or row.get("last_name")):
            row["name"] = f"{row.get('first_name', '')} {row.get('last_name', '')}".strip()
        row.pop("first_name", None)
        row.pop("last_name", None)
        problem = None
        for c in DATE_COLS & set(header):
            iso, time, p = norm_date(row.get(c, ""), a.date_order)
            if p:
                problem = f"{c}: {p}"
                break
            row[c] = iso
            if c == "date" and time and not row.get("start"):
                row["start"] = time
        for c in ("start", "end"):
            if row.get(c):
                m = re.match(r"^(\d{1,2}):(\d{2})\s*([ap]m)?$", row[c].strip(), re.I)
                if not m:
                    problem = problem or f"{c}: unreadable time '{row[c]}'"
                else:
                    hh = int(m.group(1)) % 12 + (12 if (m.group(3) or "").lower() == "pm" else 0) \
                        if m.group(3) else int(m.group(1))
                    row[c] = f"{hh:02d}:{m.group(2)}"
        if lst == "candidates":
            p = fold(row.get("is_prospect", ""))
            row["is_prospect"] = "yes" if (p in {"yes", "true", "1", "prospect"} or fold(row.get("stage")) == "prospect") else \
                ("no" if p in {"no", "false", "0", "candidate", "applicant"} else row.get("is_prospect", ""))
            need = ["name", "role"]
        elif lst == "loops":
            need = ["candidate", "date"]
        else:
            need = ["role"]
        missing = [f for f in need if not row.get(f)]
        if missing or problem:
            needs.append({"list": lst, "line": n, "reason": problem or f"missing {', '.join(missing)}",
                          "row": " | ".join(raw)[:200]})
            continue
        k = key_of(lst, row)
        if k in index:
            old = index[k]
            newer = True
            if lst == "candidates" and old.get("last_contact") and row.get("last_contact"):
                newer = row["last_contact"] >= old["last_contact"]
            keys = {"name", "role", "candidate"}
            diff = {f: (old.get(f, ""), v) for f, v in row.items()
                    if v and v != old.get(f, "") and not (f in keys and fold(v) == fold(old.get(f, "")))}
            if diff and newer:
                label = " / ".join(x for x in k if x)
                for f, (o, v) in diff.items():
                    changes.append(f"{label}: {f} '{o}' -> '{v}'")
                old.update({f: v for f, (_, v) in diff.items()})
                updated += 1
            elif diff:
                changes.append(f"{' / '.join(k)}: incoming copy is older (last_contact {row['last_contact']} "
                               f"< {old['last_contact']}); kept the tracker's values")
                unchanged += 1
            else:
                unchanged += 1
            continue
        if lst == "candidates":
            close = [r for r in current if fold(r["role"]) == k[1] and near(fold(r["name"]), k[0])]
            if close:
                needs.append({"list": lst, "line": n, "reason": "possible duplicate of '" + close[0]["name"]
                              + "' (not merged; confirm with the owner)", "row": " | ".join(raw)[:200]})
                continue
        current.append(row)
        index[k] = row
        added += 1
    print(f"{lst}: {added} added, {updated} updated, {unchanged} unchanged, {len(needs)} need a look")
    for c in changes:
        print(f"  changed: {c}")
    for x in needs:
        print(f"  needs a look: line {x['line']}: {x['reason']}")
    if a.dry_run:
        print("(dry run: nothing written)")
    else:
        save(path, out_header, current)
        if needs:
            npath = os.path.join(a.hiring, "tracker", "needs-a-look.csv")
            prior = load(npath, ["list", "line", "reason", "row"])
            save(npath, ["list", "line", "reason", "row"], prior + needs)
    return 1 if needs else 0


def business_days(a, b):
    n, d = 0, a
    while d < b:
        d += dt.timedelta(days=1)
        if d.weekday() < 5:
            n += 1
    return n


def cmd_refresh(a):
    path = os.path.join(a.hiring, "tracker", "candidates.csv")
    existing_header, _ = read_csv(path) if os.path.exists(path) else ([], [])
    header = list(existing_header) + [h for h in HEADERS["candidates"] if h not in existing_header]
    rows = load(path, header)   # keeps every column the owner added
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    n, bad = 0, []
    for r in rows:
        if r.get("stage_since"):
            try:
                since = dt.date.fromisoformat(r["stage_since"])
            except ValueError:
                bad.append(f"{r.get('name') or '(no name)'}: stage_since '{r['stage_since']}' is not YYYY-MM-DD")
                continue
            v = str((today - since).days)
            if v != r["days_in_stage"]:
                r["days_in_stage"] = v
                n += 1
    if not a.dry_run and os.path.exists(path):
        save(path, header, rows)
    print(f"candidates: days_in_stage updated on {n} row(s) (calendar days since stage_since)")
    for b in bad:
        print(f"needs a look: {b} (days_in_stage left unchanged)")
    return 0


def selftest():
    d = tempfile.mkdtemp()

    class A:
        hiring = d
        list = "candidates"
        date_order = None
        dry_run = False
        today = "2026-10-08"
    assert cmd_init(d) == 0
    inc = os.path.join(d, "in.csv")
    with open(inc, "w", encoding="utf-8") as fh:
        fh.write("Candidate Name,Job,Current Stage,Source,Recruiter,Last Activity,Gender,EEOC Race,Prospect\n"
                 "Priya Nair,Senior Backend,Onsite,Sourced,Maya,2026-10-05,F,x,no\n"
                 "Tom Becker,Senior Backend,Screen,Referral,Maya,03/04/2026,M,y,no\n"
                 "Aisha Bello,Senior Backend,Prospect,Sourced,Maya,2026-10-01,,,\n"
                 ",Senior Backend,Screen,,,,,,\n")
    A.incoming = inc
    assert cmd_import(A) == 1
    rows = load(os.path.join(d, "tracker", "candidates.csv"), HEADERS["candidates"])
    assert [r["name"] for r in rows] == ["Priya Nair", "Aisha Bello"], rows
    assert rows[1]["is_prospect"] == "yes"
    with open(os.path.join(d, "tracker", "candidates.csv"), encoding="utf-8") as fh:
        assert "Gender" not in fh.read()
    with open(inc, "w", encoding="utf-8") as fh:
        fh.write("Candidate Name,Job,Current Stage,Last Activity\n"
                 "Priya  NAIR,Senior Backend,Debrief,2026-10-07\n"
                 "P. Nair,Senior Backend,Screen,2026-10-07\n")
    assert cmd_import(A) == 1
    rows = load(os.path.join(d, "tracker", "candidates.csv"), HEADERS["candidates"])
    assert rows[0]["stage"] == "Debrief" and len(rows) == 2, rows
    # Given Name / Family Name: the family name is a name column, not a protected one
    with open(inc, "w", encoding="utf-8") as fh:
        fh.write("Given Name,Family Name,Job,Current Stage,Family Status\n"
                 "Priya,Shah,Senior Backend,Screen,x\n")
    cmd_import(A)
    cpath = os.path.join(d, "tracker", "candidates.csv")
    rows = load(cpath, HEADERS["candidates"])
    assert [r["name"] for r in rows] == ["Priya Nair", "Aisha Bello", "Priya Shah"], rows
    assert rows[0]["stage"] == "Debrief", rows
    with open(cpath, encoding="utf-8") as fh:
        assert "Family Status" not in fh.read()
    # refresh keeps the owner's extra columns and survives a hand-edited date
    hdr, body = read_csv(cpath)
    with open(cpath, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(hdr + ["referrer"])
        for i, r in enumerate(body):
            r = r + ["Ana"]
            r[hdr.index("stage_since")] = "05/10/2026" if i == 0 else "2026-10-01"
            w.writerow(r)
    assert cmd_refresh(A) == 0
    hdr2, body2 = read_csv(cpath)
    assert "referrer" in hdr2 and all(r[hdr2.index("referrer")] == "Ana" for r in body2), (hdr2, body2)
    assert body2[1][hdr2.index("days_in_stage")] == "7", body2
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", nargs="?", choices=["init", "import", "refresh"])
    ap.add_argument("--hiring", default=os.path.expanduser("~/workspace/hiring"))
    ap.add_argument("--list", choices=list(HEADERS))
    ap.add_argument("--incoming")
    ap.add_argument("--date-order", choices=["dmy", "mdy"])
    ap.add_argument("--today")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if a.command == "init":
        return cmd_init(a.hiring)
    if a.command == "refresh":
        try:
            return cmd_refresh(a)
        except (OSError, csv.Error, UnicodeDecodeError, ValueError) as exc:
            print(f"bad input: {exc}", file=sys.stderr)
            return 2
    if a.command == "import":
        if not a.list or not a.incoming:
            ap.error("import needs --list and --incoming")
        if a.incoming.lower().endswith((".xlsx", ".xls", ".pdf")):
            print("bad input: export as CSV (Ashby passthrough exports are PDF-only: ask for a candidate "
                  "list CSV instead)", file=sys.stderr)
            return 2
        try:
            return cmd_import(a)
        except (OSError, csv.Error, UnicodeDecodeError) as exc:
            print(f"bad input: {exc}", file=sys.stderr)
            return 2
    ap.error("give a command: init, import or refresh")


if __name__ == "__main__":
    sys.exit(main())
