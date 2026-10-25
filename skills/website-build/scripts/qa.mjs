#!/usr/bin/env node
// Static quality checks on a built site. Run from the project folder after
// `npm run build`:   node /home/user/skills/website-build/scripts/qa.mjs [--launch]
// --launch also fails on things that are fine in a preview but not on a live
// site (placeholder domain, starter favicon or social image, stray noindex).
// Exit code 1 means at least one ERROR. Output is short on purpose.
import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { join, relative, posix } from 'node:path';

const launch = process.argv.includes('--launch');
const root = process.cwd();
const dist = join(root, 'dist');
const errors = [];
const warns = [];
const err = (m) => errors.push(m);
const warn = (m) => warns.push(m);

if (!existsSync(dist)) {
  console.log('ERROR: no dist/ folder. Run `npm run build` first, from the project folder.');
  process.exit(1);
}

const walk = (dir) => readdirSync(dir).flatMap((f) => {
  const p = join(dir, f);
  return statSync(p).isDirectory() ? walk(p) : [p];
});
const files = walk(dist);
const fileSet = new Set(files.map((f) => '/' + relative(dist, f).split('\\').join('/')));
const htmlFiles = files.filter((f) => f.endsWith('.html'));
const routeOf = (f) => '/' + relative(dist, f).split('\\').join('/').replace(/index\.html$/, '').replace(/\.html$/, '');

const exists = (urlPath) => {
  let p = decodeURI(urlPath.split('#')[0].split('?')[0]);
  if (p === '' ) return true;
  if (fileSet.has(p)) return true;
  if (p.endsWith('/')) return fileSet.has(p + 'index.html');
  return fileSet.has(p + '/index.html') || fileSet.has(p + '.html');
};

// Pre-launch mode (site.launched = false): robots.txt blocks crawlers and every
// page is noindex on purpose, until launch day.
const robotsPath = join(dist, 'robots.txt');
const prelaunch = existsSync(robotsPath) && /Disallow:\s*\/\s*$/m.test(readFileSync(robotsPath, 'utf8'));
let placeholderCanonical = '';
const missingOg = new Set();
const SPECIAL = new Set(['/404', '/thanks/', '/404.html']);
const titles = new Map();
const markers = [/REPLACE\b/, /lorem ipsum/i, /\bTODO\b/, /__NAME__|__SLUG__|__DATE__/, /\[(?:your|insert)[^\]]*\]/i];

