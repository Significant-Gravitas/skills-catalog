#!/usr/bin/env node
// Self-host a font in the current site (run from the project folder).
//   node add-font.mjs fontshare <slug> [weights]   e.g. fontshare clash-display 500,600,700
//   node add-font.mjs fontsource <package>         e.g. fontsource fraunces  (variable if available)
// Fontshare fonts (ITF Free Font License, free for commercial use) are downloaded as
// woff2 into public/fonts/<slug>/ and declared in src/styles/fonts.css.
// Fontsource fonts are installed from npm and imported in src/styles/fonts.css.
// Base.astro imports src/styles/fonts.css. Prints the CSS font-family name to use.
import { execSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, writeFileSync, appendFileSync } from 'node:fs';
import { join } from 'node:path';

const [source, name, weightsArg] = process.argv.slice(2);
if (!source || !name) {
  console.error('usage: node add-font.mjs fontshare <slug> [weights] | fontsource <package>');
  process.exit(2);
}
if (!existsSync('package.json') || !existsSync('src')) {
  console.error('run this from the site folder (where package.json is)');
  process.exit(2);
}
const cssPath = join('src', 'styles', 'fonts.css');
if (!existsSync(cssPath)) writeFileSync(cssPath, '/* Self-hosted fonts. Managed by add-font.mjs; safe to edit. */\n');
const css = readFileSync(cssPath, 'utf8');

if (source === 'fontshare') {
  const weights = weightsArg || '400,500,600,700';
  const url = `https://api.fontshare.com/v2/css?f[]=${encodeURIComponent(name)}@${weights}&display=swap`;
  const res = await fetch(url);
  if (!res.ok) { console.error(`Fontshare returned ${res.status} for ${name}`); process.exit(3); }
  const sheet = await res.text();
  // The API sometimes appends other families; keep only the one asked for.
  const slugOf = (f) => f.toLowerCase().replace(/[^a-z0-9]+/g, '-');
  const faces = [...sheet.matchAll(/@font-face\s*{([^}]*)}/g)].map((m) => m[1])
    .filter((b) => slugOf((b.match(/font-family:\s*'([^']+)'/) || [])[1] || '') === name);
  if (!faces.length) { console.error(`no font faces for "${name}". Check the slug at https://www.fontshare.com (e.g. clash-display, cabinet-grotesk, satoshi, general-sans, gambetta, zodiak, erode, boska, sentient, panchang, tanker)`); process.exit(3); }
  const dir = join('public', 'fonts', name);
  mkdirSync(dir, { recursive: true });
  let family = '';
  let out = '';
  for (const body of faces) {
    family = (body.match(/font-family:\s*'([^']+)'/) || [])[1] || name;
    const weight = (body.match(/font-weight:\s*([\d ]+);/) || [])[1]?.trim() || '400';
    const style = (body.match(/font-style:\s*(\w+);/) || [])[1] || 'normal';
    const woff2 = (body.match(/url\('([^']+\.woff2)'\)/) || [])[1];
    if (!woff2) continue;
    const file = `${name}-${weight.replace(/\s+/g, '_')}-${style}.woff2`;
    const r = await fetch(woff2.startsWith('//') ? `https:${woff2}` : woff2);
    if (!r.ok) { console.error(`download failed: ${woff2}`); process.exit(4); }
    writeFileSync(join(dir, file), Buffer.from(await r.arrayBuffer()));
    out += `@font-face {\n  font-family: '${family}';\n  src: url('/fonts/${name}/${file}') format('woff2');\n  font-weight: ${weight};\n  font-style: ${style};\n  font-display: swap;\n}\n`;
  }
  if (!css.includes(`font-family: '${family}'`)) appendFileSync(cssPath, `\n/* ${family} from Fontshare (ITF Free Font License) */\n${out}`);
  console.log(`font-family: '${family}'   (files in ${dir})`);
} else if (source === 'fontsource') {
  let pkg = `@fontsource-variable/${name}`;
  try {
    execSync(`npm view ${pkg} version`, { stdio: 'ignore' });
  } catch {
    pkg = `@fontsource/${name}`;
  }
  execSync(`npm install --no-audit --no-fund --loglevel=error ${pkg}`, { stdio: 'inherit' });
  // @import must come before any other rule, so put it at the top.
  if (!css.includes(`'${pkg}'`)) writeFileSync(cssPath, `@import '${pkg}';\n` + css);
  const pretty = name.split('-').map((w) => w[0].toUpperCase() + w.slice(1)).join(' ');
  const family = pkg.includes('-variable/') ? `${pretty} Variable` : pretty;
  console.log(`font-family: '${family}'   (${pkg}; non-variable packages include weight 400 only unless you import more, e.g. '${pkg}/700.css')`);
} else {
  console.error('source must be fontshare or fontsource');
  process.exit(2);
}
