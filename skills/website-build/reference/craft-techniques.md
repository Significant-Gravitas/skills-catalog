# Craft techniques (tested code)

These techniques are the vocabulary, not the design. Choose the ones the concept needs, change them until they belong to this site, and invent new ones. A site built by stacking these as they are would be just another template.

Everything marked TESTED was built with Astro 7, Tailwind 4, GSAP 3.15 and Lenis 1.3, and checked in frame captures. Every technique has a reduced-motion path; keep it.

## Setup

```bash
npm i gsap lenis      # GSAP is free for commercial use, including all its plugins
node /home/user/skills/website-build/scripts/add-font.mjs fontshare clash-display 500,600,700
node /home/user/skills/website-build/scripts/add-font.mjs fontsource fraunces
```

- `add-font.mjs` prints the family name. Fontshare files are self-hosted in `public/fonts/` and Fontsource fonts are imported into `src/styles/fonts.css`, which `Base.astro` imports.
- Fontsource variable packages load the `wght` axis only. For more axes, import the axes file: `@import '@fontsource-variable/fraunces/full.css';` gives SOFT, WONK and opsz.
- To speed up the hero font, preload it in `Base.astro`'s head: `<link rel="preload" href="/fonts/clash-display/clash-display-600-normal.woff2" as="font" type="font/woff2" crossorigin>`.

Tokens go in `src/styles/global.css` (TESTED):

```css
@theme {
  --font-display: "Clash Display", system-ui, sans-serif;
  --font-serif: "Fraunces Variable", Georgia, serif;
  --ease-out-expo: cubic-bezier(.16, 1, .3, 1);
  --ease-in-out: cubic-bezier(.65, 0, .35, 1);
  --text-hero: clamp(3.5rem, 13vw, 15rem);
  --text-display: clamp(2.5rem, 7vw, 7.5rem);
}
::selection { background: var(--color-accent); color: var(--color-surface); }
```

Use them as `text-[length:var(--text-hero)]`, `font-display`, `ease-[var(--ease-out-expo)]`.

## Load sequence: headline lines rise out of masks (TESTED, CSS only)

```css
.line-mask { display: block; overflow: hidden; padding-bottom: .06em; }
.line-mask > span { display: block; animation: line-rise .9s var(--ease-out-expo) both; animation-delay: calc(var(--i, 0) * 80ms + 100ms); }
@keyframes line-rise { from { transform: translateY(105%); } }
@media (prefers-reduced-motion: reduce) { .line-mask > span { animation: none; } }
```

```astro
<h1 class="font-display font-semibold leading-[0.85] tracking-[-0.04em] text-[length:var(--text-hero)]">
  <span class="line-mask"><span style="--i:0">Low tide.</span></span>
  <span class="line-mask"><span style="--i:1">High gear.</span></span>
</h1>
```

Break the lines yourself, deliberately. The text is in the HTML, so readers without JS still see it.

## Scroll-driven animation, CSS first (TESTED)

These run off the compositor with no JS. They work in Chrome, Edge and Safari 26+; elsewhere the element simply shows its final state.

```css
@supports (animation-timeline: view()) {
  .reveal      { animation: reveal-up linear both; animation-timeline: view(); animation-range: entry 0% entry 60%; }
  .clip-reveal { animation: clip-open linear both; animation-timeline: view(); animation-range: entry 10% cover 40%; }
  .axis-scroll { animation: axis linear both; animation-timeline: view(); animation-range: cover 0% cover 100%; }
  .draw        { stroke-dasharray: 1; stroke-dashoffset: 1; animation: draw linear both; animation-timeline: view(); animation-range: entry 20% cover 60%; }
}
@keyframes reveal-up { from { opacity: 0; transform: translateY(3rem); } }
@keyframes clip-open { from { clip-path: inset(30% 20% 30% 20% round 1rem); transform: scale(1.15); } to { clip-path: inset(0 0 0 0 round 0); transform: scale(1); } }
@keyframes axis { from { font-variation-settings: "wght" 200; } to { font-variation-settings: "wght" 900; } }
@keyframes draw { to { stroke-dashoffset: 0; } }
@media (prefers-reduced-motion: reduce) {
  .reveal, .clip-reveal, .axis-scroll { animation: none !important; }
  .draw { stroke-dashoffset: 0; animation: none !important; }
}
```

- `.clip-reveal` on an image wrapper opens it from a small rounded window to full bleed.
- `.draw` on an SVG `<path pathLength="1">` draws the line as it scrolls into view. It's good for concept illustrations: tide lines, pipe routes, flower stems.
- `.axis-scroll` animates a variable font's weight (or SOFT and WONK with the full axes file) through a section.
- Use `.reveal` sparingly and with variety. The same fade on every element is a banned pattern.

## Smooth scroll with GSAP choreography (TESTED)

Put this in a page's or layout's `<script>`. Astro bundles it.

```ts
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import Lenis from 'lenis';
import 'lenis/dist/lenis.css';
gsap.registerPlugin(ScrollTrigger);

const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
if (!reduce) {
  const lenis = new Lenis({ lerp: 0.1 });
  lenis.on('scroll', ScrollTrigger.update);
  gsap.ticker.add((t) => lenis.raf(t * 1000));
  gsap.ticker.lagSmoothing(0);
}
```

