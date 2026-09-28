"""Build the deterministic data model for the expert skills workshop.

Outputs (under scratchpad/ws):
  model.json            experts, skills (metadata, no bodies), groups, kits, PRs, similarity
  dossiers/<key>.md     per-expert brief for workflow agents
  eval_batches.json     batches of skill refs to evaluate
"""
import json, math, os, re, subprocess, collections
import yaml

REPO = "/home/user/skills-catalog"
S = "/tmp/claude-0/-home-user/d376d93a-ebdc-5dd0-8a86-e43ebeea7e9d/scratchpad"
WS = f"{S}/ws"
os.makedirs(f"{WS}/dossiers", exist_ok=True)

PRS = {
    13: {"branch": "harness-compat-upstream", "dir": f"{S}/pr13", "kind": "compat",
         "title": "fix(catalog): make the upstream skills' references resolve in AutoGPT's harness"},
    14: {"branch": "skills-bookkeeping", "dir": f"{S}/pr14", "kind": "rebuild", "expert": "mina",
         "title": "feat(skills): rebuild Mina's eight bookkeeping skills in place"},
    15: {"branch": "skills-recruiting-harper", "dir": f"{S}/pr15", "kind": "rebuild", "expert": "harper",
         "title": "feat(skills): rebuild Harper's eight recruiting skills in place"},
    16: {"branch": "skills-recruiting-sofia", "dir": f"{S}/pr16", "kind": "rebuild", "expert": "sofia",
         "title": "feat(skills): rebuild Sofia's ten recruiting skills in place"},
}


def git(*args):
    return subprocess.check_output(["git", "-C", REPO, *args]).decode()


def ls_skills(rev):
    return {p.split("/")[1] for p in git("ls-tree", "--name-only", rev, "skills/").split()}


orig = ls_skills("00d9cfb")
nick = ls_skills("c0237ab") - orig
toran = ls_skills("20e6922") - ls_skills("d351390")
catalog = yaml.safe_load(open(f"{REPO}/catalog.yml"))["skills"]
cat_by_slug = {c["slug"]: c for c in catalog}
release = json.load(open(f"{REPO}/release.json"))


def group_of(slug):
    return "original" if slug in orig else "nick" if slug in nick else "toran" if slug in toran else "unknown"


def split_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except Exception:
        fm = {}
    return fm, m.group(2)


def headings(body):
    return [(len(h), t.strip()) for h, t in re.findall(r"^(#{1,4})\s+(.+)$", body, re.M)]


def pkg_files(root):
    out = []
    for dp, dn, fn in os.walk(root):
        for f in fn:
            p = os.path.join(dp, f)
            out.append({"path": os.path.relpath(p, root), "bytes": os.path.getsize(p)})
    return sorted(out, key=lambda x: x["path"])


def read_skill(root, slug):
    d = f"{root}/skills/{slug}"
    text = open(f"{d}/SKILL.md", encoding="utf-8").read()
    fm, body = split_frontmatter(text)
    return {
        "slug": slug,
        "fm_name": fm.get("name"),
        "description": fm.get("description", ""),
        "triggers": fm.get("triggers", []),
        "lines": text.count("\n") + 1,
        "bytes": len(text.encode()),
        "headings": headings(body),
        "files": pkg_files(d),
        "path": d,
    }


# ---------------- experts
experts = {}
for f in sorted(os.listdir(f"{REPO}/experts")):
    e = yaml.safe_load(open(f"{REPO}/experts/{f}", encoding="utf-8"))
    experts[e["key"]] = e
name_to_key = {e["name"].lower(): k for k, e in experts.items()}

