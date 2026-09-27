#!/usr/bin/env python3
"""Remove identity cues and instruction-like text from extracted resumes before screening.

Usage:
  python3 scripts/redact.py <txt_dir> <red_dir> --manifest <manifest.csv> --idmap <idmap.csv>

Input:  <txt_dir>/<id>.txt from extract_resumes.py (or redact_export.py) and
        its manifest.csv (for name hints and source file names).
Output: <red_dir>/<id>.txt       the only text the screener reads
        <red_dir>/redaction_log.csv  id,category,count (never the removed values)
        <idmap.csv>              id,source_file,name_hint: FOR THE HUMAN OWNER ONLY.
                                 Save it in the durable role folder; never read it
                                 back into the screening context.
Removes: the candidate's name -> [CANDIDATE]. Name tokens come from the
        detected name line (1-6 words, particles such as "de la" or "van",
        ALL-CAPS lines, pronoun tags and credentials stripped; never a line
        holding a role word or "|"); file-name tokens are used only when no
        name line was found, and never role or business words (a file called
        "Billing_Operations_Lead.txt" names no one). A name the owner typed
        into the name_hint column of <idmap.csv> is used on a re-run for a
        record with no detected name line. Each part of a hyphenated or
        apostrophe name is a token too. Tokens match as written, ALL CAPS or
        Title Case, with and without accents ("JOHNSON" -> "Johnson",
        "García" -> "Garcia", "Nguyễn" -> "Nguyen", "Dvořák" -> "Dvorak";
        every Latin accented letter, built from unicodedata), never
        lowercase, so "billing" in the work history is never a name.
        Header words ("BIO-DATA", "Personal Details", "About Me") are never
        the name; a "Name: ..." line is read as the name. A WARN is printed (without the
        name) when a name token also appears more than twice in the body;
        emails; phone numbers (9-15 digits); personal social-profile URLs
        (LinkedIn, Facebook, Instagram, X/Twitter, TikTok); the handle inside
        GitHub/GitLab URLs (the repo path stays as evidence); street addresses,
        "City, ST 12345" (a real US state code or name) anywhere; in the
        contact block also "ST 12345" and a ZIP after a place word
        ("Springfield 62704"); never a number followed by a count noun
        ("AP 15000 invoices", "NY 10000 business accounts" stay); UK
        postcodes; and "City, ST" in the contact block (never a part holding
        a role word: "Head of Billing, Stripe" stays);
        lines labelled name, full name, father's/mother's/spouse's name,
        caste, blood group, date of birth, age, gender, sex, marital status,
        nationality, citizenship, religion, place of birth, children,
        dependants, health, height, weight, photo; pronoun tags and honorifics;
        years on education lines and in the Education section (graduation
        years) -> [YEAR]; school and university names in the Education
        section (any heading starting Education, Academic or
        Qualifications, such as "EDUCATION & CERTIFICATIONS"), on a line
        starting "Education:", or on any line naming a degree (English names and
        Universidad, Université, Universität, Hochschule, Instituto, Colegio
        and similar), including a single capitalised name next to a year
        ("Stanford (2005)", ", Stanford, 2005") -> [INSTITUTION] (prestige is
        never evidence); place names in the contact line and "City, ST 12345"
        -> [LOCATION]; affiliations that name a protected group ("Society of
        Black Accountants", "Women in Finance", "Mujeres en Finanzas"), a
        religious body (church, mosque, synagogue, temple, parish) or
        disability or adaptive sport ("wheelchair basketball") ->
        [AFFILIATION]; language
        levels such as "(native)" or "native speaker" -> [LEVEL]; the whole
        sentence or line holding instruction-like text aimed at a screener ->
        [INSTRUCTION-LIKE TEXT REMOVED].
Keeps:  employment dates and tenure (they are evidence), employer and job
        titles, portfolio links without the handle, work-authorisation lines.
Patterns are mostly English-language; regex redaction misses some cues; the screen still never infers anything
from a residual cue. Exit: 0 done, 2 bad input. Stdlib only, no network.
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import screenio  # noqa: E402

EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
PHONE = re.compile(r"(?<![\w/])\+?\(?\d[\d\s().-]{7,}\d(?![\w/])")
SOCIAL = re.compile(r"(https?://)?(www\.)?(linkedin\.com|facebook\.com|instagram\.com|twitter\.com|x\.com|tiktok\.com)/\S+", re.I)
CODEHOST = re.compile(r"((?:https?://)?(?:www\.)?(?:github\.com|gitlab\.com)/)([\w.-]+)", re.I)
STREET = re.compile(r"\b\d{1,6}\s+(?:[A-Z][\w.'-]*\s){1,4}(?:Street|St|Avenue|Ave|Road|Rd|Lane|Ln|Drive|Dr|Boulevard|Blvd|Court|Ct|Way|Place|Pl|Terrace|Close|Crescent|Square|Sq)\b\.?[^\n]*")
# Takes a preceding "City, " too, so "Austin, TX 78701" leaves no city behind.
US_STATES = ("Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|District of Columbia|Florida|"
             "Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|"
             "Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|"
             "New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|"
             "South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming|Puerto Rico")
US_CODES = ("AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|"
            "NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC|PR")
# A number followed by a count noun ("15000 invoices", "10000 business accounts") is job
# evidence, never a ZIP.
COUNT_NOUN = (r"(?!\s+(?:[A-Za-z-]+\s+)?(?:accounts?|invoices?|lines?|customers?|clients?|transactions?|users?|"
              r"tickets?|records?|employees?|rows?|payments?|orders?|entries|entry|vendors?|suppliers?|units?|"
              r"items?|calls?|claims?|members?|subscribers?|journals?|cases?|people|staff|hours?|shipments?|"
              r"contracts?|reports?|students?|patients?|products?|skus?)\b)")
ZIP_TAIL = r"(?<![\d,.$£€-])\d{5}(?:-\d{4})?\b(?![\d,%]|\.\d)" + COUNT_NOUN
PLACE = r"[A-Z][a-z][a-zA-Z.'-]*(?:\s[A-Z][a-z][a-zA-Z.'-]*)?"
# Anywhere in the text: "City, ST 12345" or "City, State 12345" (a real US state code or name).
STATE_ZIP = re.compile(r"\b" + PLACE + r",\s*(?:" + US_CODES + "|" + US_STATES + r")\b\.?\s+" + ZIP_TAIL)
# Contact block only: "ST 12345" / "State 12345" with or without a city, and a bare ZIP after
# a place word ("Springfield 62704"). Finance acronyms (AP, AR, GL) are never a state.
STATE_ZIP_HEAD = re.compile(r"(?:\b" + PLACE + r",?\s+)?\b(?:" + US_CODES + "|" + US_STATES + r")\b\.?\s+" + ZIP_TAIL)
BARE_ZIP = re.compile(r"\b" + PLACE + r",?\s+" + ZIP_TAIL)
UK_POSTCODE = re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b")
CITY_STATE = re.compile(r"\b[A-Z][a-zA-Z.'-]+(?:\s[A-Z][a-zA-Z.'-]+)?,\s*(?:[A-Z]{2}|[A-Z][a-z]+)\b")
PERSONAL_LINE = re.compile(r"^\s*((?:(?:full|candidate|applicant|father|mother|husband|wife|spouse|guardian|maiden)(?:['’]?s)?\s+)?name|spouse|caste|blood group|date of birth|d\.?o\.?b\.?|born|age|gender|sex|marital status|nationality|citizenship|religion|place of birth|children|dependants|dependents|health|height|weight|photo|pronouns)\s*[:\-].*$", re.I | re.M)
INSTITUTION_INTL = re.compile(
    r"\b(?:Universidad|Universidade|Université|Universite|Universität|Universitat|Università|Universita|"
    r"Universiteit|Uniwersytet|Hochschule|École|Ecole|Instituto|Institut|Colegio|Escuela|Faculdade|"
    r"Politecnico|Politécnico|Liceo|Lycée|Gymnasium)"
    r"(?:\s+(?:de|del|la|las|los|di|du|des|der|für|fur|do|da|dos|y|e|of|the|zu)?\s*[A-ZÀ-Þ][\w'&.-]*){0,6}")
INSTITUTION = re.compile(r"\b(?:(?:University|College|School|Institute|Academy|Polytechnic)\s+of\s+(?:the\s+)?[A-Z][\w'&.-]*(?:\s+[A-Z][\w'&.-]*){0,3}|(?:[A-Z][\w'&.-]*\s+){1,4}(?:University|College|School|Institute|Academy|Polytechnic))\b")
CONTACT_SEP = re.compile(r"\s*[|•·;]\s*")
PLACE_LIKE = re.compile(r"^[A-Z][A-Za-z'.-]+(?:[\s-][A-Z][A-Za-z'.-]+){0,2}(?:,\s*[A-Z][A-Za-z]+)?(?:\s\[LOCATION\])?$")
EDU_LABEL = re.compile(r"^\s*(education|qualifications?|academic background)\s*[:\-]", re.I)
LOCATION_LINE = re.compile(r"^\s*(address|location|based in|home)\s*[:\-]?.*$", re.I | re.M)
PRONOUNS = re.compile(r"\(\s*(she|he|they|ze|xe)\s*/\s*(her|him|them|hir|xem)(\s*/\s*\w+)?\s*\)", re.I)
HONORIFIC = re.compile(r"\b(Mr|Mrs|Ms|Miss|Mx)\.?\s+(?=[A-Z])")
EDU_WORDS = re.compile(r"\b(university|college|school|academy|institute|degree|bachelor|master|b\.?sc|b\.?a\.?|m\.?sc|mba|ph\.?d|diploma|graduat\w*|class of|gpa|a-levels?|gcse|high school)\b", re.I)
YEAR = re.compile(r"\b(19[5-9]\d|20[0-4]\d)\b")
EDU_HEADING = r"(?:education|academic|qualification)"
HEADING = re.compile(r"^\s*#*\s*(experience|work experience|employment|professional experience|"
                     r"education(?:\s*(?:&|and|/)\s*[a-z ]+)?|academic[a-z ]*|qualifications?(?:\s*(?:&|and|/)\s*[a-z ]+)?|skills|summary|profile|projects|certifications|publications|volunteering|awards|languages|interests)\s*:?\s*$", re.I)
# Role and business words (ATS file names, title lines) are never a name: see screenio.ROLE_WORDS.
ROLE_WORDS = screenio.ROLE_WORDS
STOP_TOKENS = {"cv", "resume", "résumé", "final", "updated", "update", "copy", "document", "doc", "application",
               "english", "new", "the", "and", "of", "for", "draft", "version", "pdf", "docx", "txt", "v"}


AFFILIATION_GROUP = (r"(?:Black|African|Afro|Latin[oax]s?|Hispanic|Asian|Arab|Jewish|Muslim|Christian|Catholic|Sikh|Hindu|"
                     r"Indigenous|Native American|LGBTQ?\+?|Queer|Gay|Lesbian|Trans(?:gender)?|Pride|Women|Woman|Female|"
                     r"Mothers?|Moms?|Parents?|Veterans?|Disab\w*|Deaf|Blind|Mujeres|Femmes|Latinas|Hispan[oa]s|Negr[oa]s)")
ORG_WORD = r"(?:Society|Association|Network|Club|Alliance|Council|Group|Chapter|Collective|Foundation|Circle|Forum|Guild|League|Committee|Caucus|ERG|Coalition|Union)"
CAP_OR_LINK = r"(?:[A-Z][\w'&.+-]*|of|for|in|and|the|&|de|en|des|y|et)"
AFFILIATION = re.compile(
    r"\b(?:(?:" + CAP_OR_LINK + r"[ \t]+){0,5}" + AFFILIATION_GROUP + r"(?:[ \t]+" + CAP_OR_LINK + r"){0,5}[ \t]+" + ORG_WORD +
    r"|(?:" + CAP_OR_LINK + r"[ \t]+){0,5}" + ORG_WORD + r"[ \t]+(?:of|for)[ \t]+(?:" + CAP_OR_LINK + r"[ \t]+){0,3}" + AFFILIATION_GROUP +
    r"(?:[ \t]+[A-Z][\w'&.+-]*){0,4}"
    r"|" + AFFILIATION_GROUP + r"[ \t]+(?:in|en|dans|de)[ \t]+[A-Z][\w&.+-]*(?:[ \t]+[A-Z][\w&.+-]*){0,2})\b")
# Religious bodies and disability or adaptive sport name a protected group even without a
# group word: the clause holding one becomes [AFFILIATION] (a label before it stays).
RELIGIOUS_OR_DISABILITY = re.compile(
    r"(^|[:;,|•]\s*|\band\s+)([^;:,.\n|•]*?\b(?:Church|Mosque|Synagogue|Temple(?!\s+University)|Parish|Congregation|"
    r"Gurdwara|Diocese|Bible|Ministries|Latter-day|Mormon|Islamic|Quran|Torah|Chapel|"
    r"[Ww]heelchair|[Aa]daptive (?:sports?|athletics|skiing|rowing)|Paralympic\w*|Special Olympics|"
    r"[Pp]ara-?(?:athlet\w*|sport\w*))\b[^;:,.\n|•]*)", re.M)
LANG_LEVEL = re.compile(r"\(\s*(?:native|native speaker|mother tongue|first language)\s*\)|\bnative[- ](?:speaker|level|fluency|proficiency)\b|\bmother tongue\b", re.I)
EDU_SINGLE = re.compile(r"(^|,\s|\s[-\u2013\u2014]\s|\bat\s)([A-Z][a-zA-Z&'.-]+)(?=\s*(?:\(\s*\d{4}|\([^)]*\)\s*\d{4}|,\s*\d{4}|[-\u2013]\s*\d{4}))", re.M)


def name_tokens(name_hint: str, source_file: str) -> list[str]:
    """Name tokens from the detected name line; file-name tokens only when no name line exists.
    Particles ('de', 'la', 'van') are never tokens; each part of a hyphenated or apostrophe
    name ('García-López', "O'Neil") is also a token on its own."""
    toks = set()
    for part in re.split(r"\s+", screenio.clean_name_line(name_hint or "")):
        part = part.strip(".,")
        if (len(part) < 2 or not part[0].isupper() or part.lower() in STOP_TOKENS
                or part.lower() in screenio.NAME_PARTICLES):
            continue
        toks.add(part)
        for piece in re.split(r"[-'’]", part):
            if len(piece) >= 3 and piece[0].isupper() and piece.lower() not in screenio.NAME_PARTICLES:
                toks.add(piece)
    if not toks:
        stem = Path(source_file or "").stem
        for part in re.split(r"[\s_\-.()]+", stem):
            if (len(part) >= 3 and part.isalpha() and part[0].isupper() and part.lower() not in STOP_TOKENS
                    and part.lower() not in ROLE_WORDS and not re.fullmatch(r"v\d+", part.lower())):
                toks.add(part)
    return sorted(toks, key=len, reverse=True)


def _build_variants() -> dict[str, set[str]]:
    """Every Latin letter (Latin-1 to Latin Extended Additional) grouped by its accent-free
    base letter, so 'e' also matches 'ễ' and 'S' also matches 'Ș'. Built from unicodedata,
    not a hand list."""
    out: dict[str, set[str]] = {}
    for lo, hi in ((0x00C0, 0x024F), (0x1E00, 0x1EFF)):
        for cp in range(lo, hi + 1):
            ch = chr(cp)
            base = screenio.fold(ch)
            if ch.isalpha() and len(base) == 1 and base.isascii() and base != ch:
                out.setdefault(base, set()).add(ch)
    return out


VARIANTS = _build_variants()


def _accent_insensitive(form: str) -> str:
    """Regex for a name form that matches it as written and with or without any accent
    ('Jiří' matches 'Jiří', 'Jiri' and 'Jíři'), keeping the case of each letter."""
    out = []
    for ch in unicodedata.normalize("NFC", form):
        base = screenio.fold(ch)
        base = base if len(base) == 1 else ch
        chars = {ch, base} | VARIANTS.get(base, set())
        if len(chars) == 1:
            out.append(re.escape(ch))
        else:
            out.append("[" + "".join(re.escape(c) for c in sorted(chars)) + "]")
    return "".join(out)


def name_pattern(tok: str) -> re.Pattern:
    """Whole word as written, ALL CAPS or Title Case, with and without accents: 'Close' and
    'CLOSE' match, 'close' does not; 'JOHNSON' also matches 'Johnson'; 'García' matches 'Garcia'."""
    tok = unicodedata.normalize("NFC", tok)
    forms = {tok, tok.upper(), tok.title(), tok[:1].upper() + tok[1:].lower()}
    variants = sorted({_accent_insensitive(f) for f in forms if f}, key=len, reverse=True)
    return re.compile(r"(?<![\w'’-])(?:" + "|".join(variants) + r")(?![\w-])")


def whole_sentence(pattern: re.Pattern, text: str) -> re.Pattern:
    """Widen each hit to its sentence or line, so no half-instruction survives."""
    return re.compile(r"[^.!?\n]*(?:" + pattern.pattern + r")[^.!?\n]*[.!?]?", pattern.flags)


def _has_role_word(part: str) -> bool:
    return any(w.lower().strip(".,") in ROLE_WORDS for w in part.split())


def _city_state(m: re.Match) -> str:
    """'Austin, TX' -> [LOCATION]; 'Head of Billing, Stripe' is a title and employer: kept."""
    return m.group(0) if _has_role_word(m.group(0)) else "[LOCATION]"


# Degree words: a line holding one is an education line wherever it sits, so the school on it
# goes ("Spelman College, BA Economics"). An employer line with "University" but no degree stays.
DEGREE_WORDS = re.compile(r"\b(degree|bachelor(?:'?s)?|master(?:'?s)?|b\.?sc|b\.?a\.?|m\.?sc|mba|ph\.?d|diploma|"
                          r"graduat\w*|class of|gpa|a-levels?|gcse|high school|b\.?com|m\.?com|b\.?tech|m\.?tech)(?!\w)", re.I)


def redact(text: str, hint: str, source: str, counts: dict) -> str:
    def sub(pattern, repl, s, cat):
        new, n = pattern.subn(repl, s)
        if n:
            counts[cat] = counts.get(cat, 0) + n
        return new

    # One composed form, so 'é' typed as e + combining accent still matches the name patterns.
    text = unicodedata.normalize("NFC", text)
    # Instruction-like text first, so it cannot survive inside other edits.
    for pat in screenio._INJ:
        text = sub(whole_sentence(pat, text), "[INSTRUCTION-LIKE TEXT REMOVED]", text, "instruction")
    text = sub(EMAIL, "[EMAIL]", text, "email")
    text = sub(SOCIAL, "[SOCIAL PROFILE]", text, "social_profile")
    text = sub(CODEHOST, lambda m: m.group(1) + "[handle]", text, "code_handle")
    if hint:
        hint = screenio.clean_name_line(hint)
        text = sub(re.compile(_accent_insensitive(hint), re.I), "[CANDIDATE]", text, "name")
    for tok in name_tokens(hint, source):
        pat = name_pattern(tok)
        if len(re.findall(r"\b" + re.escape(tok) + r"\b", text, re.I)) > 2:
            counts["name_token_in_body"] = counts.get("name_token_in_body", 0) + 1
        text = sub(pat, "[CANDIDATE]", text, "name")
    # A particle left in front of a redacted surname ("De La [CANDIDATE]") goes with it.
    particles = "|".join(sorted(screenio.NAME_PARTICLES, key=len, reverse=True))
    text = re.sub(r"\b(?:(?:" + particles + r")\s+)+\[CANDIDATE\]", "[CANDIDATE]", text, flags=re.I)
    text = sub(STATE_ZIP, "[LOCATION]", text, "zip")
    text = sub(PHONE, lambda m: "[PHONE]" if 9 <= len(re.sub(r"\D", "", m.group(0))) <= 15 else m.group(0), text, "phone_candidates")
    text = sub(STREET, "[ADDRESS]", text, "address")
    text = sub(UK_POSTCODE, "[LOCATION]", text, "postcode")
    text = sub(PERSONAL_LINE, "[PERSONAL DATA REMOVED]", text, "personal_line")
    text = sub(PRONOUNS, "", text, "pronouns")
    text = sub(HONORIFIC, "", text, "honorific")
    text = sub(AFFILIATION, "[AFFILIATION]", text, "affiliation")
    text = sub(RELIGIOUS_OR_DISABILITY, lambda m: m.group(1) + "[AFFILIATION]", text, "affiliation")
    text = sub(LANG_LEVEL, "[LEVEL]", text, "language_level")

    lines = text.splitlines()
    out, in_edu, header_zone = [], False, True
    for i, line in enumerate(lines):
        h = HEADING.match(line)
        if h:
            header_zone = False
            in_edu = bool(re.match(EDU_HEADING, h.group(1), re.I))
        elif re.match(r"^\s*[-*•●▪]\s", line) or EDU_LABEL.match(line):
            header_zone = False  # a bullet or an inline "Education:" ends the contact block
        if header_zone and i < 8:
            nz = 0
            for zp in (STATE_ZIP_HEAD, BARE_ZIP):
                line, k = zp.subn("[LOCATION]", line)
                nz += k
            if nz:
                counts["zip"] = counts.get("zip", 0) + nz
        if header_zone and i < 8:
            if PERSONAL_LINE.match(line) or re.search(r"\[PERSONAL DATA REMOVED\]", line):
                pass
            elif LOCATION_LINE.match(line):
                line = "[LOCATION REMOVED]"
                counts["location_line"] = counts.get("location_line", 0) + 1
            else:
                before = line.count("[LOCATION]")
                line = CITY_STATE.sub(_city_state, line)
                n = line.count("[LOCATION]") - before
                # Split keeping the separators, so an evidence line keeps its exact text.
                pieces = re.split(r"(" + CONTACT_SEP.pattern + r")", line)
                parts = pieces[0::2]
                if len(parts) > 1 and any(p.strip().startswith("[") for p in parts):
                    for k in range(0, len(pieces), 2):
                        p = pieces[k]
                        if PLACE_LIKE.match(p.strip()) and not _has_role_word(p) and p.strip() != "[LOCATION]":
                            pieces[k] = "[LOCATION]"
                            n += 1
                    line = "".join(pieces)
                if n:
                    counts["location"] = counts.get("location", 0) + n
        edu_line = in_edu or bool(EDU_LABEL.match(line)) or bool(DEGREE_WORDS.search(line))
        if edu_line:
            line, n = INSTITUTION.subn("[INSTITUTION]", line)
            line, n2 = INSTITUTION_INTL.subn("[INSTITUTION]", line)
            n += n2
            singles = [0]

            def _single(m: re.Match) -> str:
                if EDU_WORDS.fullmatch(m.group(2)):
                    return m.group(0)
                singles[0] += 1
                return m.group(1) + "[INSTITUTION]"
            line = EDU_SINGLE.sub(_single, line)
            n += singles[0]
            if n:
                counts["institution"] = counts.get("institution", 0) + n
        if (edu_line or EDU_WORDS.search(line)) and YEAR.search(line):
            line, n = YEAR.subn("[YEAR]", line)
            counts["education_year"] = counts.get("education_year", 0) + n
        out.append(line)
    return "\n".join(out).strip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("txt_dir")
    ap.add_argument("red_dir")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--idmap", required=True)
    args = ap.parse_args()

    try:
        manifest, fields = screenio.read_csv(args.manifest)
    except (OSError, UnicodeDecodeError) as exc:
        print(f"error: cannot read manifest {args.manifest}: {exc}", file=sys.stderr)
        return 2
    txt_dir, red_dir = Path(args.txt_dir).expanduser(), Path(args.red_dir).expanduser()
    red_dir.mkdir(parents=True, exist_ok=True)
    # A name the owner typed into idmap.csv (for a record with no detected name line) is used
    # on a re-run; it is read here only, never printed.
    owner_names: dict[str, str] = {}
    if Path(args.idmap).expanduser().is_file():
        try:
            prev, _ = screenio.read_csv(Path(args.idmap).expanduser())
            owner_names = {r.get("id", ""): (r.get("name_hint") or "").strip() for r in prev}
        except (OSError, UnicodeDecodeError, KeyError):
            owner_names = {}
    log, idmap, done = [], [], 0
    for row in manifest:
        cid = row["id"]
        if not (row.get("name_hint") or "").strip() and owner_names.get(cid):
            row["name_hint"] = owner_names[cid]
        idmap.append({"id": cid, "source_file": row.get("source_file", ""), "name_hint": row.get("name_hint", "")})
        src = txt_dir / f"{cid}.txt"
        if row.get("parse_status") not in ("ok", "low_text") or not src.is_file():
            continue
        counts: dict[str, int] = {}
        red = redact(src.read_text(encoding="utf-8"), row.get("name_hint", ""), row.get("source_file", ""), counts)
        (red_dir / f"{cid}.txt").write_text(red, encoding="utf-8")
        counts.pop("phone_candidates", None)
        if counts.pop("name_token_in_body", 0):
            print(f"WARN {cid}: a name token also appears more than twice in the text; the owner should check with the id map that no job evidence was redacted as a name")
        phones = red.count("[PHONE]")
        if phones:
            counts["phone"] = phones
        for cat, n in sorted(counts.items()):
            log.append({"id": cid, "category": cat, "count": n})
        done += 1
    screenio.write_csv(red_dir / "redaction_log.csv", log, ["id", "category", "count"])
    screenio.write_csv(args.idmap, idmap, ["id", "source_file", "name_hint"])
    no_name = [r["id"] for r in manifest if r.get("parse_status") in ("ok", "low_text") and not r.get("name_hint")]
    print(f"redacted {done} record(s) into {red_dir}; log: redaction_log.csv; id map (owner only): {args.idmap}")
    if no_name:
        print(f"needs a look (no name line detected): {', '.join(no_name)}. Do not screen these yet: ask the owner "
              "to type the name into the name_hint column of the id map for each, then re-run this command")
    return 0


if __name__ == "__main__":
    sys.exit(main())
