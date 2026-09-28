"""Assemble the published data files for the Expert Skill Workshop artifact.

usage: python3 build_site.py [results.json]
writes site/data/index.json and site/data/x/<key>.json
"""
import json, os, re, sys, difflib

S = "/tmp/claude-0/-home-user/d376d93a-ebdc-5dd0-8a86-e43ebeea7e9d/scratchpad"
WS = f"{S}/ws"
OUT = f"{S}/site/data"
os.makedirs(f"{OUT}/x", exist_ok=True)

model = json.load(open(f"{WS}/model.json"))
results = {}
if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
    results = json.load(open(sys.argv[1]))
import copy
results = copy.deepcopy(results)
SCORE_PAT = re.compile(r"\d{1,3}\s*/\s*100|\bevals?\s+\d{2}|\b(?:scores?|scored)\s+(?:of\s+)?\d{2}\b|\b(?:highest|lowest|best|worst)[- ]eval")


def set_path(root, path, value):
    cur = root
    for k in path[:-1]:
        cur = cur[k]
    cur[path[-1]] = value


# Rewritten strings from the scrub workflow, keyed by index into ws/scrub/index.json
if results.get("scrub") and os.path.exists(f"{WS}/scrub/index.json"):
    idx = json.load(open(f"{WS}/scrub/index.json"))
    for i, text in results["scrub"].items():
        i = int(i)
        if i < len(idx):
            try:
                set_path(results, idx[i]["path"], text)
            except (KeyError, IndexError, TypeError):
                pass


DOMAIN = r"(?!\s+(?:set|sets|harness|suite|cases?|prompts?|plan|design|framework|metrics?|criteria|rubric|results?|data|loop|pipeline|runs?|ladder|scoreboard|tooling|tools?)\b)"
REVIEW_WORDS = [
    (re.compile(r"\b(its|the|top|own|their|each|this|that|whose|an?)(\s+)eval\b" + DOMAIN, re.I), lambda m: m.group(1) + m.group(2) + "review"),
    (re.compile(r"\b(its|the|top|own|their|these|those)(\s+)evals\b" + DOMAIN, re.I), lambda m: m.group(1) + m.group(2) + "reviews"),
    (re.compile(r"\b[Ee]val(\s+)(?=(?:flags?|notes?|says|asks|requires|gaps?|contradictions?|issues?|finding|findings)\b)"), lambda m: ("Review" if m.group(0)[0] == "E" else "review") + m.group(1)),
    (re.compile(r"\b[Ee]val's\b"), lambda m: "Review's" if m.group(0)[0] == "E" else "review's"),
]


def review_words(x):
    if isinstance(x, dict):
        return {k: (v if k == "quote" else review_words(v)) for k, v in x.items()}
    if isinstance(x, list):
        return [review_words(v) for v in x]
    if isinstance(x, str):
        for pat, fn in REVIEW_WORDS:
            x = pat.sub(fn, x)
    return x


for _k, _o in results.get("experts", {}).items():
    for _part in ("verified", "recs"):
        if _o.get(_part):
            _o[_part] = review_words(_o[_part])
if results.get("roster"):
    results["roster"] = review_words(results["roster"])


def clean_eval(e):
    if not e:
        return None
    return {
        "job": e.get("job"), "summary": e.get("summary"),
        "strengths": e.get("strengths", []), "missing": e.get("missing", []),
        "issues": [{k: i.get(k) for k in ("severity", "section", "quote", "problem", "fix")} for i in e.get("issues", [])],
        "scenarios": [{k: x.get(k) for k in ("kind", "prompt", "why")} for x in e.get("scenarios", [])],
        "delta": {"better": (e.get("delta") or {}).get("better", []), "worse": (e.get("delta") or {}).get("worse", [])},
    }


evals = {k: clean_eval(v) for k, v in results.get("evals", {}).items()}
exp_out = results.get("experts", {})
roster = results.get("roster")
drafts_all = results.get("drafts", {})

TEXT_EXT = {".md", ".txt", ".csv", ".json", ".py", ".sh", ".js", ".ts", ".yml", ".yaml", ".html", ".tsv", ".sql", ".toml", ".mjs"}
MAX_FILE = 120_000


