export const meta = {
  name: 'merged-skill-drafts',
  description: 'Write the merged SKILL.md for each overlap cluster, then adversarially check and correct it',
  phases: [
    { title: 'Draft', detail: 'merged SKILL.md per cluster, section by section with origins' },
    { title: 'Check', detail: 'adversarial check against the proposal and sources; returns a corrected draft' },
  ],
}

const REPO = '/home/user/skills-catalog'
const SC = '/tmp/claude-0/-home-user/d376d93a-ebdc-5dd0-8a86-e43ebeea7e9d/scratchpad'
const WS = SC + '/ws'

const S = { type: 'string' }
const SA = { type: 'array', items: { type: 'string' } }
const DRAFT_PROPS = {
  slug: S, name: S, description: S, triggers: SA,
  sections: { type: 'array', items: { type: 'object', properties: {
    heading: S, text: S,
    origin: { type: 'array', items: { type: 'object', properties: { ref: S, heading: S }, required: ['ref', 'heading'] } },
  }, required: ['heading', 'text', 'origin'] } },
  files: { type: 'array', items: { type: 'object', properties: { path: S, from_ref: S, from_path: S, note: S }, required: ['path', 'from_ref', 'from_path', 'note'] } },
  changes: { type: 'array', items: { type: 'object', properties: {
    kind: { type: 'string', enum: ['keep', 'graft', 'drop', 'rewrite', 'new'] }, detail: S, from_ref: S,
  }, required: ['kind', 'detail', 'from_ref'] } },
  open_questions: SA,
  attribution: { type: 'array', items: { type: 'object', properties: { ref: S, license: S, note: S }, required: ['ref', 'license', 'note'] } },
}
const DRAFT_REQ = ['slug', 'name', 'description', 'triggers', 'sections', 'files', 'changes', 'open_questions', 'attribution']
const DRAFT_SCHEMA = { type: 'object', properties: DRAFT_PROPS, required: DRAFT_REQ }
const CHECKED_SCHEMA = { type: 'object', properties: Object.assign({}, DRAFT_PROPS, {
  critique: { type: 'array', items: { type: 'object', properties: { issue: S, fix: S, applied: { type: 'boolean' } }, required: ['issue', 'fix', 'applied'] } },
}), required: DRAFT_REQ.concat(['critique']) }

const RULES = [
  'Rules for the merged skill:',
  '- Follow the verified proposal in the brief. Start from the base (proposed.base_ref), carry every graft (the named source heading and the concrete content listed), and leave out every drop. For recommendation "pick-one", keep the base and fold in only the listed grafts.',
  '- Where the proposal is silent, keep the base text as it is. Write your own words only as glue, and keep glue short. Do not invent facts, numbers, thresholds, tools, integrations or legal positions that no member states.',
  '- For a member with a pr13_version path, work from that version: it already fixes references that do not resolve in AutoGPT. For a member rebuilt in an open PR (ref like "14:slug"), that PR version is the one to build on.',
  '- Respect the expert persona in the expert file (identity, boundaries, voice). Anything a member says that the persona forbids (for example approving, signing, sending, legal or financial advice where the persona is non-advisory) stays out.',
  '- Platform fit per the platform brief: no slash commands, $ARGUMENTS, CLAUDE.md, ~/.claude paths, plugin commands or subagent tools; degrade gracefully when an integration is missing; draft before any outward action and ask for approval.',
  '- Never mention evaluations, scores, grades, verdicts about skill quality, which origin group a text came from, or any person\'s name. The skill must read as one product.',
  '- Shape: SKILL.md is the router and contract: when to use it, inputs to ask for, a numbered procedure with decision points, the output contract, guardrails, and a short self-check. Put depth in references/. Aim for at most about 250 lines of body.',
  '- Supporting files: list in `files` every file the merged package keeps (target `path` inside the package, the `from_ref` and `from_path` it is copied from). Link only to files you list. When you carry text from a member with an upstream licence (license in the brief), keep its LICENSE file, add an attribution entry, and note it in `attribution`.',
  '- Output the body as `sections`, in order. `heading` is the exact markdown heading line as it will appear (for example "## Inputs"), or "" for text before the first heading. `text` is the markdown under that heading, without the heading line. `origin` lists where the section comes from: member ref plus the source heading text exactly as written in that source, without the leading #s (use "" for the source\'s preamble); use an empty list for pure glue. Be accurate: the review UI scrolls to these headings.',
  '- Frontmatter: `slug` is proposed.slug (lowercase kebab-case), `name` is the display name, `description` states what it does and when to load it (at most 500 characters), `triggers` are a few short phrases a user would say (may be empty).',
  '- `changes` lists what you kept, grafted, dropped, rewrote or added, with from_ref. `open_questions` lists conflicts the proposal did not settle that a reviewer must decide.',
].join('\n')

function draftPrompt(fn) {
  return [
    'Write the merged skill for one overlap cluster of an AutoGPT expert, like resolving a merge conflict into a single file.',
    'Read first: the brief ' + WS + '/clusters/' + fn + '.json (expert, cluster, the verified merge proposal and every member package path), ' + WS + '/platform_brief.md, and the expert file named in the brief. Then read every member SKILL.md in full and open the supporting files you might carry.',
    '',
    RULES,
  ].join('\n')
}

function checkPrompt(fn, draft) {
  return [
    'Adversarially check this merged skill draft. Assume it contains mistakes; find and fix them.',
    'Inputs: the brief ' + WS + '/clusters/' + fn + '.json, ' + WS + '/platform_brief.md, the expert file, and every member package (open the sources; do not trust the draft).',
    '',
    RULES,
    '',
    'Draft JSON:',
    JSON.stringify(draft),
    '',
    'Check: (1) every graft in proposed.grafts is present with its concrete content; (2) every drop is absent; (3) no fact, number, threshold, tool or position that no member states; (4) each origin names a real heading in that member (open it); (5) links point only to listed files and every from_path exists (list the directory); (6) slug equals proposed.slug and the description says what it does and when to load it; (7) the persona\'s boundaries hold; (8) no mention of evaluations, scores, grades, origin groups or people; (9) platform fit; (10) it reads as one skill: no duplicated steps, consistent terms and labels, numbered steps in order.',
    'Return the corrected full draft in the same schema with your fixes applied, plus `critique`: one entry per change or dispute.',
  ].join('\n')
}

log('Shard ' + args.shard + ': ' + args.units.length + ' clusters')
await pipeline(
  args.units,
  fn => agent(draftPrompt(fn), { label: 'draft:' + fn, phase: 'Draft', schema: DRAFT_SCHEMA }),
  (d, fn) => d ? agent(checkPrompt(fn, d), { label: 'check:' + fn, phase: 'Check', schema: CHECKED_SCHEMA }) : null,
)
return { shard: args.shard, count: args.units.length }
