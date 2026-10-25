# The design standard

Read all of this before designing any site, and re-read the checklist at the end before every critique.

## The bar

Every site you make is built to be featured on Awwwards (Site of the Day), Godly and Siteinspire, and to make the owner's competitors feel embarrassed. It must also load fast on a cheap phone, work for screen readers, and sell the business's services.

"Clean and professional" is a failure. A site that a Squarespace, Wix or Framer template could produce is a failure. A site that looks like other AI-made sites is the worst failure of all.

You have no budget limit on craft. A top studio would charge £30,000 for this site; that is the quality the owner gets. Small business doesn't mean small ambition. A bike shop, a florist or a plumber deserves a site people talk about, and an unforgettable site is the best marketing a small business can buy.

These six questions must all be answered yes before anything is shown to anyone:
1. **Recognisable:** with the logo and name hidden, would someone who knows the business recognise it from one screenshot?
2. **Shareable:** would a design-literate stranger screenshot it to show a friend?
3. **New:** is there at least one moment on the site they have never seen before?
4. **Untemplatable:** could no website builder template produce this? If any template could, start again.
5. **Varied:** does every section have its own composition, rather than the same container with different content?
6. **Typographic:** would the typography alone carry the brand, with all images removed?

## Step 1. Study the best, every time

Before any concept, look at the current best work. Don't rely on memory: taste goes stale, and memory converges on the average.

1. Find 8 to 12 reference sites:
   - 4 to 6 from the award galleries: https://godly.website, https://www.awwwards.com/websites/sites_of_the_day/, https://www.siteinspire.com, https://land-book.com, https://www.lapa.ninja. Open the gallery page and follow through to the live sites.
   - 2 or 3 from the business's own category done brilliantly anywhere in the world, for example "best florist website design" or "award-winning restaurant website".
   - 2 or 3 from a completely different world that matches the concept's mood: a fashion house, a museum, an architect, a record label.
2. Screenshot 5 or 6 of them and look at every image: `SHOOT_WAIT=6000 bash /home/user/skills/website-build/scripts/shoot.sh <url> refs` (award sites often show a preloader first), plus `... shoot.sh <url> refs / frames` to see their motion. If a site shows a black preloader or a bot wall even then, use the gallery's own screenshots of it: the Awwwards page `/sites/<name>`, or the og:image or preview on Godly or Siteinspire. Look at those with `read_file` after downloading them.
3. For each one, write one line in SITE.md about the specific move that makes it great. Not "clean design": things like "headline set at 18vw in a condensed grotesk, bleeding off both edges, with the photo masked inside the letterforms", or "services as a long index list; hovering a row reveals a full-bleed photo behind the type".
4. Steal moves, never layouts. Combine moves from different references into something new.

## Step 2. A concept, not a theme

Great sites start from one idea, rooted in something true about the business, that decides everything else: type, grid, colour, imagery, motion and copy.

How to find it:
1. **List the business's material world:** its objects, tools, materials, places, rituals, vocabulary, sounds, time of day, history and customers' moments. A bike shop has chainrings, grease, spoke patterns, tide tables (in a harbour town), Ordnance Survey maps, workshop tickets and the click of a freewheel. A florist has Latin plant names, herbarium sheets, wrapping paper, seasons, and the cold room at 5am.
2. **Name the promise in one line,** in the customer's terms: "back on the road this week"; "flowers that say what you can't".
3. **Find the metaphor where the two meet,** and turn it into a visual system.

Examples of the level expected:
- **A harbour-town bike shop, "The Tide Table":** the site is typeset like a nautical almanac. Opening hours are set as tide times. Services form a chart legend with dotted leaders. A tide line rises through the page as you scroll and bikes sit on the waterline. Condensed grotesk display with a monospaced almanac face; sea-ink and buoy-orange on chart paper.
- **A family bakery, "4am":** the site starts in the dark at 4am, lit by oven glow, and dawn breaks as you scroll down. The palette moves from black and ember to flour-white and butter. The loaves come out of the oven as the clock in the corner ticks to opening time.
- **A florist, "The Herbarium":** every arrangement is presented as a pressed specimen on archival paper, with a Latin name, collector's label and catalogue number. A serif with real character; hairline rules; botanical illustrations drawn in SVG.
- **A plumber, "Schematic":** blueprint-blue line drawings of pipes route through the page and connect the sections. Each service is a numbered fitting in a parts diagram. An engineering mono, with a fat grotesk for headlines.
- **A criminal defence solicitor, "The Brief":** a broadsheet layout with massive serif headlines and column text, pull quotes from real outcomes, and an austere palette of newsprint, black and one red.

