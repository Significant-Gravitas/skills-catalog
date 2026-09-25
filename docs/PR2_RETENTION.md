# Retain the skills introduced by PR 2

The user's decisions on September 25, 2026 are now recorded in this draft:

- Preserve all 167 skills added by Nick in PR 2, including their original names,
  complete file bytes and catalog metadata.
- Keep the incoming PR 4 skill that shared a name, but rename it to
  `product-assumption-testing`. Nick's `product-experiment-design` stays intact.
- Keep all purpose/use-case overlaps for release. After shipping, provide a
  report ranked from worst overlap to least, using the actual released skills
  and expert assignments. These overlaps require no further pre-release choice.
- Blanket replacement/removal still applies only to the 171 entries present
  before PR 2. This repository edit does not retire production listings.

The historical boundary is `00d9cfbf2c9c01a13dc5626a50e8f4b9c4d2d35d` (171 entries),
before PR 2 merged as `c0237abc5a3503b1bb62d3422704132176305847`.

## Both product skills are retained

| Skill | Origin and purpose |
|---|---|
| `product-experiment-design` | Nick's PR 2 skill: designs and reads out statistical experiments, with sample sizing, guardrails and scale/extend/kill decisions. |
| `product-assumption-testing` | PR 4's import of Pawel Huryn's `brainstorm-experiments-existing` from `phuryn/pm-skills`: proposes low-effort tests of assumptions, including prototypes, fake doors and technical spikes. |

Only the incoming package name, paths, attribution and matching provenance
records change. Its authored guidance and archived upstream originals remain
intact. Renaming does not make its purpose different; that overlap is accepted.

[Nick's exact source](https://github.com/Significant-Gravitas/skills-catalog/blob/c0237abc5a3503b1bb62d3422704132176305847/skills/product-experiment-design/SKILL.md)
and [the incoming skill's exact upstream source](https://github.com/phuryn/pm-skills/blob/8607e3b077817f89bf4a9b623246219734ac3be0/pm-product-discovery/skills/brainstorm-experiments-existing/SKILL.md).

## Applied protection

The draft has 241 catalog entries and 499 package files: 74 imported packages
(332 files) plus 167 retained PR 2 packages (167 files).
`provenance/pr2-carryforward.json` binds every PR 2 addition to its source Git
blob, hash, mode and catalog metadata. The checker rejects missing or changed
retained packages and any unresolved exception. The imported packages retain
their separate licence, source archive and reproducible adaptation checks.

`resume-screening` was present before PR 2. Nick modified it; he did not add it.
It remains inside the original replacement/removal scope. Its modify/delete Git
conflict is a mechanical merge item, not another keep/retire decision. Its
coverage must still be handled in the final expert mapping.

## Release boundary and follow-up

PR 4 remains a draft pending runtime compatibility, final expert assignments and
the tested production migration. Reconcile `catalog.yml` with main by preserving
all PR 2 additions and the distinct incoming names, then rerun validation; do
not take either side wholesale. The research coverage ledger is not an executable
assignment map or permission to remove Nick's retained assignments.

The rollout must preserve existing users' installed copies. It needs explicit
marketplace retirement, durable backend mappings, a tested preview and rollback,
and coordination with installations before the production switch. Ordinary seed
commands alone do not supply this process.

After successful production verification, deliver the overlap report. Rank
same-expert skills that answer the same request and produce the same output
first; follow with partial overlaps and then cross-expert similarities. Show
both names, affected experts, shared purpose, material differences and a
recommendation for later review. Use the final deployed versions and mappings;
do not treat the existing research pairings as a completed post-release report.
