#!/usr/bin/env python3
"""Check a close plan: one owner per track, real dates, and what is due or overdue.

Usage (cd ~/skills/job-offer-and-close-plan first):

  python3 scripts/close_plan.py <close-plan.csv> [--today 2026-10-14] [--json out.json]
      [--candidate "Priya Nair"] [--assistant "<your own name>"] [--terms terms.json]

close-plan.csv columns (templates/close-plan.csv):
  track,owner,due_date,tz,status,notes
  - one owner per track (a person, not a team or "we");
  - due_date is ISO YYYY-MM-DD, tz an IANA zone such as Europe/Lisbon;
  - status is one of: open, done, blocked, dropped.

  - an owner is an internal named person: never the assistant, never the
    candidate (put the candidate in notes). An owner is flagged when it is
    the full --candidate / --assistant name, contains a multi-word name, or
    shares a whole first or last name with it (so "Ana" does not flag
    "Diana Ortiz") ("Marco", "Priya Nair (candidate)"); text in
    parentheses is ignored for the comparison.

Prints the plan in due-date order with OVERDUE / DUE TODAY / open / done,
lists problems (missing owner, several owners, bad date, missing or unknown
tz, a signature track dated before the answer-by track), lists overdue
tracks ("overdue since ...") and names the next check date to use for the
follow-up: the earliest open due date that is today or later (never a past
date).

Contingency order (references/contingency-order.md section 4), also PROBLEM:
  - a background / consumer-report / credit-check track with no disclosure
    and authorisation track, or dated on or before one (FCRA: the standalone
    disclosure and written authorisation come before the report is procured);
  - a medical / physical exam or drug-test track dated before the answer-by
    or signature track. This is the skill's house rule (after written
    acceptance), stricter than the law: the ADA [46] allows an exam after a
    conditional offer and before duties start. A drug test is not an ADA
    medical exam (42 U.S.C. 12114(d)); state drug-testing rules vary, so the
    line also says to confirm them with counsel.
  - with --terms: a background / credit / consumer-report or medical
    contingency in terms.json with no matching track in the plan.
Tracks are matched by words in the track name, so name them plainly
("standalone disclosure + authorisation signed", "background check ordered",
"medical exam"); vendor shorthand such as "BGC" or "Checkr" also counts as a
background check. templates/close-plan.csv has these rows ready to copy.
A plan with no tracks (header only or empty) is a PROBLEM.
Exit: 0 clean, 1 problems or overdue tracks, 2 unreadable file or bad --today.
"""

import argparse
import csv
import datetime as dt
import json
import re
import sys

try:
    import zoneinfo
except ImportError:  # Python < 3.9
    zoneinfo = None

STATUSES = {"open", "done", "blocked", "dropped"}
MULTI_OWNER = re.compile(r"[,/&+]|\band\b|^(we|team|us|tbd|tba)$", re.I)
NOT_A_PERSON = re.compile(r"^(the )?(assistant|ai|bot|agent|candidate)$", re.I)
DISCLOSURE = re.compile(r"disclos|authori[sz]", re.I)
BACKGROUND = re.compile(r"background|consumer report|credit|\bbgc\b|checkr|sterling|hireright|first advantage", re.I)
MEDICAL = re.compile(r"medical|physical exam|health (exam|check|screen)|drug (test|screen)", re.I)
DRUG = re.compile(r"drug (test|screen)", re.I)
TERMS_BACKGROUND = re.compile(r"background|credit|consumer report", re.I)
TERMS_MEDICAL = re.compile(r"medical|health|physical exam|drug", re.I)


def name_parts(name):
    """Lower-case name with parenthesised text dropped, and its word tokens."""
    base = re.sub(r"\([^)]*\)", " ", name).lower()
    base = " ".join(re.findall(r"[^\W\d_]+(?:['-][^\W\d_]+)*", base))
    return base, set(base.split())


