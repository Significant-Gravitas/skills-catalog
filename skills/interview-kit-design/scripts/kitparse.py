"""Parse a kit file in the templates/kit.md shape. Shared by check_kit.py and
build_packets.py; not run directly.

Returned structure:
    {"meta": {key: value}, "must_haves": {"M1": "text", ...},
     "slots": [{"n": 1, "title": str, "length": int|None, "interviewer": str,
                "owns": ["M1"], "clock": [(minutes, label)], "clock_raw": str,
                "questions": [{"text": str, "strong": str, "probe": str}],
                "anchors": {"M1": {"1": "...", ..., "not assessed": "..."}}}]}
"""

import re

SLOT = re.compile(r"^##\s+Slot\s+(\d+)\s*:\s*(.+?)\s*$", re.I)
H2 = re.compile(r"^##\s+(?!#)(.+?)\s*$")
H3 = re.compile(r"^###\s+(.+?)\s*$")
KV = re.compile(r"^([a-z_]+)\s*:\s*(.*?)\s*(<!--.*)?$")
MUST = re.compile(r"^\s*[-*]\s*(M\d+)\s*:\s*(.+)$")
QNUM = re.compile(r"^\s*\d+[.)]\s+(.+)$")
SUB = re.compile(r"^\s+[-*]\s*(strong( answer)?|probe)\s*:\s*(.*)$", re.I)
ANCHOR = re.compile(r"^\s*[-*]\s*([1-5]|not assessed)\s*:\s*(.+)$", re.I)
CLOCK = re.compile(r"(\d+)\s*(?:min(?:utes)?)?\s+([^,;]+)")


def strip_comments(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def parse(text):
    kit = {"meta": {}, "must_haves": {}, "slots": []}
    section = None
    sub = None
    slot = None
    anchor_id = None
    for raw in strip_comments(text).splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        m = SLOT.match(line)
        if m:
            slot = {"n": int(m.group(1)), "title": m.group(2), "length": None, "interviewer": "",
                    "owns": [], "clock": [], "clock_raw": "", "questions": [], "anchors": {}}
            kit["slots"].append(slot)
            section, sub, anchor_id = "slot", None, None
            continue
        m = H2.match(line)
        if m:
            title = m.group(1).lower()
            section = "must" if title.startswith("must") else "other"
            slot, sub = None, None
            continue
        m = H3.match(line)
        if m and slot is not None:
            title = m.group(1)
            if title.lower().startswith("question"):
                sub = "questions"
            elif title.lower().startswith("anchor"):
                sub = "anchors"
                ids = re.findall(r"M\d+", title)
                anchor_id = ids[0] if ids else (slot["owns"][0] if slot["owns"] else "?")
                slot["anchors"].setdefault(anchor_id, {})
            else:
                sub = None
            continue
        if section is None or (section == "other" and slot is None):
            m = KV.match(line.strip())
            if m and section is None:
                kit["meta"][m.group(1)] = m.group(2)
            continue
        if section == "must":
            m = MUST.match(line)
            if m:
                kit["must_haves"][m.group(1)] = m.group(2).strip()
            continue
        if slot is not None and sub is None:
            m = KV.match(line.strip())
            if m:
                k, v = m.group(1), m.group(2)
                if k == "length":
                    digits = re.findall(r"\d+", v)
                    slot["length"] = int(digits[0]) if digits else None
                elif k == "interviewer":
                    slot["interviewer"] = v
                elif k == "owns":
                    slot["owns"] = re.findall(r"M\d+", v)
                    slot["owns_raw"] = v
                elif k == "clock":
                    slot["clock_raw"] = v
                    slot["clock"] = [(int(a), b.strip()) for a, b in CLOCK.findall(v)]
            continue
        if slot is not None and sub == "questions":
            m = SUB.match(raw)
            if m and slot["questions"]:
                key = "strong" if m.group(1).lower().startswith("strong") else "probe"
                slot["questions"][-1][key] = m.group(3).strip()
                continue
            m = QNUM.match(line)
            if m:
                slot["questions"].append({"text": m.group(1).strip(), "strong": "", "probe": ""})
            continue
        if slot is not None and sub == "anchors":
            m = ANCHOR.match(line)
            if m:
                slot["anchors"][anchor_id][m.group(1).lower()] = m.group(2).strip()
    return kit
