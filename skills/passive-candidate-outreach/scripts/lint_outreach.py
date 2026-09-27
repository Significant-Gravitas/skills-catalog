#!/usr/bin/env python3
"""Lint outreach drafts before the owner sees them.

    cd ~/skills/passive-candidate-outreach && python3 scripts/lint_outreach.py \
        /home/user/outreach/drafts.json [--max-words 60] [--dnc ~/workspace/hiring/dnc.csv] \
        [--log ~/workspace/hiring/outreach-log.csv] [--similarity 0.6] [--json]

Input shape: templates/drafts.json. One object with company, sender, role and a
list of drafts (candidate, subject, body, hook_source, touch; a follow-up whose
subject starts "Re:" also carries thread_subject, the exact subject of touch 1,
unless touch 1 for the same person is in the same file).

Checks per draft (ERROR blocks showing the draft, WARN needs a look):
- ERROR the candidate is on the do-not-contact list, or the log already holds a
  decline / not-interested / dnc for them (the draft must not exist).
- ERROR body over --max-words (default 60 words: the skill's default, the owner
  can change it and it is saved as outreach_max_words).
- ERROR more than one question mark, or the question is not on its own line.
- ERROR a calendar / booking link or "book a time" (the ask is a reply only).
- ERROR scam-lookalike asks: money, fees, bank or card details, ID documents,
  or any request to continue on WhatsApp / Telegram / Signal or another messaging
  app ("DM me on WhatsApp", "find me on Telegram", "hop on Signal", "WhatsApp me",
  "my WhatsApp is", a wa.me / t.me link) (FTC job-scam data, dossier [82]).
  hook_source never silences an ask. An app name that is not an ask (a talk about
  WhatsApp payments) is a WARN, skipped only where it sits inside the hook phrase.
- ERROR the company name or the sender name is missing (verifiable sender).
- ERROR wording that implies the person is job hunting (persona boundary).
- ERROR a protected-trait or personal-life reference (age, your family, your
  health, you're older, your retirement...). Ambiguous single words ("health",
  "family", "photo", "young", "older", "retire", "crypto", "pay the") are a
  WARN ("an older ledger schema", "retire our billing monolith", "payments in
  crypto" describe the work; crypto is an ERROR only as an ask: "send/pay/
  transfer (us) (in) crypto", "paid in crypto"), and are skipped when they come from the
  company name, the sender name or the hook_source (e.g. a company called
  "Oscar Health", a hook on a crypto library). Scam and protected checks run
  on the text with the company and sender names removed.
- ERROR banned subject ("Quick question", empty). "Fwd:" is always an ERROR.
  "Re:" is an ERROR on touch 1; on a later touch it is allowed only as
  "Re: <exact subject of touch 1>" (thread_subject or touch 1 in the file).
- ERROR "just bumping"-style follow-ups that add nothing.
- WARN hype or flattery words; generic "saw your profile"; the hook source
  named in hook_source does not appear in the body.
Batch check: the first 12 words of every pair of drafts are compared (Jaccard
word overlap). At or above --similarity (default 0.6, a practitioner default,
not a published figure) the pair is an ERROR: "cards too thin, send back to
sourcing".

Exit 0 when clean, 1 when any ERROR, 2 on bad input. Warnings alone exit 0.
Run with --selftest to check the linter itself.
"""

import argparse
import csv
import json
import os
import re
import sys
import unicodedata

DEFAULT_MAX_WORDS = 60          # skill default: "under 60 words"; owner may change
DEFAULT_SIMILARITY = 0.6        # practitioner default for "two drafts open alike"
OPENING_WORDS = 12              # how much of each opening is compared

CALENDAR = re.compile(
    r"(calendly\.com|cal\.com|savvycal|zcal\.co|chilipiper|meetings\.hubspot|"
    r"outlook\.office\.com/bookwithme|calendar\.app\.google|book a (time|slot|call)|"
    r"grab (a )?time|pick a (time|slot))", re.I)
