#!/usr/bin/env python3
"""Lint interview questions (the kit, the owner's own list, or a scorecard).

    cd ~/skills/interview-kit-design && python3 scripts/question_lint.py <file.md|file.txt> [--json]

Which lines are read: in a kit file (templates/kit.md shape), only the
numbered questions under "### Questions". In any other file, numbered or
bulleted list items and any line holding a question mark. Strong-answer and
probe notes, anchor lines and table rows are skipped.

ERROR (must be rewritten before the kit goes anywhere) - the question touches a
protected characteristic or asks something unlawful or high-risk before an
offer. Each hit prints the reason and the job-related rewrite pattern from
references/unlawful-question-rewrites.md:
  age, family, health/disability, genetic, religion, origin/language,
  sex/orientation, affiliations, criminal record, salary history, affect.
  "Fit in" and age-coded team words ("young, energetic team") are ERRORs.
WARN (the skill's drop rules; the model judges in context):
  leading, tool-name recognition, double-barrelled, fortune-teller
  hypothetical, brainteaser, and a physical-ability question without "with or
  without reasonable accommodation".

Technical collocations are removed before the protected-trait rules run, so
they never ERROR: "race condition", "data race", "health check(s)",
"healthcheck", "health endpoint/probe/status", "service/system/cluster health",
"<error|edge|boundary|failure|exit|stop|loop|test> condition", and
"medical/health" used as a domain noun ("medical-claims billing", "health
records system").

Override: a line carrying "<!-- lint-ok: <reason> -->" turns its ERROR into
OVERRIDDEN (printed, exit unaffected), but only when the hit is one ambiguous
word a technical text can use (condition, race, temple, faith, pray, health,
medical, club/association/organisation/society, citizen as in "citizen
developer") and the line is not about the person. A line is about the person
when it opens with a yes/no question to them ("Are you...", "Do you...",
"Does your..."), when you/your/yourself sits within two words of the hit, or
when it holds a person-directed phrase: "your <word>",
"<word> issues/conditions/history...", "any health...", "we should know", how
old, originally from, kids/children/married/spouse/pregnant, graduation or
finish year, accent, native, energy level, passionate, confident. Anything
else stays ERROR with "override not honoured" in the reason. Copy each
OVERRIDDEN line into the kit's "Dropped or rewritten" table for the owner.
Overrides are never honoured for criminal-record, salary-history, genetic or
sex-orientation hits.

This is a lexicon: it over-flags ("travel" is fine; "the family of services"
is fine) and can miss paraphrases. Every hit is a proposal; a clean run is not
a legal review.

Exit 0 when no ERROR, 1 when any ERROR, 2 on bad input. --selftest checks itself.
"""

import argparse
import json
import re
import sys

