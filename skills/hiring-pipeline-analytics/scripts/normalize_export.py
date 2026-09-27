#!/usr/bin/env python3
"""Turn an ATS or spreadsheet export into the tracker's candidates.csv columns, safely.

Usage (cd ~/skills/hiring-pipeline-analytics first):

  python3 scripts/normalize_export.py <export.csv|.tsv|.xlsx> --out /home/user/pipeline/in \
      [--vendor auto|greenhouse|lever|ashby|workday|linkedin]  (prints that vendor's known traps; auto = detect from headers, printed as a guess) [--map extra-map.csv] \
      [--date-order dayfirst|monthfirst]

Writes OUT/candidates.csv (columns below) and OUT/hygiene.csv (category,line,detail), and
prints: protected columns dropped, columns kept but unmapped, and hygiene counts.

Canonical columns (the tracker's, from interview-coordination / sofia-getting-started):
  name,role,stage,source,owner,last_contact,next_step,waiting_on,days_in_stage,notes,is_prospect
plus optional dated columns funnel.py uses when present:
  applied_on,stage_entered_on,furthest_stage,reason,reason_type,offer_out_on,answer_by,
  offer_resolved_on,accepted_on,role_family,opening_id

Header aliases below are best-known defaults, not a vendor contract: vendors rename
columns. Anything not matched is REPORTED, never guessed; pass --map (export_column,
canonical_column) to fix it. Protected columns (references/protected-columns.txt, and
anything matching gender/race/ethnic/veteran/disab/birth/age/eeo/self-id/...) are dropped
before anything is written. A Greenhouse Harvest v1/v2 integration stopped working on
2026-08-31 (removed); use a UI export or a v3 connector. Ashby's passthrough report is a
closed-cohort PDF summary: it is not row-level, so this script refuses PDFs - ask for the
candidate or application CSV instead. A file that is not UTF-8 (Excel's Windows-1252
"CSV (Comma delimited)") is read as Windows-1252 with a one-line note; comma, semicolon
and tab delimiters are detected from the header.
Exit: 0 ok, 2 unreadable input, 5 PDF or unsupported format, 6 no name/stage column found.
"""

import argparse
import csv
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline_io as io  # noqa: E402

CANONICAL = ["name", "role", "stage", "source", "owner", "last_contact", "next_step", "waiting_on",
             "days_in_stage", "notes", "is_prospect", "applied_on", "stage_entered_on", "furthest_stage",
             "reason", "reason_type", "offer_out_on", "answer_by", "offer_resolved_on", "accepted_on",
             "role_family", "opening_id"]
ALIASES = {  # normalised header -> canonical (defaults; confirm against the owner's export)
    "name": ["name", "candidate", "candidate_name", "full_name", "contact_name", "applicant_name"],
    "role": ["role", "job", "job_name", "job_title", "posting", "posting_title", "requisition", "job_requisition", "opportunity_posting"],
    "stage": ["stage", "current_stage", "application_stage", "status", "current_status", "pipeline_stage", "step"],
    "source": ["source", "source_name", "candidate_source", "origin", "application_source", "referral_source"],
    "owner": ["owner", "recruiter", "coordinator", "opportunity_owner", "credited_to", "assigned_to"],
    "last_contact": ["last_contact", "last_activity", "last_activity_date", "last_contacted"],
    "next_step": ["next_step", "next_action"],
    "waiting_on": ["waiting_on"],
    "days_in_stage": ["days_in_stage", "days_in_current_stage", "time_in_stage"],
    "notes": ["notes"],
    "is_prospect": ["is_prospect", "prospect"],
    "applied_on": ["applied_on", "applied_at", "application_date", "date_applied", "applied_date", "created_at", "created_date", "sourced_on", "added_on"],
    "stage_entered_on": ["stage_entered_on", "entered_stage", "moved_to_stage_at", "stage_changed_at", "last_stage_change"],
    "furthest_stage": ["furthest_stage", "furthest_stage_reached", "last_stage_before_rejection"],
    "reason": ["reason", "rejection_reason", "archive_reason", "disqualification_reason", "decline_reason"],
    "reason_type": ["reason_type", "rejection_reason_type", "archive_reason_type"],
    "offer_out_on": ["offer_out_on", "offer_sent", "offer_sent_at", "offer_created_at", "offer_extended_date"],
    "answer_by": ["answer_by", "offer_expiration", "offer_expires_at", "offer_response_deadline"],
    "offer_resolved_on": ["offer_resolved_on", "offer_resolved_at", "offer_response_date"],
    "accepted_on": ["accepted_on", "hired_at", "hired_date", "hire_date", "offer_accepted_at", "offer_accepted_date"],
    "role_family": ["role_family", "department", "job_family", "team"],
    "opening_id": ["opening_id", "opening", "requisition_id", "req_id", "job_id"],
}
VENDOR_TRAPS = {  # references/data-hygiene-checklist.md has the sources
    "greenhouse": ["'Days to hire' in the time-to-fill report counts from the opening's open date, not the application [83]",
                   "prospects are not applicants: keep them out of applicant counts [86]",
                   "a merge drops the secondary profile's source and referral credit [91]",
                   "Harvest v1/v2 were removed 2026-08-31: old integrations fail; use a UI export or v3 [88]",
                   "evergreen roles need their own opening IDs [85]"],
    "ashby": ["the passthrough report is a closed cohort by default and treats skipped stages as passed; PDF export only [94]"],
    "lever": ["contacts and opportunities are counted separately; archive reasons are stored as IDs [93]"],
    "workday": ["automatic merging is narrow, so name-variant duplicates survive [92]"],
    "linkedin": ["an InMail 'response' includes 'Not interested' [96]",
                 "CSV exports exclude member contact data, cap at 5,000 per month per seat; Recruiter Lite cannot export CSV [97]"],
}
VENDOR_HINTS = [  # header signatures for --vendor auto; a guess, printed as one
    ("greenhouse", {"rejection_reason_type", "opening_id"}),
    ("lever", {"opportunity_id"}),
    ("lever", {"opportunity"}),
    ("ashby", {"application_id", "current_interview_stage"}),
    ("workday", {"job_requisition_id"}),
    ("linkedin", {"inmail_status"}),
    ("linkedin", {"project_name", "pipeline_stage"}),
]