SCAM = re.compile(
    r"(application fee|processing fee|training fee|\ba fee\b|any fees?|pay (a|us|for|upfront)|"
    r"upfront (cost|payment)|deposit (a|the|this) che(ck|que)|gift card|bitcoin|"
    r"(send|pay|transfer) (us )?(in )?crypto|paid in crypto|"
    r"wire (transfer|money)|(send|share|provide|need|confirm) (us )?(your )?(bank|card details|"
    r"account number|routing|iban|sort code|ssn|social security|passport|driver'?s licen[cs]e|"
    r"id\b|identity document)|copy of your (id|passport|licen[cs]e)|"
    r"buy (your own )?equipment|equipment purchase|starter kit)", re.I)
# Messaging apps. SKILL: never ask to move to WhatsApp, Telegram or another app.
# The app word itself; "signal processing/analysis/..." and "WhatsApp's ..." are
# topics, not the app.
_APP = (r"(?:whats\s?app|telegram|signal|viber|we\s?chat|line app|kakao\s?talk|threema|wickr|"
        r"(?:facebook|fb) messenger|messenger app|imessage|snapchat|discord|skype)\b"
        r"(?![- ]?(?:processing|process\w*|analysis|theory|detection|chains?|handling|flow|path|"
        r"boost|to[- ]noise|strength|quality)\b)(?!['’]s\b)")
# After the app word: a topic noun means the app is the subject ("talk to
# WhatsApp engineers"), not the channel.
_APP_TOPIC = (r"(?!\s+(?:engineers?|engineering|team|teams|folks|people|staff|alumni|payments?|"
              r"protocol|api|apis|backend|infra\w*|scale|servers?|bots?|clients?|codebase|sdk|"
              r"integrations?|business|outage|incident|migration)\b)")
# A verb used as a noun after a determiner is the work, not an ask
# ("your talk on WhatsApp payments", "the move to Signal").
_NOT_NOUN = ("".join(f"(?<!{d} )" for d in ("your", "the", "a", "an", "this", "that", "their", "his",
                                              "her", "its", "'s", "’s", "recent", "latest", "last",
                                              "great", "keynote", "lightning"))
             + r"(?<![\w'’-])")
_ASK_VERB = (r"(?:dm|pm|message|msg|text|ping|find|reach|hop|jump|get|chat|talk|continue|carry on|"
             r"move|switch|shift|take|add|join|connect|speak|call|ring|write|drop|go|contact|hit|"
             r"shoot|follow|catch|meet|reply|respond|answer|send|come|head|swap|migrate|transfer|"
             r"link|touch base|say hi|hmu)")
_ASK_OBJ = (r"(?:\s+with)?(?:\s+(?:me|us|you|this|it|things|(?:the|our|this) (?:conversation|chat|"
            r"thread|discussion|call)))?(?:\s+(?:a|an)(?:\s+quick)?\s+(?:line|message|note|dm|pm|"
            r"text|call|chat|hello|hi|ping))?(?:\s+(?:up|out|over|back|across|in touch|instead|"
            r"here|there))?")
