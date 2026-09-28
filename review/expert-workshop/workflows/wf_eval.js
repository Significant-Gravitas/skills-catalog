export const meta = {
  name: 'skill-eval-shard',
  description: 'Rubric + scenario evals for one shard of expert skill packages',
  phases: [{ title: 'Evaluate', detail: 'rubric + scenario evals per skill package' }],
}
const REPO = '/home/user/skills-catalog'
const SC = '/tmp/claude-0/-home-user/d376d93a-ebdc-5dd0-8a86-e43ebeea7e9d/scratchpad'
const WS = SC + '/ws'
const GROUP = { o: 'original', n: 'nick', t: 'toran' }
const W = { trigger: 10, procedure: 20, output: 15, expertise: 20, guardrails: 15, platform_fit: 10, efficiency: 10 }

function parseUnit(u) {
  const i = u.indexOf(':')
  const pre = u.slice(0, i), slug = u.slice(i + 1)
  if (GROUP[pre]) return { id: slug, slug, group: GROUP[pre], path: REPO + '/skills/' + slug }
  return { id: pre + ':' + slug, slug, group: 'pr', pr: Number(pre), path: SC + '/pr' + pre + '/skills/' + slug, main: REPO + '/skills/' + slug }
}
const idGroup = {}
for (const b of args.b) for (const u of b) { const p = parseUnit(u); idGroup[p.id] = p.group === 'pr' ? 'pr#' + p.pr : p.group }

const S = { type: 'string' }
const SA = { type: 'array', items: { type: 'string' } }
const SCORE = { type: 'integer', minimum: 1, maximum: 5 }
const SEV = { type: 'string', enum: ['blocker', 'major', 'minor'] }
const EVAL_ITEM = {
  type: 'object',
  properties: {
    id: S, summary: S, job: S,
    scores: { type: 'object', properties: { trigger: SCORE, procedure: SCORE, output: SCORE, expertise: SCORE, guardrails: SCORE, platform_fit: SCORE, efficiency: SCORE }, required: ['trigger', 'procedure', 'output', 'expertise', 'guardrails', 'platform_fit', 'efficiency'] },
    verdict: { type: 'string', enum: ['ship', 'fix', 'rewrite', 'drop'] },
    verdict_reason: S,
    scenarios: { type: 'array', items: { type: 'object', properties: { kind: { type: 'string', enum: ['typical', 'hard'] }, prompt: S, outcome: { type: 'string', enum: ['pass', 'partial', 'fail'] }, why: S }, required: ['kind', 'prompt', 'outcome', 'why'] } },
    strengths: SA,
    issues: { type: 'array', items: { type: 'object', properties: { severity: SEV, section: S, quote: S, problem: S, fix: S }, required: ['severity', 'section', 'quote', 'problem', 'fix'] } },
    missing: SA,
    delta: { type: 'object', properties: { verdict: { type: 'string', enum: ['improves', 'mixed', 'regresses', 'n/a'] }, better: SA, worse: SA }, required: ['verdict', 'better', 'worse'] },
  },
  required: ['id', 'summary', 'job', 'scores', 'verdict', 'verdict_reason', 'scenarios', 'strengths', 'issues', 'missing', 'delta'],
}
const EVAL_SCHEMA = { type: 'object', properties: { evals: { type: 'array', items: EVAL_ITEM } }, required: ['evals'] }

