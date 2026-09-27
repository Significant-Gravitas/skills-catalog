#!/usr/bin/env python3
"""Collate filed interview scorecards into a criterion-by-interviewer evidence table.

Usage:
  cd ~/skills/candidate-interview-debrief && \
  python3 scripts/collate_scorecards.py <filed_dir | file.csv | file.md ...> \
      --out <dir> [--rubric rubric.csv] [--loop loop.csv] [--scale 4] [--gap 2] \
      [--labels greenhouse] [--debrief-start 2026-10-03T10:00+01:00] [--candidate B-003] \
      [--criterion-map map.csv]

Inputs (any mix)
  * CSV scorecards written by interview-plan-and-scorecard/make_scorecards.py:
      candidate_id,interviewer,slot,criterion_id,criterion,score,evidence_quote,
      source,confidence,submitted_at
  * The markdown twin of those scorecards, filled in by hand.
  * An ATS scorecard export (CSV). Common header aliases are mapped:
      submitted_by/interviewer_name -> interviewer, attribute/question -> criterion,
      rating -> score, notes/comments -> evidence_quote, submitted/submitted_on
      -> submitted_at, overall_recommendation/recommendation -> overall.
    With --labels greenhouse, the labels "Definitely Not, No, Mixed or Neutral,
    Yes, Strong Yes" map to 1-5 and --scale becomes 5 (Greenhouse Scorecards
    FAQ, dossier [90]).
  --rubric  optional; supplies criterion names and flags unknown criteria.
  --loop    optional; supplies who was expected to file which criterion.
  --criterion-map  optional CSV with columns name,criterion_id, for ATS
            attribute names that differ from the rubric's criterion text.

ATS exports carry criterion names, not ids. When a row has no criterion_id,
its name is mapped to a rubric id by case-insensitive exact match (or through
--criterion-map). A name that does not map goes to "needs a look", and the
loop checks (missing filing, out-of-slot) are skipped for it rather than
asserted: the script never reports that someone failed to file, or scored
outside their slot, when it cannot tell which criterion they scored.
  --gap     split threshold (max - min). Default 2 on a 4-point scale is a
            default, confirm with the owner; use the company's rule if it has one.

Outputs in --out:
  debrief.md    evidence table, splits first, not-assessed, filing status,
                recorded overall recommendations (verbatim, "No Decision"
                counted separately), and a needs-a-look list
  debrief.json  the same data for flag_remarks.py

By design this script never computes a total, mean, median, weighted score or
rank for a candidate. A number like that hides the evidence and invites the
panel to anchor on it (Mediating Assessments Protocol, dossier [21]). A
score it cannot parse goes to "needs a look"; it is never guessed.

It never overwrites a filing. If two files hold the same interviewer and
criterion (for example the .md and .csv twins make_scorecards.py writes, or
a re-filed or edited copy): a blank one never replaces a filled one and the
pair goes to "needs a look"; two filled ones that differ are both kept and
shown, and listed as a process risk for the owner to resolve. With
--debrief-start, a filing with no readable time goes to "needs a look", and
each extra differing filing is checked against the start on its own time
(a changed copy filed after discussion began is an anchoring risk).
Exit 0 = collated, 1 = collated with needs-a-look items, 2 = bad input.
"""

import argparse
import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ALIASES = {
    "interviewer": ["interviewer", "submitted_by", "interviewer_name", "reviewer", "scorer"],
    "criterion_id": ["criterion_id", "attribute_id", "competency_id"],
    "criterion": ["criterion", "attribute", "competency", "question", "focus_attribute"],
    "score": ["score", "rating", "attribute_rating", "value"],
    "evidence_quote": ["evidence_quote", "evidence", "notes", "note", "comments", "comment"],
    "source": ["source", "method"],
    "confidence": ["confidence"],
    "submitted_at": ["submitted_at", "submitted", "submitted_on", "submitted_date", "filed_at"],
    "candidate_id": ["candidate_id", "candidate", "application_id"],
    "overall": ["overall", "overall_recommendation", "recommendation"],
    "slot": ["slot", "interview", "interview_name"],
}
GREENHOUSE = {"definitely not": 1, "no": 2, "mixed or neutral": 3, "mixed": 3, "neutral": 3,
              "yes": 4, "strong yes": 5}
