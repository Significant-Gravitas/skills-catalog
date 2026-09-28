export const meta = {
  name: 'expert-merge-shard',
  description: 'Per expert: cluster duplicate skills into proposed merges, verify adversarially, recommend missing skills',
  phases: [
    { title: 'Merge', detail: 'cluster duplicates, propose merged kit, review expert body' },
    { title: 'Verify', detail: 'adversarial check of each merge proposal' },
    { title: 'Recommend', detail: 'missing skills per expert with sources' },
  ],
}
const REPO = '/home/user/skills-catalog'
const SC = '/tmp/claude-0/-home-user/d376d93a-ebdc-5dd0-8a86-e43ebeea7e9d/scratchpad'
const WS = SC + '/ws'
const S = { type: 'string' }
const SA = { type: 'array', items: { type: 'string' } }
const SCORE = { type: 'integer', minimum: 1, maximum: 5 }
const SEV = { type: 'string', enum: ['blocker', 'major', 'minor'] }
const ANALYSIS_PROPS = {
  summary: S,
  body_review: { type: 'object', properties: {
    summary: S, strengths: SA, kit_alignment: S,
    issues: { type: 'array', items: { type: 'object', properties: { field: S, severity: SEV, quote: S, problem: S, fix: S }, required: ['field', 'severity', 'quote', 'problem', 'fix'] } },
  }, required: ['summary', 'strengths', 'kit_alignment', 'issues'] },
  clusters: { type: 'array', items: { type: 'object', properties: {
    id: S, job: S,
    overlap: { type: 'string', enum: ['duplicate', 'heavy', 'partial', 'adjacent'] },
    recommendation: { type: 'string', enum: ['pick-one', 'merge', 'keep-separate'] },
    members: { type: 'array', items: { type: 'object', properties: { ref: S, role: { type: 'string', enum: ['base', 'graft', 'redundant', 'keep'] }, note: S }, required: ['ref', 'role', 'note'] } },
    proposed: { type: 'object', properties: {
      slug: S, name: S, description: S, base_ref: S, rationale: S, drops: SA,
      grafts: { type: 'array', items: { type: 'object', properties: { from_ref: S, section: S, what: S }, required: ['from_ref', 'section', 'what'] } },
    }, required: ['slug', 'name', 'description', 'base_ref', 'rationale', 'drops', 'grafts'] },
  }, required: ['id', 'job', 'overlap', 'recommendation', 'members', 'proposed'] } },
  unique: { type: 'array', items: { type: 'object', properties: { ref: S, keep: { type: 'boolean' }, note: S }, required: ['ref', 'keep', 'note'] } },
  cross_expert: { type: 'array', items: { type: 'object', properties: { ref: S, other_expert: S, other_ref: S, relation: { type: 'string', enum: ['duplicate', 'overlap', 'handoff'] }, suggestion: S }, required: ['ref', 'other_expert', 'other_ref', 'relation', 'suggestion'] } },
  proposed_kit: { type: 'array', items: { type: 'object', properties: { slug: S, name: S, status: { type: 'string', enum: ['keep', 'merged', 'replace-with-pr', 'add-from-toran', 'add-from-catalog', 'new'] }, from_refs: SA, note: S }, required: ['slug', 'name', 'status', 'from_refs', 'note'] } },
  dropped: { type: 'array', items: { type: 'object', properties: { ref: S, reason: S }, required: ['ref', 'reason'] } },
}
const ANALYSIS_REQ = ['summary', 'body_review', 'clusters', 'unique', 'cross_expert', 'proposed_kit', 'dropped']
const ANALYSIS_SCHEMA = { type: 'object', properties: ANALYSIS_PROPS, required: ANALYSIS_REQ }
const VERIFIED_SCHEMA = { type: 'object', properties: Object.assign({}, ANALYSIS_PROPS, {
  critique: { type: 'array', items: { type: 'object', properties: { kind: S, target: S, issue: S, fix: S, applied: { type: 'boolean' } }, required: ['kind', 'target', 'issue', 'fix', 'applied'] } },
}), required: ANALYSIS_REQ.concat(['critique']) }
const REC_SCHEMA = { type: 'object', properties: {
  notes: S,
  recommendations: { type: 'array', items: { type: 'object', properties: {
    slug: S, name: S, purpose: S, why: S,
    priority: { type: 'string', enum: ['must', 'should', 'could'] },
    source: { type: 'object', properties: { type: { type: 'string', enum: ['catalog', 'deferred', 'upstream', 'new'] }, ref: S, url: S, license: S }, required: ['type', 'ref', 'url', 'license'] },
    overlaps_with: SA, sketch: SA,
  }, required: ['slug', 'name', 'purpose', 'why', 'priority', 'source', 'overlaps_with', 'sketch'] } },
}, required: ['notes', 'recommendations'] }
function accounting(refs, a) {
  const seen = {}
  for (const c of (a.clusters || [])) for (const m of (c.members || [])) seen[m.ref] = (seen[m.ref] || 0) + 1
  for (const u of (a.unique || [])) seen[u.ref] = (seen[u.ref] || 0) + 1
  const set = new Set(refs)
  return {
    missing: refs.filter(r => !seen[r]),
    dup: Object.keys(seen).filter(r => seen[r] > 1),
    unknown: Object.keys(seen).filter(r => !set.has(r)),
  }
}