function evalPrompt(units) {
  const list = units.map(u => u.group === 'pr'
    ? '- id "' + u.id + '" — REBUILD in open PR #' + u.pr + ': package ' + u.path + '/ (main version for delta: ' + u.main + '/)'
    : '- id "' + u.id + '" — group ' + u.group.toUpperCase() + ': package ' + u.path + '/').join('\n')
  return [
    'You are a senior reviewer grading AutoGPT expert skills so a human can resolve duplicates and decide what ships. Be exacting and evidence-based.',
    '',
    'Read first: ' + WS + '/platform_brief.md (how skills load, which tools exist, what the three origin groups are). For expert context, find each skill\'s expert(s) in ' + WS + '/catalog_index.md and read the persona in ' + REPO + '/experts/<key>.yml when it matters.',
    '',
    'Grade each skill package below. For each: read SKILL.md in full, then open every supporting file enough to judge it (references, templates, scripts, examples, checklists, evals). Read scripts\' code; never modify any package.',
    list,
    '',
    'For PR rebuild variants (ids like "14:slug"), also read the current main version and fill `delta` (improves / mixed / regresses, with concrete better/worse points). For every other id set delta.verdict to "n/a" with empty lists.',
    '',
    'Rubric — integer 1-5 each (1 broken/absent, 2 weak, 3 adequate, 4 strong, 5 best-in-class a senior practitioner would adopt unchanged). Do not reward length: a short, sharp skill can earn 4s; a long one full of filler loses efficiency.',
    '- trigger: the description/triggers make it obvious when to load it, and it is distinct from the same expert\'s other skills.',
    '- procedure: ordered, followable steps with decision points; inputs named up front.',
    '- output: a defined deliverable (format, sections, template) the user can reuse.',
    '- expertise: senior-practitioner depth, correct frameworks, current practice; a hiring manager for this role would recognise it as the job done well.',
    '- guardrails: drafts before external side effects, approval gates, no invented numbers or facts, privacy/legal/regulatory limits, clear escalation.',
    '- platform_fit: works in AutoGPT\'s harness per the brief (tools exist, graceful fallback, no Claude-Code-only constructs, no links to files the package does not ship).',
    '- efficiency: concise, progressive disclosure into references, no filler.',
    '',
    'Scenario probes: write two realistic requests a user of this expert would send that should load this skill — one "typical", one "hard" (messy or partial data, a missing integration, conflicting constraints, or a boundary case). For each, trace what the skill tells the model to do and judge whether a capable model following it would produce a senior-quality result: pass / partial / fail, and say exactly why (cite the step or the gap).',
    '',
    'Issues: up to 8, most severe first. `quote` must be copied verbatim from SKILL.md — one contiguous span from a single line, at most 160 characters, without leading markdown markers such as "- ", "1. " or "## " — so a review UI can highlight it. For an absence, use "" and put in `section` the heading where it belongs. `section` is the nearest heading above the quote.',
    'Verdict: ship (use as is), fix (targeted edits), rewrite (keep intent, redo substance), drop (redundant or unfit). `job` is the job-to-be-done in at most 8 words, phrased so duplicates across groups get the same wording (e.g. "reconcile bank statement to ledger"). `summary` is one sentence on what the skill actually does. `missing` lists what a senior practitioner would expect that is absent.',
    '',
    'Return exactly one entry per id above, with the id copied exactly.',
  ].join('\n')
}


phase('Evaluate')
log('Shard ' + args.shard + ': ' + args.b.length + ' batches')
const res = await parallel(args.b.map(batch => async () => {
  const units = batch.map(parseUnit)
  const label = 'eval:' + units.map(u => u.id).join(',').slice(0, 60)
  let r = await agent(evalPrompt(units), { label, phase: 'Evaluate', schema: EVAL_SCHEMA })
  let got = (r && r.evals) || []
  const want = new Set(units.map(u => u.id))
  const missing = units.filter(u => !got.some(e => e.id === u.id))
  if (missing.length) {
    const r2 = await agent(evalPrompt(missing), { label: 'eval-retry:' + missing.map(u => u.id).join(',').slice(0, 50), phase: 'Evaluate', schema: EVAL_SCHEMA })
    got = got.concat(((r2 && r2.evals) || []).filter(e => want.has(e.id)))
  }
  return got.filter(e => want.has(e.id))
}))
const evals = res.filter(Boolean).flat()
log('Shard ' + args.shard + ' done: ' + evals.length + ' evals')
return { shard: args.shard, count: evals.length, ids: evals.map(e => e.id) }