def detect_vendor(header):
    names = {io.norm_header(h) for h in header}
    for vendor, needed in VENDOR_HINTS:
        if needed <= names:
            return vendor
    return None


FIRST_NAMES = ["first_name", "firstname", "given_name"]
LAST_NAMES = ["last_name", "lastname", "family_name", "surname"]


def read_rows(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        print("STOP: PDF exports (e.g. Ashby passthrough) are closed-cohort summaries, not rows. Ask for the "
              "candidate/application CSV, or quote the PDF's own figures labelled with its cohort definition.", file=sys.stderr)
        sys.exit(5)
    if ext == ".xlsx":
        try:
            import openpyxl  # type: ignore
        except ImportError:
            print("error: .xlsx needs openpyxl: run `pip install --user openpyxl`, or save the sheet as CSV.", file=sys.stderr)
            sys.exit(2)
        ws = openpyxl.load_workbook(path, read_only=True, data_only=True).active
        rows = [["" if v is None else str(v) for v in r] for r in ws.iter_rows(values_only=True)]
        return rows[0], rows[1:]
    if ext not in (".csv", ".tsv", ".txt"):
        print(f"error: unsupported format {ext}; send CSV, TSV or XLSX.", file=sys.stderr)
        sys.exit(5)
    text = io.read_text(path)
    delim = io.sniff_delimiter(text[:4096], ext)
    if delim == ";":
        print("note: the export looks semicolon-delimited (Excel in a pt/de locale); read with ';'.", file=sys.stderr)
    rows = io.csv_rows(text, delim)
    if not rows:
        print("error: the export is empty.", file=sys.stderr)
        sys.exit(2)
    return rows[0], rows[1:]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("export")
    ap.add_argument("--out", required=True)
    ap.add_argument("--vendor", default="auto")
    ap.add_argument("--map")
    ap.add_argument("--date-order", choices=["dayfirst", "monthfirst"])
    a = ap.parse_args(argv)
    try:
        header, body = read_rows(a.export)
    except OSError as exc:
        print(f"error: cannot read {a.export}: {exc}", file=sys.stderr)
        return 2

    extra = {}
    for r in io.read_csv(a.map):
        if r.get("export_column") and r.get("canonical_column"):
            extra[io.norm_header(r["export_column"])] = r["canonical_column"].strip()
    alias_of = {al: canon for canon, als in ALIASES.items() for al in als}
    alias_of.update(extra)

    dropped, mapping, unmapped, first_i, last_i = [], {}, [], None, None
    for i, h in enumerate(header):
        nh = io.norm_header(h)
        if io.is_protected(h):
            dropped.append(h)
            continue
        if nh in FIRST_NAMES:
            first_i = i
        elif nh in LAST_NAMES:
            last_i = i
        elif nh in alias_of and alias_of[nh] not in mapping.values():
            mapping[i] = alias_of[nh]
        else:
            unmapped.append(h)
    if "name" not in mapping.values() and first_i is None:
        print("error: no candidate name column found. Pass --map with export_column,canonical_column "
              "(e.g. 'Candidate,name').", file=sys.stderr)
        return 6
    if "stage" not in mapping.values():
        print("error: no stage/status column found. Pass --map (e.g. 'Current Stage,stage').", file=sys.stderr)
        return 6

    os.makedirs(a.out, exist_ok=True)
    hygiene, out_rows = [], []
    openings = defaultdict(int)
    for n, raw in enumerate(body, start=2):
        if not any((c or "").strip() for c in raw):
            continue
        row = {k: "" for k in CANONICAL}
        for i, canon in mapping.items():
            row[canon] = raw[i].strip() if i < len(raw) else ""
        if first_i is not None and not row["name"]:
            parts = [raw[j].strip() for j in (first_i, last_i) if j is not None and j < len(raw)]
            row["name"] = " ".join(p for p in parts if p)
        for key in ("applied_on", "stage_entered_on", "offer_out_on", "answer_by", "offer_resolved_on", "accepted_on", "last_contact"):
            if row[key]:
                d = io.parse_date(row[key], a.date_order)
                if d:
                    row[key] = d.isoformat()
                else:
                    hygiene.append(("unparseable_date", n, f"{key}='{row[key]}'"))
        if not row["stage"]:
            hygiene.append(("missing_stage", n, row["name"]))
        if not row["owner"]:
            hygiene.append(("missing_owner", n, row["name"]))
        if row["stage"].strip().lower() in io.DEFAULT_STAGES["prospect"]:
            row["is_prospect"] = "yes"
        ap_d, acc_d = io.parse_date(row["applied_on"]), io.parse_date(row["accepted_on"])
        if ap_d and acc_d:
            if acc_d == ap_d:
                hygiene.append(("zero_day_hire", n, f"{row['name']}: applied and hired the same day (data-entry artefact)"))
            elif acc_d < ap_d:
                hygiene.append(("hire_before_application", n, row["name"]))
        if row["offer_out_on"] and not (row["offer_resolved_on"] or row["accepted_on"]) and \
                io.classify_stage(row["stage"]) not in ("offer",):
            hygiene.append(("offer_not_resolved", n, f"{row['name']}: offer out {row['offer_out_on']}, stage '{row['stage']}'"))
        if acc_d and row["opening_id"]:
            openings[row["opening_id"]] += 1
        out_rows.append(row)
    for opening, k in openings.items():
        if k > 1:
            hygiene.append(("evergreen_or_reused_opening", 0, f"opening {opening}: {k} hires (time-to-fill per hire is unreliable)"))
    seen = Counter((r["name"].lower(), r["role"].lower()) for r in out_rows)
    for (name, role), k in seen.items():
        if k > 1:
            hygiene.append(("duplicate", 0, f"{name} / {role} x{k} (merges can drop source credit - check before counting)"))

    with open(os.path.join(a.out, "candidates.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=CANONICAL)
        w.writeheader()
        w.writerows(out_rows)
    with open(os.path.join(a.out, "hygiene.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["category", "line", "detail"])
        w.writerows(hygiene)

    print(f"wrote {len(out_rows)} rows to {os.path.join(a.out, 'candidates.csv')}")
    print("Protected columns dropped (tell the owner in one line): " + (", ".join(dropped) if dropped else "none"))
    print("Mapped: " + ", ".join(f"{header[i]} -> {c}" for i, c in mapping.items()))
    if unmapped:
        print("Kept out, unmapped (fix with --map if needed): " + ", ".join(unmapped))
    counts = Counter(h[0] for h in hygiene)
    print("Hygiene: " + (", ".join(f"{k} {v}" for k, v in counts.items()) if counts else "clean"))
    vendor = a.vendor
    if vendor == "auto":
        vendor = detect_vendor(header)
        print(f"vendor: {vendor} (detected from the headers - confirm with the owner)" if vendor
              else "vendor: not detected from the headers, so no vendor traps are listed. Rerun with "
                   "--vendor greenhouse|lever|ashby|workday|linkedin once the owner confirms the source.")
    for trap in VENDOR_TRAPS.get(vendor, []):
        print(f"{vendor} trap to state in the report: {trap}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
