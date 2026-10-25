# Whose accounts? Ownership for owners and agencies

Get this right on day one. Moving a live site and a domain between accounts later is possible, but it's slow and risky.

## A business owner building their own site

Everything is in the owner's name, with their business email:
- **GitHub:** a personal account (Free) or an organisation if they have staff. The repo is private.
- **Cloudflare:** their own account (Free). The Worker, the domain (zone) and, if bought there, the domain registration all live here.
- **Domain:** registered to the business, with the business email as the contact, and auto-renew on.
- Logins and two-factor authentication stay with the owner. You never need their passwords: GitHub and Cloudflare are reached through connection cards.

## An agency building sites for clients

The constraint that shapes this: Cloudflare's GitHub app expects **one GitHub account (or organisation) per Cloudflare account**. A single agency GitHub organisation can't feed several client Cloudflare accounts.

**Default model: the agency hosts, the client owns the domain.**
- **GitHub:** one agency organisation (e.g. `acme-web`), with one private repo per client site, named after the site slug.
- **Cloudflare:** one agency Cloudflare account that hosts every client Worker. It's free, and the account allows up to 100 Workers.
- **Domains:** each client's domain is added to the agency's Cloudflare account as a zone, so it can be attached to that client's Worker. If the client buys the domain through Cloudflare, register it with the client's details as the registrant. The domain legally belongs to the client even when it sits in the agency's account.
- Record all of this in each site's SITE.md and in the handover pack (see `website-launch-care`).
- This keeps the agency's day-to-day work in one place, and you only connect GitHub and Cloudflare once.

**When a client wants everything in their own name from day one** (common for larger clients):
- The client creates their own GitHub organisation and Cloudflare account and invites the agency:
  - GitHub: organisation **People > Invite member**, role Owner or Member, plus admin on the site's repo.
  - Cloudflare: **Members** (account home, left menu; https://dash.cloudflare.com/?to=/:account/members) > **Invite members** > enter the agency's email > **Add permission policies**: scope the whole account, role **Administrator** (full access except billing and members) > **Invite members**.
- The client's GitHub organisation connects to the client's Cloudflare account, which keeps the one-to-one rule.
- In AutoGPT, the agency user connects the GitHub account that has access to the client's organisation. Connect Cloudflare through the card while the agency user is signed in to Cloudflare and can see that account.

**Handing a site over to a client later** (agency-hosted to client-owned):
1. The client creates their Cloudflare account and invites the agency as Administrator (above), so the agency's existing Cloudflare connection can see the new account and do the DNS work.
2. Transfer the repo: GitHub repo **Settings > Danger Zone > Transfer ownership** to the client's account or organisation. If the agency keeps looking after the site, the client adds the agency as a collaborator straight away, or you lose access.
3. The client connects their Cloudflare account to the repo with the import steps in `website-hosting-setup`, using the same Worker name.
4. Move the domain:
   - Add the zone to the client's Cloudflare account. It gets new nameservers.
   - Re-create the DNS records there. Export them first from the old zone: **DNS > Records > Import and Export > Export**.
   - Change the nameservers at the registrar to the new pair.
   - If the domain is registered through Cloudflare, use the registrar's account-to-account transfer (Manage Domain > Configuration). The client approves within 5 days.
   - As soon as the client's zone shows Active, attach the domain to the client's Worker (recipe 3 in `website-custom-domain`). Keep the agency's zone untouched until then.
   - Expect certificates to be reissued. Do it at a quiet time.
5. Remove the old Worker and zone from the agency account once the client's version is live.

## Rules for you

- Never create accounts on someone's behalf, and never ask for their passwords. Accounts are created by the person who will own them; you guide them.
- Never put the domain registration in the agency's legal name for a client's business unless the client explicitly asks.
- Write the ownership decision into SITE.md under "Accounts" the moment it's made.
