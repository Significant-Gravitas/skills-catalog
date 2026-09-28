"""Collect workflow agent results from every run journal into ws/results/all.json.

evals: id -> eval (with computed overall and group)
experts: key -> {merge, verified, recs}
roster: roster review
"""
import glob, json, os

S = "/tmp/claude-0/-home-user/d376d93a-ebdc-5dd0-8a86-e43ebeea7e9d/scratchpad"
WF = "/root/.claude/projects/-home-user/d376d93a-ebdc-5dd0-8a86-e43ebeea7e9d/subagents/workflows"
W = {"trigger": 10, "procedure": 20, "output": 15, "expertise": 20, "guardrails": 15, "platform_fit": 10, "efficiency": 10}
model = json.load(open(f"{S}/ws/model.json"))


def group_of(i):
    if ":" in i:
        return "pr#" + i.split(":")[0]
    s = model["skills"].get(i)
    return s["group"] if s else "?"


def overall(sc):
    return round(sum(W[k] * ((sc.get(k) or 1) - 1) / 4 for k in W))


evals, experts, roster = {}, {}, None
scrub, drafts = {}, {}
runs = sorted(glob.glob(f"{WF}/*/journal.jsonl"), key=os.path.getmtime)
for j in runs:
    labels = {}
    for line in open(j):
        try:
            e = json.loads(line)
        except Exception:
            continue
        if e.get("type") == "started":
            labels[e["agentId"]] = e.get("label", "")
        elif e.get("type") == "result":
            r = e.get("result")
            if isinstance(r, str):
                try:
                    r = json.loads(r)
                except Exception:
                    continue
            if not isinstance(r, dict):
                continue
            lab = labels.get(e["agentId"], "")
            if lab.startswith("eval"):
                for ev in r.get("evals", []):
                    ev["overall"] = overall(ev.get("scores", {}))
                    ev["group"] = group_of(ev["id"])
                    evals[ev["id"]] = ev
            elif lab.startswith("scrub:"):
                for it in r.get("items", []):
                    scrub[it["i"]] = it["text"]
            elif lab.startswith("draft:") or lab.startswith("check:"):
                fn = lab.split(":", 1)[1]
                if lab.startswith("check:") or fn not in drafts or drafts[fn].get("_stage") != "checked":
                    r["_stage"] = "checked" if lab.startswith("check:") else "draft"
                    drafts[fn] = r
            elif ":" in lab:
                kind, key = lab.split(":", 1)
                if kind in ("merge", "verify", "recommend"):
                    experts.setdefault(key, {})[{"merge": "merge", "verify": "verified", "recommend": "recs"}[kind]] = r
            elif lab == "roster":
                roster = r
            elif lab.startswith("scrub:"):
                for it in r.get("items", []):
                    scrub[it["i"]] = it["text"]
            elif lab.startswith("draft:") or lab.startswith("check:"):
                fn = lab.split(":", 1)[1]
                if lab.startswith("check:") or fn not in drafts or drafts[fn].get("_stage") != "checked":
                    r["_stage"] = "checked" if lab.startswith("check:") else "draft"
                    drafts[fn] = r

# attach deterministic accounting to verified analyses
for key, o in experts.items():
    v = o.get("verified") or o.get("merge")
    if not v:
        continue
    sc = model["scopes"][key]
    refs = sc["scope"] + sc["pr_variants"]
    seen = {}
    for c in v.get("clusters", []):
        for m in c.get("members", []):
            seen[m["ref"]] = seen.get(m["ref"], 0) + 1
    for u in v.get("unique", []):
        seen[u["ref"]] = seen.get(u["ref"], 0) + 1
    v["accounting"] = {"missing": [r for r in refs if r not in seen], "dup": [r for r, n in seen.items() if n > 1],
                       "unknown": [r for r in seen if r not in refs]}
    if "verified" not in o:
        v.setdefault("critique", [])
        v["_stage"] = "first-pass"
        o["verified"] = v
    else:
        o["verified"]["_stage"] = "verified"

all_ids = set(model["skills"]) | set(model["pr_variants"])
missing = sorted(all_ids - set(evals))
json.dump({"evals": evals, "experts": experts, "roster": roster, "noEval": missing, "scrub": scrub, "drafts": drafts},
          open(f"{S}/ws/results/all.json", "w"))
print(f"runs {len(runs)} evals {len(evals)}/{len(all_ids)} experts {len(experts)} "
      f"(verified {sum(1 for o in experts.values() if 'recs' in o)}) roster {'yes' if roster else 'no'} "
      f"scrub {len(scrub)} drafts {len(drafts)} (checked {sum(1 for d in drafts.values() if d.get('_stage') == 'checked')})")
if len(missing) < 40:
    print("missing evals:", missing)
