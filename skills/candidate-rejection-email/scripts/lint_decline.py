#!/usr/bin/env python3
r"""Check a rejection draft against the skill's content rules before it goes to the owner.

Usage:
  cd ~/skills/candidate-rejection-email && \
  python3 scripts/lint_decline.py <draft.txt|draft.md|drafts.csv> \
      [--retention-ok] [--comparative-approved] [--allow "<company>"] \
      [--allow "<role title>"] [--json]
  python3 scripts/lint_decline.py --selftest

--selftest lints known-bad drafts for every ERROR rule (including plural FCRA
terms such as "background checks" and "convictions", and capitalised
AI_REASON words at a sentence start such as "Automated ..." and "Scores ...")
plus one clean draft,
and exits 1 if a rule fails to fire or the clean draft is flagged.
Word stems in RULES must allow their plural or inflected forms (checks?,
convictions?, religio\w*): a bare stem before the closing \b misses them.

Input: one draft (plain text or markdown; an optional first line
"Subject: ..."), or drafts.csv from merge_declines.py (columns
candidate_id,subject,body). The approval footer (from the line "---" on) is
ignored.

ERROR (exit 1):
  DECISION_LATE    no decision phrase in the first two sentences of the body
  FCRA             mentions a background check, criminal record, credit or
                   consumer report, pre-employment screening, vetting, or a
                   report from a screening vendor: stop and route (references/fcra-adverse-action-routing.md)
  AI_REASON        mentions AI, an algorithm, automated screening, scores or
                   rankings as part of the reason [101]
  COMPARATIVE      compares with other candidates, unless --comparative-approved
  RETENTION        "keep on file" or talent-pool language, unless --retention-ok
                   (the owner's recorded retention policy allows it) [100]
  FUTURE_CONTACT   promises future contact
  PROTECTED        protected trait or proxy language (age, family, origin,
                   health, religion, "fit")
  LEGAL            a legal conclusion ("lawful", "discriminat", "in compliance")
  PLACEHOLDER      an unfilled {{placeholder}} or [OWNER TO CONFIRM]
--allow "<text>" (repeatable) names an owner-supplied company name, role
title, candidate name or sender ("Brightside Family Dental", "Medical Billing
Specialist", "Acme Health"). Inside those exact strings, and only there, the
PROTECTED and LEGAL rules give a NAME warning instead of an error, so a real
employer or job title does not block the draft. Every other rule, and every
other word of the draft, is linted as before. merge_declines.py passes each
row's chosen_name, role, company, sender and sender_title this way.

WARNING (exit 0 unless errors):
  NAME             a PROTECTED/LEGAL word inside an --allow string; confirm it
                   is the real company or role name, not a reason
  SUBJECT          no subject, or a subject that states the outcome
  LONG             body over 180 words (default, confirm with the owner;
                   a short decline reads as respectful, a long one invites debate)

This is a floor, not a guarantee: phrasing can slip past a lexicon, and the
human sender still reviews every draft.
Exit 0 = clean, 1 = errors, 2 = bad input.
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

DECISION = re.compile(
    r"(not (to )?(move|moving|go|going|proceed|proceeding|progress|progressing) forward|"
    r"decided not to|will not be (progressing|moving|proceeding|offering)|won't be (moving|progressing|offering)|"
    r"not (been )?successful|unsuccessful|not be offering|not proceed|not progress|"
    r"not able to offer|unable to offer|decided to (close|end))", re.I)
RULES = [
    ("FCRA", re.compile(r"\b(background (checks?|checking|screens?|screening|reports?|investigations?)|criminal (records?|history|histories|background)|credit (checks?|checking|reports?|history|histories)|consumer reports?|convictions?|convicted|driving records?|MVRs?|pre-?employment (screening|screens?|checks?|checking|vetting)|vetting|(reports?|results?) (from|of) (our|the|your) (screening |background )?(vendors?|providers?|agenc(y|ies)|screening|checks?))\b", re.I)),
    # re.I so capitalised sentence starts ("Automated ...", "Scores ...") match;
    # only the bare "AI" token stays case-sensitive so the word "ai" in other
    # text does not fire.
    ("AI_REASON", re.compile(r"((?-i:\bAI\b)|\bA\.I\.|\balgorithm\w*|\bautomat(ed|ic|ically|ion)\b|\bscreening (tool|software)|\bscor(e|ed|es|ing)\b|\brank(s|ed|ing|ings)?\b|\bmachine learning\b|\bChatGPT\b)", re.I)),
    ("COMPARATIVE", re.compile(r"\b(stronger|more qualified|better qualified|more experienced|more (relevant |direct )?experience|other candidates?|another candidate|candidates? (who|whose|with|that)|(went|go|going|gone|moved|moving|proceed(ed|ing)?) (forward )?with (another|other|a different|candidates?|someone)|more closely match\w*|closer match\w*|better (fit|match)|closer (fit|match)|highly competitive|many (strong|qualified) (applicants|candidates))\b", re.I)),
    ("RETENTION", re.compile(r"\b(on file|talent (pool|community)|(keep|hold|store) your (details|cv|resume|application|information)|retain your|hold on to your)\b", re.I)),
    ("FUTURE_CONTACT", re.compile(r"\b(keep you in mind|be in touch|reach out (to you )?(about|for|when|if|in the future|again|later)|contact you (about|when|if|for)|future (roles|opportunities|openings|positions) (that|which|may|might)|let you know (about|when|if) (other|future|new))\b", re.I)),
    ("PROTECTED", re.compile(r"\b(age|young|younger|older|overqualified|energetic|family|children|pregnan\w*|maternity|health|medical|disab\w*|accent|native speaker|nationality|religio\w*|culture fit|good fit|right fit|not a fit|gel)\b", re.I)),
    ("LEGAL", re.compile(r"\b(lawful|unlawful|legal(ly)?|discriminat\w*|in compliance|equal opportunity)\b", re.I)),
    ("PLACEHOLDER", re.compile(r"(\{\{[^}]*\}\}|\[OWNER TO CONFIRM[^\]]*\]|<[a-z _-]+>)", re.I)),
]
FLAGS = {"COMPARATIVE": "comparative_approved", "RETENTION": "retention_ok"}
# Rules an owner-supplied name or title may trip without blocking (--allow).
NAME_RULES = {"PROTECTED", "LEGAL"}
NAME_TOKEN = "Qqname"  # neutral stand-in: trips no rule


def name_rx(name: str) -> str:
    return r"(?<!\w)" + re.escape(name) + r"(?!\w)"


def mask_names(text: str, allow: list[str]) -> str:
    for name in sorted({a.strip() for a in allow if a and a.strip()}, key=len, reverse=True):
        text = re.sub(name_rx(name), NAME_TOKEN, text, flags=re.I)
    return text
MAX_WORDS = 180  # default, confirm with the owner


def split_draft(text: str) -> tuple[str, str]:
    text = text.split("\n---", 1)[0]
    lines = text.strip().splitlines()
    subject = ""
    if lines and lines[0].lower().startswith("subject:"):
        subject = lines[0].split(":", 1)[1].strip()
        lines = lines[1:]
    return subject, "\n".join(lines).strip()


def sentences(body: str) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    if paras and re.match(r"^(hi|hello|dear)\b", paras[0], re.I) and len(paras[0]) < 60:
        paras = paras[1:]
    flat = " ".join(paras)
    return [s for s in re.split(r"(?<=[.!?])\s+", flat) if s]


def lint(subject: str, body: str, opts: dict) -> list[dict]:
    out = []
    first_two = " ".join(sentences(body)[:2])
    if not DECISION.search(first_two):
        out.append({"level": "ERROR", "rule": "DECISION_LATE", "text": first_two[:160],
                    "fix": "State the decision in the first two sentences."})
    allow = [a.strip() for a in (opts.get("allow") or []) if a and a.strip()]
    raw = subject + "\n" + body
    masked = mask_names(raw, allow) if allow else raw
    for rule, rx in RULES:
        if FLAGS.get(rule) and opts.get(FLAGS[rule]):
            continue
        for m in rx.finditer(masked if rule in NAME_RULES else raw):
            out.append({"level": "ERROR", "rule": rule, "text": m.group(0),
                        "fix": "See SKILL.md guardrails and references/decline-content-rules.md."})
    for name in dict.fromkeys(allow):
        if not re.search(name_rx(name), raw, re.I):
            continue
        for rule, rx in RULES:
            if rule in NAME_RULES:
                for m in rx.finditer(name):
                    out.append({"level": "WARNING", "rule": "NAME", "text": f"{m.group(0)} (in '{name}')",
                                "fix": "Owner-supplied company/role/name; confirm it is the real name, not a reason."})
    if not subject:
        out.append({"level": "WARNING", "rule": "SUBJECT", "text": "", "fix": "Add a plain subject: 'Your application for <role>'."})
    elif DECISION.search(subject) or re.search(r"\b(reject|declin|unsuccessful|regret)", subject, re.I):
        out.append({"level": "WARNING", "rule": "SUBJECT", "text": subject, "fix": "Keep the subject plain; the decision goes in the body."})
    words = len(body.split())
    if words > MAX_WORDS:
        out.append({"level": "WARNING", "rule": "LONG", "text": f"{words} words",
                    "fix": f"Over {MAX_WORDS} words (default); shorten."})
    return out


_OPEN = "Hi Sam,\n\nThank you for your time. The team has decided not to move forward with your application. "
SELFTEST_POSITIVE = [
    ("DECISION_LATE", "Hi Sam,\n\nThank you for your time. It was good to meet you. We have now reviewed everything and decided not to move forward."),
    ("FCRA", _OPEN + "This follows the results of our background checks."),
    ("FCRA", _OPEN + "This is because of your prior convictions and the credit reports."),
    ("FCRA", _OPEN + "This follows your background check."),
    ("FCRA", _OPEN + "Your criminal records were a factor."),
    ("FCRA", _OPEN + "The consumer reports we received were a factor."),
    ("AI_REASON", _OPEN + "Our automated screening ranked other applications higher."),
    ("AI_REASON", _OPEN + "Automated screening placed your application lower."),
    ("AI_REASON", _OPEN + "Scores from the panel were below the bar."),
    ("AI_REASON", _OPEN + "Our Algorithm flagged gaps."),
    ("AI_REASON", _OPEN + "Ranked against the bar, your application fell short."),
    ("AI_REASON", _OPEN + "Our AI tool reviewed your answers."),
    ("FCRA", _OPEN + "The results of your pre-employment screening were a factor."),
    ("FCRA", _OPEN + "Your references and the report from our vendor were a factor."),
    ("FCRA", _OPEN + "Vetting raised a concern."),
    ("COMPARATIVE", _OPEN + "Someone whose experience more closely matched was chosen."),
    ("RETENTION", _OPEN + "We'll hold your application for 12 months."),
    ("FUTURE_CONTACT", _OPEN + "We may reach out in the future."),
    ("COMPARATIVE", _OPEN + "We went with another candidate."),
    ("RETENTION", _OPEN + "We will keep your details on file."),
    ("FUTURE_CONTACT", _OPEN + "We will keep you in mind."),
    ("PROTECTED", _OPEN + "We were looking for someone younger."),
    ("LEGAL", _OPEN + "Our process is fully lawful."),
    ("PLACEHOLDER", _OPEN + "{{feedback_paragraph}}"),
]
# Owner-supplied names passed with --allow: no error inside the name, but the
# same word elsewhere in the draft is still an error.
SELFTEST_ALLOW = [
    ("Subject: Your application for Medical Billing Specialist\n\nHi Zoe,\n\nThank you for applying for the "
     "Medical Billing Specialist role at Brightside Family Dental. We have decided not to move forward with "
     "your application. Thank you for your interest in Acme Health.\n\nMaya Chen",
     ["Medical Billing Specialist", "Brightside Family Dental", "Acme Health"], set()),
    (_OPEN + "Brightside Family Dental needs someone without family commitments.",
     ["Brightside Family Dental"], {"PROTECTED"}),
    (_OPEN + "We followed a lawful process at Acme Legal.", ["Acme Legal"], {"LEGAL"}),
    (_OPEN + "Acme Health used a background check.", ["Acme Health"], {"FCRA"}),
]
SELFTEST_CLEAN = _OPEN + "Thank you again, and best wishes.\n\nMaya Chen"


def selftest() -> int:
    bad = 0
    for rule, body in SELFTEST_POSITIVE:
        got = {f["rule"] for f in lint("Your application", body, {})}
        if rule not in got:
            print(f"FAIL {rule} did not fire on: {body!r}")
            bad += 1
    for text, allow, want in SELFTEST_ALLOW:
        s_, b_ = split_draft(text)
        got = {f["rule"] for f in lint(s_ or "Your application", b_, {"allow": allow}) if f["level"] == "ERROR"}
        if got != want:
            print(f"FAIL --allow {allow}: errors {sorted(got)}, want {sorted(want)}")
            bad += 1
    errs = [f for f in lint("Your application", SELFTEST_CLEAN, {}) if f["level"] == "ERROR"]
    if errs:
        print(f"FAIL clean draft flagged: {[f['rule'] for f in errs]}")
        bad += 1
    covered = {r for r, _ in SELFTEST_POSITIVE}
    missing = [r for r, _ in RULES if r not in covered]
    if missing:
        print(f"FAIL no selftest draft for: {', '.join(missing)}")
        bad += 1
    print("selftest OK" if not bad else f"selftest: {bad} failure(s)")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("draft", nargs="?")
    ap.add_argument("--retention-ok", action="store_true")
    ap.add_argument("--comparative-approved", action="store_true")
    ap.add_argument("--allow", action="append", default=[],
                    help="owner-supplied company, role or name (repeatable); see the docstring")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.draft:
        ap.error("draft is required unless --selftest is given")
    p = Path(a.draft).expanduser()
    if not p.is_file():
        print(f"error: not found: {p}", file=sys.stderr)
        return 2
    opts = {"retention_ok": a.retention_ok, "comparative_approved": a.comparative_approved,
            "allow": a.allow}
    items = []
    if p.suffix.lower() == ".csv":
        for row in csv.DictReader(p.read_text(encoding="utf-8-sig").splitlines()):
            items.append((row.get("candidate_id", "?"), row.get("subject", ""), row.get("body", "")))
    else:
        s, b = split_draft(p.read_text(encoding="utf-8-sig"))
        items.append((p.name, s, b))
    report, errors = {}, 0
    for ident, subject, body in items:
        found = lint(subject, body, opts)
        report[ident] = found
        errors += sum(1 for f in found if f["level"] == "ERROR")
    if a.json:
        print(json.dumps(report, indent=2))
    else:
        for ident, found in report.items():
            print(f"{ident}: " + ("clean" if not found else f"{len(found)} finding(s)"))
            for f in found:
                print(f"  {f['level']:7} {f['rule']}: '{f['text']}' -> {f['fix']}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
