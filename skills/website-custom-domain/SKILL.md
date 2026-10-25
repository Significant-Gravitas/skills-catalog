---
name: "website-custom-domain"
description: "Connect a website to its own domain with full hand-holding: help choose and buy a new domain at cost on Cloudflare, or move an existing domain from any registrar (GoDaddy, Namecheap, IONOS, Squarespace, Wix and others) without breaking the owner's email, then attach it to the site with automatic HTTPS and a www redirect. Use for 'connect my domain', 'buy a domain', 'use my own web address', 'domain not working'."
triggers: ["connect my domain", "buy a domain", "custom domain", "my own domain", "point my domain", "domain name for my website", "change nameservers", "domain not working", "move my domain", "use my web address"]
version: "1"
---

# Website custom domain

Goal: the site answers at `https://<domain>` with a valid certificate, `www` redirects to it (or the other way round), the owner's email keeps working throughout, and the owner understands what changed. You do the technical work; the owner does only what needs their login or their money, guided step by step.

Package files: `scripts/dnscheck.py` (registrar lookup, DNS audit, record comparison, HTTPS status, availability), `reference/registrars.md` (step-by-step nameserver changes for 19 registrars plus the email safety checklist), and `reference/cloudflare-api.md` (one-call recipes for the Cloudflare integration). All are under `/home/user/skills/website-custom-domain/`.

Choosing and buying a domain, and moving its DNS to Cloudflare, can happen any time. Only attaching it to the site needs hosting (SITE.md has a production workers.dev address; otherwise load `website-hosting-setup` first). Work from a scratch folder, `mkdir -p ~/workspace/domains && cd ~/workspace/domains`, so audit files persist.

For an agency's client, write the registrar steps addressed to the client ("you", their registrar, their login), so the agency can forward the message as it is.

## Why the domain goes onto Cloudflare's nameservers

A Worker custom domain needs the domain's DNS on Cloudflare. Pointing a single record from another DNS host isn't enough. In exchange the owner gets free DNS, automatic certificates, the www redirect, free email forwarding and visitor stats.

If the owner is wary, reassure them first: their email settings are copied and checked before anything changes, and the switch can be undone in two minutes by putting the old nameservers back. If they still refuse, say plainly that the site can then only stay on its workers.dev address, or use Cloudflare's partial setup, which needs the Business plan (roughly $200 to $250 a month), and recommend the change. Don't build a fragile workaround.

## Path A: no domain yet (buy one)

