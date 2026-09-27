#!/usr/bin/env python3
"""Gate a sourcing batch: link-or-no-card, no protected data, no invented intent.

Usage (cd ~/skills/candidate-sourcing-strategy first):
    python3 scripts/card_check.py <kept.json> --links <links.csv> [--scorecard <scorecard.md>]
        [--companies <target-companies.csv>] [--out ready.json]

Cards:  JSON list (templates/batch-card.json). Each card: name, title, company,
        location_as_stated, evidence[{must_have, text, url}], tenure,
        next_move {quote, url} or null, gap, tier, reason, search_id, channel.
Links:  CSV url,name,status,name_found,checked_on, filled from what web_fetch or
        `gh api` actually returned (templates/links.csv), one row per person
        per URL:
          name        the person the page was checked for (as on their card)
          status      ok | blocked (403, login/auth wall) | dead
          name_found  yes | no  (that person's name appears on the page)
Rules:
  * An evidence line counts only if links.csv has a row for its url AND for
    this card's name (folded like dedupe_names.py: accents, case, punctuation,
    nicknames; initials and word order ignored, so "Priya Nair" / "Priya S. Nair"
    / "Nair, Priya" match, but an extra surname does not)
    with status ok and name_found yes. A url checked only for someone else
    does not verify this card: a card built on another person's repo or post
    is exactly what the gate is for. A url cited on two cards needs a row for
    each person. Fallback: a github.com/<login>/... url with status ok counts
    for a card whose "github" field is that <login> (from `gh api`), unless
    a links.csv row for that url names someone else.
    A links file with no name column verifies nothing (add the column).
    Unverified lines are removed from the card.
  * A card with no verified evidence line is dropped ("no link, no card");
    if its links were only blocked it is listed as "could not verify".
  * Fewer than 2 verified lines: kept with a WARN (persona asks for 2-4),
    marked "thin": "thin, 1 line" (show that label on the card), and never
    tiered strong (a strong tier is lowered to worth-a-look).
  * Evidence may cite an M-id or a B-id (benchmark trait). With --scorecard,
    a line citing an id the scorecard lacks is removed; a card left with no
    lines for that reason says so (not "could not verify").
  * tier "unranked" (sub-agent cards) is refused: tier and reason every card
    before the gate.
  * More than 4: WARN; keep the four strongest.
  * Protected fields or wording (age, birth, graduation year, gender, race,
    ethnicity, religion, nationality, sexual orientation, gender identity,
    veteran status, health, disability, pregnancy, marital or
    family status or caring duties, anything read off a photo) anywhere on a
    card: the card is dropped with ERROR. The card's own name and company
    words are blanked first ("Christian's PGConf talk" on Christian Weber's
    card), and religion/veteran words are not read in location_as_stated
    ("Temple, TX"). A domain word ("a sick-leave accrual engine") still drops
    the card: rephrase the work and rerun (SKILL step 6).
  * "Open to work"/"looking for a new role" style claims need next_move with
    a quote and a verified url, otherwise the card is dropped with ERROR.
  * tier must be strong | worth-a-look | stretch, and reason must be present
    and must not rest on pedigree (school, employer brand); ordering is by
    evidence-to-bar match only.
  * Off-limits companies: any card whose company (normalised: case, accents,
    punctuation, suffixes like GmbH/Inc) matches a row of target-companies.csv
    whose boundary says "off limits" is dropped and counted. The file is
    --companies, or target-companies.csv next to --scorecard if present.
This script is a backstop, not the whole check: its word lists cannot catch
every phrasing. Read each card before it is shown.
Output: report lines on stdout; cards that pass go to --out (default
        ready.json), ordered strong -> worth-a-look -> stretch, then by
        number of verified must-haves.
Exit:   0 at least one card ready; 1 no card passed; 2 unreadable input.
Stdlib only, no network.
"""

import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

from dedupe_names import name_tokens, norm_name  # same name folding as dedupe (nicknames, accents)