RULES = [
    ("ERROR", "age", r"\b(how old|your age|age (are|were) you|what year did you (graduate|finish)|"
     r"graduation year|when did you graduate|when did you (first )?start working|year of birth|born in|date of birth|retire(ment)? plans?|"
     r"digital native|young,?\s+(team|and|energetic|dynamic|crowd|culture)|overqualified)\b",
     "Age and age proxies (ADEA help-wanted rules [45]; EEOC [34]). Ask about the experience the work needs: "
     "'Tell me about the last time you <did the work>.'"),
    ("ERROR", "family", r"\b(married|spouse|husband|wife|kids|children|childcare|pregnan\w*|maternity|"
     r"paternity|family plans|start(ing)? a family|have a family|who looks after|single parent)\b",
     "Marital status, children and childcare questions may be treated as evidence of intent (EEOC [74]). "
     "State the job requirement: 'The role travels one week a month; does that work for you?'"),
    ("ERROR", "health", r"\b(health|you('re| are)?\s+(\w+\s+){0,2}(un)?healthy|healthy enough|medical|medication|disabilit\w*|disabled|illness|sick (days|leave)|"
     r"condition|injur\w*|mental health|therapy|workers'? comp|physical (limitations|problems))\b",
     "No disability or health questions before an offer (ADA [35][46]; UK Equality Act s.60 [58]). "
     "Ask: 'Can you <essential function>, with or without reasonable accommodation?'"),
    ("ERROR", "genetic", r"\b(family (medical )?history|genetic|runs in (your|the) family)\b",
     "Genetic information, including family medical history, is off limits (GINA [47]). Remove."),
    ("ERROR", "religion", r"\b(church|mosque|synagogue|temple|religio\w*|pray|sabbath|"
     r"holidays do you (observe|celebrate)|faith)\b",
     "Religion is protected. State the schedule: 'The role covers one weekend a month; does that work?'"),
    ("ERROR", "origin", r"(where are you (originally )?from|where did you grow up|nationality|"
     r"\bcitizen(ship)?\b(?!.{0,40}authori[sz])|native (language|speaker|tongue)|mother tongue|"
     r"first language|language (do )?you speak at home|\baccent\b|ethnic\w*|\brace\b|"
     r"\bwhere were you born)",
     "National origin, language at home and accent are protected or proxies (EEOC [34]). Work authorisation "
     "only if the process needs it, as yes/no: 'Are you authorised to work in <country>?' Test a language "
     "only when the work happens in it."),
    ("ERROR", "sex-orientation", r"\b(gender|sexual|boyfriend|girlfriend|maiden name|"
     r"what does your (husband|wife|partner) do)\b",
     "Sex, gender identity and sexual orientation are protected. Remove."),
    ("ERROR", "affiliations", r"\b(clubs?|societies|organi[sz]ations?|associations?) (do|are) you (belong|a member|in)\b",
     "Club and organisation questions can reveal protected traits (EEOC [34]). Ask only about professional "
     "bodies the job requires: 'Do you hold <required licence>?'"),
    ("ERROR", "criminal-record", r"\b(ever been arrested|arrest record|criminal record|convicted|"
     r"been in (jail|prison))\b",
     "Timing and scope of criminal-history questions vary by jurisdiction; background checks follow the "
     "owner's FCRA process [48]. Remove from the interview; route to the owner or counsel "
     "(practitioner judgement for the interview rule)."),
    ("ERROR", "salary-history", r"(current (salary|pay|compensation)|salary history|previous (salary|pay)|"
     r"how much (do|did) you (make|earn)|what (are|were) you (paid|making))",
     "Never ask about current or past pay (California Labor Code 432.3 [56]; state bans [75]). "
     "Ask: 'What are your pay expectations for this role?' (offer stage only)."),
    ("ERROR", "affect", r"\b(how confident|confidence level|enthusias\w*|passionate|nervous|"
     r"energy level|seem(ed)? honest|body language|eye contact|culture fit|vibe|"
     r"(you|you'd|you'll|would you|will you) (really )?fit in|fit in with|"
     r"fits? (in )?(with )?(the|our) (team|culture))\b",
     "Never rate or probe affect, demeanour or 'fit' (EU AI Act emotion-inference ban [73]; "
     "unreliable affect scoring [106]; 'fit' as a class proxy [79]). Ask for a job behaviour instead."),
    ("WARN", "leading", r"(,? right\?|isn'?t it\?|don'?t you\?|aren'?t you\?|wouldn'?t you agree|"
     r"you'?re (fine|comfortable|ok|okay|happy) with)",
     "Drop rule: signals the wanted answer. Ask open: 'Tell me about a time you <did X>.'"),
    ("WARN", "tool-recognition", r"^\W*(\d+[.)]\s*)?[\"“']?(have you (ever )?used|are you familiar with|"
     r"do you know|have you heard of|do you have experience with)\b",
     "Drop rule: checks recognition of a tool name, not use. Ask: 'Walk me through the last thing you "
     "built with <tool>; which part was yours?'"),
    ("WARN", "double-barrelled", r"\?.+\?|\b(and|or) (how|what|when|where|who)\b.*\?",
     "Drop rule: two questions in one. Split it."),
    ("WARN", "fortune-teller", r"(where do you see yourself|in (five|5|ten|10) years|what would you do if you were)",
     "Voodoo-hiring pattern: hypothetical 'fortune-teller' question [23]. Ask about past behaviour."),
    ("WARN", "brainteaser", r"(golf balls|manhole|piano tuners|how many .{0,40} (fit|are there) in|"
     r"if you were an? (animal|colou?r|tree))",
     "Voodoo-hiring pattern: trick question with no job link [23]. Use a job-related problem."),
]
COMPILED = [(lvl, cat, re.compile(rx, re.I), why) for lvl, cat, rx, why in RULES]
# Job-related technical phrases the protected-trait lexicon would misread.
TECHNICAL = re.compile(
    r"\b(race conditions?|data races?|health[- ]?checks?|health (endpoints?|probes?|status|"
    r"dashboards?|metrics?|monitor\w*)|(service|system|cluster|node|pod|database|db|ledger) health|"
    r"(error|edge|boundary|failure|exit|stop|loop|test|pre|post) ?conditions?|"
    r"(medical|health)[- ](claims?|records?|billing|data|devices?|imaging|software|platform|"
    r"systems?|insurance|providers?|payers?))\b", re.I)
PERSONAL = {"age", "family", "health", "genetic", "religion", "origin", "affect"}
NO_OVERRIDE = {"criminal-record", "salary-history", "genetic", "sex-orientation"}
OVERRIDE = re.compile(r"<!--\s*lint-ok:\s*(.+?)\s*-->", re.I)
# the only hits an override may clear: one word that technical text also uses
AMBIGUOUS = {"condition", "conditions", "race", "temple", "faith", "pray", "health", "medical",
             "club", "clubs", "association", "associations", "organisation", "organisations",
             "organization", "organizations", "societies", "citizen"}