These examples show the level of thinking, not concepts to reuse. If the business matches one of them, find a different idea.

Write three concepts that differ in every dimension: type, colour, composition and motion language. For each, give a name, the idea in two sentences, the signature moment, the type pairing, the palette, the layout system and the motion language. Choose the boldest one that still makes the business's main action obvious. Record all three, and why you chose this one, in SITE.md. If the owner wants a different direction later, the other two are ready.

## Step 3. The signature moment

Every site has at least one moment that only it has. It's the thing people remember and mention. Ideas:
- an interaction that embodies the concept (scroll raises the tide; dragging bends a flower stem; the cursor is a spanner that tightens bolts on the service list);
- a typographic event: the name assembles from parts as the page loads, or a word morphs through variable-font axes as you scroll;
- an image that does something unexpected: a photo masked inside giant letters, or a before-and-after wipe of a repaired bike;
- a data moment made beautiful: today's actual opening state ("Open now, closes in 2h 14m"), or the season's flowers shown by month.

It must work without JavaScript as a static composition, and respect reduced motion.

## Typography

- **Display type is the hero.** Set headlines at real scale: `clamp(3.5rem, 12vw, 14rem)` is normal for a hero word. Use tight leading (0.85 to 0.95) and negative tracking (-0.02em to -0.05em). Let type bleed off the edge, overlap images, run vertically, or fill the viewport.
- **Pair with intent.** Combine a characterful display face with a disciplined text face, often with a monospaced or small-caps accent for labels, numbers and metadata. Use two families at most, plus one mono.
- **Use the fonts the best sites use.** Choose them for the concept, never because they're familiar:
  - **Fontshare** (free for commercial use, ITF Free Font License): Clash Display, Clash Grotesk, Cabinet Grotesk, Satoshi, General Sans, Switzer, Supreme, Gambetta, Zodiak, Erode, Sentient, Boska, Gambarino, Melodrama, Bespoke Serif, Bespoke Stencil, Panchang, Tanker, Chillax, Telma, Excon.
  - **Fontsource** (Google Fonts and more): Fraunces (with its SOFT and WONK axes), Instrument Serif, Young Serif, Gloock, Bodoni Moda, Libre Caslon Display, Cormorant, Italiana, DM Serif Display, Syne, Unbounded, Big Shoulders Display, Bricolage Grotesque, Familjen Grotesk, Darker Grotesque, Hanken Grotesk, Space Mono, JetBrains Mono, IBM Plex Mono, Martian Mono.
  - Install with `scripts/add-font.mjs` (see `craft-techniques.md`).
  - Never Inter, Roboto, Open Sans, Lato, Montserrat or Poppins as the display face. If Inter appears anywhere, justify it.
- **Typographic detail is where craft shows:**
  - `text-wrap: balance` on headlines and `pretty` on paragraphs;
  - tabular figures for prices and times (`font-variant-numeric: tabular-nums`);
  - small caps or mono for labels;
  - hanging punctuation on pull quotes;
  - real quotation marks and apostrophes;
  - deliberate line breaks in headlines, so no orphaned words.
- **Use variable axes** (weight, optical size, width, softness) for hover states and scroll effects.

## Composition