TIERS = ["strong", "worth-a-look", "stretch"]
PROTECTED_KEYS = re.compile(r"^(age|dob|date_of_birth|birth\w*|gender|sex|race|ethnicity|religion|nationality|citizenship|health|disability|pregnan\w*|marital\w*|family\w*|children|photo\w*|headshot|graduation\w*)$", re.I)
PROTECTED_TEXT = [
    # age and birth
    r"\b\d{2}\s*(years old|yrs old|yo|y/o)\b", r"\bborn (in|on)\b", r"\bage[ds]? \d{2}\b",
    r"\b(class of|graduat\w*(\s+in)?|grad(uation)?\s+year:?)\s*'?(19|20)?\d{2}\b", r"\b(19|20)\d{2} (grad|graduate)\b",
    r",\s*\d{2}\s*$", r"\(\s*\d{2}\s*\)\s*$",  # a bare age after a title or name: "Eng, 42", "(42)"
    r"\b(eng|engineer|developer|dev|sre|manager|lead|designer|analyst|architect|recruiter|founder|cto|ceo|he|she)\w*\s*,\s*\d{2}\s*(,|;|\)|$)",
    r"^\s*[A-Za-z][\w .'-]{0,40},\s*\d{2}\s*,",  # "Marta, 42, ..." at the start of a field
    r"\b(looks|appears|seems) (young|old|older|younger)\b", r"\b(young|older|mature|junior-aged)\s+(candidate|engineer|person|guy|woman|man)\b",
    r"\bb\. ?(19|20)\d{2}\b",  # "b. 1985"
    r"\b(bsc|b\.sc|ba|b\.a|msc|m\.sc|ma|mba|phd|ph\.d|beng|meng|degree|diploma)\.?\W{1,3}'?(19|20)\d{2}\b",  # a degree year estimates age
    r"\bin (his|her|their) (early |mid |late |mid-|early-|late-)?[1-9]0'?s\b", r"\b(early|mid|late)[- ]?[1-9]0'?s\b",
    # photo: nothing is read off a photo
    r"\b(photo|picture|headshot|avatar|selfie)s? (suggests?|shows?|looks?|seems?|appears?|indicates?)\b",
    # sexual orientation and gender identity
    r"\b(gay|lesbian|bisexual|queer|lgbt\w*|transgender|trans (man|woman|person)|non-?binary|homosexual|straight (man|woman))\b",
    # veteran status
    r"\b(veteran|ex-military|army|navy|air force|marines?)\b(?! (of|to) )",
    # race and ethnicity descriptors for a person
    r"\b(hispanic|latin[oax]|black|african[- ]american|asian|caucasian|white|arab|indigenous)\s+(engineer|developer|woman|man|person|candidate|founder|leader|dev|guy|lady|female|male)\b",
    # family, pregnancy, marital status
    r"\bpregnan\w*\b", r"\bmaternity\b", r"\bpaternity\b", r"\b(married|divorced|widowed|single mom|single dad)\b",
    r"\b(his|her|their) (wife|husband|partner|spouse|kids|children|son|daughter)\b",
    r"\b(has|with) (kids|children|a baby|a family)\b", r"\b(mother|father|mom|mum|dad|parent)s? of\b",
    r"\b(new|young|working) (mom|mum|dad|parent|mother|father)\b",
    r"\b(with|and) (a |an |her |his |their )?(husband|wife|spouse|fianc[eé]e?|boyfriend|girlfriend)\b",
    r"\b(relocat\w*|moving|moved) (with|for) (a |an |her |his |their )?(family|kids|children|partner)\b",
    r"\bcar(ing|er|es|ed) for\b|\bcaregiv\w*\b|\b(elderly|aging|ageing|sick) (parent|mother|father|relative)s?\b",
    # religion
    r"\b(christian|muslim|jewish|hindu|buddhist|catholic|sikh|mormon|evangelical|atheist)\b",
    r"\b(mosque|church|synagogue|temple|parish|gurdwara|ramadan|sabbath)\b",
    # health and disability
    r"\b(is|was|being) (disabled|ill|sick)\b", r"\b(diagnosed|chronic illness|medical leave|sick leave|disability)\b",
    r"\b(wheelchair|autis\w*|adhd|dyslexi\w*|deaf|hard of hearing|visually impaired|blind (since|from)|neurodiverg\w*|cancer (survivor|patient)|depression|anxiety disorder|bipolar|epilep\w*)\b",
    # nationality, citizenship, ethnicity
    r"\b\w+(an|ese|ish|ch|i) (national|citizen)\b", r"\bcitizen of\b", r"\b(citizenship|nationality|visa status|immigrant|native speaker)\b",
    r"\b(ethnicity|ethnic (origin|background|minority)|racial)\b",  # not bare "race": "race condition" is engineering
    # gender
    r"\b(he/him|she/her|they/them|he/they|she/they|xe/xem)\b", r"\bpronouns?:",
]
# Religion and veteran words are also place names ("Temple, TX", "Navy Pier"),
# so they are not read in location_as_stated; every other pattern is.
PLACE_SKIP = {i for i, rx in enumerate(PROTECTED_TEXT) if "mosque" in rx or "christian" in rx or "veteran" in rx}