# ---------------- skills (main)
skills = {}
for slug in sorted(os.listdir(f"{REPO}/skills")):
    s = read_skill(REPO, slug)
    c = cat_by_slug.get(slug, {})
    s.update({
        "group": group_of(slug),
        "source": c.get("source"),
        "license": c.get("license"),
        "categories": c.get("categories", []),
        "required_providers": c.get("required_providers", []),
        "adapted_from": c.get("adapted_from"),
        "assigned_to": [k for k, e in experts.items() if slug in e["skills"]],
        "toran_proposed_for": [],
        "prs": [],
    })
    skills[slug] = s

# ---------------- Toran's proposed kits
src_to_slug = {}
for c in catalog:
    if c.get("source") and c["source"] != "platform":
        src_to_slug[c["source"]] = c["slug"]
cov = json.load(open(f"{REPO}/provenance/expert-coverage.json"))
toran_kits, coverage, deferred_refs = {}, {}, {}
unmapped = []
for ex in cov["experts"]:
    k = name_to_key[ex["name"].lower()]
    kit = []
    for ref in ex["kit"]:
        repo_path = ref.replace(":", "/", 1)
        slug = src_to_slug.get(repo_path)
        if slug is None:
            unmapped.append((k, ref))
            deferred_refs.setdefault(k, []).append(ref)
            continue
        kit.append(slug)
    toran_kits[k] = {"kit": kit, "deferred": [], "rationale": ex.get("kit_rationale", ""),
                     "remaining_gaps": ex.get("remaining_gaps", [])}
    coverage[k] = [
        {"slug": o.get("slug"), "disposition": o.get("disposition"), "gap": o.get("gap"),
         "replacements": o.get("replacements", []), "essential_function": o.get("essential_function")}
        for o in ex.get("original_skills", [])
    ]
for k, refs in deferred_refs.items():
    toran_kits[k]["deferred"] = refs
# per-skill provenance assignments (Toran)
for slug in toran:
    p = f"{REPO}/provenance/skills/{slug}.json"
    if os.path.exists(p):
        pj = json.load(open(p))
        for a in pj.get("assignments", []):
            k = name_to_key.get(a["expert"].lower())
            if k and slug not in toran_kits.setdefault(k, {"kit": [], "rationale": "", "remaining_gaps": []})["kit"]:
                toran_kits[k]["kit"].append(slug)
        skills[slug]["toran_status"] = pj.get("status")
        skills[slug]["toran_review"] = pj.get("review")
        skills[slug]["upstream_author"] = pj.get("author")
        skills[slug]["source_url"] = pj.get("source_url")
for k, v in toran_kits.items():
    for slug in v["kit"]:
        if k not in skills[slug]["toran_proposed_for"]:
            skills[slug]["toran_proposed_for"].append(k)

# ---------------- PRs
pr_variants = {}  # (pr, slug) -> skill record
for num, pr in PRS.items():
    changed = git("diff", "--name-only", f"origin/main...origin/{pr['branch']}").split()
    slugs = sorted({p.split("/")[1] for p in changed if p.startswith("skills/")})
    pr["slugs"] = slugs
    for slug in slugs:
        if slug in skills:
            skills[slug]["prs"].append(num)
        if pr["kind"] == "rebuild":
            v = read_skill(pr["dir"], slug)
            v["group"] = "pr"
            v["pr"] = num
            v["base_group"] = group_of(slug)
            pr_variants[f"{num}:{slug}"] = v
    if pr["kind"] == "compat":
        pr["diffs"] = {}
        for slug in slugs:
            pr["diffs"][slug] = git("diff", f"origin/main...origin/{pr['branch']}", "--", f"skills/{slug}")

# ---------------- lexical similarity (TF-IDF cosine over description + body)
TOKEN = re.compile(r"[a-z][a-z0-9\-]{2,}")
STOP = set("""the and for with that this from your you are not but can will when what which into each
then than they them their there have has had any all use used using should must may also only more most
other such who how its it's our out one two per via about after before over under was were been being
does doesn don't make makes made just like etc""".split())


def toks(text):
    return [t for t in TOKEN.findall(text.lower()) if t not in STOP]