def owner_is(owner, person):
    """True when owner names the given person (full name, substring, or a
    shared first/last name)."""
    if not person.strip():
        return False
    o_full, o_tokens = name_parts(owner)
    p_full, p_tokens = name_parts(person)
    if not p_full:
        return False
    if o_full == p_full:
        return True
    # Substring match only for a multi-word name: a single token such as "Ana"
    # must not flag "Diana Ortiz"; it is compared as a whole word below.
    if len(p_full.split()) > 1 and (p_full in o_full or p_full in owner.lower()):
        return True
    key = {t for t in (p_full.split()[0], p_full.split()[-1]) if len(t) > 1}
    return bool(o_tokens & key)
ANSWER_BY = re.compile(r"answer[- ]by", re.I)
SIGNATURE = re.compile(r"signature|signed offer|written acceptance", re.I)


def tz_problem(tz):
    """None if tz is a usable IANA Area/City zone, else the reason."""
    if tz.upper() == "UTC":
        return None
    if "/" not in tz:
        return f"tz '{tz}' is not an IANA Area/City name (e.g. Europe/Lisbon, America/Los_Angeles)"
    if zoneinfo is None or not zoneinfo.available_timezones():
        return None  # no tz database here: the Area/City shape is all we can check
    try:
        zoneinfo.ZoneInfo(tz)
    except (zoneinfo.ZoneInfoNotFoundError, ValueError):
        return f"tz '{tz}' is not a known IANA zone"
    return None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plan")
    ap.add_argument("--today")
    ap.add_argument("--json")
    ap.add_argument("--candidate", default="", help="candidate's name: may not own a track")
    ap.add_argument("--assistant", default="", help="the assistant's own name: may not own a track")
    ap.add_argument("--terms", help="terms.json: every declared background/medical contingency needs a track")
    a = ap.parse_args(argv)
    try:
        today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    except ValueError:
        print(f"error: --today '{a.today}' is not YYYY-MM-DD", file=sys.stderr)
        return 2
    try:
        with open(a.plan, newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.DictReader(fh))
    except OSError as exc:
        print(f"error: cannot read {a.plan}: {exc}", file=sys.stderr)
        return 2
    problems, items = [], []
    if not rows:
        problems.append("plan has no tracks: copy the rows from templates/close-plan.csv and give each an owner and date")
    for i, r in enumerate(rows, start=2):
        track = (r.get("track") or "").strip()
        owner = (r.get("owner") or "").strip()
        status = (r.get("status") or "open").strip().lower()
        try:
            due = dt.date.fromisoformat((r.get("due_date") or "").strip())
        except ValueError:
            due = None
            problems.append(f"line {i} '{track}': due_date '{r.get('due_date')}' is not YYYY-MM-DD")
        if not owner:
            problems.append(f"line {i} '{track}': no owner")
        elif MULTI_OWNER.search(owner):
            problems.append(f"line {i} '{track}': owner '{owner}' is not a single named person")
        elif (NOT_A_PERSON.search(re.sub(r"\s*\([^)]*\)", "", owner).strip()) or owner_is(owner, a.candidate)
              or owner_is(owner, a.assistant)):
            problems.append(f"line {i} '{track}': owner '{owner}' must be an internal person, "
                            "not the assistant or the candidate (put the candidate in notes)")
        tz = (r.get("tz") or "").strip()
        if not tz:
            problems.append(f"line {i} '{track}': no timezone")
        elif tz_problem(tz):
            problems.append(f"line {i} '{track}': {tz_problem(tz)}")
        if status not in STATUSES:
            problems.append(f"line {i} '{track}': status '{status}' not in {sorted(STATUSES)}")
        state = status
        if due and status in ("open", "blocked"):
            state = "OVERDUE" if due < today else ("DUE TODAY" if due == today else status)
        items.append({"track": track, "owner": owner, "due_date": due.isoformat() if due else None,
                      "tz": r.get("tz", ""), "status": status, "state": state, "notes": r.get("notes", "")})

    def dated(rx, exclude=None):
        return [x for x in items if x["due_date"] and x["status"] != "dropped"
                and rx.search(x["track"]) and not (exclude and exclude.search(x["track"]))]
    ans, sig = dated(ANSWER_BY), dated(SIGNATURE)
    if ans and sig and min(s["due_date"] for s in sig) < min(a_["due_date"] for a_ in ans):
        problems.append("signature track is dated before the answer-by track")

    disclosures = dated(DISCLOSURE)
    for bg in dated(BACKGROUND, exclude=DISCLOSURE):
        if not disclosures:
            problems.append(f"'{bg['track']}' has no standalone disclosure + authorisation track before it "
                            "(FCRA; references/contingency-order.md section 1)")
        elif any(bg["due_date"] <= d["due_date"] for d in disclosures):
            problems.append(f"'{bg['track']}' ({bg['due_date']}) is dated on or before the disclosure + "
                            f"authorisation track ({max(d['due_date'] for d in disclosures)}): disclosure first")
    acceptance = [x["due_date"] for x in ans + sig]
    for med in dated(MEDICAL):
        if acceptance and med["due_date"] < max(acceptance):
            if DRUG.search(med["track"]):
                why = ("skill rule: after written acceptance. A drug test is not an ADA medical exam "
                       "(42 U.S.C. 12114(d)); state drug-testing rules vary - confirm with counsel")
            else:
                why = ("skill rule: after written acceptance; the ADA [46] itself requires only after a "
                       "conditional offer and before duties start")
            problems.append(f"'{med['track']}' ({med['due_date']}) is dated before the answer-by/signature track "
                            f"({max(acceptance)}): {why}")

    if a.terms:
        try:
            with open(a.terms, encoding="utf-8") as fh:
                conts = json.load(fh).get("contingencies", []) or []
        except (OSError, ValueError, AttributeError) as exc:
            print(f"error: cannot read {a.terms}: {exc}", file=sys.stderr)
            return 2
        live = [x for x in items if x["status"] != "dropped"]
        for c in conts:
            cname = str((c or {}).get("name", "")).strip()
            if TERMS_BACKGROUND.search(cname) and not any(BACKGROUND.search(x["track"]) and not DISCLOSURE.search(x["track"]) for x in live):
                problems.append(f"terms contingency '{cname}' has no background-check track in the plan "
                                "(add the disclosure + authorisation track and the check track from templates/close-plan.csv)")
            # A drug-test contingency needs a drug-test track; a medical exam
            # contingency needs a medical track that is not a drug test.
            needs_drug = bool(re.search(r"drug", cname, re.I))
            if TERMS_MEDICAL.search(cname) and not any(
                    MEDICAL.search(x["track"]) and bool(DRUG.search(x["track"])) == needs_drug for x in live):
                problems.append(f"terms contingency '{cname}' has no medical/drug-test track in the plan "
                                "(add it from templates/close-plan.csv, dated after written acceptance)")

    items.sort(key=lambda x: x["due_date"] or "9999")
    print(f"Close plan as of {today}:")
    for x in items:
        print(f"- {x['due_date'] or '??'} [{x['state']}] {x['track']} - {x['owner'] or 'NO OWNER'} ({x['tz'] or 'no tz'})")
    open_dates = [x["due_date"] for x in items if x["status"] in ("open", "blocked") and x["due_date"]]
    overdue = [x for x in items if x["state"] == "OVERDUE"]
    upcoming = [d for d in open_dates if d >= today.isoformat()]
    next_check = min(upcoming) if upcoming else (today.isoformat() if open_dates else None)
    for x in overdue:
        print(f"Overdue since {x['due_date']}: {x['track']} - {x['owner'] or 'NO OWNER'}")
    print(f"Next check date: {next_check or 'none - all tracks closed'}")
    for p in problems:
        print(f"PROBLEM {p}")
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"today": today.isoformat(), "items": items, "problems": problems,
                       "overdue": [{"track": x["track"], "since": x["due_date"], "owner": x["owner"]} for x in overdue],
                       "next_check": next_check}, fh, indent=2)
    return 1 if problems or overdue else 0


if __name__ == "__main__":
    sys.exit(main())
