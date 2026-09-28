export const meta = {
  name: 'roster-overlap-review',
  description: 'Expert-level overlaps, shared skills and roster gaps across all 32 experts',
  phases: [{ title: 'Roster', detail: 'expert-level overlaps and shared skills' }],
}
const REPO = '/home/user/skills-catalog'
const SC = '/tmp/claude-0/-home-user/d376d93a-ebdc-5dd0-8a86-e43ebeea7e9d/scratchpad'
const WS = SC + '/ws'
const S = { type: 'string' }
const SA = { type: 'array', items: { type: 'string' } }
const ROSTER_SCHEMA = { type: 'object', properties: {
  summary: S,
  expert_overlaps: { type: 'array', items: { type: 'object', properties: { experts: SA, overlap: { type: 'string', enum: ['duplicate-role', 'heavy', 'partial'] }, evidence: S, recommendation: { type: 'string', enum: ['merge-experts', 'differentiate', 'keep'] }, proposal: S }, required: ['experts', 'overlap', 'evidence', 'recommendation', 'proposal'] } },
  shared_skills: { type: 'array', items: { type: 'object', properties: { job: S, refs: SA, experts: SA, recommendation: S }, required: ['job', 'refs', 'experts', 'recommendation'] } },
  roster_gaps: { type: 'array', items: { type: 'object', properties: { role: S, why: S, candidate_skills: SA }, required: ['role', 'why', 'candidate_skills'] } },
  kit_size_flags: { type: 'array', items: { type: 'object', properties: { expert: S, issue: S }, required: ['expert', 'issue'] } },
}, required: ['summary', 'expert_overlaps', 'shared_skills', 'roster_gaps', 'kit_size_flags'] }


phase('Roster')
const roster = await agent([
  'Review the whole AutoGPT expert roster (32 experts) for overlaps at the expert level. Roster: ' + WS + '/roster.md; expert files in ' + REPO + '/experts/; catalog index ' + WS + '/catalog_index.md; platform brief ' + WS + '/platform_brief.md.',
  'Per-expert verified merge results:',
  args.lines,
  '',
  'Tasks: (1) expert pairs or groups whose roles substantially duplicate (for example two recruiters, two product managers, two support agents, several finance roles, several marketing roles) — give evidence from the expert files and kits, and recommend merge-experts, differentiate (say how: audience, company stage, depth, channel) or keep; (2) jobs that several experts each carry a different skill for, where one canonical shared skill should exist — name the refs and experts; (3) roles missing from the roster that users would expect, with candidate catalog skills; (4) kits that are too thin (under 5) or bloated and unfocused (over 25). summary: a short paragraph for the reviewer.',
].join('\n'), { label: 'roster', phase: 'Roster', schema: ROSTER_SCHEMA })
return roster