docs = {}
for slug, s in skills.items():
    text = open(f"{s['path']}/SKILL.md", encoding="utf-8").read()
    fm, body = split_frontmatter(text)
    docs[slug] = toks((str(fm.get("description", "")) + " ") * 3 + slug.replace("-", " ") * 3 + " " + body)
df = collections.Counter()
for t in docs.values():
    df.update(set(t))
N = len(docs)
vecs = {}
for slug, t in docs.items():
    tf = collections.Counter(t)
    v = {w: (1 + math.log(c)) * math.log(N / df[w]) for w, c in tf.items() if df[w] < N * 0.5}
    norm = math.sqrt(sum(x * x for x in v.values())) or 1
    vecs[slug] = {w: x / norm for w, x in v.items()}


def cos(a, b):
    if len(a) > len(b):
        a, b = b, a
    return sum(x * b.get(w, 0) for w, x in a.items())


slugs = sorted(vecs)
sim = {}
for i, a in enumerate(slugs):
    for b in slugs[i + 1:]:
        c = cos(vecs[a], vecs[b])
        if c >= 0.18:
            sim[(a, b)] = c
neighbors = collections.defaultdict(list)
for (a, b), c in sim.items():
    neighbors[a].append((b, c))
    neighbors[b].append((a, c))
for slug in skills:
    skills[slug]["neighbors"] = [
        {"slug": b, "cos": round(c, 3)} for b, c in sorted(neighbors[slug], key=lambda x: -x[1])[:8]
    ]

# ---------------- scopes
scopes = {}
for k, e in experts.items():
    cur = list(e["skills"])
    tk = toran_kits.get(k, {"kit": []})["kit"]
    prv = [key for key, v in pr_variants.items() if v["slug"] in cur or v["slug"] in tk]
    scope = list(dict.fromkeys(cur + tk))
    scopes[k] = {"current": cur, "toran_kit": tk, "pr_variants": prv, "scope": scope}

# ---------------- write model
model = {
    "groups": {"original": sorted(orig & set(skills)), "nick": sorted(nick), "toran": sorted(toran),
               "retired": release["retirements"]},
    "experts": experts,
    "toran_kits": toran_kits,
    "coverage": coverage,
    "scopes": scopes,
    "skills": skills,
    "pr_variants": pr_variants,
    "prs": {n: {k: v for k, v in p.items() if k != "dir"} for n, p in PRS.items()},
    "unmapped_toran_refs": unmapped,
}
json.dump(model, open(f"{WS}/model.json", "w"), indent=1, default=str)

