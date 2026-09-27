#!/usr/bin/env python3
"""Check an intake.json for completeness, list what is blocked, and diff it
against the previous intake for the same entity.

    cd ~/skills/bookkeeping-getting-started && python3 scripts/intake_check.py \
        ~/workspace/bookkeeping/<entity>/intake.json [--previous PATH] [--profile PATH]

- Required fields missing or set to null are reported as BLOCKED, with the
  question to ask. The value "open" is allowed only for `basis` and means the
  owner or accountant has not supplied it; it is never filled in.
- `--profile` (profile_sources.py JSON) cross-checks each source's rows and
  flags against what the intake says; a difference is a blocker. Files are
  joined on the name without `.csv` and without redact.py's `.masked` infix
  (or on a source's `profile_file`), so profiling the masked copies works. A
  CSV source with no profile entry is itself a blocker. A profile
  AMBIGUOUS_DATE_FORMAT blocks unless the source has `date_format_confirmed`,
  whatever the intake's own `date_format_ambiguous` says.
- An empty `opening_balances` list, or an entry with no `evidence`, is a
  blocker unless `period.first_period` is true (the business's first ever
  period, so there is nothing to bring forward).
- `--previous` prints what changed since the last intake (new or dropped
  sources, approver, basis, currency, fiscal year end or accountant changes)
  so the owner can confirm each change.

Exit 0 when nothing is blocked, 1 when something is blocked, 2 on bad input.
Template: templates/intake.json.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bkio  # noqa: E402

REQUIRED = [
    ("entity.legal_name", "What is the entity's full legal name?"),
    ("entity.slug", "Pick a short folder name for this entity (lowercase, hyphens)."),
    ("entity.jurisdiction", "Which country is the business registered in?"),
    ("entity.fiscal_year_end", "What is the fiscal year end (month and day)?"),
    ("period.start", "What is the first day of the period to work on?"),
    ("period.end", "What is the last day of the period to work on?"),
    ("reporting_currency", "What is the reporting currency?"),
    ("basis", "Cash or accrual? (\"open\" until the owner or accountant says)"),
    ("chart.source", "Where is the approved chart of accounts?"),
    ("chart.owner", "Who approves changes to the chart of accounts?"),
    ("approvers.invoices", "Who approves invoices before they are issued?"),
    ("approvers.customer_contact", "Who approves any message to a customer?"),
    ("approvers.adjustments", "Who approves adjustments and journal proposals?"),
    ("approvers.final_reports", "Who approves final reports?"),
    ("accountant", "Who is the accountant or finance owner for tax, policy and material items?"),
    ("system_of_record.name", "Where do the books live (QuickBooks, Xero, spreadsheet, none)?"),
    ("system_of_record.owner_holds_export_copy", "Does the owner hold their own exported copy of the books?"),
]


def get(d, dotted):
    cur = d
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def file_key(path):
    """Join key for a source file and its profile: the basename, lower-cased,
    without .csv and without the .masked infix that redact.py's copies carry,
    so a profile of bank.masked.csv matches an intake source bank.csv."""
    name = os.path.basename(path or "").strip().lower()
    if name.endswith(".csv"):
        name = name[:-4]
    if name.endswith(".masked"):
        name = name[:-7]
    return name


def check(intake, profile=None):
    blocked, warnings = [], []
    for field, question in REQUIRED:
        v = get(intake, field)
        if v in (None, "", []):
            blocked.append((field, question))
    if get(intake, "basis") not in (None, "open", "cash", "accrual", "modified cash"):
        warnings.append(f"basis '{get(intake, 'basis')}' is not cash/accrual/open: confirm the wording with the accountant")
    sources = intake.get("sources") or []
    if not sources:
        blocked.append(("sources", "Which exports or records do you have for the period?"))
    period = intake.get("period") or {}
    if not period.get("first_period"):
        obs = [o for o in (intake.get("opening_balances") or []) if isinstance(o, dict)]
        if not obs:
            blocked.append(("opening_balances", "What are the opening balances for the period, and which "
                            "record supports each (signed-off trial balance, statement)? If this is the "
                            "business's first ever period, say so."))
        for o in obs:
            if not o.get("evidence"):
                blocked.append((f"opening_balances[{o.get('account') or '?'}]",
                                f"Which record supports the opening balance of {o.get('account') or 'this account'}?"))
    for s in sources:
        name = s.get("file") or s.get("name") or "?"
        for f in ("entity_confirmed", "dates", "rows", "control_total", "currency"):
            if s.get(f) in (None, "", False) and s.get("state") != "blocked":
                warnings.append(f"source {name}: {f} not recorded")
        if s.get("entity_confirmed") is False:
            blocked.append((f"sources[{name}].entity", f"Does {name} belong to {get(intake, 'entity.legal_name')}?"))
        if s.get("date_format_ambiguous") and not s.get("date_format_confirmed"):
            blocked.append((f"sources[{name}].date_format", f"Are dates in {name} day/month or month/day?"))
        d = s.get("dates") or {}
        if period.get("start") and d.get("from") and d["from"] > period["start"]:
            warnings.append(f"source {name} starts {d['from']}, after the period start {period['start']}")
        if period.get("end") and d.get("to") and d["to"] < period["end"]:
            warnings.append(f"source {name} ends {d['to']}, before the period end {period['end']}")
    if profile:
        by_file = {file_key(p["file"]): p for p in profile}
        for s in sources:
            src = s.get("profile_file") or s.get("file") or ""
            p = by_file.get(file_key(src))
            if not p:
                if src.lower().endswith(".csv"):
                    blocked.append((f"sources[{os.path.basename(src)}].profile",
                                    f"no profile for {os.path.basename(src)}: run profile_sources.py on it "
                                    "(or its .masked.csv copy) and pass the JSON with --profile"))
                continue
            if s.get("rows") is not None and int(s["rows"]) != p["rows"]:
                blocked.append((f"sources[{p['file']}].rows",
                                f"Intake says {s['rows']} rows but the file has {p['rows']}: which is right?"))
            for flag in p["flags"]:
                if flag.startswith(("BALANCE_BREAK", "UNREADABLE", "RAGGED_ROWS", "BOTH_DEBIT_AND_CREDIT", "NO_ROWS")):
                    blocked.append((f"sources[{p['file']}]", f"{p['file']}: {flag}"))
            name = s.get("file") or s.get("name") or "?"
            if (p.get("date_format_ambiguous") or any(f.startswith("AMBIGUOUS_DATE_FORMAT") for f in p["flags"])) \
                    and not s.get("date_format_confirmed") \
                    and f"sources[{name}].date_format" not in [b[0] for b in blocked]:
                blocked.append((f"sources[{name}].date_format",
                                f"Are dates in {name} day/month or month/day? (profile: AMBIGUOUS_DATE_FORMAT)"))
    for q in intake.get("open_questions") or []:
        if not q.get("answer"):
            blocked.append((q.get("id", "open_question"), q.get("question", "?")))
    return blocked, warnings


def diff(prev, cur):
    changes = []
    for field in ("entity.legal_name", "entity.fiscal_year_end", "reporting_currency", "basis",
                  "chart.source", "chart.owner", "approvers.invoices", "approvers.customer_contact",
                  "approvers.adjustments", "approvers.final_reports", "accountant",
                  "system_of_record.name"):
        a, b = get(prev, field), get(cur, field)
        if a != b:
            changes.append(f"{field}: {a!r} -> {b!r}")
    pf = {s.get("system", "") + "|" + (s.get("account") or "") for s in prev.get("sources") or []}
    cf = {s.get("system", "") + "|" + (s.get("account") or "") for s in cur.get("sources") or []}
    for k in sorted(cf - pf):
        changes.append(f"new source: {k}")
    for k in sorted(pf - cf):
        changes.append(f"source no longer supplied: {k}")
    return changes


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        bkio.die(f"{path} not found", "write the intake from templates/intake.json first")
    except json.JSONDecodeError as e:
        bkio.die(f"{path} is not valid JSON: {e}", "fix the JSON syntax at the reported line")


def selftest():
    here = os.path.dirname(os.path.abspath(__file__))
    ex = os.path.join(here, "..", "examples", "bramble-april-intake")
    intake = load(os.path.join(ex, "intake.json"))
    blocked, _ = check(intake)
    ids = [b[0] for b in blocked]
    assert "sources[bank-main-2026-04.csv].date_format" in ids, ids
    assert "Q3" in ids and "Q4" not in ids, ids   # answered questions are not blockers
    prev = json.loads(json.dumps(intake))
    prev["approvers"]["final_reports"] = "Jo"
    assert any("approvers.final_reports" in c for c in diff(prev, intake))
    # profiling the masked copy (SKILL step 3) must still carry the balance break
    import shutil
    import tempfile
    import profile_sources
    with tempfile.TemporaryDirectory() as d:
        masked = os.path.join(d, "bank-main-2026-04.masked.csv")
        shutil.copy(os.path.join(ex, "bank-main-2026-04.csv"), masked)
        card = os.path.join(d, "amex-2026-04.masked.csv")
        shutil.copy(os.path.join(ex, "amex-2026-04.csv"), card)
        prof = [profile_sources.profile(masked), profile_sources.profile(card)]
    b3, _ = check(intake, prof)
    ids3 = [b[0] for b in b3]
    assert any(i.startswith("sources[bank-main-2026-04.masked.csv]") for i in ids3), ids3
    assert len(b3) == 5, b3
    b4, _ = check(intake, prof[1:])
    assert "sources[bank-main-2026-04.csv].profile" in [b[0] for b in b4], b4
    # the profile's ambiguity blocks even when the intake did not copy the flag
    noamb = json.loads(json.dumps(intake))
    for s in noamb["sources"]:
        s.pop("date_format_ambiguous", None)
    noamb["open_questions"] = [q for q in noamb["open_questions"] if q["id"] != "Q1"]
    b5 = [b[0] for b in check(noamb, prof)[0]]
    assert "sources[bank-main-2026-04.csv].date_format" in b5, b5
    assert "sources[bank-main-2026-04.csv].date_format" not in [b[0] for b in check(noamb)[0]]
    # no opening balance blocks, unless this is the first ever period
    noob = json.loads(json.dumps(intake))
    noob["opening_balances"] = []
    assert "opening_balances" in [b[0] for b in check(noob)[0]]
    noob["opening_balances"] = [{"account": "Bank ****4417", "value": "29617.59", "evidence": None}]
    assert "opening_balances[Bank ****4417]" in [b[0] for b in check(noob)[0]]
    noob["period"]["first_period"] = True
    assert not [b for b in check(noob)[0] if b[0].startswith("opening_balances")]
    tmpl = load(os.path.join(here, "..", "templates", "intake.json"))
    b2, _ = check(tmpl)
    assert b2, "an empty template must be blocked"
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("intake", nargs="?")
    ap.add_argument("--previous")
    ap.add_argument("--profile")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.intake:
        bkio.die("no intake.json given", "pass ~/workspace/bookkeeping/<entity>/intake.json")
    intake = load(a.intake)
    profile = load(a.profile) if a.profile else None
    blocked, warnings = check(intake, profile)
    print(f"BLOCKED ({len(blocked)})")
    for field, q in blocked:
        print(f"- {field}: {q}")
    print(f"WARNINGS ({len(warnings)})")
    for w in warnings:
        print(f"- {w}")
    if a.previous:
        changes = diff(load(a.previous), intake)
        print(f"CHANGED SINCE PREVIOUS INTAKE ({len(changes)}): confirm each with the owner")
        for c in changes:
            print(f"- {c}")
    sys.exit(1 if blocked else 0)


if __name__ == "__main__":
    main()