- **The hero is a poster, not a form.** "Headline, subhead, two buttons, image on the right" is banned. Compose the first screen like a magazine cover or a film poster: one dominant element, a surprising scale relationship, and the main action placed with intent. The business's name, what it does, where, and how to act must still be clear within three seconds.
- **Use a real grid and break it on purpose.** Work on a 12-column grid (or a concept-specific one, such as an almanac table or a broadsheet's columns). Use asymmetry, overlaps (type over image, image breaking out of its column), full-bleed moments next to tight text columns, and extreme whitespace next to density.
- **Make every section a different composition.** Vary scale, density, alignment and rhythm down the page: a full-bleed image, then an index list, then a pinned storytelling sequence, then a quote set enormous, then a horizontal scroller. Never use the same container-with-heading-and-cards pattern twice.
- **Treat the edges.** Use the whole viewport. Content stuck in a centred 1100 px column on a 1440 px screen is a template tell.
- **Mobile is designed too, not just stacked.** Re-compose for 390 px: big type stays big (fluid), interactions become touch-native (swipe, tap reveals), and the signature moment has a mobile form.

## Imagery

- **Art-direct every image:** deliberate crops, consistent treatment (a duotone in the palette, grain, a colour grade), masks and clip-paths, and scale contrast (one enormous image next to small details).
- **Their real photos come first.** Make even average phone photos look intentional through crop, treatment, scale and context.
- **No usable photos?** Make this a design opportunity, not a gap:
  1. **Bespoke illustration in code:** SVG drawings, patterns and generative art that come from the concept (tide lines, spoke patterns, herbarium line drawings, blueprint schematics). Draw them properly: many paths, real detail, consistent line weight.
  2. **AI-generated art direction** through the platform's image generator (`find_capability(query="generate image")`):
     - Use it for atmospheric and illustrative images: texture, landscape, still life, abstract and editorial illustration.
     - Use one consistent prompt style, palette and treatment across the set. Generate several and keep only the best.
     - Never depict the business's actual staff, premises, products or customers as if they were real. Never generate fake people for testimonials or a team.
     - Tell the owner which images are generated, and give them a short shoot list to replace them later.
  3. **Typography as image:** posters built from type alone.
- **Never use generic stock photos** (handshakes, laptops, smiling models), flat icon sets, or emoji as icons.

## Colour, texture and light

- **Palettes with conviction:** one dominant colour, one surprising accent, used sparingly and precisely. Consider dark sites, saturated sites and duotone sites; the timid white-plus-blue default is banned.
- **Material:** grain or noise overlays, paper tones, printed-ink effects (multiply blending, misregistration), glass and light only where the concept calls for it.
- **Colour changes as story:** sections can change the page's background (dawn breaking, tide rising) as you scroll.
- **Contrast stays accessible:** at least 4.5:1 for body text. Bold design and accessibility are not in conflict.

## Motion

Motion is choreography, not decoration. Every movement says something about the concept.

- **Load sequence:** the first screen assembles in under 1.2 seconds. Headline lines rise out of masks, staggered 60 to 90 ms apart. The image wipes in. The main action arrives last. It never delays reading: the text is in the HTML at full opacity for anyone without JS or with reduced motion.
- **Scroll:**
  - parallax depth between layers;
  - pinned sequences that tell a short story (three steps of a service, the day of a bakery);
  - progress-linked transforms: scale, clip-path, colour and variable-font axes;
  - reveals that use masks and transforms, not just opacity fades.
- **Hover and touch:** every interactive element responds. Underlines draw, buttons attract (magnetic), list rows reveal images, and cursors change where the concept supports it. On touch, the equivalent happens on tap or as the element enters the viewport.
- **Page transitions:** Astro view transitions with shared elements (the hero image morphs into the detail page).
- **Easing and timing:** use custom curves such as `cubic-bezier(.16,1,.3,1)` (expo out) and `cubic-bezier(.65,0,.35,1)` (in-out). Avoid linear and the default `ease`. Use 400 to 900 ms for big moves and 150 to 250 ms for micro-interactions.
- **Tools:** CSS scroll-driven animations first (`animation-timeline: view()`). Use GSAP with ScrollTrigger (free, including all plugins) for choreography that CSS can't do. Use Lenis for smooth scrolling when it suits the concept. Techniques and tested code are in `craft-techniques.md`.
- **Reduced motion:** everything has a `prefers-reduced-motion` path that shows the final composition without movement.

## Details that separate great from good

- The header is designed for the concept: transparent over the hero, `mix-blend-mode: difference`, a navigation index, or a menu that opens into a full-screen typographic moment. It is never a white bar with links on the right.
- The footer is a finale: the name enormous, contact details set beautifully, maybe the signature moment once more. It is never a three-column link dump.
- Text selection colour, focus rings, scrollbar and caret colour are styled to match.
- The 404 page and the thanks page carry the concept. The 404 is often the funniest page on a great site.
- The favicon and the social share image are designed from the concept.
- Micro-copy has voice: button labels, form placeholders, the "open now" line.
- Numbers, prices and times are typeset like data.
- Loading feels instant: fonts preloaded, nothing jumps, and images arrive with intent.

## Copy

Design and copy are one piece of work. Write headlines that a great copywriter would be proud of: specific, rhythmic, sometimes witty, always true. "Bikes, back on the road the same week" is fine. "Flat tyre? Low tide? Either way, we'll get you out by Friday." is the level to aim for. It is true for that shop, says where it is, and sounds like a person. Every fact still has to come from the owner; voice is where you have freedom.

## Banned: an instant fail if any of these appear

- A hero of headline, subhead and two buttons in a left column, with an image or plain colour on the right.
- A row of three (or four) identical cards with an icon, a title and two lines of text.
- Centred section titles with a grey paragraph underneath, repeated down the page.
- Alternating zigzag image and text rows.
- "How we can help", "Why choose us", "Our services" or "What our clients say" as headings.
- Default Tailwind looks: `rounded-md` buttons everywhere, `text-gray-600` paragraphs, `shadow` cards, everything inside `max-w-6xl mx-auto`.
- Gradient blobs, glassmorphism or purple-to-blue gradients without a concept reason.
- Generic stock photos, generic icon sets, emoji icons.
- Inter, Roboto, Poppins or Montserrat as display type.
- A white top bar with a logo on the left and links on the right, as the only header idea.
- Fade-in-on-scroll applied identically to every element as the only motion.
- Any section you could paste unchanged into another business's site.

## The critique loop (mandatory, at least twice before any owner sees the site)

After the hero, and again after the full page:
1. Capture everything and look at every image:
   - `shoot.sh dist shots /` for full pages (rendered with reduced motion, so they show the final composition);
   - `shoot.sh dist shots / frames` for motion contact sheets. Add `FRAMES_AT=...` to land frames inside pinned sections, and `SHOOT_EVAL=...` to capture the open menu or a hover state;
   - `bash /home/user/skills/website-build/scripts/speed.sh dist` for Lighthouse scores. The sandbox CPU is slow, so treat its performance score as a floor, but the "Fix first" list is real.
2. Put your work next to your two strongest reference screenshots. Look at them back to back.
3. Write the harshest critique an Awwwards juror would write: specific and unsparing. Then score each 1 to 10:

   | Criterion | 10 looks like |
   |---|---|
   | Concept | one idea, rooted in the business, visible in every section |
   | Typography | expressive, perfectly set; it could carry the brand alone |
   | Composition | varied, bold, gridded and deliberately broken; designed for phones too |
   | Imagery | art-directed and consistent; no weak image anywhere |
   | Motion | choreographed and meaningful; perfect easing; a reduced-motion path |
   | Signature moment | genuinely new; people would mention it |
   | Detail | header, footer, 404, states, micro-copy, favicon all crafted |
   | Distinctiveness | it could only be this business; no template could produce it |
   | Business clarity | who, what, where and how to act are clear in 3 seconds |
   | Speed and access | measured with speed.sh, never estimated. Accessibility 95+; performance 90+, or 75+ on the sandbox's slow CPU with nothing but minor items in its Fix first list; contrast, keyboard and reduced motion all work |

4. Anything below 9 gets redesigned, not tweaked: rethink that part, rebuild it, re-capture and re-score. Record each round's scores and changes in SITE.md.
5. Only when every score is 9 or 10, and all six questions at the top are yes, does the owner see it.

Be honest in scoring. Inflated scores make you ship mediocre work, and the owner will notice even if you don't.
