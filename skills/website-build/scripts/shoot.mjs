#!/usr/bin/env node
// Full-page screenshots through the Chrome DevTools protocol, with no npm
// packages (Node 22+ has fetch and WebSocket built in).
// Usage: node shoot.mjs <url> <out-prefix> [phone|desktop|both|og]
// Writes <out-prefix>-phone.png and/or <out-prefix>-desktop.png and prints their paths.
// Pages taller than 2000 px are saved as -part0, -part1... slices of 1800 px
// (read_file accepts at most 2000 px per side), up to 9000 px of page.
import { spawn } from 'node:child_process';
import { writeFileSync, mkdtempSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const [url, prefix, which = 'both'] = process.argv.slice(2);
if (!url || !prefix) {
  console.error('usage: node shoot.mjs <url> <out-prefix> [phone|desktop|both]');
  process.exit(2);
}
const candidates = ['google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser'];
const which_ = (cmd) => {
  for (const dir of (process.env.PATH || '').split(':')) {
    const p = join(dir, cmd);
    if (existsSync(p)) return p;
  }
  return null;
};
const chrome = process.env.CHROME_PATH || candidates.map(which_).find(Boolean);
if (!chrome) {
  console.error('no Chrome or Chromium found');
  process.exit(3);
}

const port = 9300 + Math.floor(Math.random() * 500);
const profile = mkdtempSync(join(tmpdir(), 'shoot-'));
const proc = spawn(chrome, [
  '--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage', '--hide-scrollbars',
  '--no-first-run', '--no-default-browser-check', `--remote-debugging-port=${port}`,
  // Background services off: without these, headless Chrome can hang on page loads.
  '--disable-features=Translate,OptimizationHints,MediaRouter,DialMediaRouteProvider,CalculateNativeWinOcclusion,InterestFeedContentSuggestions,CertificateTransparencyComponentUpdater,AutofillServerCommunication,PrivacySandboxSettings4',
  '--disable-extensions',
  '--disable-component-extensions-with-background-pages',
  '--disable-background-networking',
  '--disable-component-update',
  '--disable-client-side-phishing-detection',
  '--disable-sync',
  '--metrics-recording-only',
  '--disable-default-apps',
  '--mute-audio',
  '--disable-backgrounding-occluded-windows',
  '--disable-renderer-backgrounding',
  '--disable-background-timer-throttling',
  '--password-store=basic',
  '--use-mock-keychain',
  '--disable-hang-monitor',
  '--disable-domain-reliability',
  `--user-data-dir=${profile}`, 'about:blank',
], { stdio: 'ignore' });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const killAll = () => { try { proc.kill('SIGKILL'); } catch {} };
const hardStop = setTimeout(() => { console.error('timed out'); killAll(); process.exit(4); }, 90000);

async function target() {
  for (let i = 0; i < 60; i++) {
    try {
      const list = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
      const page = list.find((t) => t.type === 'page');
      if (page) return page.webSocketDebuggerUrl;
    } catch {}
    await sleep(250);
  }
  throw new Error('Chrome did not start');
}

function client(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let id = 0;
  const pending = new Map();
  const listeners = [];
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      msg.error ? reject(new Error(msg.error.message)) : resolve(msg.result);
    } else if (msg.method) {
      for (const l of listeners) l(msg);
    }
  };
  const ready = new Promise((r, j) => { ws.onopen = r; ws.onerror = j; });
  return {
    ready,
    send: (method, params = {}) => new Promise((resolve, reject) => {
      const n = ++id;
      pending.set(n, { resolve, reject });
      ws.send(JSON.stringify({ id: n, method, params }));
    }),
    once: (method, ms) => new Promise((resolve) => {
      const t = setTimeout(() => resolve(null), ms);
      listeners.push((m) => { if (m.method === method) { clearTimeout(t); resolve(m); } });
    }),
    close: () => ws.close(),
  };
}

const VIEWS = {
  phone: { width: 390, height: 844, deviceScaleFactor: 1, mobile: true },
  desktop: { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false },
  og: { width: 1200, height: 630, deviceScaleFactor: 1, mobile: false, exact: true },
};

try {
  const cdp = client(await target());
  await cdp.ready;
  await cdp.send('Page.enable');
  const views = which === 'both' ? ['phone', 'desktop'] : [which];
  for (const v of views) {
    const m = VIEWS[v];
    const { exact, ...metrics } = m;
    await cdp.send('Emulation.setDeviceMetricsOverride', metrics);
    if (m.mobile) {
      await cdp.send('Emulation.setUserAgentOverride', {
        userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1',
      });
    }
    const loaded = cdp.once('Page.loadEventFired', 30000);
    await cdp.send('Page.navigate', { url });
    await loaded;
    // Let fonts, lazy images and transitions settle; scroll to trigger lazy loading.
    await cdp.send('Runtime.evaluate', {
      expression: `(async () => { for (let y = 0; y < document.body.scrollHeight; y += 600) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 80)); } window.scrollTo(0, 0); await document.fonts.ready; })()`,
      awaitPromise: true,
    });
    await sleep(600);
    const { result } = await cdp.send('Runtime.evaluate', {
      expression: 'Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0)',
      returnByValue: true,
    });
    const full = Math.max(result.value || m.height, m.height);
    const height = m.exact ? m.height : Math.min(full, 9000);
    if (!m.exact && full > height) console.error(`TRUNCATED: page is ${full}px tall; captured the top ${height}px`);
    const slices = height <= 2000 ? [[0, height]] : [];
    for (let y = 0; height > 2000 && y < height; y += 1800) slices.push([y, Math.min(1800, height - y)]);
    for (const [i, [y, h]] of slices.entries()) {
      const shot = await cdp.send('Page.captureScreenshot', {
        format: 'png',
        captureBeyondViewport: true,
        clip: { x: 0, y, width: m.width, height: h, scale: 1 },
      });
      const file = slices.length === 1 ? `${prefix}-${v}.png` : `${prefix}-${v}-part${i}.png`;
      writeFileSync(file, Buffer.from(shot.data, 'base64'));
      console.log(file);
    }
  }
  cdp.close();
  clearTimeout(hardStop);
  killAll();
  process.exit(0);
} catch (e) {
  console.error(`screenshot failed: ${e.message}`);
  clearTimeout(hardStop);
  killAll();
  process.exit(5);
}
