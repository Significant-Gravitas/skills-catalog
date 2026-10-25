---
name: "website-build"
description: "Build or redesign a production-grade business website (Astro + Tailwind, static, fast, accessible, SEO-ready) from a brief, the owner's existing site or socials, and real content, with screenshot QA before anyone sees it. Use for 'build me a website', 'redesign my site', 'landing page', 'add a page'."
triggers: ["build a website", "new website", "redesign my website", "landing page", "website for my business", "make me a site", "add a page to my website", "website design", "rebuild our site", "one page website"]
version: "1"
---

# Website build

You are building a real website that a business will put its name on. The bar is a site a good independent web studio would ship: it loads fast on a phone, reads clearly, looks like this business and nobody else, and every fact on it is true. You do the work; the owner reacts to previews.

Package files live at `/home/user/skills/website-build/`:
- Scripts: `scripts/new-site.sh`, `scripts/qa.mjs`, `scripts/shoot.sh`.
- References: read `reference/design-direction.md` and `reference/content-and-seo.md` once per new site, before designing and writing. Open `reference/quality-bar.md` and `reference/forms-and-extras.md` only when you need them (final checks; forms, bookings, maps).

## The defaults (use them unless there is a real reason not to)

- **Stack:** Astro 7 static site, Tailwind 4, no client-side framework. Plain HTML and CSS with a sprinkle of JS beats React for a business site on speed, SEO, hosting cost and maintainability.
- **Where it lives:** `~/workspace/sites/<slug>/`, a git repo. `<slug>` is 3 to 20 characters of a-z, 0-9 and hyphens (e.g. `harbour-bakery`). The same slug becomes the GitHub repo and the Cloudflare Worker name, so choose it once and never change it.
- **Hosting:** the owner's own GitHub and Cloudflare accounts, free tier (see `website-hosting-setup`). Don't build anything that needs a server unless the brief truly needs one.
- **Pre-launch mode:** until launch day `site.launched` is `false` in `src/site.config.mjs`. Every page then carries `noindex` and `robots.txt` blocks crawlers, so the free workers.dev address works as an unlisted staging site that the owner can open, but search engines ignore. `website-launch-care` flips it at launch.
- **The project notes file:** `SITE.md` in the repo root. It holds the brief, the design direction, the page list, the accounts and addresses, the decisions and the status. Read it at the start of every turn that touches the site and update it before you stop. It is what lets work continue across turns, chats and budget pauses. It is private to the owner's repo; never put passwords or keys in it.

When not to build it yourself, said plainly with a recommendation:
- **A real online shop** (cart, stock, shipping, tax): recommend Shopify, Square Online or Etsy, and offer to build the brand site that links to it.
- **Logins, dashboards, members' areas or bookings with payments:** use a booking or membership service and embed it (see `reference/forms-and-extras.md`), or scope a separate app.
- **A shop, booking system or members' area already running on their current site** (a florist platform, a salon booking site, a WordPress shop): the new site can't replace it on the same address. Before launch, the owner (or you, with their OK) asks that vendor to serve it on its own subdomain (`shop.<domain>`, `book.<domain>`) or an address they provide, and the new site links to it. Launch waits until that address works. Record it in SITE.md as a launch blocker.
- **A blog the owner will update weekly without you:** say that edits go through you or a pull request. If they need self-serve editing, suggest a hosted CMS later; don't block the build on it.

## Stage plan (each stage ends with a commit and a SITE.md update)

A full site rarely fits in one turn. Work in these stages and stop cleanly between them if the turn's budget runs low, so the next turn (or the owner pressing "Keep going") resumes from SITE.md without redoing work.

1. **Resume check.** Run `ls ~/workspace/sites/ 2>/dev/null` and read the matching `SITE.md`. If the site exists only on GitHub (a new computer, or an existing repo), clone it: `cd ~/workspace/sites && gh repo clone <owner>/<slug> && cd <slug> && npm ci` (timeout 300). Never start a second copy of a site that already exists.
2. **Brief.** Gather before you ask (see Brief below).
3. **Scaffold.** `bash /home/user/skills/website-build/scripts/new-site.sh <slug> "<Business Name>"` with `timeout` 300. It copies a production starter (SEO head, structured data, sitemap, robots, 404, privacy page, contact page, security headers, Cloudflare config), installs, builds and makes the first commit. If the folder already exists, work in it. Then write SITE.md with the brief. Ignore other sites in `~/workspace/sites/` that aren't this one.
4. **Direction.** Read `reference/design-direction.md`. Write the direction (type, palette, layout idea, photography, voice) into SITE.md in about six lines. Tell the owner in one line, then carry on without waiting.
5. **Home page first.** Apply the design tokens, build the home page with real copy and real images, then run QA (below). The home page is what the owner judges you on, so make it the best page.
6. **First look, before any accounts.** Send the owner the home page screenshots (the phone one first, then desktop) with the one-line direction, and ask what they think. Don't ask them to connect GitHub or Cloudflare before they've seen and liked a design. In the same message say the next step: putting it on their free accounts, so every later look is a live link they can open on their phone. Carry on with the other pages while they react.
7. **Remaining pages.** Usually 3 to 6 more. Reuse components; keep the header nav to the pages a visitor actually needs.
8. **QA and commit.** Full QA on every page. Commit with a plain message.
9. **Hand off to publishing.** If SITE.md has no hosting yet, load `website-hosting-setup` once the owner is happy with the direction. Otherwise load `website-preview-publish` and send a preview.

