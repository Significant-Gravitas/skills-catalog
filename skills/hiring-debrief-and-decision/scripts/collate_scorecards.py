#!/usr/bin/env python3
"""Collate filed scorecards into a competency-grouped debrief brief.

    cd ~/skills/hiring-debrief-and-decision && python3 scripts/collate_scorecards.py \
        --candidate "Priya Nair" --role "Senior Backend Engineer" \
        --scorecards ~/workspace/hiring/debriefs/<role-slug>/<candidate-slug>/scorecards \
        [--loops ~/workspace/hiring/tracker/loops.csv] [--kit ~/workspace/hiring/roles/<role-slug>/kit.md] \
        [--debrief-start 2026-10-09T11:00+01:00] [--gap 2] [--bar 0.9] \
        [--minutes 40] [--order "Dev Rao,Ana Silva,Sam Lee,Lena Ortiz"] [--hm "Lena Ortiz"] \
        [--include-outside] [--keep 2,5] [--out brief.md] [--json]

Scorecards: one .md per interviewer in templates/scorecard-1to5.md shape, or
one CSV export with columns candidate, interviewer, competency_id, competency,
rating, evidence, recommendation, reason, filed_at (one row per rating).
Unreadable files go to "needs a look"; a rating is never guessed.

What it produces
- Roll-call: every interviewer expected from loops.csv (not cancelled) with
  their competency and whether their scorecard is in. Filed share against --bar
  (default 0.9: "nine in ten filed"; default, confirm with the owner). Below the
  bar: warns that the room will argue from memory and names competencies with
  no written evidence.
- One block per competency (never per person): every 1-5 rating with the
  interviewer's name and their evidence quoted as FACT; empty evidence flagged;
  "not assessed" listed; a split when ratings are --gap (default 2) or more apart.
  Splits lead.
- Overall recommendations are listed per interviewer, never tallied. "No
  decision" or a blank overall is counted separately: it is not a neutral vote.
  An overall filled while a competency rating is blank is flagged.
- Late filings: filed_at after --debrief-start.
- Remarks not about the job: every sentence of evidence or overall reason that
  holds a CUT match from templates/remark-flags.csv (affect, age, family,
  health, origin, appearance; via flag_remarks.cut_spans) is replaced with a
  numbered "[removed #n: <category>]" in the brief, the --out file and the
  --json output, with one removal note per competency. The unredacted text is
  never printed or saved here. Removals are listed on stderr only (number,
  interviewer, where, category, flagged word) so they can be checked against
  flag_remarks.py; a lexicon over-cuts technical text ("invoice generation").
  Every flagged word in the sentence is listed. --keep n[,n] restores removal
  n only when its sentence holds exactly one flagged word and that word has a
  technical sense (KEEPABLE: generation, retire, foreign, health, looks ...);
  otherwise it prints "not restored" and the sentence stays cut. The brief
  then says "Restored #n" in its notes. Numbering is stable
  for the same scorecards (file order, rating order, then overall reason).
- No loop log (or no rows for this candidate): the roll-call says the expected
  count is unknown and asks for the owner's list; no filed share is claimed.
- Out-of-slot ratings: a rating on a competency the interviewer's slot does not
  own (the scorecard's "competencies:" header, else that interviewer's loop
  coverage) is tagged "[outside this slot]", left out of split detection
  (unless --include-outside), and listed as a challenge question, because the
  kit gives each must-have exactly one owner.
- Running order: --order if given (the owner knows seniority), else slot order
  with the hiring manager (--hm or roles.csv) last, marked "confirm seniority:
  junior first". Minutes (default 40 of a 30-45 minute meeting; confirm) are
  split 5 opening, 5 decision, the rest weighted 3 per split, 2 per thin
  competency, 1 otherwise.
No average, total, score or rank is computed anywhere, by design: the persona
never scores a candidate, and the debrief keeps each competency's evidence
visible for the humans who decide.

Exit 0; 1 when the filed share is below the bar or a file needs a look;
2 on bad input. --selftest uses a temp folder.
"""

import argparse
import csv
import datetime as dt
import glob
import json
import os
import re
import sys
import tempfile
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flag_remarks import DEFAULT_LEXICON, cut_spans, load_lexicon  # noqa: E402

REMOVED_RX = re.compile(r"\[removed #\d+: [a-z/ -]+\]")

DEFAULT_GAP = 2
DEFAULT_BAR = 0.9
DEFAULT_MINUTES = 40


