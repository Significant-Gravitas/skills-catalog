# Content and SEO

Read this before writing copy. Good copy is specific, true and written for the customer's moment. Good small-business SEO is mostly the same thing, plus a few technical basics the starter already covers.

## Copy rules

- **Lead with the customer's need, in their words.** "Same-day boiler repairs in Leeds", not "Excellence in heating solutions".
- **Specific beats impressive.** "Open 7am, sourdough out by 8" beats "Artisan baked goods".
- **Short sentences, plain words, active voice.** Read it aloud; cut anything you'd skip.
- **One idea per section, with one clear action.** Repeat the primary action (call, book, enquire) at the top, the middle and the end.
- **Facts come from the owner, their existing site, their Google Business Profile or their materials.** Never invent prices, reviews, awards, years, team members, guarantees or numbers. If a strong claim would help but you don't have it, ask for it as a specific question ("How many years have you been trading?").
- **Keep the owner's voice.** If their Instagram is chatty, the site can be too. A solicitor's site should sound like a careful solicitor.
- **No filler sections.** No "Our Mission/Vision/Values" unless the owner has real ones. No lorem ipsum ever; QA blocks it.
- **Headings say something.** Never "Our services", "How we can help", "Why choose us" or "What our clients say". Write headings in the concept's voice that carry information ("Fixed by Friday, priced on the board" only if both facts are true; "The tide table" for opening hours in an almanac concept).
- **Voice is where you have freedom; facts are where you have none.** Write like the brand's best copywriter: rhythm, wit, specificity. Every claim still traces to the owner's facts.

## Page set by business type (adapt, don't pad)

| Type | Pages |
|---|---|
| Local service (trades, cleaning, repairs) | Home (services, area covered, reviews, call button), Services (one section or page per main service), About, Contact |
| Food and drink | Home (hours, location, signature items, order or book), Menu (real HTML text, not a PDF only), About or Story, Contact and find us |
| Health, beauty, wellness | Home, Treatments with prices, Team, Book (embed their booking system), Contact |
| Professional services | Home, Services or Practice areas, Team (real bios), Insights only if they will write them, Contact |
| Event venue, hospitality | Home with big imagery, Spaces, Packages or Rates, Gallery, Enquire |
| Single offer or campaign | One landing page: promise, proof, details, FAQ, one action |

Every site also gets Privacy and 404 (both in the starter).

## Titles and descriptions

- **Title:** about 50 to 60 characters. Home: `<Business> | <What> in <Place>`. Other pages: `<Page topic> in <Place>`; the layout appends `| <Business>`.
- **Description:** 120 to 155 characters. Say what, where and why, and end with the action. No keyword stuffing.
- **Headings:** one `h1` per page that says what the page is about in human words; `h2`s for sections, in order.

## Local SEO basics (these move the needle for small businesses)

1. **Name, address and phone are identical everywhere:** the site footer, the contact page, `site.config.mjs`, Google Business Profile, Facebook and directories. The starter puts them in structured data (schema.org) from `site.config.mjs`; set `schemaType` to the closest type (Restaurant, Bakery, Plumber, Dentist, HairSalon, LegalService, AccountingService, ProfessionalService...).
2. **A page or section per main service, and the towns served,** in real sentences. Don't build doorway pages for twenty towns.
3. **Google Business Profile** is often worth more than the website for local search. At launch the owner adds the new website address to it (see `website-launch-care`).
4. **Real reviews**, quoted with first name and source, with the owner's permission. Never fabricate or "improve" them.
5. **Fast and mobile-friendly.** The starter and the image rules handle this; QA and PageSpeed confirm it.

## When replacing an existing site

- List every old URL before building (sitemap, nav, a quick crawl). Keep the URLs that have value (`/menu`, `/services/boiler-repair`) the same where possible.
- Every old URL that changes gets a 301 redirect in `public/_redirects` at launch (`website-launch-care` covers it). This keeps their Google rankings and old links working.
- Carry over the content that works: their best-performing pages, reviews, FAQs. Improve the writing, keep the facts.

## Images and alt text

- Alt text says what the image shows and why it's there, in one plain sentence ("Fresh sourdough loaves cooling on the bakery counter"). Decorative images get `alt=""`.
- Never put important text inside images; search engines and screen readers can't read it reliably.

## Social previews

- `public/og.png` is the image shown when a page is shared on WhatsApp, Facebook, LinkedIn and others. Make it 1200 x 630: the logo or name, a short line, a brand colour or a strong photo. The starter makes a plain placeholder; replace it before launch (QA in launch mode checks).
- A page can pass its own `image` to `Base` (a path under `public/`).