NOT_ASSESSED = {"not assessed", "n/a", "na", "not_assessed", "-", "not rated"}


def norm(h: str) -> str:
    return re.sub(r"[\s\-]+", "_", str(h).strip().lower())


def canon(row: dict) -> dict:
    low = {norm(k): (v or "").strip() for k, v in row.items() if k}
    out = {}
    for key, names in ALIASES.items():
        for n in names:
            if low.get(n):
                out[key] = low[n]
                break
        out.setdefault(key, "")
    out["_has_overall"] = any(n in low for n in ALIASES["overall"])
    return out


def parse_md(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig")
    head = re.search(r"candidate\s+(\S+)\s*\|\s*interviewer\s+(.+)", text)
    cand, who = (head.group(1), head.group(2).strip()) if head else ("", "")
    sub = re.search(r"Submitted at[^:\n]*:[ \t]*(.*)$", text, re.M)
    rows = []
    for m in re.finditer(r"^## (\S+): (.+?)$(.*?)(?=^## |\Z)", text, re.M | re.S):
        cid, name, body = m.group(1), m.group(2), m.group(3)
        if cid.lower() == "filing":
            continue

        def field(label):
            f = re.search(rf"^- {label}[^:]*:[ \t]*(.*)$", body, re.M)
            return f.group(1).strip() if f else ""
        rows.append({"candidate_id": cand, "interviewer": who, "criterion_id": cid,
                     "criterion": name.strip(), "score": field("Score"),
                     "evidence_quote": field("Evidence"), "source": field("Source"),
                     "confidence": field("Confidence"),
                     "submitted_at": sub.group(1).strip() if sub else "", "overall": "", "slot": "",
                     "_has_overall": False})
    vis = re.search(r"before seeing other interviewers' scores[^:\n]*:[ \t]*(\S*)", text, re.M)
    for r in rows:
        r["filed_blind"] = vis.group(1) if vis else ""
    return rows


def load(paths: list[str]) -> tuple[list[dict], list[str]]:
    rows, problems = [], []
    files = []
    for p in paths:
        pp = Path(p).expanduser()
        if pp.is_dir():
            files += sorted(x for x in pp.iterdir() if x.suffix.lower() in (".csv", ".md")
                            and x.name != "ledger.csv")
        elif pp.is_file():
            files.append(pp)
        else:
            problems.append(f"not found: {p}")
    for f in files:
        try:
            if f.suffix.lower() == ".md":
                got = parse_md(f)
            else:
                got = [canon(r) for r in csv.DictReader(f.read_text(encoding="utf-8-sig").splitlines())]
            if not got:
                problems.append(f"{f.name}: no scorecard rows found")
            for r in got:
                r["_file"] = f.name
            rows += got
        except Exception as exc:  # report, never guess
            problems.append(f"{f.name}: could not read ({exc})")
    return rows, problems


def parse_score(raw: str, scale: int, labels: str | None):
    s = raw.strip().lower()
    if not s:
        return None, "blank"
    if s in NOT_ASSESSED:
        return "not assessed", None
    if labels == "greenhouse" and s in GREENHOUSE:
        return GREENHOUSE[s], None
    m = re.fullmatch(r"(\d+)(\s*/\s*\d+)?", s)
    if m and 1 <= int(m.group(1)) <= scale:
        return int(m.group(1)), None
    return None, f"unreadable score '{raw}'"


def parse_time(raw: str):
    if not raw:
        return None, "none"
    try:
        t = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
    except ValueError:
        return None, "unparsed"
    return t, ("zoned" if t.tzinfo else "zone UNKNOWN")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--rubric")
    ap.add_argument("--loop")
    ap.add_argument("--scale", type=int, default=4)
    ap.add_argument("--gap", type=int, default=2)
    ap.add_argument("--labels", choices=["greenhouse"])
    ap.add_argument("--debrief-start")
    ap.add_argument("--candidate")
    ap.add_argument("--criterion-map")
    a = ap.parse_args()
    if a.labels == "greenhouse":
        a.scale = 5

    rows, look = load(a.inputs)
    if not rows:
        print("error: no scorecard rows found; " + "; ".join(look), file=sys.stderr)
        return 2
    if a.candidate:
        other = {r["candidate_id"] for r in rows if r["candidate_id"] and r["candidate_id"] != a.candidate}
        if other:
            look.append(f"rows for other candidates ignored: {sorted(other)}")
        rows = [r for r in rows if not r["candidate_id"] or r["candidate_id"] == a.candidate]

    names = {}
    if a.rubric:
        for r in csv.DictReader(Path(a.rubric).read_text(encoding="utf-8-sig").splitlines()):
            r = {norm(k): (v or "").strip() for k, v in r.items() if k}
            names[r.get("criterion_id", "")] = r.get("criterion", "")
    by_name = {v.strip().lower(): k for k, v in names.items() if k and v}
    if a.criterion_map:
        for r in csv.DictReader(Path(a.criterion_map).read_text(encoding="utf-8-sig").splitlines()):
            r = {norm(k): (v or "").strip() for k, v in r.items() if k}
            nm = r.get("name") or r.get("criterion") or r.get("attribute", "")
            if nm and r.get("criterion_id"):
                by_name[nm.lower()] = r["criterion_id"]
    expected = {}
    if a.loop:
        for r in csv.DictReader(Path(a.loop).read_text(encoding="utf-8-sig").splitlines()):
            r = {norm(k): (v or "").strip() for k, v in r.items() if k}
            for cid in re.split(r"[;,]", r.get("criterion_ids", "")):
                if cid.strip():
                    expected.setdefault(r.get("interviewer", ""), set()).add(cid.strip())

    start, start_kind = parse_time(a.debrief_start or "")
    table: dict[str, dict[str, dict]] = {}
    interviewers, filing, overall = [], {}, {}
    risks_early: list[str] = []
    unmapped: dict[str, set] = {}  # interviewer -> criterion names that map to no rubric id
    for r in rows:
        who = r["interviewer"] or f"(unnamed in {r['_file']})"
        cid = r["criterion_id"]
        if not cid and r["criterion"]:
            cid = by_name.get(r["criterion"].strip().lower(), "")
            if cid:
                r["criterion_id"] = cid
            else:
                cid = r["criterion"]
                if (a.rubric or expected) and cid not in unmapped.get(who, set()):
                    look.append(f'{who}: cannot map "{cid}" to a rubric criterion; loop checks skipped for it '
                                "(use --rubric, or --criterion-map for ATS attribute names)")
                unmapped.setdefault(who, set()).add(cid)
        if not cid:
            look.append(f"{r['_file']}: a row with no criterion")
            continue
        if who not in interviewers:
            interviewers.append(who)
        if names and r["criterion_id"] and r["criterion_id"] not in names:
            look.append(f"{who}: criterion '{r['criterion_id']}' is not in the rubric (out-of-rubric, exclude)")
        score, err = parse_score(r["score"], a.scale, a.labels)
        if err and err != "blank":
            look.append(f"{who} / {cid}: {err}")
        cell = {"score": score, "raw": r["score"], "quote": r["evidence_quote"],
                "source": r["source"], "confidence": r["confidence"], "file": r["_file"],
                "submitted_at": r["submitted_at"]}
        if score is None and err == "blank":
            cell["status"] = "blank (not filed?)"
        elif isinstance(score, int) and not r["evidence_quote"]:
            cell["status"] = "score without evidence"
        names.setdefault(cid, r["criterion"] if r["criterion"] != cid else "")
        cells = table.setdefault(cid, {})
        prev = cells.get(who)
        is_blank = cell.get("status", "").startswith("blank")
        if prev is None:
            cells[who] = cell
        else:
            prev_blank = prev.get("status", "").startswith("blank")
            if prev_blank and is_blank:
                pass
            elif prev_blank or is_blank:
                kept, other = (prev, cell) if is_blank else (cell, prev)
                if "also" in prev and kept is cell:
                    cell["also"] = prev.pop("also")
                cells[who] = kept
                look.append(f"{who} / {cid}: blank in {other['file']}, filled in {kept['file']}; "
                            "showing the filled one. Confirm with the interviewer which copy is their filing")
            elif (prev["raw"], prev["quote"]) != (cell["raw"], cell["quote"]):
                prev.setdefault("also", []).append(cell)
                risks_early.append(f"two filings for {who}/{cid}: {prev['file']} (score {prev['raw'] or '?'}) vs "
                                   f"{cell['file']} (score {cell['raw'] or '?'}); both shown, the owner decides "
                                   "which counts. Never drop one without saying so")
                look.append(f"{who} / {cid}: two different filings ({prev['file']}, {cell['file']}); "
                            "ask the interviewer which is final")
        t, kind = parse_time(r["submitted_at"])
        f = filing.setdefault(who, {"submitted_at": r["submitted_at"], "kind": kind,
                                    "filed_blind": r.get("filed_blind", ""), "late": None,
                                    "_t": t, "files": []})
        if r["_file"] not in f["files"]:
            f["files"].append(r["_file"])
        if f["kind"] in ("none", "unparsed") and kind not in ("none", "unparsed") and not is_blank:
            f.update(submitted_at=r["submitted_at"], kind=kind, _t=t)
        if not f["filed_blind"] and r.get("filed_blind"):
            f["filed_blind"] = r["filed_blind"]
        rec = r.get("overall", "")
        if rec or r.get("_has_overall"):
            overall[who] = rec or overall.get(who, "")

    for who, f in filing.items():
        t, kind = f.pop("_t"), f["kind"]
        if not start:
            continue
        if t is None:
            look.append(f"{who}: no readable filing time ('{f['submitted_at'] or 'blank'}' in "
                        f"{', '.join(f['files'])}); ask the interviewer, never guess")
        elif kind == start_kind:
            f["late"] = t > start
        else:
            f["late"] = "cannot compare (zone unknown)"

    overall = {w: (v or "No Decision") for w, v in overall.items()}
    splits = []
    for cid, cells in table.items():
        nums = [c["score"] for c in cells.values() if isinstance(c["score"], int)]
        if len(nums) >= 2 and max(nums) - min(nums) >= a.gap:
            splits.append(cid)
    risks = list(risks_early)
    if start:
        for cid, cells in table.items():
            for who, c in cells.items():
                for other in c.get("also", []):
                    t, kind = parse_time(other.get("submitted_at", ""))
                    if t is not None and kind == start_kind and t > start:
                        risks.append(f"{who}: second filing {other['file']} at {other['submitted_at']}, "
                                     "after the debrief started; may be anchored on discussion")
                    elif t is None or kind != start_kind:
                        look.append(f"{who}: cannot tell whether second filing {other['file']} "
                                    f"('{other.get('submitted_at') or 'no time'}') came before the debrief start")
    if expected:
        for cid, cells in table.items():
            for who in cells:
                if cid in unmapped.get(who, set()):
                    continue
                if who in expected and cid not in expected[who]:
                    owner = [w for w, c in expected.items() if cid in c]
                    risks.append(f"{who} scored {cid}, which the loop assigns to {', '.join(owner) or 'nobody'}; "
                                 "the panel decides whether that evidence counts")
    for who, f in filing.items():
        if f["late"] is True:
            risks.append(f"{who} filed after the debrief started ({f['submitted_at']}); may be anchored on discussion")
        elif isinstance(f["late"], str):
            risks.append(f"{who}: filing time {f['late']}")
        if f.get("filed_blind", "").lower().startswith("n"):
            risks.append(f"{who} says they saw other scores before filing")
    order = list(names) if names else []
    table = {cid: table[cid] for cid in sorted(table, key=lambda c: order.index(c) if c in order else len(order))}
    missing = []
    for who, cids in expected.items():
        for cid in sorted(cids):
            cell = table.get(cid, {}).get(who)
            if not cell and unmapped.get(who):
                look.append(f"{who}: cannot confirm a filing for {cid}; their unmapped criteria "
                            f"({', '.join(sorted(unmapped[who]))}) may include it")
            elif not cell or cell.get("status", "").startswith("blank"):
                missing.append(f"{who}: {cid}")

    data = {"candidate": a.candidate or "", "scale": a.scale, "gap": a.gap,
            "interviewers": interviewers, "criteria": {cid: names.get(cid, "") for cid in table},
            "cells": table, "splits": splits, "missing_filings": missing, "process_risks": risks,
            "filing": filing, "overall_recorded": overall,
            "no_decision_count": sum(1 for v in overall.values() if v.strip().lower() in ("no decision", "")),
            "needs_a_look": look,
            "note": "No total, mean or rank is computed by design."}
    out = Path(a.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    (out / "debrief.json").write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    (out / "debrief.md").write_text(render(data), encoding="utf-8")
    print(f"collated {len(rows)} rows from {len(interviewers)} interviewer(s); "
          f"{len(splits)} split(s); {len(missing)} missing filing(s); {len(look)} needs-a-look")
    print(f"wrote {out / 'debrief.md'} and {out / 'debrief.json'}")
    return 1 if look else 0


def fmt(cell: dict | None) -> str:
    if not cell:
        return "-"
    s = cell["score"]
    head = "not assessed" if s == "not assessed" else (str(s) if s is not None else (cell.get("status") or "?"))
    if cell.get("status") == "score without evidence":
        head += " (no evidence given)"
    q = cell["quote"].replace("|", "/")
    text = f'{head} - "{q}"' if q else head
    for other in cell.get("also", []):
        text += f" / ALSO FILED in {other['file']}: " + fmt({k: v for k, v in other.items() if k != "also"})
    return text


def label(d: dict, cid: str) -> str:
    name = d["criteria"].get(cid, "")
    return cid if not name or name == cid else f"{cid} {name}"


def render(d: dict) -> str:
    who = d["interviewers"]
    L = [f"# Scorecard collation: candidate {d['candidate'] or '(unspecified)'}", "",
         f"Scale 1-{d['scale']}; split = gap of {d['gap']} or more (default unless the company set one).",
         "No total, average or rank is computed.", "", "## Resolve first (splits)", ""]
    if not d["splits"]:
        L.append("None at this threshold.")
    for cid in d["splits"]:
        L.append(f"- **{label(d, cid)}**")
        for w, c in d["cells"][cid].items():
            if isinstance(c["score"], int):
                L.append(f"  - {w}: {fmt(c)} (source: {c['source'] or '?'}, confidence: {c['confidence'] or '?'})")
    L += ["", "## Evidence by criterion", "",
          "| Criterion | " + " | ".join(who) + " |", "|---|" + "---|" * len(who)]
    for cid, cells in d["cells"].items():
        L.append(f"| {label(d, cid)} | " + " | ".join(fmt(cells.get(w)) for w in who) + " |")
    na = [f"{cid} ({w})" for cid, cells in d["cells"].items() for w, c in cells.items() if c["score"] == "not assessed"]
    L += ["", "## Not assessed", "", ", ".join(na) if na else "None."]
    L += ["", "## Filing", ""]
    for w in who:
        f = d["filing"].get(w, {})
        late = f.get("late")
        L.append(f"- {w}: submitted {f.get('submitted_at') or 'no time recorded'} ({f.get('kind', 'none')})"
                 + (f"; after debrief start: {({True: 'yes', False: 'no'}).get(late, late)}" if late is not None else "")
                 + (f"; filed before seeing peers: {f['filed_blind']}" if f.get("filed_blind") else ""))
    if d["missing_filings"]:
        L.append("- Expected but not filed: " + ", ".join(d["missing_filings"]))
    if d["overall_recorded"]:
        L += ["", "## Overall recommendations as recorded in the ATS (verbatim, not combined)", ""]
        for w, v in d["overall_recorded"].items():
            L.append(f"- {w}: {v}")
        L.append(f"- No Decision: {d['no_decision_count']} (counted separately; not a neutral vote)")
    L += ["", "## Process risks", ""] + ([f"- {x}" for x in d["process_risks"]] or ["None found by the script."])
    L += ["", "## Needs a look", ""] + ([f"- {x}" for x in d["needs_a_look"]] or ["None."])
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main())