def read_text(p):
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def split_fm(text):
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    return (m.group(1), m.group(2)) if m else ("", text)


def skill_record(ref):
    if ":" in ref:
        pr, slug = ref.split(":", 1)
        v = model["pr_variants"][ref]
        base = model["skills"].get(slug, {})
        rec = dict(v)
        rec.update({"ref": ref, "group": "pr", "pr": int(pr), "base_group": v.get("base_group"),
                    "mainRef": slug, "assigned_to": base.get("assigned_to", []),
                    "toran_proposed_for": base.get("toran_proposed_for", []),
                    "source": base.get("source"), "license": base.get("license"),
                    "categories": base.get("categories", [])})
    else:
        rec = dict(model["skills"][ref])
        rec["ref"] = ref
    root = rec.pop("path")
    text = read_text(f"{root}/SKILL.md") or ""
    fm, body = split_fm(text)
    rec["frontmatter"] = fm
    rec["body"] = body
    files = []
    for f in rec.get("files", []):
        if f["path"] == "SKILL.md":
            continue
        entry = {"path": f["path"], "bytes": f["bytes"]}
        ext = os.path.splitext(f["path"])[1].lower()
        if (ext in TEXT_EXT or f["path"].endswith("LICENSE")) and f["bytes"] <= MAX_FILE:
            t = read_text(f"{root}/{f['path']}")
            if t is not None:
                entry["text"] = t
        files.append(entry)
    rec["files"] = files
    rec.pop("headings", None)
    if ":" in ref:
        main_text = read_text(f"/home/user/skills-catalog/skills/{rec['mainRef']}/SKILL.md") or ""
        rec["diff"] = "".join(difflib.unified_diff(
            main_text.splitlines(True), text.splitlines(True),
            fromfile=f"main/{rec['mainRef']}/SKILL.md", tofile=f"PR #{rec['pr']}/{rec['slug']}/SKILL.md", n=2))
    elif 13 in (rec.get("prs") or []):
        rec["pr13diff"] = model["prs"]["13"]["diffs"].get(ref) or model["prs"].get(13, {}).get("diffs", {}).get(ref)
    rec["eval"] = evals.get(ref)
    return rec


def clean_expert(e):
    keep = ["key", "name", "role", "job_title", "tagline", "avatar_url", "categories", "bio", "identity",
            "voice_preferences", "voice_samples", "boundaries", "day_one", "preloads", "routines", "skills"]
    return {k: e.get(k) for k in keep}


index = {"experts": [], "groups": {g: len(v) for g, v in model["groups"].items()},
         "prs": {n: {"title": p["title"], "kind": p["kind"], "branch": p["branch"], "slugs": p["slugs"],
                     "expert": p.get("expert")} for n, p in model["prs"].items()},
         "roster": roster, "has_results": bool(results) and len(exp_out) == len(model["experts"]) and not results.get("noEval")}

