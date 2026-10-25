#!/usr/bin/env node
// Full-page screenshots through the Chrome DevTools protocol, with no npm
// packages (Node 22+ has fetch and WebSocket built in).
// Usage: node shoot.mjs <url> <out-prefix> [phone|desktop|both|og|sheet|frames|frames-phone]
// frames: viewport shots during the load sequence (150, 600, 1500 ms) and at
// scroll positions after motion settles, so motion can be judged from stills.
// Env: SHOOT_WAIT=ms extra settle time before capturing (preloaders on reference
//      sites often need 5000-8000); SHOOT_EVAL='js' runs in the page before capture
//      (e.g. open the menu); FRAMES_AT=0.1,0.2,... scroll fractions for frames.
// Writes <out-prefix>-phone.png and/or <out-prefix>-desktop.png and prints their paths.
// Pages taller than 2000 px are saved as -part0, -part1... slices of 1800 px
// (read_file accepts at most 2000 px per side), up to 14400 px of page.
import { spawn } from 'node:child_process';
import { writeFileSync, mkdtempSync, existsSync, rmSync } from 'node:fs';
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
// Kill Chrome and delete its throwaway profile (tens of MB per run otherwise).
const killAll = () => {
  try { proc.kill('SIGKILL'); } catch {}
  for (let k = 0; k < 20; k++) {
    try { rmSync(profile, { recursive: true, force: true }); break; } catch { Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 100); }
  }
};
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
  sheet: { width: 1960, height: 1240, deviceScaleFactor: 1, mobile: false, exact: true },
};

