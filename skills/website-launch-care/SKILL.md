---
name: "website-launch-care"
description: "Launch a website properly and look after it afterwards: pre-launch checklist, speed and accessibility scores, keeping old URLs working with redirects, Google Search Console, Google Business Profile, free visitor stats, email forwarding, weekly health checks and a client handover pack. Use for 'launch the site', 'go live checklist', 'get it on Google', 'site maintenance', 'hand the site over to the client'."
triggers: ["launch the website", "go live checklist", "get my site on google", "search console", "website maintenance", "hand over the website", "website analytics", "old website links", "website health check", "is my website ok"]
version: "1"
---

# Website launch and care

Launch is the day the domain points at the new site. Done well, nobody notices anything except a better site: old links still work, Google picks it up within days, the contact form delivers, and the owner knows what they have. Afterwards, a light routine keeps it healthy.

Package files under `/home/user/skills/website-launch-care/`:
- `scripts/speed.sh`: Lighthouse scores for a live URL.
- `scripts/old-urls.py`: lists an existing site's URLs.
- `scripts/check-redirects.sh`: proves old URLs still land.
- `reference/handover-template.md`: the owner or client handover pack.

## 1. Before launch (on the production workers.dev address)

Work through this, fix what fails, and record the results in SITE.md:

1. **Content signed off.** The owner has seen and approved every page through previews. Run `node /home/user/skills/website-build/scripts/qa.mjs --launch`. At this point the only errors allowed are pre-launch mode and the site address; those two are cleared in the launch commit. Fix everything else now. Load `website-build` if its files aren't in `/home/user/skills/`.
2. **Old URLs captured** (when replacing a site). Do this before the domain moves, while the old site is still up:
   ```bash
   cd ~/workspace/sites/<slug>
   python3 /home/user/skills/website-launch-care/scripts/old-urls.py https://<old-domain> > old-urls.txt
   ```
   Map every old path that doesn't exist on the new site to its best new page in `public/_redirects`, one rule per line:
   ```
   /about-us        /about/        301
   /services.html   /services/     301
   /blog/*          /news/         301
   ```
   Exact rules match the path only, not `?query` strings. Wildcard rules (`/gallery/*`) also catch URLs with queries and carry the query over. Up to 2,000 static and 100 wildcard rules are allowed. Group numbered families (`/design-123/...`) under one wildcard rule.
   - Anything without a sensible equivalent goes to the closest section, not to the home page.
   - Where there's no section at all (for example a shop that isn't moving), list it in SITE.md under "Unmapped old URLs, owner decision". Launch waits until the owner decides.
   - Commit `old-urls.txt` too.
3. **Contact form tested.** Submit a real test message on the production address. The owner confirms it arrived (check spam).
4. **Phone and email links** tapped on the phone screenshot or tested by the owner.
5. **Speed and accessibility:**
   ```bash
   bash /home/user/skills/website-launch-care/scripts/speed.sh https://<slug>.<subdomain>.workers.dev/
   ```
   Pass `timeout: 360`. Targets: accessibility, best practices and SEO at least 95, performance at least 90 on Google's own test. The sandbox's Lighthouse runs on a small machine, so its performance score is pessimistic; treat 75+ there as fine if the listed problems are minor. Fix the "Fix first" items that are real (oversized images, missing alt, low contrast, render-blocking fonts).
6. **Social preview:** `public/og.png` is a real 1200 x 630 image, and the favicon is the real logo mark.
7. **Legal:** the privacy notice matches what the site collects and the owner has read it. Company details are present where the law requires them.
8. **Analytics decided:** Cloudflare Web Analytics by default (step 3 below).

Tell the owner what's ready in two or three lines, plus anything they must still give you, then agree the launch moment. A weekday morning is best; avoid Friday evenings.

## 2. Launch

1. Attach the domain: follow "Attach the domain" in `website-custom-domain`. It covers the DNS cutover, the certificate, the www redirect, and the launch commit (`site.url`, `launched: true`, the route in `wrangler.jsonc`), then waits for the domain to serve it.
2. Check the old URLs: `bash /home/user/skills/website-launch-care/scripts/check-redirects.sh https://<domain> old-urls.txt`. Fix every BROKEN line with a `_redirects` rule, publish, and re-run.
3. Check the domain once more: `python3 /home/user/skills/website-custom-domain/scripts/dnscheck.py status <domain>`, then `speed.sh https://<domain>/`.
4. Tell the owner it's live, with the link and the two or three things you checked (old links, form, email).
5. **Launching without a domain** (the owner chose to stay on the workers.dev address): the launch commit is just `launched: true` in `src/site.config.mjs`, with `site.url` kept as the workers.dev address. Run QA in launch mode, push to `main`, `wait` until it's live, and record `Launched: <date>, on workers.dev` in SITE.md. Search Console then uses a URL-prefix property for that address.
6. If an old website or hosting plan was replaced, schedule a reminder for a week later (`tool:schedule_followup` into this chat): suggest cancelling the old website plan (Wix, Squarespace, old hosting) once they're happy. Never cancel the domain, or any email service that still runs on it.

