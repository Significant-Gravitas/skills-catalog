#!/usr/bin/env python3
"""Flag scorecard remarks that are not job evidence.

    cd ~/skills/hiring-debrief-and-decision && python3 scripts/flag_remarks.py \
        <scorecards dir | collate JSON | notes .md/.txt> [--lexicon templates/remark-flags.csv] [--json]

Reads the evidence and reason text of every scorecard (or any notes file:
chat or mail excerpts, meeting notes saved as text) and matches it against the
lexicon in templates/remark-flags.csv (pattern, category, action, question):

    exclude             categories that are never about the job: affect,
                        age, family, health, origin/religion, appearance. Cut the
                        remark and note the removal in one line without repeating it.
    ask-for-behaviour   fit, pedigree / resume grading, comparing candidates, and
                        labels with no behaviour ("strong instincts", "seemed junior").
                        Put the facilitator's challenge to the interviewer.

Job-related technical phrases are removed before matching, so they are never
proposed for a cut: "health check(s)", "health endpoint/probe", "service/system
health", "race condition", "retired the <legacy thing>", "energy trading/sector/
market...", "medical-claims/records/billing...", "blind spot/review/test",
"foreign key", "looks right/correct/good...", "ill-defined/-formed", "code/next/
test... generation", "mature codebase/CI/process...", "presence check",
"retired two cron jobs/services...", "foreign-currency/exchange/FX", "looks up
the key/row/rate...", "health insurance claims". Every match is reported, not
only the first per rule, so a sentence with a technical word and a real remark
shows both.

A lexicon over-flags ("strong answer on rollback" is fine) and misses
paraphrases. Every hit is a proposal for a human; nothing is deleted here.
collate_scorecards.py imports cut_spans() from here, so the saved brief never
repeats a remark this lexicon would cut.

Exit 0 with no hits, 1 with hits, 2 on bad input. --selftest checks itself.
"""

import argparse
import csv
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LEXICON = os.path.join(HERE, "..", "templates", "remark-flags.csv")


EXEMPT = re.compile(
    r"\b(health[- ]?checks?|health (endpoints?|probes?|status|metrics?|dashboards?|monitor\w*)|"
    r"(service|system|cluster|node|pod|database|db|ledger|queue) health|race conditions?|"
    r"retir(e|ed|es|ing) (the|a|an|our|their|its|old|legacy|two|three|four|five|six|several|\d+)\b"
    r"( \w+)?( cron| batch)? (jobs?|services?|endpoints?|tables?|queues?|servers?|apis?|flags?|"
    r"scripts?|systems?|workers?|hosts?|clusters?|versions?|features?)\b|"
    r"retir(e|ed|es|ing) (the|a|an|our|their|its|old|legacy)\b[\w -]{0,30}|"
    r"foreign[- ](currenc(y|ies)|exchange|fx|keys?|tax|payments?|transactions?)|"
    r"look(s|ed|ing)? up (the|a|an|each|every|its|their)? ?(key|keys|row|rows|record|records|value|values|id|ids|"
    r"account|accounts|invoice|invoices|rate|rates|price|prices)\b|"
    r"health[- ]insurance[- ]claims?|"
    r"energy (trading|sector|market|markets|company|companies|desk|grid|provider|industry|billing|data)|"
    r"(medical|health)[- ](claims?|records?|billing|data|devices?|imaging|software|platform|systems?)|"
    r"blind (spots?|reviews?|tests?|writes?|signatures?|index)|"
    r"foreign[- ]keys?|looks? (right|correct|good|fine|wrong|reasonable|solid|safe|sound|like)|"
    r"ill-(defined|formed|posed|suited)|"
    r"(code|test|data|report|lead|key|next|new|first|previous|second) generation|"
    r"mature (codebase|process|practice|tooling|testing|ci|pipeline|product)s?|"
    r"presence (checks?|detection))\b", re.I)


def scrub(text):
    """Blank out job-related technical phrases the lexicon would misread."""
    return EXEMPT.sub(lambda m: " " * len(m.group(0)), text or "")


def cut_spans(text, rules):
    """Matches of 'exclude' rules (remarks never about the job) in text."""
    clean = scrub(text)
    return [(m.start(), m.end(), cat) for rx, cat, action, _ in rules if action == "exclude"
            for m in rx.finditer(clean)]


def load_lexicon(path):
    rules = []
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rules.append((re.compile(r["pattern"], re.I), r["category"], r["action"], r["question"]))
    return rules