_VIA = r"(?:on|over|via|to|in|into|onto|through|using)"
APP_ASK = re.compile(
    # DM / message / find / hop / continue / move ... (me) on|via|to <app>
    rf"((?:\blet['’]?s\s+|\b{_NOT_NOUN}){_ASK_VERB}\b{_ASK_OBJ}\s+{_VIA}\s+(?:the\s+)?{_APP}{_APP_TOPIC}|"
    # "... me on Telegram", "us via Signal"
    rf"\b(?:me|us)\s+(?:on|over|via|at|through)\s+(?:the\s+)?{_APP}{_APP_TOPIC}|"
    # "WhatsApp me", "Telegram us"
    r"\b(?:whats\s?app|telegram|viber|we\s?chat|threema|imessage|snapchat|discord|skype)\s+(?:me|us)\b|"
    # "my WhatsApp is ...", "our Telegram group"
    rf"\b(?:my|our)\s+{_APP}|"
    # "are you on Telegram?", "do you use Signal?", "prefer WhatsApp?"
    rf"\b(?:are|r)\s+(?:you|u)\s+(?:on|using)\s+{_APP}{_APP_TOPIC}|"
    rf"\b(?:do|would|could)\s+you\s+(?:use|have|prefer)\s+{_APP}{_APP_TOPIC}|\bprefer\s+{_APP}{_APP_TOPIC}|"
    # "easier on WhatsApp", "easiest to DM me on WhatsApp", "WhatsApp is easier", "... WhatsApp instead"
    rf"\b(?:easier|easiest|quicker|quickest|faster|simpler|better)\s+(?:for (?:you|us)\s+)?"
    rf"(?:to\s+\w+\s+(?:me\s+|us\s+)?)?(?:on|over|via)\s+{_APP}{_APP_TOPIC}|"
    rf"\b{_APP}\s+(?:is|would be|might be|works?)\s+(?:easier|quicker|faster|simpler|better|fine|ok|okay)\b|"
    rf"\b(?:is|would)\s+{_APP}\s+(?:be\s+)?(?:easier|quicker|faster|simpler|better|fine|ok|okay)\b|"
    rf"\b(?:on|over|via)\s+{_APP}\s+instead\b|"
    r"\bsignal app\b|"
    # invite links
    r"\bwa\.me/|chat\.whatsapp\.com|api\.whatsapp\.com/send|\bt\.me/|\btelegram\.me/|\bsignal\.me/)", re.I)
APP_WORD = re.compile(rf"\b{_APP}", re.I)
# Ambiguous single words: WARN, not ERROR (a healthcare company, a crypto repo).
# Skipped when the word is in hook_source.
SCAM_SOFT = re.compile(r"\b(crypto\w*|pay the)\b", re.I)
JOB_HUNT = re.compile(
    r"(looking for (a )?new (role|job|opportunit)|open to new opportunit|"
    r"your job (search|hunt)|since you'?re (looking|searching)|job[- ]seeking|"
    r"on the market|ready for a change|time to move on)", re.I)
PROTECTED = re.compile(
    r"\b(age|aged|youthful|you'?re (older|retir\w*)|you are (older|retir\w*)|your (age|retirement)|"
    r"(near(ing)?|close to|planning|plans? for) (your )?retirement|older than (you|most)|"
    r"graduat(ed|ion) (in|year)|class of \d{4}|"
    r"married|wife|husband|spouse|kids|children|pregnan\w*|maternity|"
    r"church|religio\w*|faith|nationality|native (speaker|of)|accent|"
    r"your (family|health|photo|looks)|young (family|kids|children|team)|"
    r"illness|disab\w*|your picture|where you'?re from|originally from)\b",
    re.I)
PROTECTED_SOFT = re.compile(r"\b(health\w*|family|photo\w*|young\w*|older|retir\w*)\b", re.I)
BANNED_SUBJECTS = {"", "quick question", "opportunity", "exciting opportunity",
                   "job opportunity", "hi", "hello", "hey", "following up"}
FAKE_THREAD = re.compile(r"^\s*(re|fwd?|fw)\s*:", re.I)
BUMP = re.compile(
    r"(just bumping|bumping this|circling back|touching base|just following up|"
    r"per my last|following up on my (last|previous)|any update\?|floating this)",
    re.I)
HYPE = re.compile(
    r"\b(rock ?star|ninja|guru|unicorn|world[- ]class|amazing opportunity|dream job|"
    r"incredible opportunity|game[- ]changing|crush(ing)? it|10x)\b", re.I)
GENERIC = re.compile(r"(came across your profile|saw your profile|impressive background|"
                     r"your experience caught my eye)", re.I)


def fold(text):
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower()).split()


def name_key(name):
    return " ".join(fold(name))


def words(text):
    return re.findall(r"[\w'’-]+", text or "")   # Unicode \w: 'João' is one word


def load_names(path, column_options, status_filter=None):
    names = set()
    if not path or not os.path.exists(path):
        return names
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for row in csv.DictReader(fh):
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            if status_filter and not status_filter(row):
                continue
            for col in column_options:
                if row.get(col):
                    names.add(name_key(row[col]))
                    break
    return names