for (const f of htmlFiles) {
  const html = readFileSync(f, 'utf8');
  const route = routeOf(f);
  const isSpecial = SPECIAL.has(route) || route.startsWith('/404');
  const text = html.replace(/<script[\s\S]*?<\/script>/gi, '').replace(/<style[\s\S]*?<\/style>/gi, '');

  for (const m of markers) {
    const hit = text.match(m);
    if (hit) err(`${route}: placeholder text left: "${hit[0]}"`);
  }
  if (!/<html[^>]*\slang="[^"]+"/i.test(html)) err(`${route}: <html> has no lang`);
  if (!/<meta[^>]+name="viewport"/i.test(html)) err(`${route}: no viewport meta`);

  const decode = (t) => t.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'");
  const title = decode((html.match(/<title>([\s\S]*?)<\/title>/i) || [])[1]?.trim() ?? '');
  if (!title) err(`${route}: missing <title>`);
  else {
    if (title.length > 65) warn(`${route}: title is ${title.length} chars (aim for 65 or fewer)`);
    if (!isSpecial) titles.set(title, [...(titles.get(title) || []), route]);
  }
  const desc = decode((html.match(/<meta[^>]+name="description"[^>]+content="([^"]*)"/i) || [])[1] ?? '');
  if (!desc) err(`${route}: missing meta description`);
  else if (!isSpecial && (desc.length < 50 || desc.length > 160)) warn(`${route}: description is ${desc.length} chars (aim for 50 to 160)`);

  const h1s = (html.match(/<h1[\s>]/gi) || []).length;
  if (h1s === 0) err(`${route}: no <h1>`);
  if (h1s > 1) warn(`${route}: ${h1s} <h1> elements (use one)`);

  for (const img of html.match(/<img\b[^>]*>/gi) || []) {
    if (!/\salt=/i.test(img)) err(`${route}: image without alt: ${img.slice(0, 90)}`);
    if (!/\swidth=/i.test(img) || !/\sheight=/i.test(img)) warn(`${route}: image without width/height (layout shift): ${img.slice(0, 70)}`);
  }

  const refs = [...html.matchAll(/\s(?:href|src)="([^"]+)"/gi)].map((m) => m[1]);
  for (const r of refs) {
    if (/^(https?:|mailto:|tel:|data:|#|javascript:|sms:|\/\/)/i.test(r)) continue;
    const abs = r.startsWith('/') ? r : posix.join(posix.dirname(route.endsWith('/') ? route + 'x' : route), r);
    if (!exists(abs)) err(`${route}: broken link or asset: ${r}`);
  }
  for (const r of html.match(/href="tel:[^"]*"/gi) || []) {
    if (!/^href="tel:\+?[0-9()\-]{6,}"$/.test(r)) warn(`${route}: odd phone link ${r} (use digits, ideally +country code)`);
  }

  if (/name="robots"\s+content="[^"]*noindex/i.test(html) && !isSpecial && !prelaunch) {
    (launch ? err : warn)(`${route}: page is set to noindex`);
  }
  const canonical = (html.match(/<link[^>]+rel="canonical"[^>]+href="([^"]+)"/i) || [])[1] || '';
  if (/example\.workers\.dev|example\.com/.test(canonical)) placeholderCanonical = canonical;
  const og = (html.match(/<meta[^>]+property="og:image"[^>]+content="([^"]+)"/i) || [])[1] || '';
  if (og) {
    try {
      const ogPath = new URL(og).pathname;
      if (!exists(ogPath)) missingOg.add(ogPath);
    } catch { warn(`${route}: og:image is not a full URL: ${og}`); }
  }
}

if (prelaunch && launch) err('site is still in pre-launch mode: set launched: true in src/site.config.mjs (search engines are blocked until then)');
if (placeholderCanonical) {
  (launch ? err : warn)(`site address is still the placeholder (${new URL(placeholderCanonical).origin}); set site.url in src/site.config.mjs to the real address`);
}
for (const p of missingOg) err(`social preview image ${p} is missing from public/ (make a 1200x630 PNG)`);
for (const [t, routes] of titles) if (routes.length > 1) warn(`same title "${t}" on ${routes.join(', ')}`);

if (!fileSet.has('/404.html')) err('no 404.html (add src/pages/404.astro)');
if (!files.some((f) => /sitemap-index\.xml$/.test(f))) warn('no sitemap (set `site` in astro.config.mjs)');

for (const f of files) {
  const kb = statSync(f).size / 1024;
  if (/\.(png|jpe?g|webp|avif|gif)$/i.test(f) && kb > 400) warn(`${'/' + relative(dist, f)}: image is ${Math.round(kb)} KB (aim for under 400 KB; use astro:assets <Image>)`);
  if (/\.(js)$/i.test(f) && kb > 150) warn(`${'/' + relative(dist, f)}: script is ${Math.round(kb)} KB`);
}

const ph = join(root, 'starter-placeholders.txt');
if (existsSync(ph)) {
  for (const line of readFileSync(ph, 'utf8').split('\n').filter(Boolean)) {
    const [hash, file] = line.trim().split(/\s+/);
    const p = join(root, file);
    if (existsSync(p) && createHash('sha256').update(readFileSync(p)).digest('hex') === hash) {
      (launch ? err : warn)(`${file} is still the starter placeholder; replace it with the real logo or image`);
    }
  }
}

console.log(`QA: ${htmlFiles.length} pages, ${errors.length} errors, ${warns.length} warnings${launch ? ' (launch mode)' : ''}${prelaunch ? '; pre-launch: hidden from search engines' : ''}`);
for (const e of errors.slice(0, 40)) console.log('ERROR: ' + e);
for (const w of warns.slice(0, 25)) console.log('WARN:  ' + w);
if (errors.length > 40 || warns.length > 25) console.log('(list truncated)');
process.exit(errors.length ? 1 : 0);