_AMB = r"(health|medical|conditions?|faith|pray\w*|temple|race|citizen\w*)"
PERSON_DIRECTED = re.compile(
    r"\b(your|you're|you've|you'd)\s+(\w+\s+)?" + _AMB + r"|\b" + _AMB +
    r"\s+(\w+\s+)?(you|your|issues?|problems?|conditions?|history|status|needs?|concerns?)\b|"
    r"\bany\s+(\w+\s+)?" + _AMB + r"|we should know|how old|originally from|\bkids?\b|children|"
    r"married|spouse|pregnan|graduat|finish(ed)? your degree|\baccent|\bnative\b|energy level|"
    r"passionate|confident", re.I)
# a yes/no question put to the person ("Are you ...", "Do you ...")
YESNO_TO_YOU = re.compile(r"^\W*(\d+[.)]\s*)?(are|do|did|have|will|would|can|could|is|does)\s+"
                          r"(you|your)\b", re.I)
PRONOUN = re.compile(r"^(you|your|yours|yourself|you're|you've|you'd|you'll)$", re.I)
WORD = re.compile(r"[\w'’]+")


def near_pronoun(text, start, end, reach=2):
    """True when you/your/yourself sits within `reach` words of the span."""
    toks = [(m.start(), m.end(), m.group(0).replace("’", "'")) for m in WORD.finditer(text)]
    idx = [i for i, (a, b, _) in enumerate(toks) if a < end and b > start]
    if not idx:
        return False
    lo, hi = max(0, idx[0] - reach), min(len(toks), idx[-1] + reach + 1)
    return any(PRONOUN.match(t[2]) for t in toks[lo:hi])


def person_directed(text, m):
    return bool(PERSON_DIRECTED.search(text) or YESNO_TO_YOU.search(text)
                or near_pronoun(m.string, m.start(), m.end()))


PHYSICAL = re.compile(r"\b(lift\w*|carry\w*|stand(ing)? for|climb\w*|kneel\w*|"
                      r"\d+[- ]?(pounds?|lbs?|kg))\b", re.I)
ACCOMMODATION = re.compile(r"with or without (a )?reasonable accommodation", re.I)
SKIP = re.compile(r"^\s*[-*]?\s*(strong( answer)?|probe|what a strong answer shows)\s*:", re.I)
ITEM = re.compile(r"^\s*(\d+[.)]|[-*])\s+")


ANCHOR_LINE = re.compile(r"^\s*[-*]\s*([1-5]|not assessed)\s*:", re.I)
H = re.compile(r"^\s*#{2,3}\s+(.+)$")


def candidate_lines(text):
    """In a kit (has '### Questions'), only numbered items under Questions
    headings are read. Otherwise list items and '?' lines. Table rows and
    anchor lines are never read (the kit's 'Dropped or rewritten' table quotes
    the bad originals on purpose)."""
    lines = text.splitlines()
    is_kit = any(re.match(r"^\s*###\s+questions", l, re.I) for l in lines)
    in_q = False
    for n, line in enumerate(lines, 1):
        h = H.match(line)
        if h:
            in_q = h.group(1).lower().startswith("questions")
            continue
        if not line.strip() or SKIP.match(line) or line.lstrip().startswith("|")                 or ANCHOR_LINE.match(line):
            continue
        if is_kit:
            if in_q and re.match(r"^\s*\d+[.)]\s+", line):
                yield n, line.strip()
            continue
        if ITEM.match(line) or "?" in line:
            yield n, line.strip()


def lint(text):
    hits = []
    for n, line in candidate_lines(text):
        ov = OVERRIDE.search(line)
        clean = OVERRIDE.sub("", line)
        scrubbed = TECHNICAL.sub(" ", clean)
        for lvl, cat, rx, why in COMPILED:
            m = rx.search(scrubbed if cat in PERSONAL else clean)
            if m:
                level = lvl
                if lvl == "ERROR" and ov and cat not in NO_OVERRIDE and \
                        m.group(0).strip().lower() in AMBIGUOUS and not person_directed(clean, m):
                    level = "OVERRIDDEN"
                    why = f"owner-visible override: {ov.group(1)}. List it in the kit's Dropped or rewritten table."
                elif lvl == "ERROR" and ov:
                    why = ("override not honoured: this is a question about the person, not a technical "
                           "word the lexicon misreads. " + why)
                hits.append({"line": n, "level": level, "category": cat, "match": m.group(0).strip(),
                             "text": clean.strip()[:160], "why_and_rewrite": why})
        if PHYSICAL.search(clean) and not ACCOMMODATION.search(clean):
            hits.append({"line": n, "level": "WARN", "category": "physical-ability",
                         "match": PHYSICAL.search(clean).group(0),
                         "text": clean.strip()[:160],
                         "why_and_rewrite": "Ability questions must add 'with or without reasonable "
                                            "accommodation' (ADA [35][46]) and ask only about an essential "
                                            "function: 'The role lifts 50-pound racks; can you do that, "
                                            "with or without reasonable accommodation?'"})
    return hits


