# Design direction

Read this before designing a site. The aim is a site that looks like this business, one a stranger would trust in five seconds on a phone, and nothing like the generic AI template look.

## What makes a site look generic (avoid all of it)

- A purple-to-blue gradient hero, glassmorphism cards and floating blobs.
- "Elevate", "Unlock", "Seamless", "Your journey starts here" or any headline that could belong to any company.
- Three identical icon cards ("Quality / Service / Value") under the hero.
- Stock photos of smiling people at laptops, handshakes or a generic skyline.
- Everything centred, everything the same size, emojis as icons.
- Every section a white card with a shadow and rounded corners.
- A testimonial carousel with invented names.

## How to find the direction (in this order)

1. **The business itself.** What is it like to walk in, call or hire them? A family bakery, a criminal lawyer and a surf school should not share a layout. Write three adjectives the owner would agree with ("warm, unfussy, local" or "precise, calm, expensive").
2. **Their real assets.** Logo colours, shopfront, van, menu, uniforms, the photos they already post. Take the palette from these, not from a palette generator.
3. **Their customers' moment.** Someone with a burst pipe needs the phone number in the top corner on a phone. Someone choosing a wedding venue wants big photos and a calm pace. Design for that moment.
4. **The category's good examples.** Look at two or three well-regarded sites in the same trade and town (web search), and note what they do well. Don't copy them.

Write the direction into SITE.md like this:

```
Direction: warm, unfussy, local
Type: Fraunces (headlines, 600) + Inter (body)
Palette: cream #FBF6EE surface, espresso #2B1D14 ink, terracotta #C4562B accent, muted #6E5C50, line #E9DFD2
Layout: big photo hero with the hours and the "Order for pickup" button over it; menu as a clean two-column list, not cards
Photography: their own Instagram photos, warm and close-up; no stock people
Voice: short sentences, first person plural, a little dry humour
```

## Type

Use one or two families, self-hosted with Fontsource. Install the package, then import it once in `src/layouts/Base.astro` (`import '@fontsource-variable/fraunces';`) and set the tokens in `global.css`:

```css
--font-display: "Fraunces Variable", Georgia, serif;
--font-sans: "Inter Variable", ui-sans-serif, system-ui, sans-serif;
```

Pairings that work (npm package names checked October 2026):

| Feel | Headline | Body |
|---|---|---|
| Warm, crafted (food, bakery, florist) | `@fontsource-variable/fraunces` | `@fontsource-variable/inter` |
| Editorial, established (law, finance, consultancy) | `@fontsource-variable/source-serif-4` or `@fontsource-variable/newsreader` | `@fontsource-variable/libre-franklin` |
| Modern, confident (trades, fitness, tech services) | `@fontsource-variable/bricolage-grotesque` or `@fontsource-variable/space-grotesk` | `@fontsource-variable/dm-sans` |
| Friendly, clear (health, childcare, community) | `@fontsource-variable/figtree` or `@fontsource-variable/outfit` | the same family |
| Elegant, high-end (venues, salons, interiors) | `@fontsource-variable/cormorant-garamond` or `@fontsource/instrument-serif` | `@fontsource-variable/manrope` or `@fontsource-variable/instrument-sans` |
| Plain and serious (B2B, engineering) | `@fontsource-variable/schibsted-grotesk` or `@fontsource-variable/archivo` | the same family |

Variable packages register the family as "<Name> Variable". Non-variable ones (`@fontsource/instrument-serif`) register "<Name>" and only include weight 400 unless you import a weight file (`@fontsource/instrument-serif/400.css`).

Sizes and rhythm:
- Body 17 to 18 px on mobile (`text-[17px] sm:text-lg`), line height about 1.6, line length 60 to 75 characters (`max-w-prose` or `max-w-2xl`).
- Headline scale with clear steps: h1 `text-4xl sm:text-6xl`, h2 `text-2xl sm:text-4xl`, h3 `text-xl`. Tighten tracking on big headlines (`tracking-tight`).
- Never more than three font sizes in one section.

## Colour

- Five tokens are enough: surface, ink, muted, line, accent (plus accent-ink, the text colour on the accent). Add a second accent only if the brand truly has one.
- Body text contrast at least 4.5:1, large text at least 3:1. Check with this one-liner (WCAG relative luminance):
  ```bash
  node -e 'const L=h=>{const c=h.match(/\w\w/g).map(x=>parseInt(x,16)/255).map(v=>v<=0.03928?v/12.92:((v+0.055)/1.055)**2.4);return 0.2126*c[0]+0.7152*c[1]+0.0722*c[2]};const [a,b]=process.argv.slice(1).map(L);console.log(((Math.max(a,b)+0.05)/(Math.min(a,b)+0.05)).toFixed(2))' 2B1D14 FBF6EE
  ```
- An off-white or tinted surface (cream, stone, cool grey) usually looks more considered than pure white. Pure black text is harsh; use a very dark brand-tinted ink.
- Use the accent for actions and small highlights, not for big backgrounds, unless the brand is loud on purpose.

## Layout

- **Mobile first.** Design the 390 px layout, then let it open up. Most local-business visitors are on phones.
- **The first screen on a phone** shows who they are, what they do, where (if local), and the main action. For trades and emergencies, put a tap-to-call button in the header.
- **Vary the sections.** Alternate full-bleed photo, text-plus-image split, a simple list, a quote. Not five card grids in a row.
- **Spacing:** generous and consistent. Section padding `py-16 sm:py-24`, content width `max-w-6xl` with `px-5`. Align things to a few shared edges.
- **Real proof near the action:** a genuine review with the reviewer's first name and source ("Google review"), the number of years only if true, logos of real clients only with permission.
- **Contact details in the footer on every page:** name, address, phone, email and hours, matching the Google Business Profile exactly.

## Photography

- Their own photos beat any stock. Ask for 5 to 15: the place, the work, the people, the product.
- Crop with intent: one strong hero image, then supporting images at consistent aspect ratios (`aspect-[4/3] object-cover`).
- If they have no photos yet, design a typographic hero with a strong colour field rather than fake stock. Say what photos would lift it, and suggest a phone shoot list (shopfront in morning light, hands at work, the three best products, the team).

## Motion

- Subtle or none. A fade-up on scroll is fine; parallax, autoplaying carousels and animated counters are not.
- Respect `prefers-reduced-motion` (the starter disables animation for those visitors).

## Self-check before the first preview

Look at the phone screenshot and ask:
- Could this header and hero belong to a different business? If yes, it's generic. Use their name, their place, their photo, their words.
- Is the main action obvious within one second?
- Does it look calm? Count the colours, font sizes and button styles on screen. Fewer is better.
- Would the owner proudly send it to their best customer?