Use Lenis only when the concept wants weight and glide. Some concepts are better with crisp native scrolling.

## Pinned storytelling (TESTED)

A tall section with a sticky stage. GSAP scrubs a transform as you scroll through it.

```astro
<section class="pin-story relative h-[300vh]">
  <div class="sticky top-0 flex h-dvh items-center justify-center overflow-hidden">
    <p class="pin-word font-display text-[length:var(--text-hero)] leading-none">Tide</p>
  </div>
</section>
```

```ts
gsap.fromTo('.pin-word', { scale: 0.6, letterSpacing: '0.4em' }, {
  scale: 2.4, letterSpacing: '-0.04em', ease: 'none',
  scrollTrigger: { trigger: '.pin-story', start: 'top top', end: 'bottom bottom', scrub: true },
});
```

Use it for three steps of a service, a day in the life, a before-and-after, or a product assembling. Use a timeline (`gsap.timeline({ scrollTrigger: {...} })`) for several steps.

## Horizontal scroll section, desktop only (TESTED)

```astro
<section class="hscroll overflow-hidden">
  <div class="hscroll-track flex w-max gap-8 px-5 py-24"> ...panels... </div>
</section>
```

```ts
gsap.matchMedia().add('(min-width: 768px)', () => {
  const track = document.querySelector<HTMLElement>('.hscroll-track')!;
  gsap.to(track, {
    x: () => -(track.scrollWidth - innerWidth), ease: 'none',
    scrollTrigger: { trigger: '.hscroll', pin: true, scrub: 1, end: () => '+=' + (track.scrollWidth - innerWidth), invalidateOnRefresh: true },
  });
});
```

On phones it becomes a native swipe row: add `overflow-x-auto snap-x snap-mandatory` to the section and `snap-start` to the panels, inside `@media (max-width: 767px)`.

## Magnetic buttons (TESTED)

```ts
if (matchMedia('(hover: hover)').matches && !reduce) {
  document.querySelectorAll<HTMLElement>('.magnetic').forEach((el) => {
    const xTo = gsap.quickTo(el, 'x', { duration: 0.6, ease: 'power3' });
    const yTo = gsap.quickTo(el, 'y', { duration: 0.6, ease: 'power3' });
    el.addEventListener('pointermove', (e) => {
      const r = el.getBoundingClientRect();
      xTo((e.clientX - r.left - r.width / 2) * 0.35);
      yTo((e.clientY - r.top - r.height / 2) * 0.35);
    });
    el.addEventListener('pointerleave', () => { xTo(0); yTo(0); });
  });
}
```

## Marquee (TESTED)

```css
.marquee { display: flex; overflow: hidden; white-space: nowrap; }
.marquee > div { display: flex; flex-shrink: 0; gap: 3rem; padding-right: 3rem; animation: marquee 30s linear infinite; }
@keyframes marquee { to { transform: translateX(-100%); } }
@media (prefers-reduced-motion: reduce) { .marquee > div { animation: none; } }
```

Use two identical `<div>` children, with `aria-hidden="true"` on the marquee. The facts it shows must also appear somewhere readable. It's only right when the concept wants it (a ticker, a tide, a departure board), not as decoration.

## Grain and material (TESTED)

```css
.grain::after {
  content: ""; position: fixed; inset: -50%; z-index: 60; pointer-events: none; opacity: .08;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='3' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
}
```

For paper, add a warm tint plus grain. For print, use `mix-blend-mode: multiply` on images and type over a paper tone, optionally with a 1 to 2 px offset duplicate in a second ink for misregistration.

## Hover-reveal index list

Services or products as a big typographic list; hovering a row shows its image, which follows the pointer.

```astro
<ul class="hover-list relative">
  {items.map((it) => (
    <li><a href={it.href} class="group flex items-baseline justify-between border-b border-ink py-6 font-display text-5xl" data-img={it.img}>
      <span class="transition-transform duration-500 ease-[var(--ease-out-expo)] group-hover:translate-x-6">{it.name}</span>
      <span class="font-mono text-sm tabular-nums">{it.price}</span>
    </a></li>
  ))}
  <img class="hover-img pointer-events-none fixed left-0 top-0 z-40 w-72 -translate-x-1/2 -translate-y-1/2 scale-90 rounded-sm opacity-0 transition-[opacity,scale] duration-300" alt="" />
</ul>
```

```ts
const img = document.querySelector<HTMLImageElement>('.hover-img');
if (img && matchMedia('(hover: hover)').matches) {
  const xTo = gsap.quickTo(img, 'x', { duration: 0.5, ease: 'power3' });
  const yTo = gsap.quickTo(img, 'y', { duration: 0.5, ease: 'power3' });
  document.querySelectorAll<HTMLAnchorElement>('.hover-list a').forEach((a) => {
    a.addEventListener('pointerenter', () => { img.src = a.dataset.img!; img.style.opacity = '1'; img.style.scale = '1'; });
    a.addEventListener('pointerleave', () => { img.style.opacity = '0'; img.style.scale = '.9'; });
  });
  addEventListener('pointermove', (e) => { xTo(e.clientX); yTo(e.clientY); });
}
```