def texts_from(src):
    """Yield (who, where, text)."""
    if os.path.isdir(src):
        for p in sorted(glob.glob(os.path.join(src, "*.md"))):
            with open(p, encoding="utf-8") as fh:
                body = fh.read()
            who = re.search(r"^interviewer:\s*(.+)$", body, re.M)
            who = who.group(1).strip() if who else os.path.basename(p)
            for line in body.splitlines():
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if len(cells) >= 4 and re.match(r"^M\d+$", cells[0]):
                    yield who, f"{cells[0]} rating {cells[2]}", "|".join(cells[3:])
            m = re.search(r"^reason:\s*(.+)$", body, re.M | re.I)
            if m:
                yield who, "overall reason", m.group(1)
    elif src.endswith(".json"):
        with open(src, encoding="utf-8") as fh:
            res = json.load(fh)
        for b in res.get("blocks", []):
            for r in b.get("ratings", []):
                yield r["interviewer"], f"{b['id']} rating {r['rating']}", r.get("evidence", "")
        for o in res.get("overall", []):
            yield o["interviewer"], "overall reason", o.get("reason", "")
    else:
        with open(src, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                if line.strip():
                    yield "notes", f"line {n}", line.strip()


def scan(src, rules):
    hits = []
    for who, where, text in texts_from(src):
        clean = scrub(text)
        for rx, cat, action, question in rules:
            for m in rx.finditer(clean):
                rating = re.search(r"rating (\d)", where)
                q = question.replace("<rating>", rating.group(1)) if rating else                     question.replace("puts this at a <rating>", "is behind this")
                hits.append({"who": who, "where": where, "category": cat, "action": action,
                             "match": m.group(0), "text": text[:160], "say": q})
    return hits


def selftest():
    import tempfile
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "lena.md"), "w", encoding="utf-8") as fh:
        fh.write("interviewer: Lena Ortiz\n| M2 | Live data | 4 | \"Strong architecture instincts\" |\n"
                 "| M4 | Explains | 3 | \"Seemed nervous but good culture fit\" |\nreason: better than the other candidate\n")
    hits = scan(d, load_lexicon(DEFAULT_LEXICON))
    cats = {h["category"] for h in hits}
    for want in ("label-no-behaviour", "affect", "fit", "comparison"):
        assert want in cats, (want, hits)
    assert any("puts this at a 4" in h["say"] for h in hits)
    notes = os.path.join(d, "notes.txt")
    with open(notes, "w", encoding="utf-8") as fh:
        fh.write("Dev: Built the pricing engine for an energy trading desk; showed the latency numbers.\n"
                 "Ana: Explained how she retired the legacy queue and migrated consumers.\n"
                 "Sam: Walked through health checks and readiness probes she wrote for 40 services.\n"
                 "Lena: Walked through the race condition in the payout job.\n"
                 "Lena: Honestly she looked tired, but a great fit.\n")
    hits = scan(notes, load_lexicon(DEFAULT_LEXICON))
    lines = {(h["where"], h["category"]) for h in hits}
    assert not any(w in ("line 1", "line 2", "line 3", "line 4") and c in ("affect", "age", "health")
                   for w, c in lines), lines
    assert ("line 5", "appearance") in lines and ("line 5", "fit") in lines, lines
    rules = load_lexicon(DEFAULT_LEXICON)
    for ok in ("Added a foreign key from payouts to invoices and backfilled it.",
               "Her backfill plan looks correct: batches of 10k, checksum per batch.",
               "Turned ill-defined billing requirements into a tested spec.",
               "Wrote the code generation step for the next generation API.",
               "Moved us onto a mature CI pipeline; added a presence check on the lock."):
        assert not cut_spans(ok, rules), (ok, cut_spans(ok, rules))
    assert cut_spans("She looks tired and seemed nervous.", rules)
    # billing-domain evidence is not cut
    for ok in ("Fixed the foreign-currency rounding on refunds.",
               "Retired two cron jobs by moving them onto the queue.",
               "Looks up the key before writing, so retries are safe.",
               "Built the health insurance claims export."):
        assert not cut_spans(ok, rules), (ok, cut_spans(ok, rules))
    # every flagged word is reported, not only the first per rule
    with open(notes, "w", encoding="utf-8") as fh:
        fh.write("Fixed the foreign rounding, though her accent was hard to follow.\n"
                 "Retired the cron, and she looked exhausted and scruffy on camera.\n")
    hits = scan(notes, rules)
    got = {(h["where"], h["match"].lower()) for h in hits}
    assert ("line 1", "foreign") in got and ("line 1", "accent") in got, got
    assert any(w == "line 2" and "exhausted" in m for w, m in got), got
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", nargs="?")
    ap.add_argument("--lexicon", default=DEFAULT_LEXICON)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.source:
        ap.error("give a scorecards folder, a collate JSON or a notes file")
    try:
        hits = scan(os.path.expanduser(a.source), load_lexicon(a.lexicon))
    except (OSError, ValueError, KeyError, re.error) as exc:
        print(f"bad input: {exc}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(hits, indent=1))
    else:
        if not hits:
            print("no flagged remarks (a lexicon check; still read every line)")
        for h in hits:
            verb = "CUT" if h["action"] == "exclude" else "ASK"
            print(f"{verb}\t{h['who']} · {h['where']} · {h['category']} ('{h['match']}')\n\t{h['text']}\n\t-> {h['say']}")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