## 3. Straight after launch (the owner clicks; you guide, one message each)

**Google Search Console** (gets the site into Google search and reports problems):
1. Go to https://search.google.com/search-console and sign in with the Google account that should own the site's data. The business account is better than a personal one.
2. **Add property**, choose **Domain**, type `<domain>`, then **Continue**.
3. Google notices the domain is on Cloudflare and offers **Start verification**. Sign in to Cloudflare when asked and **Authorize**. Verification adds a TXT record automatically. If it shows a TXT record to copy instead, send it to me: I'll add it through the Cloudflare integration, or tell you where to paste it under **DNS > Records**.
4. Open **Sitemaps** and submit `sitemap-index.xml`.
5. If this replaced an old site on the same domain, nothing else is needed: the redirects carry the rankings over.

**Bing (and through it, ChatGPT search and Copilot):** https://www.bing.com/webmasters, sign in, **Import from Google Search Console**. That's one click once Search Console is verified.

**Google Business Profile** (often the biggest source of local customers): https://business.google.com, then **Edit profile > Contact > Website**. Put in `https://<domain>`, then **Save**. Check that the name, address, phone and hours there match the site exactly. If they differ, ask which is right and fix the other.

**Other places the address appears:** Facebook and Instagram bio, email signatures, booking pages, directories (Yelp, Checkatrade, Houzz...), printed materials. Give the owner a short list of the ones you found.

**Visitor stats (Cloudflare Web Analytics, free, no cookies):** Cloudflare dashboard > **Analytics & Logs > Web Analytics** (or search "Web Analytics") > **Add a site** > choose `<domain>` from the list > **Done**. For a domain on Cloudflare this works with automatic setup, with nothing to add to the code. Once it's on, set `analytics: true` in `src/site.config.mjs` (the privacy page then mentions it) and publish. If the owner doesn't want stats, leave it false. If Cloudflare shows a JavaScript snippet instead, send it to me and I'll add it before `</body>` in `Base.astro`. The token in it is public (it appears in the page source), so it's fine to paste, unlike API tokens or passwords.

**Email forwarding (only if they have no mailbox at the domain yet):** to receive `hello@<domain>` in an existing Gmail or Outlook inbox for free:
1. Cloudflare dashboard > **Email Service > Email Routing** (older screens: Email > Email Routing) > **Onboard domain**. Cloudflare adds the records.
2. **Destination addresses**: add their inbox, then click the verification link in the email that arrives.
3. **Routing rules > Create**: address `hello`, action **Send to an email**, the inbox. **Save**.
4. Test from a different email account.

Never do this when MX records already exist (Google Workspace, Microsoft 365, or registrar email); it would take over their mail. Forwarding is receive-only. To send as `hello@`, they need a mailbox service; recommend Google Workspace or Microsoft 365, or Zoho Mail for a cheap one.

## 4. Looking after the site

Offer this once, after launch, in one line, then set it up if they agree:

- **Weekly health check (routine `site-health-weekly`):** checks the home page loads over HTTPS with the right title, the sitemap is there, and the domain isn't within 45 days of expiring (via `https://rdap.org/domain/<domain>`). It reports what's wrong with a recommended fix, or one line saying all sites are healthy. Switch it on with `tool:schedule_routine` after asking which addresses to watch.
- **Monthly upkeep (routine `site-upkeep-monthly`):** updates dependencies on a branch, rebuilds, runs QA and sends a preview for approval.
  - It needs the routine to be granted the GitHub connection when it's switched on.
  - If the platform asks for approval before each push, nobody is there to approve one in a scheduled run. In that case the owner needs a standing approval for your shell commands, or the routine only reports what's outdated.
  - If the owner declines, do upkeep when they next ask for a change.
- **Content changes:** through `website-preview-publish`, any time.

For SSL: Cloudflare renews certificates automatically, so nothing needs doing.

For domain renewal: Cloudflare Registrar auto-renews if a card is on file. At other registrars, check auto-renew is on and note the expiry date (from `dnscheck.py audit`) in SITE.md.

## 5. Handover pack

At launch, and whenever a client relationship ends or the owner asks "what do I have?", write `HANDOVER.md` in the repo from `reference/handover-template.md`:
- what's where (repo, Cloudflare account, domain registrar, form service, analytics);
- who owns each login;
- how to request changes;
- what costs what and when it renews;
- what to do if the site is down.

Fill it from SITE.md; never include passwords. Commit it, then send the owner the GitHub link to the file, or a PDF if they prefer (render the markdown with any converter available in the sandbox).

For agencies handing a site to a client's own accounts, load `website-hosting-setup` and follow "Handing a site over to a client later" in its `reference/accounts.md` (`/home/user/skills/website-hosting-setup/reference/accounts.md`).
