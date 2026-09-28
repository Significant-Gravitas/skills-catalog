"""Build balanced shard args for wf_expert.js from collected evals."""
import json, sys
ONLY = set(sys.argv[1].split(",")) if len(sys.argv) > 1 and sys.argv[1] else None
N = int(sys.argv[2]) if len(sys.argv) > 2 else 8
TAG = sys.argv[3] if len(sys.argv) > 3 else ""

S = "/tmp/claude-0/-home-user/d376d93a-ebdc-5dd0-8a86-e43ebeea7e9d/scratchpad"
model = json.load(open(f"{S}/ws/model.json"))
res = json.load(open(f"{S}/ws/results/all.json"))
evals = res["evals"]


def group(ref):
    if ":" in ref:
        return "pr#" + ref.split(":")[0]
    return model["skills"][ref]["group"]


def line(ref):
    e = evals.get(ref)
    if not e:
        return f"- {ref} [{group(ref)}] (no eval available)"
    top = f" — top issue ({e['issues'][0]['severity']}): {e['issues'][0]['problem']}" if e.get("issues") else ""
    d = e.get("delta") or {}
    delta = f" — vs main: {d['verdict']}" if d.get("verdict") not in (None, "n/a") else ""
    return f"- {ref} [{group(ref)}] {e['overall']}/100 {e['verdict']}{delta} — job: {e['job']} — {e['summary']}{top}"


items = []
for key in model["experts"]:
    if ONLY and key not in ONLY:
        continue
    sc = model["scopes"][key]
    refs = sc["scope"] + sc["pr_variants"]
    import os
    os.makedirs(f"{S}/ws/evals", exist_ok=True)
    open(f"{S}/ws/evals/{key}.md", "w").write("\n".join(line(r) for r in refs) + "\n")
    items.append((len(refs), [key, refs, f"(The eval lines are in {S}/ws/evals/{key}.md — read that file in full; one line per in-scope ref.)"]))
items.sort(key=lambda x: -x[0])
shards = [[] for _ in range(N)]
load = [0] * N
for w, it in items:
    k = load.index(min(load))
    shards[k].append(it)
    load[k] += w + 8
out = [{"shard": TAG + str(i), "e": s} for i, s in enumerate(shards) if s]
json.dump(out, open(f"{S}/ws/expert_shards.json", "w"))
for s in out:
    print(s["shard"], [e[0] for e in s["e"]], sum(len(e[1]) for e in s["e"]), len(json.dumps(s)))
