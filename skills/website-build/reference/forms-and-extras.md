# Forms, bookings, maps and other extras

The site is static, so anything interactive comes from a small trusted service. Pick the simplest one that does the job, and prefer what the owner already uses.

## Contact form: Web3Forms (default)

Why: free for 250 submissions a month, no server, no account to manage. The owner gets each message by email. Submissions are only kept in the Web3Forms dashboard for 30 days on the free plan, which doesn't matter because they arrive by email.

Getting the form ID (the owner does this, about one minute):
1. Open https://web3forms.com and enter the email address that should receive enquiries in "Create your Access Key". Use a business address the owner reads daily.
2. Web3Forms emails them an access key. They paste it into the chat.

This key is a public form identifier. It sits in the page's HTML and only lets the form deliver to that inbox, so it is not a password or API key, and the "don't share keys in chat" rule doesn't apply to it. Call it the "form ID" when you ask, so the owner isn't alarmed.

Put it in `src/forms.config.mjs` (`web3formsKey: '...'`). The starter's contact page then shows the form, with a hidden spam honeypot. It sends in the background and then shows the site's own `/thanks/` page. Without JavaScript, the form still works and lands on Web3Forms' thank-you page. Until there's a form ID, the page shows the phone number and email address only.

Test it before launch: submit one real test message from the production workers.dev address and ask the owner to confirm it arrived (check spam too). An untested contact form is the most common way a new site silently loses business.

Alternatives:
- **Formspree** (free for 50 submissions a month): the form posts to `https://formspree.io/f/<form-id>`. Good if the owner already has it.
- **Existing tools**: if they use HubSpot, Mailchimp, Typeform, Jotform or Tally, embed or link that form instead.
- **No form at all** is a fine choice for trades that live on the phone: big tap-to-call and WhatsApp buttons (`https://wa.me/<number-in-international-format-without-plus>`).

## Bookings and appointments

Embed or link the system the owner already uses. Don't build booking logic.
- Services and appointments: Calendly, Square Appointments, Fresha, Treatwell, Booksy, Acuity, SimplyBook.me, Cal.com.
- Restaurants: OpenTable, Resy, SevenRooms, ResDiary, or their EPOS booking page.
- Classes and fitness: Mindbody, Glofox, TeamUp.

Prefer a clear "Book now" button that opens the booking page over a heavy inline widget on the home page. If an inline embed is wanted, put it on the Book page only, and lazy-load it:

```astro
<iframe src="https://calendly.com/<user>/<event>" title="Book an appointment" loading="lazy" class="h-[720px] w-full rounded-md border border-line"></iframe>
```

## Maps

- No API key is needed for a basic embed: `https://www.google.com/maps?q=<url-encoded business name and address>&output=embed`.
- Put it on the Contact page only, `loading="lazy"`, with a plain text address and a "Get directions" link next to it (`https://www.google.com/maps/dir/?api=1&destination=<url-encoded address>`).
- On the home page, a small static image of the area with the address and a directions link is lighter than a live map.

## Menus, price lists and documents

- Put menus and price lists on the page as real HTML text, so they're searchable, readable on phones and easy to update. A PDF download can sit alongside, not instead.
- Store prices in a small data file (`src/data/menu.json` or `.ts`) and render it, so updates are one edit.

## Reviews

- Quote real reviews (first name, source, date), with the owner's agreement, as static text. Link to the Google reviews page.
- Avoid live review widgets: they're slow, often break, and some inject tracking.

## Social media

- Link to profiles with simple icons in the footer.
- Don't embed live Instagram or Facebook feeds; they're slow, often break and track visitors. If the feed matters, show a few photos the owner supplies, linking to the profile.

## Video

- Never autoplay with sound. For a hero video, use a short silent muted loop under 3 MB with a poster image, or just a strong photo.
- For YouTube, use a click-to-load thumbnail (or `youtube-nocookie.com` with `loading="lazy"`).

## Newsletter sign-up

Use the owner's email tool's embed form (Mailchimp, MailerLite, Kit, Buttondown). Put it in the footer or on one page, not as a pop-up.

## Analytics

Cloudflare Web Analytics: free, no cookies, no consent banner needed. It's enabled at launch (see `website-launch-care`). Don't add Google Analytics unless the owner insists; if they do, it needs a cookie consent banner in the UK and EU.
