# Quality bar

A page is done when all of this is true. `qa.mjs` checks the mechanical items; you check the rest by looking at the screenshots and reading the page.

## Content
- Every fact is from the owner or their materials. No placeholders on anything you call finished, and none at all at launch.
- Phone, email, address and hours match the Google Business Profile exactly.
- The main action is clear and repeated. Phone numbers are tap-to-call links (`tel:+441132345678`), emails are `mailto:` links.
- Spelling and grammar are clean, in the owner's variety of English (UK or US) and in their language.

## Mobile (check the phone screenshot first)
- Nothing scrolls sideways. Text never touches the edge (at least 20 px padding).
- Tap targets are at least 44 px high, with space between them.
- The headline and the main action are visible on the first screen.
- Body text is at least 16 px. Line length is comfortable.

## Accessibility (WCAG 2.2 AA, the practical subset)
- Text contrast at least 4.5:1 (3:1 for large text and icons). Check the accent button text too.
- Every image has `alt`; decorative ones get `alt=""`.
- Headings in order; one `h1`.
- Links say where they go ("See the menu", not "Click here").
- Keyboard: every link and button is reachable, with a visible focus ring (the starter sets one). The skip link works.
- Form fields have visible labels, the right `type` and `autocomplete`.
- No information is carried by colour alone. Motion respects reduced-motion.

## Performance
- No client-side framework unless the brief needs one. Total JS on a normal page is under about 50 KB.
- Photos go through `astro:assets` `<Image>`, with width and height set, lazy below the fold, and the first image eager.
- At most two font families, self-hosted.
- Third-party embeds (maps, booking, video) load lazily or behind a click, never on every page by default.
- Target PageSpeed Insights mobile scores of at least 90 for Performance, Accessibility, Best Practices and SEO (checked at launch in `website-launch-care`).

## SEO
- Unique title (about 50 to 60 characters) and description (120 to 155 characters) on every page.
- `site.url` in `src/site.config.mjs` is the real address before launch, so canonical links, the sitemap and social previews are correct.
- Structured data matches the visible facts (the starter builds it from `site.config.mjs`).
- `og.png` is a real 1200 x 630 image. The favicon is the real logo mark.
- Old URLs have 301 redirects when replacing a site.

## Trust and legal
- A privacy notice that matches what the site collects (the starter's page is a starting point; the owner must read and approve it). In the UK and EU a site that collects form data needs one.
- No cookie banner is needed if the site uses only Cloudflare Web Analytics and no other trackers. If the owner insists on Google Analytics, Meta Pixel or similar, a consent banner is needed; say so and recommend against it for a small site.
- Business details the law requires where relevant. UK limited companies show the company name, number and registered office; many EU countries require an Impressum. Ask the owner for them; don't guess.
- Testimonials are real and permitted. Logos of clients are used with permission.

## Code
- Builds cleanly with `npm ci && npm run build` (no warnings you haven't read).
- No secrets in the repo. The Web3Forms key is fine because it is public by design.
- `wrangler.jsonc` `name` equals the slug and the Cloudflare Worker name.
- Components are small and readable; facts live in `site.config.mjs`; colours and fonts live in `global.css` tokens.
