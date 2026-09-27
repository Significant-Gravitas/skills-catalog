#!/usr/bin/env python3
r"""Flag interview questions that ask about protected traits, health or other drift.

Usage:
  cd ~/skills/interview-plan-and-scorecard && \
  python3 scripts/question_lint.py <question-bank.md|.txt|.csv> [--json]
  python3 scripts/question_lint.py --selftest

--selftest runs a table of known-bad lines, at least one per alternation of
every rule (R1-R15), plus clean lines and a template-format bank, and exits 1
if any line fails to fire its rule, so a dead stem or pattern is caught.
Word stems in RULES must end in \w* (for example disabilit\w*): a stem
followed by the closing word boundary never matches the real word.

Lines that start with "Do not score" or "Weak evidence" are template guidance,
not questions, and are skipped.

Reads every non-empty line (for a CSV, every cell of a `question` or
`follow_up` column). Each hit prints the line, the rule id, and the row of
references/unlawful-question-rewrites.md that holds the job-related rewrite.

This is a lexicon floor, not legal review. It over-flags on purpose (a
"travel" or "weekend" question may be fine when it states a real job
requirement); the model judges each hit in context against the reference and
shows the owner what it changed. It cannot catch every unlawful question.

Exit 0 = no hits, 1 = hits to review, 2 = bad input (missing, unreadable
or non-UTF-8/UTF-16 file, or a file with no questions).
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

# id, pattern, why, rewrite row in references/unlawful-question-rewrites.md
RULES = [
    ("AGE", r"\b(how old|your age|age\b|born in|(what )?year (were|was) you born|birth ?date|date of birth|year (did )?you graduate|graduation year|when did you graduate|retir\w*|digital natives?|young\w*|energetic|(are you|you'?re|you are) (over|under) (\d\d|thirty|forty|fifty|sixty)|in (your|their|her|his) (twenties|thirties|forties|fifties|sixties)|(what year|when) did you (finish|leave|complete) (high )?(school|college|university))\b", "age or an age proxy", "R1"),
    ("ORIGIN", r"\b(where are you (really |originally )?from|originally from|nationalit\w*|native (english|language|tongue|speak\w*)|native (english |language )?speakers?|first language|mother tongue|accent\w*|ethnic\w*|rac(e|es|ial\w*)|heritage|birthplace|where were you born|languages? (are |is )?(spoken|you speak) at home|second language|english (is not|isn'?t) (your|their|her|his) (first|native)|which country (are you|do you come) from|(native|home) country|country of (origin|birth)|ancest\w*|lived in (this|the) country|gr(o|e)w up)\b", "national origin, race or ethnicity", "R2"),
    ("CITIZEN", r"\b(are you a (us |u\.s\. |uk )?citizen|citizenship|green cards?|visa status|immigration status)\b", "citizenship beyond the lawful yes/no authorisation question", "R3"),
    ("FAMILY", r"\b(married|marital|spouse\w*|husband\w*|wi(fe|ves)|partner'?s? (do|does|job|work)|do you have a (partner|significant other)|little ones|having (a )?bab(y|ies)|(are you|currently) expecting( a (baby|child))?(?=\s*[?.!]*\s*$)|expecting a (baby|child)|dependants?|dependents|(any|have a) dependent|child\w*|kids?|pregnan\w*|family plans|plan\w* (to|on) (have|start)\w*|start(ing)? a family|maternity|paternity|single parent\w*|(are you|being) a (mother|father|parent|mum|mom|dad))\b", "marital status, children, pregnancy or caring duties", "R4"),
    ("HEALTH", r"\b(health\w*|medical\w*|illness\w*|sick (days|leave)|disabilit\w*|disabled|medication\w*|prescription\w*|mental (health|illness\w*|conditions?|or physical)|therap\w*|injur\w*|workers'? comp\w*|condition that|physical limitations?|handicap\w*|impairment\w*|impaired|wheelchair\w*|depress\w*|anxiety|bipolar|diabet\w*|cancer|treated for)\b", "health or disability before an offer", "R5"),
    ("GENETIC", r"\b(family (medical|health) history|genetic\w*|runs? in (your|the) family)\b", "genetic information, including family medical history", "R6"),
    ("RELIGION", r"\b(church\w*|religio\w*|pray\w*|mosques?|synagogues?|temples?|faith\w*|sabbath|holy days?|christmas|ramadan|easter|observan\w*|christian\w*|muslims?|jewish|jews?|hindu\w*|sikh\w*|buddhis\w*|catholic\w*|protestant\w*|atheis\w*)\b", "religion or religious observance", "R7"),
    ("SEX", r"\b(gender\w*|sexual orientation|sexuality|gay|lesbian\w*|transgender|maiden name|mrs\.?|miss\b|girlfriend\w*|boyfriend\w*)\b", "sex, gender or sexual orientation", "R8"),
    ("ARREST", r"\b(arrest\w*|convict\w*|criminal record\w*|trouble with the (police|law))\b", "arrest record (not conviction) and fair-chance rules on conviction history", "R9"),
    ("PAY_HISTORY", r"\b(current (salary|pay|compensation|comp)|previous (salary|pay)|last (salary|pay)|how much (do|did) you (make|earn)|salary history|what are you (making|earning))\b", "salary history (banned in many jurisdictions)", "R10"),
    ("CLUBS", r"\b(clubs?|organi[sz]ations? (do|are) you|societ(y|ies) (do|are) you|affiliations?|union members?\w*)\b", "memberships that can reveal protected traits or union activity", "R11"),
    ("APPEARANCE", r"\b(height|weigh\w*|photo\w*|picture of you|how tall|appearance)\b", "appearance or a photograph before an offer", "R12"),
    ("AFFECT", r"\b(rate (their|the candidate'?s) (confidence|energy|enthusiasm)|body language|eye contact|seemed nervous|culture fit|gel with|vibe\w*)\b", "affect, demeanour or unsupported fit (not scoreable evidence)", "R13"),
    ("SCHEDULE", r"\b(weekends?|nights?|overtime|travel\w*|shifts?|on[- ]call|lift\w*|standing)\b", "a real requirement asked the wrong way can drift into religion, family or disability", "R14"),
    ("MILITARY", r"\b(type of discharge|dishonou?rabl\w*|discharge status)\b", "military discharge type", "R15"),
]
COMPILED = [(rid, re.compile(p, re.I), why, row) for rid, p, why, row in RULES]

# An ability or schedule requirement ("... with or without reasonable
# accommodation?") belongs in the unscored "Ability requirements" section of
# templates/question-bank.md. Flag it when it is mapped to a criterion, either
# on the same line ("Q3 (C3, Priya): ... reasonable accommodation?") or under a
# template heading ("### Q3: C3, <criterion>" then a later
# "- **Question (read as written):** ..." line). The heading scope ends at the
# next heading, so the "### Ability requirements" section is never flagged.
ABILITY_ON_CRITERION = re.compile(r"^\s*(#+\s*)?Q\d+\s*[(:,]\s*C\d+", re.I)
HEADING = re.compile(r"^\s*#+\s")
ABILITY_TEXT = re.compile(r"reasonable accommodation|can you (perform|meet|work) (that|this|the) (schedule|requirement)", re.I)
# Guidance lines in the template ("Do not score: ... accent ...", "Weak
# evidence looks like: ...") name topics to avoid; they are not questions.
GUIDANCE = re.compile(r"^[-*\s]*(\*\*)?\s*(do not score|weak evidence)", re.I)


def ability_hit(line: str, under_criterion: bool = False):
    if (under_criterion or ABILITY_ON_CRITERION.search(line)) and ABILITY_TEXT.search(line):
        return {"rule": "ABILITY_SCORED", "match": ABILITY_TEXT.search(line).group(0),
                "why": "an ability/schedule requirement mapped to a scored criterion; move it to the "
                       "unscored 'Ability requirements' section (templates/question-bank.md)",
                "rewrite_row": "R5/R14"}
    return None


def lint_lines(lines: list[str]) -> list[dict]:
    hits = []
    under = False
    for n, line in enumerate(lines, start=1):
        if HEADING.match(line):
            under = bool(ABILITY_ON_CRITERION.search(line))
        if GUIDANCE.match(line):
            continue
        for rid, rx, why, row in COMPILED:
            m = rx.search(line)
            if m:
                hits.append({"line": n, "text": line, "rule": rid, "match": m.group(0),
                             "why": why, "rewrite_row": row})
        ah = ability_hit(line, under)
        if ah:
            hits.append({"line": n, "text": line, **ah})
    return hits


class BadInput(Exception):
    pass


def read_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return raw.decode("utf-16")  # Windows Notepad "Unicode"
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise BadInput(f"{path} is not UTF-8 or UTF-16 text; save it as UTF-8 and re-run")


def lines_of(path: Path) -> list[str]:
    text = read_text(path)
    if path.suffix.lower() == ".csv":
        out = []
        for row in csv.DictReader(text.splitlines()):
            for k, v in row.items():
                if k and re.search(r"question|follow", k, re.I) and v:
                    out.append(v.strip())
        return out
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


# Table-driven: at least one known-bad line per alternation of every rule
# (so a stem that cannot match its real word is caught); each must fire its
# own rule id. Every line of the review's qbad2.md fixture is included.
SELFTEST_POSITIVE = [
    ("AGE", "What year were you born?"), ("AGE", "How old are you?"),
    ("AGE", "Is this role OK given your age?"), ("AGE", "What is your date of birth?"),
    ("AGE", "What is your birthdate?"), ("AGE", "Were you born in the 80s?"),
    ("AGE", "What year did you graduate?"), ("AGE", "What was your graduation year?"),
    ("AGE", "When did you graduate?"), ("AGE", "When do you plan to retire? Any retirement plans?"),
    ("AGE", "How many years until retirement?"), ("AGE", "We want a digital native."),
    ("AGE", "We are a young team."), ("AGE", "Are you energetic?"),
    ("ORIGIN", "Where are you originally from?"), ("ORIGIN", "Where are you really from?"),
    ("ORIGIN", "What is your nationality?"), ("ORIGIN", "Are you a native English speaker?"),
    ("ORIGIN", "Are you a native speaker?"), ("ORIGIN", "What is your native language?"),
    ("ORIGIN", "Is English your first language?"), ("ORIGIN", "What is your mother tongue?"),
    ("ORIGIN", "Nice accent, where's it from?"), ("ORIGIN", "What is your ethnicity?"),
    ("ORIGIN", "What is your ethnic background?"), ("ORIGIN", "What race are you?"),
    ("ORIGIN", "Tell me about your heritage."), ("ORIGIN", "What is your birthplace?"),
    ("ORIGIN", "Where were you born?"), ("ORIGIN", "What languages are spoken at home?"),
    ("ORIGIN", "Is English a second language for you?"),
    ("ORIGIN", "English isn't your first language, is it?"),
    ("CITIZEN", "Are you a US citizen?"), ("CITIZEN", "What is your citizenship?"),
    ("CITIZEN", "Do you have a green card?"), ("CITIZEN", "What is your visa status?"),
    ("CITIZEN", "What is your immigration status?"),
    ("FAMILY", "Are you pregnant or planning to be?"), ("FAMILY", "Do you have kids?"),
    ("FAMILY", "Are you married?"), ("FAMILY", "What is your marital status?"),
    ("FAMILY", "What does your spouse do?"), ("FAMILY", "What does your wife do?"),
    ("FAMILY", "Does your husband work?"), ("FAMILY", "What is your partner's job?"),
    ("FAMILY", "Do you have children?"), ("FAMILY", "Who does the childcare?"),
    ("FAMILY", "Any family plans?"), ("FAMILY", "Are you planning to start a family soon?"),
    ("FAMILY", "Do you plan on having kids?"), ("FAMILY", "Thinking of starting a family?"),
    ("FAMILY", "Will you take maternity leave?"), ("FAMILY", "Paternity leave plans?"),
    ("FAMILY", "Are you a single parent?"), ("FAMILY", "Are you a mother?"),
    ("HEALTH", "Do you have a disability we should know about?"), ("HEALTH", "Are you disabled?"),
    ("HEALTH", "Any injury that stops you lifting?"), ("HEALTH", "Are you on any medication?"),
    ("HEALTH", "Any health issues?"), ("HEALTH", "Any medical conditions?"),
    ("HEALTH", "Any illnesses?"), ("HEALTH", "How many sick days did you take?"),
    ("HEALTH", "Any prescriptions?"), ("HEALTH", "Do you have any mental or physical impairments?"),
    ("HEALTH", "Any mental health history?"), ("HEALTH", "Are you in therapy?"),
    ("HEALTH", "Ever filed for workers' comp?"), ("HEALTH", "Do you have a condition that affects work?"),
    ("HEALTH", "Any physical limitations?"), ("HEALTH", "Are you handicapped in any way?"),
    ("HEALTH", "Is your hearing impaired?"),
    ("GENETIC", "Does anything run in the family? Any family medical history?"),
    ("GENETIC", "Do you have any genetic conditions or genetics testing?"),
    ("GENETIC", "Does diabetes run in your family?"),
    ("RELIGION", "What is your religion?"), ("RELIGION", "Are you religious?"),
    ("RELIGION", "Do you need time off for prayers?"), ("RELIGION", "Which church do you attend?"),
    ("RELIGION", "Do you go to mosque?"), ("RELIGION", "Which synagogue?"),
    ("RELIGION", "Do you go to temple?"), ("RELIGION", "What faith are you?"),
    ("RELIGION", "Do you keep the sabbath?"), ("RELIGION", "Which holy days do you take?"),
    ("RELIGION", "Can you work Christmas?"), ("RELIGION", "Do you fast for Ramadan?"),
    ("RELIGION", "Are you off at Easter?"), ("RELIGION", "Are you observant?"),
    ("SEX", "What is your maiden name?"), ("SEX", "What is your gender?"),
    ("SEX", "What is your sexual orientation?"), ("SEX", "Are you gay?"),
    ("SEX", "Are you a lesbian?"), ("SEX", "Are you transgender?"), ("SEX", "Is it Mrs or Ms?"),
    ("SEX", "Is it Miss Smith?"), ("SEX", "Does your girlfriend mind?"), ("SEX", "Does your boyfriend work?"),
    ("ARREST", "Have you ever been arrested?"), ("ARREST", "Were you arrested last year?"),
    ("ARREST", "Do you have an arrest record?"), ("ARREST", "Any arrests?"),
    ("ARREST", "Were you ever convicted of a crime?"), ("ARREST", "Do you have a criminal record?"),
    ("PAY_HISTORY", "What is your current salary?"), ("PAY_HISTORY", "What was your previous pay?"),
    ("PAY_HISTORY", "What was your last salary?"), ("PAY_HISTORY", "How much do you make?"),
    ("PAY_HISTORY", "Share your salary history."), ("PAY_HISTORY", "What are you earning now?"),
    ("CLUBS", "Which clubs do you belong to?"), ("CLUBS", "What organisations are you in?"),
    ("CLUBS", "Which societies are you part of?"), ("CLUBS", "Any affiliations?"),
    ("CLUBS", "Are you a union member?"),
    ("APPEARANCE", "How tall are you?"), ("APPEARANCE", "What is your height?"),
    ("APPEARANCE", "What do you weigh?"), ("APPEARANCE", "Send a photograph."),
    ("APPEARANCE", "Send a picture of you."), ("APPEARANCE", "Rate their appearance."),
    ("AFFECT", "Rate the candidate's confidence."), ("AFFECT", "Watch their body language."),
    ("AFFECT", "Did they make eye contact?"), ("AFFECT", "They seemed nervous."),
    ("AFFECT", "Culture fit?"), ("AFFECT", "Would you gel with a small, fast team?"),
    ("AFFECT", "Good vibes."),
    ("SCHEDULE", "Can you work weekends?"), ("SCHEDULE", "Can you work nights?"),
    ("SCHEDULE", "Is overtime OK?"), ("SCHEDULE", "Can you do travelling?"),
    ("SCHEDULE", "Can you work shifts?"), ("SCHEDULE", "Can you be on-call?"),
    ("SCHEDULE", "Can you do the lifting?"), ("SCHEDULE", "Is standing all day OK?"),
    ("MILITARY", "Were you dishonorably discharged?"), ("MILITARY", "What type of discharge?"),
    ("MILITARY", "What is your discharge status?"), ("MILITARY", "Was it a dishonourable discharge?"),
    # review-2-r3 qbad3.md lines, plus one line per new alternation
    ("ORIGIN", "Which country are you from?"), ("ORIGIN", "Which country do you come from?"),
    ("ORIGIN", "What is your native country?"), ("ORIGIN", "Do you visit your home country?"),
    ("ORIGIN", "What is your country of origin?"), ("ORIGIN", "What is your country of birth?"),
    ("ORIGIN", "What's your ancestry?"), ("ORIGIN", "Where are your ancestors from?"),
    ("ORIGIN", "How long have you lived in this country?"), ("ORIGIN", "Where did you grow up?"),
    ("ORIGIN", "Where you grew up, did people speak English?"),
    ("AGE", "Are you over 40?"), ("AGE", "You're under thirty, right?"),
    ("AGE", "Is she in her fifties?"), ("AGE", "What year did you finish school?"),
    ("AGE", "When did you leave college?"),
    ("RELIGION", "Are you a Christian?"), ("RELIGION", "Are you Muslim?"), ("RELIGION", "Are you Jewish?"),
    ("RELIGION", "Are you Hindu?"), ("RELIGION", "Are you a Sikh?"), ("RELIGION", "Are you Buddhist?"),
    ("RELIGION", "Are you Catholic?"), ("RELIGION", "Are you Protestant?"), ("RELIGION", "Are you an atheist?"),
    ("RELIGION", "Are you a Jew?"),
    ("FAMILY", "Do you have a partner?"), ("FAMILY", "What does your partner do for a living?"),
    ("FAMILY", "Who looks after your little ones?"), ("FAMILY", "Are you planning on having a baby?"),
    ("FAMILY", "Are you currently expecting?"), ("FAMILY", "Are you expecting a baby?"),
    ("FAMILY", "Do you have any dependants?"), ("FAMILY", "Any dependents?"),
    ("FAMILY", "Do you have a dependent at home?"), ("FAMILY", "Do you have a significant other?"),
    ("HEALTH", "Do you need a wheelchair?"), ("HEALTH", "Have you ever been treated for depression?"),
    ("HEALTH", "Do you have anxiety?"), ("HEALTH", "Are you bipolar?"), ("HEALTH", "Are you diabetic?"),
    ("HEALTH", "Have you had cancer?"),
    ("ARREST", "Have you ever been in trouble with the police?"), ("ARREST", "Any trouble with the law?"),
]
# Lines that must raise no hit at all.
SELFTEST_CLEAN = [
    "Walk me through the last month-end close you ran, from the first task to sign-off.",
    "Tell me about a procedure you wrote that other people used. How did you keep it current?",
    "Write the reconciliation query for the sample data and explain your duplicate check.",
    "- **Do not score:** prestige, polish, confidence, accent, shared interests",
    "- **Weak evidence looks like:** vague about which steps were theirs",
    # Lawful or out-of-scope lines that must stay clean (the sponsorship
    # yes/no question is the R3 rewrite itself).
    "Are you legally allowed to work here without sponsorship?",
    "Will you now or in the future require sponsorship for employment?",
    "What are you expecting to learn in the first 90 days?",
    "We process over 40 invoices a day; how would you triage them?",
    "Which tasks are dependent on the ledger close finishing first?",
    "When did you get your first job in accounts payable?",
    "How does finance partner with operations at your company?",
    "Are you a veteran?",
]
# A bank in templates/question-bank.md format: the mapping is in the heading.
SELFTEST_TEMPLATE_BANK = """### Q3: C3, Writes policy others follow
- **Question (read as written):** "Month-end close runs to 19:00. Can you meet that schedule, with or without reasonable accommodation?"
- **Do not score:** accent
### Ability requirements (only if the role has them)
- "This role requires month-end evenings. Can you perform that, with or without reasonable accommodation?"
"""


def selftest() -> int:
    bad = 0
    for rid, line in SELFTEST_POSITIVE:
        fired = [r for r, rx, _, _ in COMPILED if rx.search(line)]
        if rid not in fired:
            print(f"FAIL {rid} did not fire on: {line}")
            bad += 1
    for line in SELFTEST_CLEAN:
        fired = [h["rule"] for h in lint_lines([line])]
        if fired:
            print(f"FAIL clean line hit {fired}: {line}")
            bad += 1
    if not ability_hit("Q3 (C3, Priya): Month-end runs to 19:00. Can you meet that schedule, with or without reasonable accommodation?"):
        print("FAIL ABILITY_SCORED did not fire on a criterion-mapped accommodation question")
        bad += 1
    if ability_hit("AR1 (all candidates, not scored): Can you meet that schedule, with or without reasonable accommodation?"):
        print("FAIL ABILITY_SCORED fired on an unscored ability requirement")
        bad += 1
    th = lint_lines(SELFTEST_TEMPLATE_BANK.splitlines())
    got = [h["line"] for h in th if h["rule"] == "ABILITY_SCORED"]
    if got != [2]:
        print(f"FAIL template-format bank: ABILITY_SCORED on lines {got}, want [2]")
        bad += 1
    other = [h["rule"] for h in th if h["rule"] != "ABILITY_SCORED"]
    if other:
        print(f"FAIL template-format bank raised {other}")
        bad += 1
    covered = {rid for rid, _ in SELFTEST_POSITIVE}
    missing = [rid for rid, *_ in RULES if rid not in covered]
    if missing:
        print(f"FAIL no selftest line for: {', '.join(missing)}")
        bad += 1
    print("selftest OK" if not bad else f"selftest: {bad} failure(s)")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("bank", nargs="?")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.bank:
        ap.error("bank is required unless --selftest is given")
    p = Path(a.bank)
    if not p.is_file():
        print(f"error: file not found: {a.bank}", file=sys.stderr)
        return 2
    try:
        lines = lines_of(p)
    except (BadInput, UnicodeDecodeError, csv.Error) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    if not lines:
        print(f"error: no questions found in {a.bank} (empty file, or a CSV with no "
              "question/follow_up column)", file=sys.stderr)
        return 2
    if not any(re.search(r"[A-Za-z]", ln) for ln in lines):
        print(f"error: no English text found in {a.bank}; the lexicon is English-only, so the lint "
              "cannot check this file (wrong encoding, or a bank in another language: review it "
              "by hand against the reference)", file=sys.stderr)
        return 2
    hits = lint_lines(lines)
    if a.json:
        print(json.dumps(hits, indent=2))
    else:
        for h in hits:
            print(f"line {h['line']} [{h['rule']} -> references/unlawful-question-rewrites.md {h['rewrite_row']}] "
                  f"'{h['match']}': {h['why']}\n    {h['text']}")
        print(f"{len(hits)} hit(s). Review each in context; rewrite or confirm it states a real job requirement."
              if hits else "No hits. The lint is a floor: still read the bank against the reference.")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
