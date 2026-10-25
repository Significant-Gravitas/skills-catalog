# <Business name> website: handover

Last updated: <date>

## The short version
Your website is <https://domain>. It's a fast static site that you own outright. The code is in your GitHub, it's hosted free on your Cloudflare account, and the domain is registered with <registrar> in <owner>'s name.

## What's where
| Thing | Where | Owner's login | Notes |
|---|---|---|---|
| Website code | GitHub: `<owner>/<slug>` (private) | <GitHub account> | Every change is recorded here |
| Hosting | Cloudflare account <email>, Worker `<slug>` | <who> | Free plan |
| Domain | <registrar>, renews <date> | <who> | Auto-renew: <on/off> |
| DNS | Cloudflare, zone `<domain>` | <who> | Email records: <provider> |
| Contact form | Web3Forms, delivering to <email> | <who> | Free plan, 250 messages a month |
| Visitor stats | Cloudflare Web Analytics | <who> | No cookies, no banner needed |
| Search | Google Search Console, Bing Webmaster Tools | <Google account> | Sitemap submitted <date> |
| Email | <provider> | <who> | Not changed by the website |

## Addresses
- Live site: https://<domain>
- Backup address (always works): https://<slug>.<subdomain>.workers.dev
- Previews of changes appear at https://<branch>-<slug>.<subdomain>.workers.dev

## Making changes
Ask in the chat ("change our opening hours", "add a page for X"). You'll get a preview link and a screenshot first; nothing goes live until you say so. Every change can be undone.

## What it costs
- Hosting: free (Cloudflare Workers free plan).
- Domain: about <price> a year at <registrar>, next renewal <date>.
- Form: free up to 250 messages a month.

## If something looks wrong
1. Check https://<slug>.<subdomain>.workers.dev. If that works but the domain doesn't, it's a domain or DNS issue.
2. Check https://www.cloudflarestatus.com for a Cloudflare outage.
3. Ask in the chat. Any recent change can be rolled back in minutes.

## Accounts and access checklist
- [ ] The owner can sign in to GitHub, Cloudflare and the registrar with two-factor authentication on.
- [ ] Recovery email addresses are the business's, not a former employee's or the agency's.
- [ ] Domain auto-renew is on and the card on file is current.