def mask_own_name(text, card):
    """Blank the card's own name and company words, so 'Christian's talk' for
    Christian Weber is not read as religion. Words of one or two letters stay."""
    words = set()
    for field in ("name", "company"):
        words |= {w for w in re.split(r"[^\w]+", str(card.get(field) or "")) if len(w) > 2}
    for w in sorted(words, key=len, reverse=True):
        text = re.sub(r"(?<!\w)" + re.escape(w) + r"(?!\w)", "_", text, flags=re.I)
    return text


INTENT_TEXT = re.compile(
    r"(#?\bopen\s*to\s*work\b|\bopen to (new )?(opportunit\w+|roles?|offers?|positions?|jobs?|a move|new challenges)"
    r"|\b(seeking|exploring|considering|pursuing) (a )?(new )?(roles?|opportunit\w+|positions?|jobs?|challenges?)"
    r"|\bavailable (for (hire|work|new \w+)|immediately)|\bactively (looking|searching|interviewing)"
    r"|\blooking for (a )?(new )?(role|job|position|opportunit\w+|challenge)"
    r"|\bjob[- ]?(hunting|seeking|search)|\bon the (job )?market\b|\bwants? to (leave|move)|\bready for (a|the) next (role|step|move|challenge)"
    r"|\b(unhappy|restless|frustrated) (at|with|in)\b|\bflight risk\b|\blikely to move\b|\bpoachable\b"
    r"|\b(his|her|their|my|the) next (challenge|role|chapter|adventure|opportunity|move)\b|\bnext (chapter|adventure)\b"
    r"|\b(recently |just )?(laid off|let go|made redundant)\b|\blayoffs? (hit|affected)\b"
    r"|\b(thinking|thought) (about|of) (leaving|moving|a change)\b|\b(planning|plans|about) to (leave|quit|move)\b)",
    re.I,
)
SUFFIXES = {"inc", "incorporated", "ltd", "limited", "llc", "llp", "plc", "gmbh", "ag", "sa", "sas",
            "sarl", "bv", "nv", "co", "corp", "corporation", "company", "oy", "ab", "as", "srl",
            "spa", "pty", "kk", "the"}
PEDIGREE = re.compile(r"\b(school|university|college|ivy|stanford|harvard|mit|oxford|cambridge|faang|big tech|ex-google|ex-meta|pedigree|prestig\w+)\b", re.I)
MIN_EVIDENCE, MAX_EVIDENCE = 2, 4  # persona: "two to four lines of evidence"


