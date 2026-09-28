"""Write per-expert verified merge summaries to ws/roster_lines.md and print the roster workflow args."""
import json

S = "/tmp/claude-0/-home-user/d376d93a-ebdc-5dd0-8a86-e43ebeea7e9d/scratchpad"
model = json.load(open(f"{S}/ws/model.json"))
res = json.load(open(f"{S}/ws/results/all.json"))
out = []
for key in model["experts"]:
    o = res["experts"].get(key) or {}
    v = o.get("verified")
    if not v:
        out.append(f"- {key}: (no analysis)")
        continue
    kit = ", ".join(k["slug"] for k in v.get("proposed_kit", []))
    cx = "; ".join(f"{c['ref']}→{c['other_expert']}:{c['other_ref']} ({c['relation']})" for c in v.get("cross_expert", []))
    recs = ", ".join(r["slug"] for r in o["recs"].get("recommendations", [])) if o.get("recs") else "(still being generated)"
    out.append(f"- {key} — {v.get('summary', '')}\n  proposed kit ({len(v.get('proposed_kit', []))}): {kit}\n  cross-expert: {cx or 'none'}\n  recommended adds: {recs or 'none'}")
open(f"{S}/ws/roster_lines.md", "w").write("\n".join(out) + "\n")
print(json.dumps({"lines": f"(Read {S}/ws/roster_lines.md in full: one entry per expert with its verified summary, proposed kit, cross-expert overlaps and recommended additions.)"}))