On touch devices, show each row's image inline under the name instead. The data URLs must point to optimised images (use `getImage()` from `astro:assets`).

## Sticky stacking panels

```astro
{panels.map((p, i) => (
  <section class="sticky top-0 flex min-h-dvh items-center" style={`z-index:${i}; background:${p.bg}`}>...</section>
))}
```

Each panel slides over the last as you scroll; it's good for process steps. Add a subtle `scale` on the panel underneath with a scroll-driven animation for depth.

## Header that inverts over anything

Warning for any fixed header: `backdrop-filter` (Tailwind `backdrop-blur`), `transform` or `filter` on the header makes it the containing block for its `position: fixed` children. A full-screen mobile menu inside it then gets trapped inside the header bar. Put the menu overlay outside the header element, or drop those properties while the menu is open.


```css
.site-header { position: fixed; inset: 0 0 auto; z-index: 50; mix-blend-mode: difference; color: white; }
```

It works over any photo or colour. Make sure the menu stays readable when open (remove the blend mode there).

## Image inside type

```css
.type-mask { background: url('/hero.webp') center/cover; -webkit-background-clip: text; background-clip: text; color: transparent; }
```

Keep a readable fallback colour for print and forced-colours mode: `@media (forced-colors: active) { .type-mask { color: CanvasText; background: none; } }`.

## Live "open now" line (data made beautiful)

```astro
<p id="open-now" class="font-mono text-sm" data-hours='{"2":[540,1050],"3":[540,1050],"4":[540,1050],"5":[540,1050],"6":[540,1050]}'>Tue to Sat, 9:00 to 17:30</p>
<script>
  const el = document.getElementById('open-now')!;
  const hours = JSON.parse(el.dataset.hours!); // day (0 = Sunday) -> [open, close] in minutes, local time
  const now = new Date(new Date().toLocaleString('en-US', { timeZone: 'Europe/London' }));
  const mins = now.getHours() * 60 + now.getMinutes();
  const today = hours[now.getDay()];
  if (today && mins >= today[0] && mins < today[1]) {
    const left = today[1] - mins;
    el.textContent = `Open now · closes in ${Math.floor(left / 60)}h ${left % 60}m`;
  } else {
    el.textContent = 'Closed now · ' + el.textContent;
  }
</script>
```

Set the business's own time zone. The static text is the no-JS fallback, so it must be true on its own.

## Page transitions (Astro view transitions)

```astro
---
import { ClientRouter } from 'astro:transitions';
---
<head> ... <ClientRouter /> </head>
<img transition:name={`work-${slug}`} ... />   <!-- the same name on the list and detail page morphs between them -->
```

With `ClientRouter`, scripts don't re-run on navigation. Wrap set-up code in `document.addEventListener('astro:page-load', () => { ... })`, and kill ScrollTriggers on `astro:before-swap` (`ScrollTrigger.getAll().forEach((t) => t.kill())`). Use it when the concept benefits; it's not a default.

## Custom cursor (only when it is the concept)

Use a custom cursor only when it means something: a spanner for a bike shop, a pipette for a lab, a petal for a florist. Hide it on touch devices and keep the native cursor for text fields. A generic dot-follower cursor is decoration and a template tell.

## Generated imagery through the platform

`find_capability(query="generate image")` finds the image generators (Flux, Recraft, Ideogram and others).
- Write one art-direction paragraph for the whole site: medium, lighting, palette (hex values), lens or illustration style, grain, composition. Reuse it in every prompt so the set feels like one shoot.
- Generate 3 or 4 options per slot, look at them all with `read_workspace_file`, and keep only the best. Re-roll anything with tell-tale AI faults: hands, text, warped geometry, plastic skin.
- Then run it through `astro:assets` like any photo.
- Never generate the business's people, premises, products or customers as if real (see design-standard.md).

## Performance guardrails for rich sites

- GSAP with ScrollTrigger and Lenis is about 50 KB compressed. That's fine; three animation libraries are not.
- Animate only `transform`, `opacity`, `clip-path` and `filter`. Never animate layout properties (width, height, top) on scroll.
- Put `will-change` only on elements that are animating right now.
- The hero image is `loading="eager"` with `fetchpriority="high"`. Preload the hero font.
- Big illustrations (maps from OpenStreetMap, detailed SVG drawings) are the usual performance killer. Simplify paths (fewer points, `npx svgo`), and serve large static ones as an `<img src="...svg">` or a WebP through `astro:assets`, not inline. Inline only the paths you animate. Avoid animating dozens of SVG elements every frame; animate a few groups with transforms.
- Prefer CSS scroll-driven animation for simple reveals. Every `scroll` listener does work on the main thread, so throttle it to `requestAnimationFrame`, or use one ScrollTrigger.
- Measure after every major addition: `bash /home/user/skills/website-build/scripts/speed.sh dist`. Fix what its "Fix first" list says before adding more.