**Budget:** each turn has a spending limit, and on smaller plans a full site takes several turns. When the turn's budget warning appears, finish the file you're on, then commit, update SITE.md, and tell the owner in one line what's done and what's next. If the day's budget is used up, offer to carry on tomorrow and schedule it with `tool:schedule_followup` (this chat's `session_id`, a morning time) so the owner doesn't have to remember.

## Brief: gather first, then ask once

Before asking anything, collect what already exists:
- **Their current website**, if any: `web_fetch` the home page and key pages. Keep every fact, the services, prices, hours, team names, testimonials, the logo file and photos. List every URL of the old site (try `/sitemap.xml`, then the nav links). The old URLs are needed for redirects at launch.
- **Google Business Profile, Facebook, Instagram, booking or menu pages** from a web search for the business name and town. These give hours, address, phone, reviews and photo style.
- **Files the owner uploaded** (logo, photos, menus, price lists). Look at images with `read_file` before using them.

Then ask once, batched, with `ask_question`, only for what you could not find and cannot sensibly default. Usually these:
- what the site must get visitors to do (call, book, visit, enquire, buy elsewhere);
- the three to five things they sell or do, in order of importance;
- the logo and real photos, if none were found;
- for an enquiry form, the form ID from Web3Forms (see `reference/forms-and-extras.md`: a public ID, about a minute to get);
- anything that must not appear.

Missing facts stay missing. No opening hours known? Leave `hoursText` empty and put the question in the batch. Never present something nearby (delivery times, phone hours) as opening hours.

Defaults when the owner doesn't say: pages Home, Services (or Menu), About, Contact, plus Privacy and 404. The primary action is a phone call on mobile and an enquiry form on desktop. Tone is plain, warm and specific.

Never invent a fact: no made-up prices, reviews, awards, years in business, team members, certifications, guarantees or statistics. Descriptive claims count too: "prices are on the board", "come in and test ride", "family-run", "same-day" are facts. Write them only if the owner or their materials say so. If a fact is missing, write around it or use a clearly marked placeholder (QA blocks launch until it is replaced). A preview can carry a few placeholders; a launch can't.

## Building

What the starter gives you (edit these; leave the rest):

| File | What it is |
|---|---|
| `src/site.config.mjs` | the business facts; everything reads it |
| `src/styles/global.css` | design tokens (`@theme`): colours and fonts |
| `src/layouts/Base.astro` | `<head>` (SEO, social tags, structured data, build marker), header and footer; import fonts here |
| `src/components/Header.astro` | name, call button and nav. Add pages to `nav`; on phones the links wrap onto their own row |
| `src/components/Footer.astro` | address, phone, email, hours and privacy link, from the config |
| `src/pages/index.astro` | home page, full of REPLACE markers that QA refuses to pass |
| `src/pages/contact.astro` | contact details, plus a Web3Forms form when `src/forms.config.mjs` has a form ID (otherwise an email button) |
| `src/pages/privacy.astro`, `404.astro`, `thanks.astro` | ready; adjust wording to the business |
| `public/` | `favicon.svg` and `og.png` placeholders (replace before launch), `_headers` |

The working rules:

- **Edit `src/site.config.mjs` first.** Name, description, locale (`en-GB` or `en-US` for English; it sets spelling and the page language), phone and `phoneHref` (international format, `+44...`), email, address, `hoursText` (for people) and `hours` (schema.org format), socials, schema type. Components read it, so facts live in one place. Leave `url` until hosting exists and `launched` false until launch.
- **Design tokens in `src/styles/global.css`** (`@theme`). Components use token classes (`bg-accent`, `text-muted`, `font-display`), never raw hex values. Fonts are self-hosted with Fontsource (`npm i @fontsource-variable/<font>`, then import it in `Base.astro`); never link Google Fonts.
- **Choosing photos from their old site or socials:** use only real, sharp, large-enough images (thumbnails under about 600 px wide look bad on modern screens). Skip anything with a photographer's watermark, identifiable customers or guests (wedding couples, patients), other brands' logos, or private details (names on sympathy cards, number plates). When in doubt, ask.
- **Images:** put photos in `src/assets/` and render them with Astro's `<Image>` (`import { Image } from 'astro:assets'`), giving width and height (or `widths`/`sizes` for responsive), real `alt` text, and `loading="eager"` only for the first image in view. The originals can be large; Astro makes small WebP files at build. Download the owner's existing photos with `curl -L -o`. Never use AI-generated or stock images that pretend to show the business's own staff, premises, products or customers. Neutral stock (texture, a city) is acceptable with a licence that allows it (Unsplash, Pexels); note the source in SITE.md.
- **Pages:** one `<h1>` per page, sensible heading order, and a unique title and description passed to `Base`. Add a page to the `nav` list in `src/components/Header.astro` when you build it, not before (QA treats links to unbuilt pages as broken), and only if it belongs in the menu.
- **Components:** keep them small (`Hero.astro`, `ServiceCard.astro`, `Testimonial.astro`, `CTA.astro`). No UI kits, no icon fonts. Inline SVG icons, few of them.
- **JS:** none by default. A mobile menu needs no JS if the nav fits; otherwise use a `<details>` element. Keep animation subtle, CSS only, and honour reduced motion (the starter does).
- **Forms:** use the starter's contact page with Web3Forms (`src/forms.config.mjs`); see `reference/forms-and-extras.md` for getting the key from the owner and for booking, maps and menu embeds.
- **Writing files:** write several files per `bash_exec` call with heredocs (`cat > path <<'EOF'`). Keep each call under about 2,000 words. Don't paste whole files back into the chat.

Shell habits that avoid stalls:
- Pass `timeout: 300` to `bash_exec` for `npm install`, `npm ci` and builds.
- Never start `astro dev` or `astro preview` and leave it running: background processes die when the turn ends. `shoot.sh` serves `dist/` itself and stops afterwards.
- Never `pkill -f` or `pgrep -f` with a pattern that also appears in your own command line; it matches your own shell. Kill by PID.
- Build output is long. Pipe it: `npm run build 2>&1 | tail -20`.

## QA loop (every page, every time before a preview)

From the project folder:

```bash
npm run build 2>&1 | tail -15
node /home/user/skills/website-build/scripts/qa.mjs
bash /home/user/skills/website-build/scripts/shoot.sh dist shots /
```

- `qa.mjs` checks placeholders, titles, descriptions, `h1`, `lang`, `alt` text, image dimensions, broken internal links, image weight, the sitemap and the 404. Fix every ERROR. Fix WARNs unless you can say why one is fine. `--launch` adds the checks that only matter for go-live.
- `shoot.sh` takes full-page shots, phone (390 px wide, real phone emulation) and desktop (1440 px), into `shots/`, and prints the file names. Pages taller than 2000 px come as slices, `home-phone-part0.png`, `-part1.png` and so on, top to bottom, because `read_file` accepts at most 2000 px. Pass a page path as the third argument for other pages (`/contact/`).
- **Look at every slice with `read_file`, phone first.** Bugs hide below the first screen: footers, forms, the last section on mobile. Check: text never touches the screen edge; nothing overflows sideways; the headline and main action are visible without scrolling on the phone; contrast is clearly readable; images aren't stretched or blurry; spacing is consistent; the page looks designed, not like a template. Fix and re-shoot until you would show it to a client.
- **Fact check before anyone sees it:** read the page text once more and trace every sentence to the brief or the owner's materials. Cut what you can't trace.
- If `shoot.sh` says no browser produced a screenshot, say so. Rely on QA and review the live preview by screenshotting its URL (`shoot.sh https://<preview-url>`) once it is deployed.

To show the owner, upload the phone shot (`home-phone.png`, or `home-phone-part0.png` for long pages, plus any slice that shows what you're asking about) with `write_workspace_file(source_path=...)` and embed it as `![Home on a phone](workspace://<id>#image/png)`. Add the desktop `part0` for a first look.

## Committing

```bash
git add -A && git commit -q -m "Home page: hero, services, reviews, contact strip"
```

Commit at the end of each stage. The commit messages become the change log the owner can read on GitHub, so write them in plain words. Pushing and previews belong to `website-preview-publish`; pushing needs the GitHub connection from `website-hosting-setup`.

## Telling the owner

Keep replies short. At the end of a building stage, give one line of what now exists and the next step. The first time, also give the direction in one line ("Warm cream and deep green, a serif headline, big food photos, booking button up top"). Ask about taste only when two directions are genuinely equal. Otherwise choose, show the preview and let them react.

When something they asked for is a bad idea (autoplay video, a carousel of ten slides, a wall of stock photos, a pop-up on arrival), say so in one line, do the better thing, and offer theirs if they still want it.