try {
  const cdp = client(await target());
  await cdp.ready;
  await cdp.send('Page.enable');
  if (which === 'frames' || which === 'frames-phone') {
    const v = which === 'frames' ? 'desktop' : 'phone';
    const m = VIEWS[v];
    const { exact, ...metrics } = m;
    await cdp.send('Emulation.setDeviceMetricsOverride', metrics);
    if (!m.mobile) await cdp.send('Emulation.setEmulatedMedia', { features: [{ name: 'hover', value: 'hover' }, { name: 'pointer', value: 'fine' }] });
    const t0 = Date.now();
    await cdp.send('Page.navigate', { url });
    cdp.once('Page.domContentEventFired', 15000).then(() => cdp.send('Runtime.evaluate', { expression: "document.documentElement.style.scrollBehavior = 'auto'" }).catch(() => {}));
    const snap = async (label) => {
      let shot;
      for (let k = 0; k < 40 && !shot; k++) {
        try { shot = await cdp.send('Page.captureScreenshot', { format: 'png' }); } catch { await sleep(50); }
      }
      if (!shot) { console.error(`frame ${label} failed`); return; }
      const file = `${prefix}-frames-${v}-${label}.png`;
      writeFileSync(file, Buffer.from(shot.data, 'base64'));
      console.log(file);
    };
    for (const ms of [150, 600, 1500]) {
      const wait = ms - (Date.now() - t0);
      if (wait > 0) await sleep(wait);
      await snap(`load-${String(ms).padStart(4, '0')}ms`);
    }
    await sleep(800 + Number(process.env.SHOOT_WAIT || 0));
    if (process.env.SHOOT_EVAL) {
      await cdp.send('Runtime.evaluate', { expression: process.env.SHOOT_EVAL, awaitPromise: true }).catch(() => {});
      await sleep(900);
      await snap('after-eval');
    }
    const { result } = await cdp.send('Runtime.evaluate', {
      expression: 'Math.max(document.documentElement.scrollHeight, document.body.scrollHeight) - innerHeight',
      returnByValue: true,
    });
    const max = Math.max(result.value || 0, 0);
    const at = (process.env.FRAMES_AT || '0.12,0.25,0.4,0.55,0.7,0.88').split(',').map(Number).filter((x) => x >= 0 && x <= 1);
    for (const [i, f] of at.entries()) {
      const y = Math.round(max * f);
      // Scroll in steps so scroll-linked animations see intermediate positions.
      await cdp.send('Runtime.evaluate', {
        expression: `(async () => { const from = scrollY, to = ${y}; for (let k = 1; k <= 8; k++) { scrollTo({ top: from + (to - from) * k / 8, behavior: 'instant' }); await new Promise(r => setTimeout(r, 40)); } })()`,
        awaitPromise: true,
      });
      await sleep(900);
      await snap(`scroll-${i + 1}-${Math.round(f * 100)}pct`);
    }
    cdp.close();
    clearTimeout(hardStop);
    killAll();
    process.exit(0);
  }
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
    // Full-page shots show the finished composition: with reduced motion emulated,
    // scroll-triggered reveals and pinned sequences render in their final state
    // (and the reduced-motion path gets checked too). Motion is judged from frames.
    if (!m.exact) {
      const pointer = m.mobile ? [] : [{ name: 'hover', value: 'hover' }, { name: 'pointer', value: 'fine' }];
      await cdp.send('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }, ...pointer] });
    }
    const loaded = cdp.once('Page.loadEventFired', 30000);
    await cdp.send('Page.navigate', { url });
    await loaded;
    // Let fonts, lazy images and transitions settle; scroll to trigger lazy loading.
    await cdp.send('Runtime.evaluate', {
      expression: `(async () => { document.documentElement.style.scrollBehavior = 'auto'; for (let y = 0; y < document.body.scrollHeight; y += 600) { window.scrollTo({ top: y, behavior: 'instant' }); await new Promise(r => setTimeout(r, 80)); } window.scrollTo({ top: 0, behavior: 'instant' }); await document.fonts.ready; })()`,
      awaitPromise: true,
    });
    await sleep(600 + Number(process.env.SHOOT_WAIT || 0));
    if (process.env.SHOOT_EVAL) {
      await cdp.send('Runtime.evaluate', { expression: process.env.SHOOT_EVAL, awaitPromise: true }).catch(() => {});
      await sleep(900);
    }
    const { result } = await cdp.send('Runtime.evaluate', {
      expression: 'Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0)',
      returnByValue: true,
    });
    const full = Math.max(result.value || m.height, m.height);
    const height = m.exact ? m.height : Math.min(full, 14400);
    if (!m.exact && full > height) console.error(`TRUNCATED: page is ${full}px tall; captured the top ${height}px`);
    const slices = height <= 2000 ? [[0, height]] : [];
    for (let y = 0; height > 2000 && y < height; y += 1800) slices.push([y, Math.min(1800, height - y)]);
    const save = (i, data) => {
      const file = slices.length === 1 ? `${prefix}-${v}.png` : `${prefix}-${v}-part${i}.png`;
      writeFileSync(file, Buffer.from(data, 'base64'));
      console.log(file);
    };
    if (m.exact) {
      const shot = await cdp.send('Page.captureScreenshot', { format: 'png', clip: { x: 0, y: 0, width: m.width, height, scale: 1 } });
      save(0, shot.data);
      continue;
    }
    // Scroll-and-stitch: capture viewport-sized tiles while scrolling (so 100vh
    // sections, sticky stages and lazy images render as a visitor sees them),
    // then stack the tiles in a plain page and slice that.
    const tiles = [];
    for (let y = 0, k = 0; y < height; y += m.height, k++) {
      const { result: pos } = await cdp.send('Runtime.evaluate', {
        expression: `(async () => { scrollTo({ top: ${y}, behavior: 'instant' }); await new Promise(r => setTimeout(r, 260)); return scrollY; })()`,
        awaitPromise: true, returnByValue: true,
      });
      if (k === 1) {
        // Fixed headers and buttons would repeat on every tile; show them once, at the top.
        await cdp.send('Runtime.evaluate', {
          expression: `for (const el of document.querySelectorAll('body *')) { if (getComputedStyle(el).position === 'fixed') el.style.visibility = 'hidden'; }`,
        });
        await sleep(60);
      }
      const shot = await cdp.send('Page.captureScreenshot', { format: 'png' });
      const file = join(profile, `tile-${k}.png`);
      writeFileSync(file, Buffer.from(shot.data, 'base64'));
      tiles.push({ file, top: pos.value });
    }
    const page = join(profile, 'stitch.html');
    writeFileSync(page, `<!doctype html><html><body style="margin:0;background:#fff"><div style="position:relative;width:${m.width}px;height:${height}px;overflow:hidden">${
      tiles.map((t) => `<img src="file://${t.file}" style="position:absolute;left:0;top:${t.top}px;width:${m.width}px;height:${m.height}px">`).join('')
    }</div></body></html>`);
    await cdp.send('Emulation.setEmulatedMedia', { features: [] });
    await cdp.send('Emulation.setDeviceMetricsOverride', { width: m.width, height: 1000, deviceScaleFactor: 1, mobile: false });
    const stitched = cdp.once('Page.loadEventFired', 30000);
    await cdp.send('Page.navigate', { url: `file://${page}` });
    await stitched;
    await sleep(200);
    for (const [i, [y, h]] of slices.entries()) {
      const shot = await cdp.send('Page.captureScreenshot', {
        format: 'png', captureBeyondViewport: true, clip: { x: 0, y, width: m.width, height: h, scale: 1 },
      });
      save(i, shot.data);
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
