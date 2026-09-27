#!/usr/bin/env python3
"""Mail-merge unsent rejection drafts from a batch sheet, blocking any row without a confirmed decision.

Usage:
  cd ~/skills/candidate-rejection-email && \
  python3 scripts/merge_declines.py <decline-batch.csv> --out <dir> [--templates templates/decline-by-stage.md]

Input: templates/decline-batch.csv columns
  candidate_id, chosen_name, email, role, company, stage (application|screen|loop),
  decision_maker, decision_date (YYYY-MM-DD), consumer_report_involved (no|yes|unknown),
  feedback_approved_verbatim, comparative_approved (yes only if the
  decision-maker approved a comparison with other candidates in writing),
  thanks_detail (starts after "Thank you for your time", e.g. "on our call
  on 2 October"), expenses_line, retention_line, sender, sender_title

A row is BLOCKED (no draft written) when:
  * decision_maker or decision_date is empty, or the date is not YYYY-MM-DD
    -> "needs human confirmation";
  * consumer_report_involved is not exactly "no" -> FCRA stop (yes) or ask (unknown/blank);
    see references/fcra-adverse-action-routing.md;
  * chosen_name, role, company, stage or sender is empty, or stage is unknown;
  * the candidate_id or email appears on more than one row (every copy is
    blocked: "duplicate row: confirm which one is the decision"), so one
    candidate never gets two drafts;
  * the lint (lint_decline.py) finds an error in the merged draft.

The owner-supplied identity fields (chosen_name, role, company, sender,
sender_title) are passed to the lint as --allow names: a PROTECTED or LEGAL
word inside them ("Medical Billing Specialist", "Brightside Family Dental",
"Acme Health") is a NAME warning on the draft, not a block. The free-text
fields (feedback, thanks_detail, expenses_line, retention_line) and the rest
of the template are linted in full.

Feedback, expenses and retention text are inserted verbatim, only from their
columns, and never generated. retention_line is used only if it is filled
(it must be the owner's recorded policy wording) and switches the RETENTION
lint rule off for that row only.

Outputs in --out:
  drafts.md   blocked rows first, then each draft with its approval footer
  drafts.csv  candidate_id,email,subject,body,status (status is always DRAFT)
Nothing is sent. Exit 0 = all rows drafted, 1 = some rows blocked, 2 = bad input.
"""

import argparse
import csv
import re
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from lint_decline import lint, split_draft  # noqa: E402

REQUIRED = ["chosen_name", "role", "company", "stage", "sender"]