def load_json(p):
    try:
        data = json.loads(Path(p).expanduser().read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"error: cannot read {p}: {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(data, list):
        print("error: cards file must be a JSON list", file=sys.stderr)
        sys.exit(2)
    return data


def load_links(p):
    """{url: [(name, status, name_found), ...]}; one row per person per url."""
    try:
        with Path(p).expanduser().open(encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            reader.fieldnames = [(f or "").strip().lower() for f in (reader.fieldnames or [])]
            rows = list(reader)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: cannot read links file {p}: {exc}", file=sys.stderr)
        sys.exit(2)
    if rows and "url" not in rows[0]:
        print(f"error: links file {p} has no 'url' column (header: url,name,status,name_found,checked_on)", file=sys.stderr)
        sys.exit(2)
    if rows and "name" not in rows[0]:
        print(f"WARN  links file {p} has no 'name' column: no evidence line can be tied to a person, so none "
              "is verified. Add the column, one row per person per URL (templates/links.csv)")
    links = {}
    for r in rows:
        url = (r.get("url") or "").strip()
        if url:
            links.setdefault(url, []).append(((r.get("name") or "").strip(), (r.get("status") or "").strip().lower(),
                                              (r.get("name_found") or "").strip().lower()))
    return links


def same_person(a, b):
    """True when two written names are the same person by dedupe's folding."""
    if not a or not b:
        return False
    if name_tokens(a) == name_tokens(b):
        return True
    if norm_name(a) == norm_name(b) and norm_name(a)[1]:
        return True
    ta = {x for x in name_tokens(a) if len(x) > 1}
    tb = {x for x in name_tokens(b) if len(x) > 1}
    return len(ta) >= 2 and ta == tb  # initials and word order ignored; an extra surname is not the same person


GH_URL = re.compile(r"^https?://(www\.)?github\.com/([A-Za-z0-9-]+)(/|$)", re.I)


def link_for(links, url, card):
    """(status, name_found, why) for this url as checked for this card's person."""
    url = (url or "").strip()
    rows = links.get(url, [])
    if not rows:
        return "", "", "not in links.csv"
    name = card.get("name", "")
    mine = [r for r in rows if same_person(r[0], name)]
    for _, status, found in mine:
        if status == "ok" and found == "yes":
            return "ok", "yes", ""
    login = str(card.get("github") or "").strip().lstrip("@").lower()
    m = GH_URL.match(url)
    others = [r for r in rows if r[0] and not same_person(r[0], name)]
    if login and m and m.group(2).lower() == login and not others and any(r[1] == "ok" for r in rows):
        return "ok", "yes", ""
    if mine:
        return mine[0][1], mine[0][2], "checked for this person but not ok/yes"
    if all(r[1] == "blocked" for r in rows):
        return "blocked", "no", ""
    others = sorted({r[0] for r in rows if r[0]})
    return "", "", ("checked only for " + ", ".join(others)) if others else "no name on its links.csv row"


def must_ids(p):
    """Ids an evidence line may cite: must-haves (M1..) and benchmark traits
    (B1.., under '## Benchmark'), so a 'find people like this hire' card counts."""
    try:
        text = Path(p).expanduser().read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: cannot read scorecard {p}: {exc}", file=sys.stderr)
        sys.exit(2)
    return set(re.findall(r"^- ([MB]\d+):", text, re.M))


def norm_company(c):
    c = unicodedata.normalize("NFKD", c or "")
    c = "".join(ch for ch in c if not unicodedata.combining(ch)).lower().replace("&", " and ")
    return " ".join(w for w in re.sub(r"[^\w\s]", " ", c).split() if w not in SUFFIXES)


def off_limits(companies_path, scorecard_path):
    p = Path(companies_path).expanduser() if companies_path else None
    if p is None and scorecard_path:
        cand = Path(scorecard_path).expanduser().parent / "target-companies.csv"
        p = cand if cand.exists() else None
    if p is None:
        return set(), None
    try:
        with p.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
    except OSError as exc:
        print(f"error: cannot read companies file {p}: {exc}", file=sys.stderr)
        sys.exit(2)
    return {norm_company(r.get("company", "")) for r in rows
            if re.search(r"off[- ]?limits?", r.get("boundary", "") or "", re.I) and r.get("company")}, p


def strings(obj):
    """Every string value on the card, one per line (urls skipped), so a
    pattern anchored with $ sees the end of a field."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k != "url":
                yield from strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v)
    elif isinstance(obj, str):
        yield obj


def arg(args, flag):
    if flag in args:
        i = args.index(flag)
        if i + 1 < len(args):
            return args[i + 1]
    return None


def main(argv):
    args = argv[1:]
    if not args or args[0].startswith("-") or not arg(args, "--links"):
        print(__doc__, file=sys.stderr)
        return 2
    cards = load_json(args[0])
    links = load_links(arg(args, "--links"))
    ids = must_ids(arg(args, "--scorecard")) if arg(args, "--scorecard") else None
    out = Path(arg(args, "--out") or "ready.json")
    blocked_cos, cos_file = off_limits(arg(args, "--companies"), arg(args, "--scorecard"))
    if cos_file is None:
        print("WARN  no target-companies.csv found; off-limits companies not checked (pass --companies)")
    ready, dropped, unverifiable, off = [], 0, [], 0
    for card in cards:
        who = f"{card.get('name', '?')} ({card.get('company', '?')})"
        if norm_company(card.get("company", "")) in blocked_cos:
            off += 1
            dropped += 1
            print(f"DROP  {who}: company is off limits in the scorecard's boundaries")
            continue
        problems = []
        bad_keys = [k for k in card if PROTECTED_KEYS.match(k)]
        if bad_keys:
            problems.append(f"protected field(s) {bad_keys}")
        text = "\n".join(strings({k: v for k, v in card.items()
                                  if k not in ("name", "company", "search_id", "channel", "location_as_stated")}))
        masked = mask_own_name(text, card)
        loc = mask_own_name("\n".join(strings(card.get("location_as_stated", ""))), card)
        for i, rx in enumerate(PROTECTED_TEXT):
            m = re.search(rx, masked, re.I | re.M) or (None if i in PLACE_SKIP else re.search(rx, loc, re.I | re.M))
            if m:
                problems.append(f"protected wording '{m.group(0)}'")
        text = text + "\n" + "\n".join(strings(card.get("location_as_stated", "")))
        nm = card.get("next_move")
        if INTENT_TEXT.search(text):
            if not (isinstance(nm, dict) and nm.get("quote") and link_for(links, nm.get("url", ""), card)[0] == "ok"):
                problems.append("claims they want a move without a quoted, verified public statement")
        if card.get("tier") == "unranked":
            problems.append("tier 'unranked' (a sub-agent card): give it a tier and a one-line reason before the gate (step 6), then rerun")
        elif card.get("tier") not in TIERS:
            problems.append(f"tier must be one of {TIERS}")
        reason = card.get("reason", "")
        if not reason:
            problems.append("no one-line reason for the tier")
        elif PEDIGREE.search(reason):
            problems.append(f"reason rests on pedigree ('{PEDIGREE.search(reason).group(0)}'); rank on evidence against the bar only")
        if problems:
            dropped += 1
            print(f"ERROR dropped {who}: " + "; ".join(problems))
            continue
        verified, blocked_only, unknown_ids = [], True, []
        for ev in card.get("evidence", []):
            status, found, why = link_for(links, ev.get("url"), card)
            if why.startswith("checked only for") or why.startswith("no name"):
                print(f"WARN  {who}: {ev.get('url')} {why}, not for this person; line removed "
                      "(add a links.csv row for this name only if the page names them)")
            if status == "ok" and found == "yes":
                if ids is not None and ev.get("must_have") not in ids:
                    print(f"WARN  {who}: evidence cites {ev.get('must_have')!r}, not an M- or B-id on the scorecard; line removed")
                    unknown_ids.append(str(ev.get("must_have")))
                    continue
                verified.append(ev)
            elif status != "blocked":
                blocked_only = False
        if not verified:
            dropped += 1
            if unknown_ids:
                print(f"DROP  {who}: its verified lines cite ids not on the scorecard ({', '.join(sorted(set(unknown_ids)))}); "
                      "fix the ids (M- or B-ids from the scorecard) and rerun")
            elif card.get("evidence") and blocked_only:
                unverifiable.append(who)
                print(f"DROP  {who}: links behind a login/403 wall; could not verify (ask for an export or another public link)")
            else:
                print(f"DROP  {who}: no verified evidence link (no link, no card)")
            continue
        removed = len(card.get("evidence", [])) - len(verified)
        if removed:
            print(f"WARN  {who}: {removed} evidence line(s) removed (link not verified)")
        if len(verified) < MIN_EVIDENCE:
            print(f"WARN  {who}: only {len(verified)} verified evidence line; thin card")
            card["thin"] = "thin, 1 line"  # shown only with this label, never as strong fit
            if card.get("tier") == "strong":
                card["tier"] = "worth-a-look"
                print(f"WARN  {who}: a thin card is never 'strong'; tier set to worth-a-look")
        if len(verified) > MAX_EVIDENCE:
            print(f"WARN  {who}: {len(verified)} lines; keeping the first {MAX_EVIDENCE}")
            verified = verified[:MAX_EVIDENCE]
        if nm and not (isinstance(nm, dict) and link_for(links, nm.get("url", ""), card)[0] == "ok"):
            card["next_move"] = None
            print(f"WARN  {who}: next-move statement not verified; set to 'nothing said publicly'")
        card["evidence"] = verified
        ready.append(card)
    ready.sort(key=lambda c: (TIERS.index(c["tier"]), -len({e.get("must_have") for e in c["evidence"]})))
    out.write_text(json.dumps(ready, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"summary: {len(ready)} ready, {dropped} dropped ({len(unverifiable)} could not verify, {off} off limits); written to {out}")
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
