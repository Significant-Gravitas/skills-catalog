export const meta = {
  name: 'scrub-score-mentions',
  description: 'Rewrite review text so it no longer cites eval scores or grades',
  phases: [{ title: 'Scrub', detail: 'rewrite flagged strings without scores' }],
}

const WS = '/tmp/claude-0/-home-user/d376d93a-ebdc-5dd0-8a86-e43ebeea7e9d/scratchpad/ws'
const SCHEMA = { type: 'object', properties: { items: { type: 'array', items: { type: 'object', properties: { i: { type: 'integer' }, text: { type: 'string' } }, required: ['i', 'text'] } } }, required: ['items'] }

phase('Scrub')
await parallel(args.batches.map(b => () => agent([
  'Read ' + WS + '/scrub/batch_' + b + '.json: a list of {i, text} strings from a skills review.',
  'Some of them cite internal evaluation results: numeric scores ("Eval 56.", "59/100", "(44)", "56 vs 44", "evals 54-62"), grades or verdict words used as grades ("all \'fix\'", "55/100 rewrite", "the highest eval in scope", "wins on eval").',
  'Rewrite each string so it no longer cites those scores, grades or eval verdicts. Keep every other fact, name, heading, slug and recommendation. Where a score carried meaning, say it qualitatively and specifically instead (for example "stronger on procedure and guardrails", "thinner than the in-house skill").',
  'Leave a string exactly as it is when its numbers or words like "verdict", "pass" or "score" belong to the subject matter itself (a skill that produces verdicts, a 10-to-16-week plan, a lead score), not to the review\'s own grading.',
  'Do not add commentary. Return every i from the file with its final text.',
].join('\n'), { label: 'scrub:' + b, phase: 'Scrub', schema: SCHEMA })))
return { batches: args.batches }