def selftest():
    bad = """1. Do you have young kids?
2. Where are you originally from?
3. You're comfortable with Stripe, right?
4. Any health issues we should know about?
5. What is your current salary?
6. Are you authorised to work in Portugal?
7. Walk me through a billing bug you traced to its root.
   - Strong answer: names the symptom and the data they pulled.
8. Have you used Kafka?
9. How confident did you feel?
"""
    hits = lint(bad)
    cats = {(h["line"], h["category"]) for h in hits}
    for want in [(1, "family"), (2, "origin"), (3, "leading"), (4, "health"),
                 (5, "salary-history"), (9, "tool-recognition"), (10, "affect")]:
        assert want in cats, (want, cats)
    assert not any(h["line"] in (6, 7, 8) for h in hits), hits
    tech = """1. Tell me about a race condition you debugged in production.
2. How did you design the service health checks for the ledger?
3. Walk me through how you handled a medical-claims billing edge case.
4. Would you fit in with our young, energetic team?
5. The role requires lifting 50-pound server racks; can you do that?
6. Any health conditions we should know about?
7. The role lifts 50-pound racks; can you do that, with or without reasonable accommodation?
8. What does the payout job's temple deploy step do? <!-- lint-ok: Temple is our deploy tool -->
9. Have you ever been arrested? <!-- lint-ok: owner asked -->
"""
    hits = lint(tech)
    by = {}
    for h in hits:
        by.setdefault(h["line"], set()).add((h["level"], h["category"]))
    assert not any(l in by for l in (1, 2, 3, 7)), by
    assert ("ERROR", "affect") in by[4] and ("ERROR", "age") in by[4], by
    assert ("WARN", "physical-ability") in by[5], by
    assert ("ERROR", "health") in by[6], by
    assert by[8] == {("OVERRIDDEN", "religion")}, by
    assert ("ERROR", "criminal-record") in by[9], by
    # an override never clears a question about the person
    person = """1. Do you have young kids? <!-- lint-ok: owner wants to know about on-call -->
2. Where are you originally from? <!-- lint-ok: relocation -->
3. How old are you? <!-- lint-ok: insurance -->
4. Any health conditions we should know about? <!-- lint-ok: on-call -->
5. What condition was the ledger in when you inherited it? <!-- lint-ok: state of the system -->
6. How did you run our citizen developer programme? <!-- lint-ok: internal low-code programme -->
"""
    by = {}
    for h in lint(person):
        by.setdefault(h["line"], set()).add(h["level"])
    for n in (1, 2, 3, 4):
        assert "ERROR" in by[n] and "OVERRIDDEN" not in by[n], (n, by)
    assert by[5] == {"OVERRIDDEN"} and by[6] == {"OVERRIDDEN"}, by
    # bare "you" questions and a pronoun next to the word are about the person too
    bare = """1. Are you a US citizen? <!-- lint-ok: visa -->
2. Do you pray during working hours? <!-- lint-ok: rota -->
3. Are you in good health? <!-- lint-ok: on-call -->
4. Do you attend temple on Saturdays? <!-- lint-ok: weekend on-call -->
5. Do you practise a faith that would stop weekend on-call? <!-- lint-ok: rota -->
6. Is there a medical reason you left? <!-- lint-ok: gap -->
7. Are you healthy enough for on-call?
8. What condition was the ledger in when you inherited it? <!-- lint-ok: state of the system -->
"""
    by = {}
    for h in lint(bare):
        by.setdefault(h["line"], set()).add(h["level"])
    for n in range(1, 8):
        assert "ERROR" in by.get(n, set()) and "OVERRIDDEN" not in by[n], (n, by)
    assert by[8] == {"OVERRIDDEN"}, by
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.file:
        ap.error("give the file holding the questions")
    try:
        with open(a.file, encoding="utf-8") as fh:
            hits = lint(fh.read())
    except OSError as exc:
        print(f"bad input: {exc}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(hits, indent=1))
    else:
        if not hits:
            print("clean: no drift or drop-rule hits (a lexicon check, not a legal review)")
        for h in hits:
            print(f"{h['level']}\tline {h['line']}\t{h['category']}\t'{h['match']}'\n"
                  f"\t{h['text']}\n\t-> {h['why_and_rewrite']}")
    return 1 if any(h["level"] == "ERROR" for h in hits) else 0  # OVERRIDDEN and WARN exit 0


if __name__ == "__main__":
    sys.exit(main())