def closed_in_log(row):
    return (row.get("status") in {"declined", "dnc"}
            or row.get("reply_type") == "not-interested")


def in_hook_phrase(text, hit, hook_words, reach=2):
    """True when this app-name hit is part of the hook phrase: the app word is in
    hook_source and a neighbouring word (within `reach`) is another hook word."""
    own = set(fold(hit.group(0)))
    if not own or not own <= hook_words:
        return False
    others = hook_words - own - {"on", "the", "a", "an", "of", "at", "in", "your", "my"}
    near = fold(text[:hit.start()])[-reach:] + fold(text[hit.end():])[:reach]
    return any(w in others for w in near)


def mask(text, names):
    """Remove the company and sender names so their words never trip a check."""
    for n in names:
        if n:
            text = re.sub(re.escape(n), " ", text, flags=re.I)
    return text


def subj_key(s):
    return " ".join(fold(s))


def lint(doc, max_words, dnc, closed, similarity):
    issues = []
    company = (doc.get("company") or "").strip()
    sender = (doc.get("sender") or "").strip()
    drafts = doc.get("drafts")
    if not isinstance(drafts, list) or not drafts:
        raise ValueError("drafts.json needs a non-empty 'drafts' list")
    if not company or not sender:
        issues.append(("ERROR", "*", "company and sender must be set at the top of drafts.json"))

    def add(level, who, msg):
        issues.append((level, who, msg))

    first_subjects = {name_key(d.get("candidate") or ""): (d.get("subject") or "").strip()
                      for d in drafts if int(d.get("touch") or 1) == 1}
    names = [company, sender]
    openings = []
    for i, d in enumerate(drafts):
        who = d.get("candidate") or f"draft {i + 1}"
        body = d.get("body") or ""
        subject = (d.get("subject") or "").strip()
        touch = int(d.get("touch") or 1)
        key = name_key(who)
        if key in dnc:
            add("ERROR", who, "on the do-not-contact list: delete this draft, keep no other data")
        if key in closed:
            add("ERROR", who, "the log already holds a decline or not-interested: no further touches")
        n = len(words(body))
        if n > max_words:
            add("ERROR", who, f"{n} words, over the {max_words}-word limit")
        qs = body.count("?")
        if qs > 1:
            add("ERROR", who, f"{qs} question marks; ask one question only")
        elif qs == 1:
            line = next(l for l in body.splitlines() if "?" in l).strip()
            if touch == 1 and not line.endswith("?"):
                add("ERROR", who, "the question must sit on its own line, ending the line")
            elif touch == 1 and len(re.split(r"(?<=[.!])\s+", line)) > 1:
                add("ERROR", who, "the question must sit on its own line, not after another sentence")
        elif touch == 1:
            add("ERROR", who, "first note has no question; end with one reply-able question")
        m_subject, m_body = mask(subject, names), mask(body, names)
        for label, rx in (("calendar or booking link", CALENDAR),
                          ("scam-lookalike ask (money, bank, ID or app move)", SCAM),
                          ("scam-lookalike ask (money, bank, ID or app move)", APP_ASK),
                          ("implies they are job hunting", JOB_HUNT),
                          ("protected-trait or personal-life reference", PROTECTED),
                          ("'just bumping'-style line; give something new", BUMP)):
            for text in (m_subject, m_body):
                m = rx.search(text)
                if m:
                    add("ERROR", who, f"{label}: '{m.group(0)}'")
                    break
        hook_words = set(fold(d.get("hook_source") or ""))
        for label, rx in (("possible scam-lookalike wording; check it is not an ask for money", SCAM_SOFT),
                          ("possible personal-life reference; keep it only if it is about the work",
                           PROTECTED_SOFT)):
            for text in (m_subject, m_body):
                hits = [h.group(0) for h in rx.finditer(text)
                        if not (set(fold(h.group(0))) - {"on", "the"}) <= hook_words]
                if hits:
                    add("WARN", who, f"{label}: '{hits[0]}'")
                    break
        # A messaging-app name that is not an ask (asks are the ERROR above) is a WARN.
        # hook_source never silences an ask; it only skips the occurrence that sits
        # inside the hook phrase itself ("your WhatsApp payments talk").
        if not any(APP_ASK.search(t) for t in (m_subject, m_body)):
            for text in (m_subject, m_body):
                hits = [h.group(0) for h in APP_WORD.finditer(text)
                        if not in_hook_phrase(text, h, hook_words)]
                if hits:
                    add("WARN", who, "messaging app named; check it is not an ask to move off "
                                     f"email/LinkedIn: '{hits[0]}'")
                    break
        bare = re.sub(r"^\s*(re|fwd?|fw)\s*:\s*", "", subject, flags=re.I)
        if bare.lower().strip(" .!?") in BANNED_SUBJECTS:
            add("ERROR", who, f"subject '{subject}' is banned; make the hook the subject")
        m = FAKE_THREAD.search(subject)
        if m and (touch == 1 or not m.group(1).lower() == "re"):
            add("ERROR", who, "subject fakes a reply or forward thread")
        elif m:
            orig = (d.get("thread_subject") or first_subjects.get(key) or "").strip()
            if not orig:
                add("ERROR", who, "a 'Re:' follow-up needs thread_subject (the exact subject "
                                  "of touch 1); without it, drop the 'Re:'")
            elif subj_key(bare) != subj_key(orig):
                add("ERROR", who, f"'Re:' subject does not match the first note's subject "
                                  f"'{orig}'; never fake a thread")
        joined = f"{subject}\n{body}".lower()
        if company and company.lower() not in joined:
            add("ERROR", who, f"company '{company}' not named in the note")
        if sender and sender.split()[0].lower() not in joined:
            add("ERROR", who, f"sender '{sender}' not named (sign the note)")
        m = HYPE.search(body)
        if m:
            add("WARN", who, f"hype or flattery: '{m.group(0)}'")
        m = GENERIC.search(body)
        if m:
            add("WARN", who, f"generic opener '{m.group(0)}'; cite the specific work instead")
        src = d.get("hook_source") or ""
        if touch == 1:
            src_words = [w for w in fold(src) if len(w) > 3]
            if not src_words:
                add("WARN", who, "no hook_source given; the hook must name a specific piece of work")
            elif not any(w in fold(body) + fold(subject) for w in src_words):
                add("WARN", who, f"hook source '{src}' does not appear in the note")
            openings.append((who, set(fold(body)[:OPENING_WORDS])))
    for a in range(len(openings)):
        for b in range(a + 1, len(openings)):
            wa, sa = openings[a]
            wb, sb = openings[b]
            if not sa or not sb:
                continue
            j = len(sa & sb) / len(sa | sb)
            if j >= similarity:
                add("ERROR", f"{wa} / {wb}",
                    f"openings {j:.2f} alike (limit {similarity}): cards too thin, send back to sourcing")
    return issues