GROUPS = ["original", "nick", "toran", "pr"]
for key, e in model["experts"].items():
    sc = model["scopes"][key]
    refs = sc["scope"] + sc["pr_variants"]
    skills = {r: skill_record(r) for r in refs}
    out = exp_out.get(key) or {}
    analysis = copy.deepcopy(out.get("verified"))
    if analysis:
        analysis.pop("accounting", None) if not (analysis.get("accounting") or {}).get("missing") and not (analysis.get("accounting") or {}).get("dup") else None
    recs = out.get("recs")
    extra = {}
    wanted = set()
    if analysis:
        for c in analysis.get("cross_expert", []):
            wanted.add(c.get("other_ref", ""))
        for k in analysis.get("proposed_kit", []):
            for r in k.get("from_refs", []):
                wanted.add(r)
        for c in analysis.get("clusters", []):
            for mbr in c.get("members", []):
                wanted.add(mbr.get("ref", ""))
            for g in (c.get("proposed") or {}).get("grafts", []):
                wanted.add(g.get("from_ref", ""))
        for u in analysis.get("unique", []):
            wanted.add(u.get("ref", ""))
    drafts = {}
    for fn, dr in drafts_all.items():
        k2, cid = fn.split("__", 1)
        if k2 == key:
            drafts[cid] = dr
            for sec in dr.get("sections", []):
                for o in sec.get("origin", []):
                    wanted.add(o.get("ref", ""))
    if recs:
        for r in recs.get("recommendations", []):
            if r.get("source", {}).get("type") == "catalog":
                wanted.add(r["source"].get("ref", ""))
    for r in wanted:
        r = (r or "").strip().strip("`")
        if r and r not in skills and (r in model["skills"] or r in model["pr_variants"]):
            extra[r] = skill_record(r)
    data = {
        "expert": clean_expert(e),
        "toran": model["toran_kits"].get(key, {}),
        "coverage": model["coverage"].get(key, []),
        "scope": {"current": sc["current"], "toran_kit": sc["toran_kit"], "pr_variants": sc["pr_variants"], "refs": refs},
        "skills": skills,
        "extra": extra,
        "analysis": analysis,
        "recs": recs,
        "drafts": drafts,
    }
    json.dump(data, open(f"{OUT}/x/{key}.json", "w"), separators=(",", ":"))

    def avg(g):
        xs = [s["eval"]["overall"] for s in skills.values() if s.get("group") == g and s.get("eval")]
        return round(sum(xs) / len(xs)) if xs else None

    index["experts"].append({
        "key": key, "name": e["name"], "role": e["role"], "job_title": e["job_title"], "tagline": e["tagline"],
        "categories": e["categories"],
        "counts": {g: sum(1 for s in skills.values() if s.get("group") == g) for g in GROUPS},
        "current": len(sc["current"]),
        "proposed": len(analysis["proposed_kit"]) if analysis else None,
        "clusters": len(analysis["clusters"]) if analysis else None,
        "recs": len(recs["recommendations"]) if recs else None,
        "drafts": len(drafts),
        "summary": analysis.get("summary") if analysis else None,
        "bytes": os.path.getsize(f"{OUT}/x/{key}.json"),
    })

for n, p in index["prs"].items():
    rows = []
    for slug in p["slugs"]:
        mv = evals.get(slug)
        pv = evals.get(f"{n}:{slug}") if p["kind"] == "rebuild" else None
        sk = model["skills"].get(slug, {})
        rows.append({"slug": slug, "group": sk.get("group"), "experts": sk.get("assigned_to", []) or sk.get("toran_proposed_for", [])})
    p["rows"] = rows
json.dump(index, open(f"{OUT}/index.json", "w"), separators=(",", ":"))
tot = sum(x["bytes"] for x in index["experts"])
print("wrote", len(index["experts"]), "expert files,", round(tot / 1e6, 2), "MB total; largest",
      max(index["experts"], key=lambda x: x["bytes"])["key"], max(x["bytes"] for x in index["experts"]))


hits = []
for fn in [f"{OUT}/index.json"] + [f"{OUT}/x/{f}" for f in os.listdir(f"{OUT}/x")]:
    txt = open(fn).read()
    for k in ("\"overall\"", "\"scores\"", "\"verdict_reason\"", "\"outcome\"", "\"avg\""):
        if k in txt:
            hits.append((os.path.basename(fn), k))
    d = json.load(open(fn))
    def walk(x, path):
        if isinstance(x, dict):
            for kk, v in x.items():
                if kk in ("body", "text", "frontmatter", "diff", "pr13diff", "quote", "files", "sections"):
                    continue
                walk(v, path + [kk])
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, path + [i])
        elif isinstance(x, str) and SCORE_PAT.search(x):
            hits.append((os.path.basename(fn), "/".join(map(str, path[-4:])), SCORE_PAT.search(x).group(0), x[:90]))
    walk(d, [])
print("score leak scan:", len(hits))
for h in hits[:25]:
    print("  ", h)

# Score-free export of the review results for the repository
clean = {"evals": evals, "experts": {}, "roster": roster, "drafts": drafts_all}
for key in model["experts"]:
    o = exp_out.get(key) or {}
    v = copy.deepcopy(o.get("verified"))
    if v:
        v.pop("accounting", None)
        v.pop("_stage", None)
    clean["experts"][key] = {"proposal": v, "recommendations": o.get("recs")}
json.dump(clean, open(f"{S}/site/review_clean.json", "w"), indent=1, ensure_ascii=False)
print("wrote review_clean.json", round(os.path.getsize(f"{S}/site/review_clean.json") / 1e6, 2), "MB")