# ---------------- dossiers
GL = {"original": "ORIGINAL (pre-PR2, 171 roster)", "nick": "NICK (PR 2, 167)", "toran": "TORAN (PR 4/#7, 74 upstream)"}
for k, e in experts.items():
    sc = scopes[k]
    L = [f"# Expert dossier: {e['name']} ({k}) — {e['role']} / {e['job_title']}",
         f"Expert file: {REPO}/experts/{k}.yml  (read it in full: persona, identity, voice, boundaries, day_one, preloads, routines, skills)",
         f"Tagline: {e['tagline']}", f"Categories: {', '.join(e['categories'])}", ""]
    L.append("## Current bundled skills (live kit, in order)")
    for s in sc["current"]:
        sk = skills[s]
        L.append(f"- `{s}` [{GL[sk['group']]}] — {sk['path']}/SKILL.md ({sk['lines']} lines, {len(sk['files'])} files)"
                 + (f" — open PRs: {sk['prs']}" if sk["prs"] else ""))
    L.append("")
    L.append("## Toran's proposed kit for this expert (upstream packages, NOT currently assigned)")
    tk = toran_kits.get(k, {})
    for s in sc["toran_kit"]:
        sk = skills[s]
        L.append(f"- `{s}` [{GL[sk['group']]}] — {sk['path']}/SKILL.md — upstream: {sk.get('source')} ({sk.get('license')}), status {sk.get('toran_status')}"
                 + (f" — PR #13 compat changes" if 13 in sk["prs"] else ""))
    for ref in tk.get("deferred", []):
        L.append(f"- DEFERRED upstream (in Toran's kit but not installed in the catalog; see {REPO}/docs/DEFERRED_SKILLS.md): {ref}")
    if tk.get("rationale"):
        L.append(f"Kit rationale: {tk['rationale']}")
    for g in tk.get("remaining_gaps", []) or []:
        L.append(f"Remaining gap noted by Toran's review: {g if isinstance(g, str) else json.dumps(g)}")
    L.append("")
    if coverage.get(k):
        L.append("## Toran's coverage review of this expert's original skills")
        for o in coverage[k]:
            L.append(f"- `{o['slug']}`: {o['disposition']} — {str(o.get('gap') or '')[:300]}")
        L.append("")
    if sc["pr_variants"]:
        L.append("## Open rebuild PR versions of this expert's skills (proposed replacements, same slugs)")
        for key in sc["pr_variants"]:
            v = pr_variants[key]
            L.append(f"- PR #{v['pr']} `{v['slug']}` — {v['path']}/SKILL.md ({v['lines']} lines, {len(v['files'])} files)")
        L.append("")
    L.append("## Lexical near-neighbours (TF-IDF cosine) for in-scope skills — hints only, verify by reading")
    for s in sc["scope"]:
        nb = [f"{n['slug']}({n['cos']}, {skills[n['slug']]['group']}, experts={','.join(skills[n['slug']]['assigned_to']) or '-'})"
              for n in skills[s]["neighbors"][:5]]
        L.append(f"- `{s}` → " + ("; ".join(nb) if nb else "none ≥0.18"))
    open(f"{WS}/dossiers/{k}.md", "w").write("\n".join(L) + "\n")

# ---------------- eval batches: every active skill + every PR variant
units = []
for slug, s in skills.items():
    units.append({"id": slug, "slug": slug, "group": s["group"], "path": s["path"],
                  "experts": s["assigned_to"] or s["toran_proposed_for"], "bytes": sum(f["bytes"] for f in s["files"])})
for key, v in pr_variants.items():
    units.append({"id": key, "slug": v["slug"], "group": "pr", "pr": v["pr"], "path": v["path"],
                  "experts": [PRS[v["pr"]]["expert"]], "bytes": sum(f["bytes"] for f in v["files"])})
# group batches by expert affinity so each evaluator sees related skills; cap ~60KB of content or 6 skills
units.sort(key=lambda u: ((u["experts"] or ["~"])[0], u["group"], u["slug"]))
batches, cur, cur_bytes = [], [], 0
for u in units:
    heavy = u["bytes"] > 60000
    limit = 2 if u["group"] == "pr" or heavy else 6
    if cur and (len(cur) >= limit or cur_bytes + u["bytes"] > 120000 or
                (cur[0]["experts"] or ["~"])[0] != (u["experts"] or ["~"])[0]):
        batches.append(cur)
        cur, cur_bytes = [], 0
    cur.append(u)
    cur_bytes += u["bytes"]
if cur:
    batches.append(cur)
json.dump(batches, open(f"{WS}/eval_batches.json", "w"), indent=1)

print("skills", len(skills), "pr variants", len(pr_variants), "batches", len(batches),
      "units", len(units), "unmapped toran refs", len(unmapped))
print("groups", {g: sum(1 for s in skills.values() if s["group"] == g) for g in ["original", "nick", "toran"]})
print("similar pairs >=0.18", len(sim), ">=0.3", sum(1 for c in sim.values() if c >= .3), ">=0.45", sum(1 for c in sim.values() if c >= .45))
for k in experts:
    print(k, len(scopes[k]["current"]), len(scopes[k]["toran_kit"]), len(scopes[k]["pr_variants"]))