def load_templates(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    found = dict(re.findall(r"<!-- template:(\w+) -->\n(.*?)\n<!-- /template -->", text, re.S))
    if not found:
        print(f"error: no <!-- template:... --> blocks in {path}", file=sys.stderr)
        sys.exit(2)
    return found


def spaced(text: str) -> str:
    text = (text or "").strip()
    return f" {text}" if text and text[0] not in ",.;:" else text


def para(text: str) -> str:
    text = (text or "").strip()
    return f"{text}\n\n" if text else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("batch")
    ap.add_argument("--out", required=True)
    ap.add_argument("--templates", default=str(HERE.parent / "templates" / "decline-by-stage.md"))
    a = ap.parse_args()
    src = Path(a.batch).expanduser()
    if not src.is_file():
        print(f"error: not found: {src}", file=sys.stderr)
        return 2
    templates = load_templates(Path(a.templates))
    rows = [{k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
            for r in csv.DictReader(src.read_text(encoding="utf-8-sig").splitlines())]
    if not rows:
        print("error: the batch has no rows", file=sys.stderr)
        return 2

    seen_ids: dict[str, int] = {}
    seen_mail: dict[str, int] = {}
    for r in rows:
        if r.get("candidate_id"):
            seen_ids[r["candidate_id"]] = seen_ids.get(r["candidate_id"], 0) + 1
        if r.get("email"):
            seen_mail[r["email"].lower()] = seen_mail.get(r["email"].lower(), 0) + 1

    blocked, drafts = [], []
    for r in rows:
        cid = r.get("candidate_id") or "(no id)"
        why = []
        if seen_ids.get(r.get("candidate_id", ""), 0) > 1 or seen_mail.get(r.get("email", "").lower(), 0) > 1:
            why.append("duplicate row (same candidate_id or email appears more than once): "
                       "confirm which one is the decision and delete the other")
        if not r.get("decision_maker") or not r.get("decision_date"):
            why.append("needs human confirmation: decision_maker and decision_date are required")
        else:
            try:
                date.fromisoformat(r["decision_date"])
            except ValueError:
                why.append(f"decision_date '{r['decision_date']}' is not YYYY-MM-DD")
        report = r.get("consumer_report_involved", "").lower()
        if report == "yes":
            why.append("FCRA stop: a consumer report is involved; draft nothing and route to the owner's pre-adverse action process")
        elif report != "no":
            why.append("ask the owner: did a background or consumer report play any part? (consumer_report_involved must be yes or no)")
        missing = [k for k in REQUIRED if not r.get(k)]
        if missing:
            why.append(f"missing {', '.join(missing)}")
        stage = r.get("stage", "").lower()
        if stage and stage not in templates:
            why.append(f"unknown stage '{stage}' (use {', '.join(sorted(templates))})")
        if why:
            blocked.append((cid, why))
            continue

        fields = {
            "chosen_name": r["chosen_name"], "role": r["role"], "company": r["company"],
            "thanks_detail": spaced(r.get("thanks_detail", "")),
            "feedback_paragraph": para(r.get("feedback_approved_verbatim")),
            "expenses_paragraph": para(r.get("expenses_line")),
            "retention_paragraph": para(r.get("retention_line")),
            "sender": r["sender"], "sender_title": r.get("sender_title", ""),
        }
        text = templates[stage]
        for k, v in fields.items():
            text = text.replace("{{" + k + "}}", v)
        text = re.sub(r"\n{3,}", "\n\n", text).rstrip() + "\n"
        subject, body = split_draft(text)
        allow = [r.get(k, "") for k in ("chosen_name", "role", "company", "sender", "sender_title")]
        findings = lint(subject, body, {"retention_ok": bool(r.get("retention_line")),
                                        "comparative_approved": r.get("comparative_approved", "").lower() == "yes",
                                        "allow": allow})
        errors = [f for f in findings if f["level"] == "ERROR"]
        if errors:
            blocked.append((cid, [f"lint {f['rule']}: '{f['text']}'" for f in errors]))
            continue
        footer = (f"---\nDecision confirmed by: {r['decision_maker']}, {r['decision_date']}. "
                  f"Feedback approved verbatim: {'yes' if r.get('feedback_approved_verbatim') else 'none included'}. "
                  f"Consumer report involved: no (owner). Sender: {r['sender']}. "
                  f"Status: DRAFT, not sent.")
        drafts.append({"candidate_id": cid, "email": r.get("email", ""), "subject": subject,
                       "body": body, "footer": footer,
                       "warnings": [f"{f['rule']}: {f['text']}" for f in findings if f["level"] == "WARNING"]})

    out = Path(a.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    md = [f"# Decline drafts: {len(drafts)} ready, {len(blocked)} blocked", ""]
    if blocked:
        md += ["## Blocked (no draft written)", ""]
        for cid, why in blocked:
            md.append(f"- **{cid}**: " + "; ".join(why))
        md.append("")
    for d in drafts:
        md += [f"## {d['candidate_id']} <{d['email']}>", "", f"Subject: {d['subject']}", "", d["body"], "", d["footer"]]
        if d["warnings"]:
            md.append("Warnings: " + "; ".join(d["warnings"]))
        md.append("")
    (out / "drafts.md").write_text("\n".join(md), encoding="utf-8")
    with (out / "drafts.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["candidate_id", "email", "subject", "body", "status"])
        w.writeheader()
        for d in drafts:
            w.writerow({"candidate_id": d["candidate_id"], "email": d["email"], "subject": d["subject"],
                        "body": d["body"], "status": "DRAFT"})
    print(f"{len(drafts)} draft(s) written, {len(blocked)} blocked -> {out / 'drafts.md'}")
    for cid, why in blocked:
        print(f"BLOCKED {cid}: " + "; ".join(why))
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