const COMMON = 'Ref format: a plain slug is the version on main; "14:slug" is that skill rebuilt in open PR #14 (likewise 15 and 16).\n'
  + 'Inputs to read: ' + WS + '/platform_brief.md; the expert dossier; the expert file; every in-scope SKILL.md (skim supporting files where it matters). ' + WS + '/catalog_index.md lists every catalog skill with owners; ' + WS + '/roster.md lists all 32 experts.'


log('Shard ' + args.shard + ': ' + args.e.map(e => e[0]).join(', '))
const expertOut = {}
await pipeline(
  args.e,
  async ([key, refs, evalText]) => {
    const prompt = [
      'You are resolving a three-way skill merge for one AutoGPT expert, the way you would resolve a merge conflict. ORIGINAL roster skills, NICK\'s PR 2 skills and TORAN\'s 74 upstream packages (plus any open rebuild-PR versions) compete to be this expert\'s kit. A human reviewer will start from your proposal and decide.',
      '',
      'Expert: ' + key + ' — dossier ' + WS + '/dossiers/' + key + '.md — expert file ' + REPO + '/experts/' + key + '.yml (read both in full).',
      COMMON,
      '',
      'Evals already produced for the in-scope refs (overall 0-100, verdict, job-to-be-done, summary, top issue):',
      evalText,
      '',
      'In-scope refs — every one must appear exactly once across clusters[].members and unique[]: ' + refs.join(', '),
      '',
      'Tasks:',
      '1. Cluster refs that do the same job-to-be-done (duplicates or heavy/partial overlaps), across groups. The main and PR versions of one slug always share a cluster. For each cluster choose a base (best eval plus best fit for this expert\'s persona and the platform) and give member roles: base, graft (content to carry over), redundant (nothing worth keeping), keep (stays as its own skill in a keep-separate cluster). In `proposed`, list grafts with the source heading and the concrete content to carry, what to drop, and the merged skill\'s slug, name and a shippable frontmatter description (at most 300 characters). recommendation: "pick-one" when one member already covers the rest, "merge" when grafts are needed, "keep-separate" when the overlap is adjacent and both jobs matter (then base_ref may be "").',
      '2. Put skills with no overlap in `unique`, saying whether each stays in the kit.',
      '3. Cross-expert: flag refs that duplicate or overlap a skill another expert owns (use the catalog index and near-neighbour hints; open the other skill before claiming). Say whether to share one canonical skill, hand off, or differentiate.',
      '4. Propose the final ordered kit, in marketplace order with getting-started first. Status per entry: keep | merged | replace-with-pr | add-from-toran | add-from-catalog | new; from_refs names the refs it comes from. List everything left out in `dropped` with the reason.',
      '5. Review the expert body (identity, voice_preferences, voice_samples, boundaries, day_one, preloads, routines): alignment with the proposed kit (routines, preloads or day_one naming skills that would be dropped or renamed; promises no skill covers), persona sharpness, boundary gaps, voice quality. `quote` must be verbatim from the YAML value, at most 160 characters; `field` names the YAML field (e.g. routines[2].prompt).',
      '6. `summary`: 3-5 sentences a reviewer reads first — what this expert\'s kit looks like across the three groups and the main merge calls.',
      'Be concrete: every claim must be checkable by opening the files.',
    ].join('\n')
    const a = await agent(prompt, { label: 'merge:' + key, phase: 'Merge', schema: ANALYSIS_SCHEMA })
    return a
  },
  async (a, [key, refs, evalText]) => {
    if (!a) return null
    const chk = accounting(refs, a)
    const prompt = [
      'Adversarially verify this merge proposal for the AutoGPT expert "' + key + '". Assume it contains mistakes; find and fix them.',
      'Inputs: dossier ' + WS + '/dossiers/' + key + '.md, expert file ' + REPO + '/experts/' + key + '.yml, and the SKILL.md files it cites.',
      COMMON,
      '',
      'Evals for the in-scope refs:',
      evalText,
      '',
      'Deterministic accounting of the proposal: refs not accounted for: ' + (chk.missing.join(', ') || 'none') + '; refs listed more than once: ' + (chk.dup.join(', ') || 'none') + '; refs not in scope: ' + (chk.unknown.join(', ') || 'none') + '.',
      'In-scope refs: ' + refs.join(', '),
      '',
      'Proposal JSON:',
      JSON.stringify(a),
      '',
      'Check, opening files rather than trusting the proposal: (1) every in-scope ref accounted for exactly once; (2) each cluster is a real overlap; (3) duplicates the analyst missed; (4) merges or drops that lose a capability nothing else in the kit covers; (5) base choices that contradict the evals without a stated reason; (6) grafts citing headings or content that do not exist in the source; (7) cross-expert claims that are wrong or missing; (8) body-review issues that are wrong or missed, including routines/preloads/day_one that reference skills the proposed kit drops or renames, and quotes that are not verbatim; (9) proposed kit order and statuses consistent with the clusters.',
      'Return the corrected full proposal in the same schema with your fixes applied, plus `critique`: one entry per change or dispute (kind, target, issue, fix, applied=true if you changed the proposal).',
    ].join('\n')
    const v = await agent(prompt, { label: 'verify:' + key, phase: 'Verify', schema: VERIFIED_SCHEMA })
    const out = v || Object.assign({}, a, { critique: [] })
    out.accounting = accounting(refs, out)
    return out
  },
  async (v, [key, refs, evalText]) => {
    if (!v) return null
    const kit = (v.proposed_kit || []).map(k => '- ' + k.slug + ' (' + k.status + ') — ' + k.name + (k.note ? ' — ' + k.note : '')).join('\n')
    const prompt = [
      'Recommend skills the AutoGPT expert "' + key + '" should have but does not, after the verified merge below. Read ' + WS + '/platform_brief.md, the dossier ' + WS + '/dossiers/' + key + '.md and the expert file ' + REPO + '/experts/' + key + '.yml first.',
      '',
      'Verified proposed kit:',
      kit,
      '',
      'Expert-body review summary: ' + (v.body_review ? v.body_review.summary + ' Alignment: ' + v.body_review.kit_alignment : ''),
      'Dropped: ' + (v.dropped || []).map(d => d.ref).join(', '),
      '',
      'Sources, in order of preference: (a) an existing catalog skill — ' + WS + '/catalog_index.md (unassigned skills and other experts\' skills both count; read the SKILL.md before recommending it); (b) a deferred upstream package — ' + REPO + '/docs/DEFERRED_SKILLS.md; (c) a public open-source skill with a redistribution-compatible licence (MIT, Apache-2.0, CC-BY-4.0) — if WebSearch/WebFetch are available via ToolSearch, find and verify one and give the exact URL; never invent a URL; (d) new, written by us.',
      'Ground each recommendation in what people in this role actually do (job postings, professional standards, common tools) and what the platform can run. Do not recommend anything the kit already covers — open the kit skills before claiming a gap. Give 3-8 recommendations ranked by impact: proposed slug, name, one-line purpose, why (evidence), priority (must/should/could), source (type, ref, url — "" when none, licence — "" when new), overlaps_with (kit slugs it touches), and a 3-6 bullet sketch of the sections it needs. `notes`: anything the reviewer should know about coverage.',
    ].join('\n')
    const r = await agent(prompt, { label: 'recommend:' + key, phase: 'Recommend', schema: REC_SCHEMA })
    expertOut[key] = { verified: v, recs: r }
    return key
  },
)

return { shard: args.shard, done: Object.keys(expertOut) }
