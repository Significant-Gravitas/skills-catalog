# Expert skill workshop

A review workspace for resolving every expert's skills across the three groups that
share the catalog, treated like a merge conflict:

- **Original**: the 171 roster skills present before PR 2 (`00d9cfb`), of which 164 are
  still active.
- **Nick · PR 2**: the 167 skills added in PR 2 (`c0237ab`).
- **Toran · 74**: the upstream packages added in #7 (selected in #4). None of them is
  assigned to an expert today. Their proposed kits come from
  `provenance/expert-coverage.json` and `provenance/skills/*.json`.
- **Open PRs**: the rebuilds in #14 (Mina), #15 (Harper) and #16 (Sofia), and the
  harness reference fixes for the upstream packages in #13.

The page is a private Artifact. Each overlap opens in a three-way merge editor: source A on the left, the editable result in the middle, source B on the right, aligned section by section, with take A, take B, A then B and B then A per section:
https://claude.ai/artifact/Eh5JaRFXb3YmzcnGKheSG7

## What is in it

| Folder | Contents |
| --- | --- |
| `page/index.html` | The workshop page. It loads `data/index.json` and `data/x/<expert>.json`, published alongside it. |
| `results/review.json` | The qualitative review of every skill version (what it does, strengths, issues with fixes, gaps, scenario walk-throughs), each expert's verified merge proposal with the verifier's critique, recommendations, the roster-level review, and the merged SKILL.md drafts. It carries no numeric scores or grades. |
| `tools/` | `build_model.py` (groups, kits, scopes, TF-IDF near-neighbours, dossiers, review batches), `collect.py` (merges workflow journals into one results file), `make_expert_args.py` and `make_roster_args.py` (workflow inputs), `build_site.py` (the published data files and the score-free `review.json`). |
| `workflows/` | The Workflow scripts (`wf_eval.js`, `wf_expert.js`, `wf_roster.js`, `wf_draft.js`, `wf_scrub.js`) and `platform_brief.md`, which every agent read before judging platform fit. |

The scripts hard-code the scratchpad paths of the session that produced them. Point
`S`/`WS` at a working folder, and point the PR worktrees at checkouts of the PR
branches, before re-running them.

## How the results were produced

1. **Review.** Each skill version was read against a rubric covering trigger, procedure,
   output, expertise, guardrails, platform fit and efficiency, with one typical and one
   hard scenario walk-through. The review records what the skill does, its strengths, up
   to 8 issues with verbatim quotes and fixes, what a senior practitioner would miss,
   and, for PR rebuilds, what got better or worse than main. Internal scores were used
   only to guide the merge agents; they are not published here or on the page. The
   upstream packages were read on `main`, before #13's reference fixes, and the merge
   agents were told to discount those specific issues.
2. **Merge.** Per expert, one agent clustered the in-scope skills by job-to-be-done
   across the groups. For each cluster it chose a base, listed grafts (source heading
   and content), listed what to leave out, and wrote the merged skill's name and
   description. It then proposed an ordered kit, flagged overlaps with other experts,
   and reviewed the expert body (identity, voice, boundaries, day one, preloads,
   routines).
3. **Verify.** A second agent tried to refute each proposal. It checked accounting,
   real overlap, capability loss, base choice against evals, graft headings,
   cross-expert claims and body quotes, then returned a corrected proposal and a
   critique list.
4. **Recommend.** A third agent proposed the missing skills for each expert. Sources
   were ranked: an existing catalog skill, then a deferred upstream package, then a
   licence-compatible open-source skill with a pinned URL, then a new skill.
5. **Roster.** One agent reviewed overlaps between whole experts, jobs that should
   share one canonical skill, missing roles, and kit sizes.
6. **Merged drafts.** For each overlap to merge, one agent wrote the merged SKILL.md
   section by section, recording where each section came from. A second agent checked it
   against the proposal and the sources, and returned a corrected draft.

## Reviewer state

Notes, choices and review status live in the Artifact's database, not in this folder.
The collections are:

- `notes`: `{expert, kind, ref, file, field, section, quote, body, type, status, reply}`
- `decisions/<expert>__<kind>__<target>`: `{choice, base, note, order, edited}`
- `merges/<expert>__<overlap>`: the merge editor's result for one overlap: `{left, right, rows[{text, origins, state, src}], fm{name, slug, description}, dismissed}`
- `status/<expert>`: the review state per expert.
- `meta/claude` and `meta/claude_<expert>`: Claude's pass summaries, shown as banners on the page.