def fold(t):
    t = unicodedata.normalize("NFKD", t or "")
    t = "".join(c for c in t if not unicodedata.combining(c)).lower()
    return " ".join(re.sub(r"[^a-z0-9 ]+", " ", t).split())


def parse_md(path):
    with open(path, encoding="utf-8") as fh:
        text = re.sub(r"<!--.*?-->", "", fh.read(), flags=re.S)
    meta = {}
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text.replace("\r\n", "\n"), re.S)
    body = text
    if m:
        body = m.group(2)
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            if v:
                meta[k.strip().lower()] = v.strip()
    ratings = []
    for line in body.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4 and re.match(r"^M\d+$", cells[0]):
            ratings.append({"id": cells[0], "competency": cells[1], "rating": cells[2].lower(),
                            "evidence": "|".join(cells[3:]).strip()})
    rec = re.search(r"^\s*recommendation\s*:\s*(.*)$", body, re.M | re.I)
    reason = re.search(r"^\s*reason\s*:\s*(.*)$", body, re.M | re.I)
    if not meta.get("interviewer") or not ratings:
        raise ValueError("no 'interviewer:' header or no rating rows (| M1 | name | 1-5 | evidence |)")
    return {"interviewer": meta["interviewer"], "candidate": meta.get("candidate", ""),
            "filed_at": meta.get("filed_at", ""), "slot": meta.get("slot", ""), "ratings": ratings,
            "competencies": meta.get("competencies", ""),
            "recommendation": (rec.group(1).strip() if rec else ""), "reason": (reason.group(1).strip() if reason else ""),
            "file": os.path.basename(path)}


def parse_csv(path, candidate):
    cards = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for r in csv.DictReader(fh):
            r = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
            if candidate and r.get("candidate") and fold(r["candidate"]) != fold(candidate):
                continue
            c = cards.setdefault(r["interviewer"], {"interviewer": r["interviewer"], "candidate": r.get("candidate", ""),
                                                    "filed_at": r.get("filed_at", ""), "slot": "", "ratings": [],
                                                    "recommendation": r.get("recommendation", ""),
                                                    "reason": r.get("reason", ""), "file": os.path.basename(path)})
            c["ratings"].append({"id": r.get("competency_id", "?"), "competency": r.get("competency", ""),
                                 "rating": r.get("rating", "").lower(), "evidence": r.get("evidence", "")})
    return list(cards.values())


# Flagged words that also have a plain technical meaning. --keep restores a
# removal only when its sentence holds exactly one flagged word and that word
# is one of these; a sentence with two or more flagged words, or a word that
# only ever describes a person ("exhausted", "accent", "pregnant"), stays cut.
KEEPABLE = re.compile(
    r"(generation|retir\w*|foreign|health|medical|looks?|mature|blind|ill|energy|family|"
    r"weight|polished|confiden(t|ce)|calm|young|sick|church|hair)", re.I)


def redact(text, rules, log, keep, who, where):
    """Replace every sentence holding a CUT match with a numbered marker, unless
    its number is in keep. Appends to log; returns (text, sentences removed)."""
    if not text or not cut_spans(text, rules):
        return text, 0
    quoted = text.strip()[:1] in "\"“" and text.strip()[-1:] in "\"”"
    inner = text.strip()[1:-1] if quoted else text
    parts = re.split(r"(?<=[.!?;])\s+", inner)
    kept, gone = [], 0
    for p in parts:
        spans = cut_spans(p, rules)
        if not spans:
            kept.append(p)
            continue
        n = len(log) + 1
        spans = sorted(set(spans))
        cat = spans[0][2]
        words = [(c, p[s:e]) for s, e, c in spans]
        restorable = len(spans) == 1 and bool(KEEPABLE.fullmatch(words[0][1].strip()))
        log.append({"n": n, "interviewer": who, "where": where, "category": cat,
                    "categories": sorted({c for c, _ in words}), "flagged_count": len(words),
                    "match": "; ".join(f"{c} ('{w}')" for c, w in words),
                    "kept": n in keep and restorable, "keep_refused": n in keep and not restorable})
        if n in keep and restorable:
            kept.append(p)
        else:
            gone += 1
            kept.append(f"[removed #{n}: {cat}]")
    out = " ".join(kept)
    whole = bool(REMOVED_RX.fullmatch(out))
    return (f"\"{out}\"" if quoted and not whole else out), gone