1. **Suggest names.** Offer three to five, short, easy to say on the phone, no hyphens. Prefer `.com`, or the local country domain (`.co.uk`, `.ie`, `.ca`...) for a local business. Check them quickly: `python3 /home/user/skills/website-custom-domain/scripts/dnscheck.py available name1.com name1.co.uk name2.com`. Present the free ones with your recommendation.
2. **Where to buy:** Cloudflare Registrar, in the same account as the site. It charges what the registry charges, with no markup (about $10 to $11 a year for `.com`, about $5 for `.co.uk`). DNS is set up automatically, so no nameserver step is needed.
   - Check the ending is sold there first: https://www.cloudflare.com/tld-policies/. Cloudflare doesn't sell `.com.au`, `.au` or `.de`, and many country endings (`.ie` among them) may be missing.
   - **Not sold at Cloudflare:** buy at a local registrar (VentraIP or Crazy Domains in Australia; IONOS or Strato in Germany; the national registry's list of accredited registrars elsewhere).
     1. Add the domain in Cloudflare first (B2). Its new nameservers can then go in at checkout, or straight after purchase in the registrar's nameserver settings (B4).
     2. A brand-new domain has no email to protect, so skip the audit and `compare`.
     3. `.com.au` needs the business's ABN or ACN, and the name must match or closely relate to the business, so have them ready.
3. **The owner buys it** (it's their money and their legal contact details). Send these steps:
   1. In the Cloudflare dashboard, open **Domain Registration > Register Domains** (or go to https://dash.cloudflare.com/?to=/:account/registrar/register).
   2. Search for `<name>` and click **Purchase**.
   3. Choose how many years. Keep **auto-renew** on.
   4. Enter the business contact details (letters without accents only) and the card.
   5. Click **Complete purchase**. Then click the verification link in the email Cloudflare sends; unverified domains get suspended.
4. When they say it's done, it's already an active zone on Cloudflare. Go to **Attach the domain** below.

## Path B: they already own the domain

### B1. Find out where it is and what depends on it (you, no login needed)

```bash
mkdir -p ~/workspace/domains && cd ~/workspace/domains
python3 /home/user/skills/website-custom-domain/scripts/dnscheck.py audit <domain>
```

This gives the registrar, the expiry date, the current nameservers, whether DNSSEC is on, the email provider and every record visible from outside. It saves `dns-audit-<domain>.json`.

Read the result for the things that matter:
- **Email in use** (MX records)? Then email safety is the top priority. Nothing switches until `compare` passes (B3).
- **An existing website** (bare domain or www pointing somewhere)? It keeps running on the old host until launch day; you copy its records as they are.
- **The domain is on a website builder's DNS** (Squarespace, Wix, GoDaddy Websites + Marketing, Hostinger Builder)? Moving nameservers disconnects that site. That's fine if the new site replaces it, so plan the nameserver change for launch day (read the builder's section in `reference/registrars.md`).
- **Mail on the website address?** `audit` prints "MAIL ON THE WEBSITE ADDRESS" when email depends on the bare domain or www (common with cPanel hosting: `MX example.com`, a `mail` CNAME to the bare domain, or SPF with `a`/`mx`). Launch would break that mail. Fix it in the zone before launch, as described in "Mail on the website address" below.
- **Other names follow the website address?** It prints those too (e.g. `shop CNAME example.com`). Ask what each is for, then point each at its real service or remove it before launch.
- **Already on Cloudflare nameservers?** Check whether it's the owner's Cloudflare account (recipe 0 in `reference/cloudflare-api.md`, or ask). If yes, skip to **Attach the domain**.
- **The registrar is unknown or reads like a reseller?** The registry shows the accredited registrar, which is often not the brand the owner knows: "Team Blue Internet Services" is behind 123-reg and other UK brands, and "Tucows" is behind Hover and many resellers. Ask the owner who they pay for the domain each year (a renewal email shows it). Use that company's section in `reference/registrars.md`; if there isn't one, use the universal flow and ask for screenshots.
- **DNS held somewhere other than the registrar?** The nameservers point at a third party: a web agency, a hosting company or a website platform. The records live there, so ask for an export from them. The nameserver change itself is still made at the registrar.
- **Mail on the old website's server?** `audit` prints a warning when the mail host shares an IP with the old website. Their mailboxes then live with the old web host. Launch won't touch them (the `mail` records are copied), but the owner must not cancel that hosting plan until the mail has moved. Say so now, and write it in SITE.md.
- **A shop or booking system on the same domain, hosted by the old platform?** See `website-build` ("When not to build it yourself"). Its own subdomain must work before launch.

Then tell the owner in a few short lines what you found and the plan, for example: "Your domain is at GoDaddy and your email runs on Microsoft 365. I'll copy every email setting to Cloudflare first and check it, and only then ask you to make one change at GoDaddy. Your email won't stop."

### B2. Add the domain to Cloudflare, copying every record

**With the Cloudflare integration connected** (preferred): run recipe 1 in `reference/cloudflare-api.md`. One `execute` creates the zone and copies every audited record, all set to DNS only. It returns the two assigned nameservers.

**Without it**, guide the owner:
1. Cloudflare dashboard > **Domains** > **Onboard a domain** (older screens say "Add a domain" or "Add a site").
2. Enter `<domain>` (no www) and keep the quick scan. **Continue**.
3. Choose the **Free** plan.
4. On the DNS records review, add anything missing from your audit. Send them the exact list of records to add (`cf-records` output, written as simple rows). Email-related records must be **DNS only** (grey cloud). **Continue**.
5. Copy the two nameservers Cloudflare shows (they look like `ada.ns.cloudflare.com` and `bob.ns.cloudflare.com`) and send them to you.

Either way, record the zone and the assigned nameservers in SITE.md under "Domain".

### B3. Prove the copy is complete before anything changes

```bash
cd ~/workspace/domains
python3 /home/user/skills/website-custom-domain/scripts/dnscheck.py compare <domain> <first-assigned-nameserver>
```

It asks Cloudflare's assigned nameserver for every record in the audit and lists anything missing or different. Cloudflare already answers for the pending zone on those nameservers. Fix every line (recipe 1 again, or send the owner the missing rows), then run `compare` until it reports 0 to fix.

The audit can't see records at unusual names (custom DKIM selectors, odd subdomains). So also ask the owner, or their IT person, for an export or a screenshot of the DNS page at the current host. For Microsoft 365 or Google Workspace, compare against the admin console's required-records list too (see the checklist in `reference/registrars.md`).

### B4. The registrar change (the owner clicks; you guide)

From `reference/registrars.md`, take the **registrar's** section (the company they pay for the domain) and send one numbered message. A website builder's section, Wix or Squarespace for example, only tells you what breaks when the domain moves away from it:
1. If the audit showed DNSSEC ON: switch it off first, using that registrar's DNSSEC steps. Where the registrar says to wait (Gandi 12 to 24 hours, OVHcloud 24 hours, IONOS 8 hours, GoDaddy up to 90 minutes), schedule the next step instead of rushing it.
2. Remove the domain lock or "Domain Guard" if the registrar requires it for nameserver changes.
3. Replace ALL existing nameservers with exactly the two Cloudflare ones. Don't keep any old ones alongside.
4. Save, and tell you when it's done.

Include the registrar's help link. If the screen doesn't match, ask for a screenshot.

### B5. Wait for activation, without making the owner wait with you

```bash
python3 /home/user/skills/website-custom-domain/scripts/dnscheck.py status <domain>
```

Check right after they confirm, then every couple of minutes for up to about ten minutes, in one `bash_exec` call with `timeout: 700`: `for i in 1 2 3 4 5; do python3 .../dnscheck.py status <domain> | head -1; sleep 110; done`. Most changes show within an hour; registrars quote up to 24 to 48 hours. If it isn't active yet, schedule a follow-up into this chat with `tool:schedule_followup` (pass the `session_id`, `delay_seconds` 3600), saying what to check. Tell the owner you'll carry on by yourself and message when it's live. Cloudflare also emails them when the domain is active.

As soon as `status` shows the Cloudflare nameservers:
- Email: re-run `compare` (now it's the live answer), and ask the owner to send themselves an email from another account and reply to it.
- Their old website, if any, keeps working (its records were copied). Nothing visible has changed yet.

## Attach the domain (launch)

Do this when the owner says to put the new site on the domain. That is usually the launch: load `website-launch-care` for the checklist and old-URL redirects first.

**With the integration:** recipe 3 in `reference/cloudflare-api.md`. In one call it removes the old website records for the bare domain and www, attaches the domain to the Worker (Cloudflare issues the certificate), sets up the www redirect and turns on Always Use HTTPS. Email records are never touched.

**Without it**, guide the owner:
1. **Workers & Pages** > `<slug>` > **Settings** > **Domains & Routes** (newer screens: a **Domains** tab) > **Add** > **Custom Domain** > type `<domain>` > **Add Custom Domain**. If Cloudflare says a record already exists for that name, it's the old website's: they confirm replacing it, or first delete the bare-domain A/AAAA/CNAME records under **DNS > Records**.
2. www redirect:
   1. Under **DNS > Records > Add record**, add type `AAAA`, name `www`, IPv6 address `100::`, Proxy status on (orange cloud). Delete any old www record first.
   2. Then **Rules > Overview > Create rule > Redirect Rule**, using the "Redirect from WWW to root" template if offered. Set Request URL `https://www.*`, target `https://${1}`, status 301, preserve query string. **Deploy**.
3. **SSL/TLS > Edge Certificates > Always Use HTTPS**: on.

Then, in all cases:
1. Check it: `dnscheck.py status <domain>`. Expect a valid certificate on both hosts, 200 on the main one, and a 301 from the other. The main host's certificate usually appears within minutes. On a zone that only just became active, the www certificate can take longer (Cloudflare allows up to 24 hours), so check the main host first and recheck www later.
2. Make the code match, in one commit to `main` (this is the launch the owner approved):
   - `src/site.config.mjs`: `url: 'https://<domain>'` and `launched: true`.
   - `wrangler.jsonc`: add `"routes": [{ "pattern": "<domain>", "custom_domain": true }]`, so later deploys keep the domain attached. Keep `"workers_dev": true` and `"preview_urls": true`.
   - Run QA in launch mode (`node /home/user/skills/website-build/scripts/qa.mjs --launch`); it must pass. Push, then `deploy-status.sh wait https://<domain>` until it serves the new build.
3. Update SITE.md. Keep the `Production:` line as the workers.dev address (the preview tooling reads it) and add a Domain section: `Domain: https://<domain>`, registrar, renewal date from the audit, nameservers, zone id, main host and redirect.
4. Tell the owner in two lines: it's live at `https://<domain>` (a link), and email was checked.

## Mail on the website address

If `audit` flagged mail that depends on the bare domain or www, fix it before launch, while the old site is still up:
1. Note the old web server's IP (the bare domain's A record in the audit).
2. In the Cloudflare zone, create `mail.<domain>` as an `A` record to that IP, DNS only, if it doesn't exist as a real host already.
3. Point every MX that targets the bare domain at `mail.<domain>` (same priority). Point `mail`, `smtp`, `imap` and `webmail` CNAMEs that target the bare domain at `mail.<domain>` too, or make them A records to the same IP.
4. In SPF, replace `a` and `mx` with `ip4:<that IP>` (keep every other part).
5. Run `compare` with the email checklist in mind, and ask the owner to send and receive a test email.
6. Their mail host may have certificates for `mail.<domain>` only; if mail apps complain afterwards, the host's support can confirm the right server names.

Recipe 3 refuses to run while these dependencies remain.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `status` still shows the old nameservers after a day | The change wasn't saved, a lock blocked it, or the old ones were kept alongside. Ask for a screenshot of the registrar's nameserver page. |
| "Pending Nameserver Update" in Cloudflare for days | Same as above. Free zones that aren't activated within 28 days are deleted; re-add if needed. |
| Site unreachable after the switch, with DNSSEC involved | DNSSEC was still on. Switch it off at the registrar now. Recovery takes hours, so warn the owner. Re-enable later through Cloudflare (see the end of `reference/registrars.md`). |
| Email stopped | A missing MX, SPF, DKIM or autodiscover record. Run `compare` and add what's missing as DNS only. As a last resort, have the owner put the old nameservers back (the old host still has the records). |
| Certificate error on the domain | Wait up to 15 minutes after attaching. Check that CAA records allow the certificate authorities Cloudflare uses (letsencrypt.org, pki.goog, ssl.com, sectigo.com), or delete restrictive CAA records. |
| `ERR_TOO_MANY_REDIRECTS` | Usually an old redirect rule or page rule plus the new one. List the rules under **Rules** and remove the duplicate. |
| www works but the bare domain doesn't (or the reverse) | One of the two steps in Attach is missing. Re-run recipe 3 or check both dashboard steps. |
| "Custom domain already exists / hostname in use" | It's attached to another Worker or has a CNAME. Remove that first. |
| The owner pasted a Cloudflare API token in chat | After the platform's standard reply, tell them to delete it now at https://dash.cloudflare.com/profile/api-tokens, and use the Cloudflare sign-in card instead. |

Never tell the owner the domain is live until `dnscheck.py status` shows a valid certificate and the new site's build on the domain.