def selftest():
    doc = {
        "company": "Northwind Tools", "sender": "Maya Chen", "role": "Billing engineer",
        "drafts": [
            {"candidate": "Priya Nair", "touch": 1, "hook_source": "Postgres migration post",
             "subject": "Your zero-downtime Postgres migration post",
             "body": "Hi Priya, I read your post on moving a 4TB Postgres table with zero downtime. "
                     "Northwind Tools is hiring one engineer to own billing, and live migrations "
                     "are most of the job.\nOpen to a short chat?\nMaya Chen, Northwind Tools"},
            {"candidate": "Bad Actor", "touch": 1, "hook_source": "talk",
             "subject": "Quick question",
             "body": "Hi, saw your profile. Since you're looking for a new role, move to WhatsApp? "
                     "Book a time: calendly.com/x. Are you free?"},
            {"candidate": "Dana Blocked", "touch": 1, "hook_source": "repo",
             "subject": "Your repo", "body": "Hi Dana, Northwind Tools. Maya. Chat?"},
        ]}
    issues = lint(doc, 60, {name_key("Dana Blocked")}, set(), 0.6)
    got = {(lvl, who) for lvl, who, _ in issues}
    assert ("ERROR", "Priya Nair") not in got, issues
    assert ("ERROR", "Bad Actor") in got
    assert ("ERROR", "Dana Blocked") in got
    msgs = " ".join(m for _, w, m in issues if w == "Bad Actor")
    for needle in ("calendar", "scam", "job hunting", "banned", "question marks"):
        assert needle in msgs, (needle, msgs)
    twins = {"company": "Acme", "sender": "Jo Park", "drafts": [
        {"candidate": "A", "touch": 1, "hook_source": "talk", "subject": "Your talk",
         "body": "Hi, I watched your talk on queues at Acme and it was great for us.\nChat? Jo, Acme"},
        {"candidate": "B", "touch": 1, "hook_source": "talk", "subject": "Your talk",
         "body": "Hi, I watched your talk on queues at Acme and it was great for us.\nChat? Jo, Acme"}]}
    assert any("too thin" in m for _, _, m in lint(twins, 60, set(), set(), 0.6))
    # a healthcare company name and a crypto hook are not protected-trait or scam ERRORs
    health = {"company": "Oscar Health", "sender": "Maya Chen", "drafts": [
        {"candidate": "Sam Poe", "touch": 1, "hook_source": "FHIR parser talk",
         "subject": "Your FHIR parser talk",
         "body": "Hi Sam, I watched your FHIR parser talk at PyCon.\nOscar Health is hiring an "
                 "engineer to own claims ingestion.\nWorth a reply?\nMaya Chen, Oscar Health"},
        {"candidate": "Kim Lee", "touch": 1, "hook_source": "post-quantum crypto library",
         "subject": "Your post-quantum crypto library",
         "body": "Hi Kim, I read your post-quantum crypto library docs.\nOscar Health is hiring "
                 "for that work.\nWorth a reply?\nMaya Chen, Oscar Health"},
        {"candidate": "Lu Fam", "touch": 1, "hook_source": "talk", "subject": "Your talk",
         "body": "Hi Lu, I saw your talk.\nHow is your family?\nMaya Chen, Oscar Health"},
        {"candidate": "Mo Pay", "touch": 1, "hook_source": "talk", "subject": "Your talk",
         "body": "Hi Mo, I saw your talk. You pay a small fee in crypto.\nWorth a reply?\nMaya Chen, Oscar Health"}]}
    iss = lint(health, 60, set(), set(), 0.6)
    errs = {(l, w) for l, w, _ in iss}
    assert ("ERROR", "Sam Poe") not in errs and ("ERROR", "Kim Lee") not in errs, iss
    assert ("ERROR", "Lu Fam") in errs and ("ERROR", "Mo Pay") in errs, iss
    # "Re:" follow-up: allowed only with the exact first-note subject
    thread = {"company": "Northwind Tools", "sender": "Maya Chen", "drafts": [
        {"candidate": "Priya Nair", "touch": 2,
         "thread_subject": "Your zero-downtime Postgres migration post",
         "subject": "Re: Your zero-downtime Postgres migration post",
         "body": "Hi Priya, one more detail: on-call is one week in six.\nWorth a reply?\n"
                 "Maya Chen, Northwind Tools"},
        {"candidate": "Tomas Varga", "touch": 4, "subject": "Re: Your Buzzwords talk",
         "body": "Hi Tomas, I will leave it here.\nMaya Chen, Northwind Tools"},
        {"candidate": "Ola B", "touch": 2, "thread_subject": "Your talk", "subject": "Re: Something else",
         "body": "Hi Ola, one more detail.\nMaya Chen, Northwind Tools"},
        {"candidate": "New Person", "touch": 1, "hook_source": "talk", "subject": "Re: Your talk",
         "body": "Hi, your talk.\nWorth a reply?\nMaya Chen, Northwind Tools"}]}
    errs = {(l, w) for l, w, _ in lint(thread, 60, set(), set(), 0.6)}
    assert ("ERROR", "Priya Nair") not in errs, errs
    for who in ("Tomas Varga", "Ola B", "New Person"):
        assert ("ERROR", who) in errs, (who, errs)
    idd = {"company": "Acme", "sender": "Jo Park", "drafts": [
        {"candidate": "Id Ask", "touch": 1, "hook_source": "talk", "subject": "Your talk",
         "body": "Hi, I saw your talk. Please send your ID and pay a small fee first.\nWorth a reply?\nJo, Acme"}]}
    msgs = " ".join(m for _, _, m in lint(idd, 60, set(), set(), 0.6))
    assert "scam" in msgs, msgs
    # describing the work is not a protected-trait or scam ERROR; personal phrasings and asks are
    work = {"company": "Northwind Tools", "sender": "Maya Chen", "drafts": [
        {"candidate": "A One", "touch": 1, "hook_source": "talk", "subject": "Your talk",
         "body": "Hi A, I saw your talk.\nWe are moving off an older ledger schema.\nWorth a reply?\n"
                 "Maya Chen, Northwind Tools"},
        {"candidate": "B Two", "touch": 1, "hook_source": "talk", "subject": "Your talk",
         "body": "Hi B, I saw your talk.\nNorthwind Tools builds payments in crypto.\nWorth a reply?\n"
                 "Maya Chen, Northwind Tools"},
        {"candidate": "C Three", "touch": 1, "hook_source": "talk", "subject": "Your talk",
         "body": "Hi C, I saw your talk.\nWe are about to retire our billing monolith.\nWorth a reply?\n"
                 "Maya Chen, Northwind Tools"},
        {"candidate": "D Four", "touch": 1, "hook_source": "talk", "subject": "Your talk",
         "body": "Hi D, I saw your talk. Since you're older, this may suit you.\nWorth a reply?\n"
                 "Maya Chen, Northwind Tools"},
        {"candidate": "E Five", "touch": 1, "hook_source": "talk", "subject": "Your talk",
         "body": "Hi E, I saw your talk. Before your retirement, one more role?\nWorth a reply?\n"
                 "Maya Chen, Northwind Tools"},
        {"candidate": "F Six", "touch": 1, "hook_source": "talk", "subject": "Your talk",
         "body": "Hi F, I saw your talk. To start, send us crypto for the kit.\nWorth a reply?\n"
                 "Maya Chen, Northwind Tools"}]}
    iss = lint(work, 60, set(), set(), 0.6)
    errs = {w for l, w, m in iss if l == "ERROR" and ("protected" in m or "scam" in m)}
    assert not errs & {"A One", "B Two", "C Three"}, iss
    assert {"D Four", "E Five", "F Six"} <= errs, iss
    # an app name in an honest hook is not an ask; asks to move apps stay ERROR
    apps = {"company": "Northwind Tools", "sender": "Maya Chen", "drafts": [
        {"candidate": "G Seven", "touch": 1, "hook_source": "WhatsApp payments talk",
         "subject": "Your WhatsApp payments talk",
         "body": "Hi G, I watched your WhatsApp payments talk at QCon São Paulo.\nNorthwind Tools is "
                 "hiring one engineer.\nWorth a reply?\nMaya Chen, Northwind Tools"},
        {"candidate": "H Eight", "touch": 1, "hook_source": "signal processing talk",
         "subject": "Your talk on signal processing",
         "body": "Hi H, I watched your talk on signal processing for fraud scoring.\nNorthwind Tools is "
                 "hiring one engineer.\nWorth a reply?\nMaya Chen, Northwind Tools"},
        {"candidate": "I Nine", "touch": 1, "hook_source": "talk", "subject": "Your talk",
         "body": "Hi I, I saw your talk. Can we chat on Signal instead?\nMaya Chen, Northwind Tools"},
        {"candidate": "J Ten", "touch": 1, "hook_source": "talk", "subject": "Your talk",
         "body": "Hi J, I saw your talk. Message me on Telegram for details.\nWorth a reply?\n"
                 "Maya Chen, Northwind Tools"}]}
    iss = lint(apps, 60, set(), set(), 0.6)
    scam = {w for l, w, m in iss if "scam" in m and l == "ERROR"}
    assert scam == {"I Nine", "J Ten"}, iss
    assert not any(w in ("G Seven", "H Eight") for l, w, m in iss if "scam" in m), iss
    # r4: asks are ERROR whatever the hook; topical mentions are not
    def body(line):
        return f"Hi K, I watched your WhatsApp payments talk.\n{line}\nMaya Chen, Northwind Tools"
    asks = ["Easiest to DM me on WhatsApp?", "Find me on Telegram and we can talk?", "DM me on Telegram",
            "Hop on WhatsApp with me?", "Text me on WhatsApp.", "Reach me via Telegram.",
            "Let's move to Signal.", "Ping me on Signal.", "Easier to chat over WhatsApp.",
            "Send me a message on WhatsApp.", "WhatsApp me.", "Can we talk on WhatsApp instead?",
            "Add me on Telegram: @maya.", "My WhatsApp is +351 900 000 000.", "Are you on Telegram?",
            "Happy to continue on WhatsApp if easier.", "Drop me a line on Signal.",
            "Jump on a quick call over WhatsApp?", "Write to me via Viber.", "wa.me/351900000000",
            "Is WhatsApp easier for you?", "Get in touch on WhatsApp."]
    drafts = [{"candidate": f"K{i}", "touch": 1, "hook_source": "WhatsApp payments talk",
               "subject": "Your WhatsApp payments talk", "body": body(a)} for i, a in enumerate(asks)]
    iss = lint({"company": "Northwind Tools", "sender": "Maya Chen", "drafts": drafts}, 60, set(), set(), 1.0)
    got = {w for l, w, m in iss if l == "ERROR" and "app move" in m}
    assert got == {f"K{i}" for i in range(len(asks))}, (sorted({d["candidate"] for d in drafts} - got), iss)
    topical = ["Your WhatsApp payments talk showed how retries go wrong.",
               "I'd love to talk about your work at WhatsApp.",
               "Your talk on WhatsApp's ledger was sharp.",
               "Our billing runs on Kafka, not Telegram bots.",
               "Your post on the move to Signal protocol keys was clear."]
    drafts = [{"candidate": f"T{i}", "touch": 1, "hook_source": "WhatsApp payments talk",
               "subject": "Your WhatsApp payments talk", "body": body(t + "\nWorth a reply?")}
              for i, t in enumerate(topical)]
    iss = lint({"company": "Northwind Tools", "sender": "Maya Chen", "drafts": drafts}, 60, set(), set(), 1.0)
    assert not any("app move" in m for l, w, m in iss), iss
    # the hook phrase itself is skipped; another bare mention still WARNs
    assert not any(w == "T0" and "messaging app" in m for l, w, m in iss), iss
    assert any(w == "T1" and "messaging app" in m and l == "WARN" for l, w, m in iss), iss
    assert len(words("Hi João, QCon São Paulo")) == 5
    print("selftest ok")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("drafts", nargs="?")
    ap.add_argument("--max-words", type=int, default=DEFAULT_MAX_WORDS)
    ap.add_argument("--similarity", type=float, default=DEFAULT_SIMILARITY)
    ap.add_argument("--dnc", default=os.path.expanduser("~/workspace/hiring/dnc.csv"))
    ap.add_argument("--log", default=os.path.expanduser("~/workspace/hiring/outreach-log.csv"))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not a.drafts:
        ap.error("give the drafts.json path (shape: templates/drafts.json)")
    try:
        with open(a.drafts, encoding="utf-8") as fh:
            doc = json.load(fh)
        dnc = load_names(a.dnc, ["name", "candidate"])
        closed = load_names(a.log, ["candidate", "name"], closed_in_log)
        issues = lint(doc, a.max_words, dnc, closed, a.similarity)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"bad input: {exc}. Fix drafts.json to match templates/drafts.json.", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps([{"level": l, "draft": w, "issue": m} for l, w, m in issues], indent=1))
    else:
        if not issues:
            print(f"clean: {len(doc['drafts'])} draft(s) pass")
        for level, who, msg in issues:
            print(f"{level}\t{who}\t{msg}")
    return 1 if any(l == "ERROR" for l, _, _ in issues) else 0


if __name__ == "__main__":
    sys.exit(main())