def numeric(r):
    return int(r) if re.fullmatch(r"[1-5]", r or "") else None


def parse_time(s):
    try:
        return dt.datetime.fromisoformat(s) if s else None
    except ValueError:
        return None


def collate(a):
    cards, needs = [], []
    src = os.path.expanduser(a.scorecards)
    if os.path.isdir(src):
        for p in sorted(glob.glob(os.path.join(src, "*.md"))):
            try:
                cards.append(parse_md(p))
            except (ValueError, OSError) as exc:
                needs.append(f"{os.path.basename(p)}: {exc}")
    elif src.lower().endswith(".csv"):
        cards = parse_csv(src, a.candidate)
    else:
        raise ValueError("--scorecards must be a folder of .md scorecards or a .csv export")
    expected = []
    if a.loops and os.path.exists(os.path.expanduser(a.loops)):
        with open(os.path.expanduser(a.loops), newline="", encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                r = {k.strip(): (v or "").strip() for k, v in r.items() if k}
                if fold(r.get("candidate")) == fold(a.candidate) and fold(r.get("role")) == fold(a.role) \
                        and "cancel" not in r.get("status", "").lower():
                    for who in re.split(r"[;,]", r.get("interviewers", "")):
                        if who.strip():
                            expected.append({"interviewer": who.strip(), "coverage": r.get("coverage", ""),
                                             "date": r.get("date", "")})
    rules = load_lexicon(DEFAULT_LEXICON)
    keep = {int(x) for x in re.findall(r"\d+", getattr(a, "keep", None) or "")}
    removals = []
    owned = {}
    for e in expected:
        owned.setdefault(fold(e["interviewer"]), set()).update(re.findall(r"M\d+", e["coverage"]))
    for c in cards:
        own = set(re.findall(r"M\d+", c.get("competencies", ""))) or owned.get(fold(c["interviewer"]), set())
        for r in c["ratings"]:
            r["outside_slot"] = bool(own) and r["id"] not in own
            r["evidence"], r["removed"] = redact(r["evidence"], rules, removals, keep,
                                                 c["interviewer"], f"{r['id']} rating {r['rating']}")
        c["reason"], c["reason_removed"] = redact(c["reason"], rules, removals, keep,
                                                  c["interviewer"], "overall reason")
    include_outside = getattr(a, "include_outside", False)
    kit_names = {}
    if a.kit and os.path.exists(os.path.expanduser(a.kit)):
        with open(os.path.expanduser(a.kit), encoding="utf-8") as fh:
            for line in fh:
                m = re.match(r"^\s*[-*]\s*(M\d+)\s*:\s*(.+)$", line)
                if m:
                    kit_names[m.group(1)] = m.group(2).strip()
    filed_names = {fold(c["interviewer"]) for c in cards}
    roll = []
    for e in expected:
        roll.append({**e, "filed": fold(e["interviewer"]) in filed_names})
    for c in cards:
        if not any(fold(e["interviewer"]) == fold(c["interviewer"]) for e in expected):
            roll.append({"interviewer": c["interviewer"], "coverage": "", "date": "", "filed": True,
                         "note": "not on the loop log" if expected else ""})
    n_exp = len(expected) or len(cards)
    n_filed = sum(1 for r in roll if r["filed"] and not r.get("note")) if expected else len(cards)
    ratio = (n_filed / n_exp) if expected else (1.0 if cards else 0.0)
    comps = {}
    for c in cards:
        for r in c["ratings"]:
            comps.setdefault(r["id"], {"id": r["id"], "name": kit_names.get(r["id"]) or r["competency"], "ratings": []})
            comps[r["id"]]["ratings"].append({"interviewer": c["interviewer"], **r})
    for e in expected:
        for mid in re.findall(r"M\d+", e["coverage"]):
            comps.setdefault(mid, {"id": mid, "name": kit_names.get(mid, ""), "ratings": []})
    for mid, name in kit_names.items():
        comps.setdefault(mid, {"id": mid, "name": name, "ratings": []})
    blocks = []
    for mid, comp in sorted(comps.items(), key=lambda kv: int(kv[0][1:]) if kv[0][1:].isdigit() else 999):
        counted = [r for r in comp["ratings"] if include_outside or not r.get("outside_slot")]
        nums = [numeric(r["rating"]) for r in counted if numeric(r["rating"]) is not None]
        split = len(nums) >= 2 and max(nums) - min(nums) >= a.gap
        empty = [r["interviewer"] for r in comp["ratings"] if numeric(r["rating"]) is not None
                 and len(re.sub(r"[\"'“”\s]", "", REMOVED_RX.sub("", r["evidence"]))) < 3]
        outside = [f"{r['interviewer']} ({r['rating']})" for r in comp["ratings"] if r.get("outside_slot")]
        removed = sum(r.get("removed", 0) for r in comp["ratings"])
        na = [r["interviewer"] for r in comp["ratings"] if r["rating"] == "not assessed"]
        thin = not nums or bool(empty) or len(nums) == 1   # one voice, or no usable evidence
        nos = [x["n"] for x in removals if not x["kept"] and x["where"].startswith(mid + " ")]
        back = [x["n"] for x in removals if x["kept"] and x["where"].startswith(mid + " ")]
        blocks.append({**comp, "split": split, "empty_evidence": empty, "not_assessed": na,
                       "no_written_evidence": not nums, "thin": thin, "outside_slot": outside,
                       "removed_remarks": removed, "removed_numbers": nos, "restored_numbers": back})
    blocks.sort(key=lambda b: (not b["split"], not b["thin"], b["id"]))
    overall, no_decision, early = [], 0, []
    for c in cards:
        rec = c["recommendation"].strip().lower()
        if rec in ("", "no decision", "no-decision", "none", "undecided"):
            no_decision += 1
        overall.append({"interviewer": c["interviewer"], "recommendation": c["recommendation"] or "(blank)",
                        "reason": c["reason"], "removed_remarks": c.get("reason_removed", 0)})
        if rec not in ("", "no decision") and any(not r["rating"] for r in c["ratings"]):
            early.append(c["interviewer"])
    late = []
    start = parse_time(a.debrief_start) if a.debrief_start else None
    for c in cards:
        t = parse_time(c["filed_at"])
        if start and t and t.tzinfo and start.tzinfo and t > start:
            late.append(f"{c['interviewer']} filed {c['filed_at']} (after the debrief start {a.debrief_start})")
        elif start and not t:
            late.append(f"{c['interviewer']}: no usable filed_at; cannot tell whether it came before the debrief")
    hm = a.hm
    if not hm and a.loops:
        roles_path = os.path.join(os.path.dirname(os.path.expanduser(a.loops)), "roles.csv")
        if os.path.exists(roles_path):
            with open(roles_path, newline="", encoding="utf-8-sig") as fh:
                for r in csv.DictReader(fh):
                    if fold(r.get("role")) == fold(a.role):
                        hm = (r.get("hiring_manager") or "").strip()
    if a.order:
        order, order_note = [x.strip() for x in a.order.split(",") if x.strip()], "owner's order"
    else:
        people = [r["interviewer"] for r in roll]
        seen, order = set(), []
        for p in people:
            if fold(p) not in seen and fold(p) != fold(hm):
                order.append(p)
                seen.add(fold(p))
        if hm:
            order.append(hm)
        order_note = "slot order with the hiring manager last; confirm seniority (junior first)"
    body = max(a.minutes - 10, 5)
    weights = {b["id"]: (3 if b["split"] else 2 if b["thin"] else 1) for b in blocks}
    total_w = sum(weights.values()) or 1
    # largest-remainder split so the minutes add up exactly to the meeting length
    raw = {k: body * w / total_w for k, w in weights.items()}
    alloc = {k: int(v) for k, v in raw.items()}
    for k in sorted(raw, key=lambda k: raw[k] - alloc[k], reverse=True)[: body - sum(alloc.values())]:
        alloc[k] += 1
    return {"candidate": a.candidate, "role": a.role, "roll_call": roll, "filed": n_filed, "expected": n_exp,
            "filed_ratio": round(ratio, 2), "bar": a.bar, "below_bar": bool(expected) and ratio < a.bar,
            "expected_unknown": not expected, "blocks": blocks,
            "removals": [{k: v for k, v in x.items() if k != "match"} for x in removals],
            "_removal_words": [x["match"] for x in removals],
            "overall": overall, "no_decision_count": no_decision, "overall_before_ratings": early,
            "late_or_unknown_filing": late, "running_order": order, "order_note": order_note,
            "minutes": {"opening": 5, "decision": 5, **alloc, "total": a.minutes}, "needs_a_look": needs}


def render(res):
    if res.get("expected_unknown"):
        head = (f"## Roll-call ({res['filed']} scorecard{'' if res['filed'] == 1 else 's'} filed; no loop log, so the expected count "
                "is unknown: give the owner's list)")
    else:
        head = f"## Roll-call ({res['filed']} of {res['expected']} filed; bar {res['bar']:.0%})"
    L = [f"# Debrief brief: {res['candidate']} · {res['role']}", "", head, ""]
    for r in res["roll_call"]:
        L.append(f"- {r['interviewer']}{' (' + r['coverage'] + ')' if r.get('coverage') else ''}: "
                 f"{'filed' if r['filed'] else 'NOT FILED'}{' · ' + r['note'] if r.get('note') else ''}")
    if res["below_bar"]:
        missing = [b["id"] for b in res["blocks"] if b["no_written_evidence"]]
        L += ["", f"**Warning:** under {res['bar']:.0%} filed. The room will argue from memory. "
              f"Competencies with no written evidence: {', '.join(missing) or 'none'}. "
              "Anyone unfiled writes a rating down before discussion starts."]
    for n in res["late_or_unknown_filing"]:
        L.append(f"- Process risk: {n}")
    L += [""]
    for b in res["blocks"]:
        tag = "Split first — " if b["split"] else ""
        L += [f"## {tag}{b['id']} {b['name']}".rstrip(), ""]
        if not b["ratings"]:
            L.append("- No written evidence: no scorecard rated this competency.")
        for r in b["ratings"]:
            ev = r["evidence"] or "(empty)"
            tag = " [outside this slot]" if r.get("outside_slot") else ""
            L.append(f"- {r['interviewer']}, {r['rating']}{tag}: {ev} [FACT, scorecard]")
            L.append("  INFERENCE: <<does the evidence earn the rating? one line>>")
        if b.get("removed_numbers"):
            L.append(f"- Removed {', '.join('#' + str(n) for n in b['removed_numbers'])}: "
                     "remark(s) not about the job (not repeated).")
        if b.get("restored_numbers"):
            L.append(f"- Restored {', '.join('#' + str(n) for n in b['restored_numbers'])}: the flagged word "
                     "is a technical term (checked against flag_remarks.py).")
        if b.get("outside_slot"):
            L.append(f"- Outside the owning slot (not counted for splits): {', '.join(b['outside_slot'])}. "
                     "Challenge: which slot's question produced this, and what did you see?")
        for who in b["empty_evidence"]:
            L.append(f"- Flag: {who} rated without evidence; quote what sits there instead.")
        if b["not_assessed"]:
            L.append(f"- Not assessed by: {', '.join(b['not_assessed'])}")
        L.append("")
    L += ["## Overall recommendations (listed, never tallied)", ""]
    for o in res["overall"]:
        L.append(f"- {o['interviewer']}: {o['recommendation']}" + (f" — \"{o['reason']}\"" if o["reason"] else ""))
    L.append(f"- No decision or blank: {res['no_decision_count']} (counted separately; not a neutral vote)")
    for who in res["overall_before_ratings"]:
        L.append(f"- Flag: {who} gave an overall with a competency rating blank")
    gone = [x for x in res.get("removals", []) if x["where"] == "overall reason"]
    if any(not x["kept"] for x in gone):
        L.append(f"- Removed from overall reasons {', '.join('#' + str(x['n']) for x in gone if not x['kept'])}: "
                 "remark(s) not about the job (not repeated).")
    if any(x["kept"] for x in gone):
        L.append(f"- Restored in overall reasons {', '.join('#' + str(x['n']) for x in gone if x['kept'])}: "
                 "the flagged word is a technical term (checked against flag_remarks.py).")
    challenges = [f"{b['id']}: {x} rated outside their slot" for b in res["blocks"] for x in b.get("outside_slot", [])]
    L += ["", "## Open questions (cheapest fix each)", "", "- <<two or three things nobody can answer yet>>"]
    L += [f"- Challenge: {c}; which evidence, from which question?" for c in challenges]
    L += ["",
          f"## Running order ({res['order_note']})", "",
          "- Speakers: " + ", ".join(res["running_order"]),
          "- Minutes: " + ", ".join(f"{k} {v}" for k, v in res["minutes"].items() if k != "total")
          + f" (of {res['minutes']['total']})", "",
          "## Decision record", "", "Left blank until the decision-maker states it in their words."]
    if res["needs_a_look"]:
        L += ["", "## Needs a look"] + [f"- {n}" for n in res["needs_a_look"]]
    return "\n".join(L) + "\n"


def selftest():
    d = tempfile.mkdtemp()
    sc = os.path.join(d, "scorecards")
    os.makedirs(sc)

    def card(name, rows, rec, filed):
        body = "\n".join(f"| {i} | {c} | {r} | {e} |" for i, c, r, e in rows)
        with open(os.path.join(sc, f"{fold(name).replace(' ', '-')}.md"), "w", encoding="utf-8") as fh:
            fh.write(f"---\ncandidate: Priya Nair\nrole: sbe\ninterviewer: {name}\nfiled_at: {filed}\n---\n"
                     f"## Ratings\n| id | competency | rating | evidence |\n| --- | --- | --- | --- |\n{body}\n"
                     f"## Overall\nrecommendation: {rec}\nreason: x\n")
    card("Ana Silva", [("M2", "Live data", "2", '"Could not say how it would roll back"')], "no hire",
         "2026-10-05T16:40+01:00")
    card("Lena Ortiz", [("M2", "Live data", "4", '"Strong architecture instincts. Seemed nervous and a bit old-school."')],
         "hire", "2026-10-09T11:20+01:00")
    card("Dev Rao", [("M3", "Billing", "4", '"Traced a double charge to webhook retries"')], "no decision",
         "2026-10-05T15:00+01:00")
    with open(os.path.join(d, "loops.csv"), "w", encoding="utf-8") as fh:
        fh.write("candidate,role,date,start,end,tz,interviewers,coverage,status,scorecards\n"
                 "Priya Nair,SBE,2026-10-05,10:00,11:00,Europe/Lisbon,Dev Rao,M3,done,in\n"
                 "Priya Nair,SBE,2026-10-05,11:10,11:55,Europe/Lisbon,Ana Silva,M2,done,in\n"
                 "Priya Nair,SBE,2026-10-05,12:30,13:15,Europe/Lisbon,Lena Ortiz,M2,done,in\n"
                 "Priya Nair,SBE,2026-10-05,14:00,14:45,Europe/Lisbon,Sam Lee,M1,done,out\n")

    class A:
        candidate, role, scorecards, loops, kit = "Priya Nair", "SBE", sc, os.path.join(d, "loops.csv"), None
        debrief_start, gap, bar, minutes, order, hm = "2026-10-09T11:00+01:00", 2, 0.9, 40, None, "Lena Ortiz"
    res = collate(A)
    assert res["filed"] == 3 and res["expected"] == 4 and res["below_bar"], res
    assert res["blocks"][0]["id"] == "M2" and res["blocks"][0]["split"], res["blocks"]
    assert any(b["id"] == "M1" and b["no_written_evidence"] for b in res["blocks"])
    assert res["no_decision_count"] == 1
    assert any("Lena Ortiz filed" in x for x in res["late_or_unknown_filing"])
    assert res["running_order"][-1] == "Lena Ortiz"
    text = render(res)
    assert "average" not in text.lower() and "Split first" in text
    assert "nervous" not in text and "old-school" not in text and "[removed #1: affect]" in text, text
    res.pop("_removal_words")
    assert "nervous" not in json.dumps(res), res
    # a rating outside the interviewer's slot is tagged and does not make a split
    with open(os.path.join(d, "loops.csv"), "w", encoding="utf-8") as fh:
        fh.write("candidate,role,date,start,end,tz,interviewers,coverage,status,scorecards\n"
                 "Priya Nair,SBE,2026-10-05,10:00,11:00,Europe/Lisbon,Dev Rao,M3,done,in\n"
                 "Priya Nair,SBE,2026-10-05,11:10,11:55,Europe/Lisbon,Ana Silva,M2,done,in\n"
                 "Priya Nair,SBE,2026-10-05,12:30,13:15,Europe/Lisbon,Lena Ortiz,M4,done,in\n")
    res = collate(A)
    m2 = next(b for b in res["blocks"] if b["id"] == "M2")
    assert not m2["split"] and m2["outside_slot"] == ["Lena Ortiz (4)"], m2
    assert "[outside this slot]" in render(res)
    # technical English is not cut; a real over-cut can be restored with --keep
    card("Dev Rao", [("M3", "Billing", "4",
                      '"Added a foreign key from payouts to invoices. Her backfill plan looks correct: batches '
                      'of 10k, checksum per batch. Turned ill-defined billing requirements into a tested spec. '
                      'Explained invoice generation per tenant."')], "no decision", "2026-10-05T15:00+01:00")
    res = collate(A)
    m3 = next(b for b in res["blocks"] if b["id"] == "M3")
    ev = m3["ratings"][0]["evidence"]
    assert "foreign key" in ev and "looks correct" in ev and "ill-defined" in ev, ev
    assert m3["removed_numbers"] and not m3["empty_evidence"], m3
    n = m3["removed_numbers"][0]
    A.keep = str(n)
    res = collate(A)
    m3 = next(b for b in res["blocks"] if b["id"] == "M3")
    assert "invoice generation" in m3["ratings"][0]["evidence"] and m3["restored_numbers"] == [n], m3
    assert f"Restored #{n}" in render(res)
    # --keep never restores a sentence that holds a second flagged word, or a
    # word that only describes a person
    card("Dev Rao", [("M3", "Billing", "4",
                      '"Retired two cron jobs by moving them onto the queue, and she looked exhausted and '
                      'scruffy on camera. Traced the double charge to webhook retries."')],
         "hire", "2026-10-05T15:00+01:00")
    dev = os.path.join(sc, "dev-rao.md")
    with open(dev, encoding="utf-8") as fh:
        body = fh.read().replace("reason: x", "reason: Fixed the foreign rounding, though her accent was "
                                 "hard to follow.")
    with open(dev, "w", encoding="utf-8") as fh:
        fh.write(body)
    A.keep = None
    res = collate(A)
    nums = [x["n"] for x in res["removals"]]
    A.keep = ",".join(str(x) for x in nums)
    res = collate(A)
    text = render(res)
    assert "exhausted" not in text and "scruffy" not in text and "accent" not in text, text
    assert all(not x["kept"] and x["keep_refused"] for x in res["removals"]), res["removals"]
    A.keep = None
    # no loop log: the expected count is unknown, not "0 of N"
    A.loops = os.path.join(d, "missing.csv")
    res = collate(A)
    text = render(res)
    assert res["expected_unknown"] and not res["below_bar"] and "3 scorecards filed; no loop log" in text, text
    assert "not on the loop log" not in text and "0 of" not in text, text
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--candidate")
    ap.add_argument("--role")
    ap.add_argument("--scorecards")
    ap.add_argument("--loops", default=os.path.expanduser("~/workspace/hiring/tracker/loops.csv"))
    ap.add_argument("--kit")
    ap.add_argument("--debrief-start")
    ap.add_argument("--gap", type=int, default=DEFAULT_GAP)
    ap.add_argument("--bar", type=float, default=DEFAULT_BAR)
    ap.add_argument("--minutes", type=int, default=DEFAULT_MINUTES)
    ap.add_argument("--order")
    ap.add_argument("--hm")
    ap.add_argument("--include-outside", action="store_true",
                    help="count ratings outside the interviewer's slot when detecting splits")
    ap.add_argument("--keep", help="removal numbers to restore (n[,n]) after checking each flagged word "
                                     "is plainly a technical term")
    ap.add_argument("--out")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not (a.candidate and a.role and a.scorecards):
        ap.error("--candidate, --role and --scorecards are required")
    try:
        res = collate(a)
    except (OSError, ValueError, KeyError) as exc:
        print(f"bad input: {exc}", file=sys.stderr)
        return 2
    words = res.pop("_removal_words")
    for x, w in zip(res["removals"], words):
        print(f"removal #{x['n']}{' (restored)' if x['kept'] else ''}: {x['interviewer']} · {x['where']} · "
              f"{x['flagged_count']} flagged word(s): {w}", file=sys.stderr)
        if x.get("keep_refused"):
            why = (f"it holds {x['flagged_count']} flagged words" if x["flagged_count"] > 1
                   else "the flagged word only ever describes a person")
            print(f"  removal #{x['n']}: not restored ({why}); ask the interviewer to refile the sentence "
                  "as job evidence", file=sys.stderr)
    text = render(res)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(os.path.expanduser(a.out))), exist_ok=True)
        with open(os.path.expanduser(a.out), "w", encoding="utf-8") as fh:
            fh.write(text)
    print(json.dumps(res, indent=1, default=str) if a.json else text)
    return 1 if res["below_bar"] or res["needs_a_look"] else 0


if __name__ == "__main__":
    sys.exit(main())
