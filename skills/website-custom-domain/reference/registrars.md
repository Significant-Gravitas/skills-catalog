# Registrar guide: pointing an existing domain at Cloudflare

Researched October 2026 from each registrar's own help pages (links included). Labels in **bold** or quotes are the registrar's own words. **UNVERIFIED** marks steps that couldn't be confirmed on an official page.

How to use this with the owner:
- Send the steps for their registrar only, as a short numbered list. Fill in the two Cloudflare nameservers exactly, and include the help link.
- Registrar screens change. If a label doesn't match, ask the owner to send a screenshot (look at it with `read_workspace_file`) or to read out what they see. For anything UNVERIFIED, say "look for something like ...", and suggest the registrar's support chat as the fallback.
- Before any nameserver change, the email safety check in SKILL.md must pass (`dnscheck.py compare`). Switch DNSSEC off first where this guide says so.
- Never ask for the owner's registrar password. They click; you guide.

## Universal flow (for every registrar)
1. Find registrar + current nameservers + DNSSEC state (dnscheck.py audit).
2. Run the DNS audit (dnscheck.py audit) and save the output.
3. In Cloudflare: **Onboard a domain** > enter apex domain > let it scan > pick plan (Free) > **review every record against the audit**, import missing ones (email checklist below). Set mail-related records to DNS only.
4. Turn OFF DNSSEC at the registrar (Cloudflare: "Changing nameservers while DNSSEC is active can cause your domain to become unreachable"). Where the registrar says to wait (Gandi 12 to 24 h, OVH 24 h, IONOS 8 h, GoDaddy up to 90 min), wait.
5. At the registrar replace ALL existing nameservers with the two Cloudflare assigned ("If their names are not copied exactly, your DNS will not resolve correctly"). Don't keep any old ones alongside.
6. Wait. Cloudflare: "Wait up to 24 hours"; registrars quote 24 to 72 h; usually 1 to 4 h. Cloudflare checks automatically (first after 60 s, then at growing intervals); a re-check can be triggered from the domain's Overview page (exact button label UNVERIFIED). Zone shows **Active** when done; Free zones not activated within 28 days are deleted.
7. Test website + send/receive email. Optionally re-enable DNSSEC via Cloudflare (see the end of this file).
Source: https://developers.cloudflare.com/dns/zone-setups/full-setup/setup/ ; Cloudflare's own registrar link list is on that page.

## Per-registrar instructions

### Quick table
| Registrar | DNSSEC must be removed by user? | Big gotcha | Stated time |
|---|---|---|---|
| GoDaddy | Yes if on (DNS > DNSSEC) | M365/Professional Email/W+M site records; Domain Protection verification | 1 h typical, up to 48 h |
| Namecheap | Yes if on (Advanced DNS) | Free redirects + email forwarding stop | up to 24 h |
| Squarespace | Done inside flow | Squarespace site disconnects; PayPal links break | up to 48 h |
| IONOS | Only with DNS Pro/Domain Guard | Domain Guard blocks NS change; account-specific DKIM | up to 48 h |
| Hostinger | Not supported on its NS | Builder needs CNAME to connect.hostinger.com, DNS only | up to 24 h |
| Wix | Paid add-on, off-steps UNVERIFIED | Unassign from site first; Wix records must be DNS only | up to 48 h |
| Porkbun | Check both DNSSEC fields | Porkbun hosting/email/forwarding break | up to 48 h |
| 123-reg | UNVERIFIED | Turn lock off first | 24 to 48 h |
| Network Solutions | Toggle on DNS tab | Premium DNS disabled | 24 to 72 h |
| Bluehost | Yes, explicit instruction | Copy hosting + email records | 24 to 48 h |
| OVHcloud | Yes, 24 h to take effect | Zone not copied | ≤48 h (72 h w/ DNSSEC) |
| Gandi | Yes, then wait 12 to 24 h | Premium DNS off; LiveDNS stops | 12 to 24 h |
| Dynadot | "Clear DNSSEC" | Abnormal status blocks save | not stated |
| Name.com | DS "Remove" (path UNVERIFIED) | Delete old NS first | ~48 h |
| Crazy Domains | Not supported on its NS | Domain Lock may block | 24 to 72 h |
| VentraIP | Remove DS entries | All records replaced instantly | 2 to 24 h |
| Hover | Only if DS present | Irreversible once saved; Connect/forwarding stop | 24 to 48 h |
| Strato | Via Domain Guard (off-steps UNVERIFIED) | NS greyed out if custom MX/A/SPF set; .es/.fr/.be can't | ≤24 h |
| one.com | Auto-disabled | Website Builder/shop/email stop | 5 min  to  24 h |

### GoDaddy
- Nameservers: https://www.godaddy.com/help/change-my-domain-nameservers-664 (godaddy.com blocks bots; read from Wayback copy ~Jun 2026. Cloudflare links the same article id as https://www.godaddy.com/help/change-nameservers-for-your-domain-names-664)
- DNSSEC: https://www.godaddy.com/help/turn-dnssec-on-or-off-6420
- M365 DNS: https://www.godaddy.com/help/what-are-my-dns-settings-for-microsoft-365-42241 , https://www.godaddy.com/help/set-mail-destination-for-my-domain-at-another-company-9216 , autodiscover: https://www.godaddy.com/help/fix-microsoft-365-email-not-working-19308
- Professional Email DNS: https://www.godaddy.com/help/what-are-my-dns-settings-for-professional-email-42103
- Websites + Marketing on external DNS: https://www.godaddy.com/help/connect-an-external-domain-to-my-websites-marketing-or-version-7-site-40564
- Steps:
  1. DNSSEC off first (best practice; GoDaddy doesn't say "first"): Domain Settings > **"DNS"** > **"DNSSEC"** > **"Turn Off DNSSEC"** > **"Remove"** ("may take up to 90 minutes to be reflected in your account").
  2. Sign in to **"Domain Portfolio"** > select the domain (opens **"Domain Settings"**).
  3. **"DNS"** > **"Nameservers"** > **"I'll use my own nameservers"** > enter both Cloudflare nameservers.
  4. **"Save"** > **"Continue"**. With **"Domain Protection"**, expect identity verification (2SV code, or one-time password to account email).
- Gotchas:
  - GoDaddy's warning: "Changing your nameservers may break existing connections to your website or email."
  - Microsoft 365 bought from GoDaddy: get exact records from **Email & Office Dashboard** > **"Users"** > **"Manage"** next to a user > **"Set Mail Destination"**; recreate MX, TXT (SPF + MS verification), CNAME (`autodiscover` -> `autodiscover.outlook.com`) and any DKIM/DMARC in Cloudflare.
  - Professional Email: same **"Set Mail Destination"** path lists the records.
  - Websites + Marketing site: in Cloudflare add `A @ 13.248.243.5` and `CNAME www -> yourdomain.com` (TTL 3600); "a few minutes up to 72 hours".
  - Premium DNS, parking page, domain (transfer) lock effects: UNVERIFIED (parking page presumably disappears).
- Time: "Most DNS changes take effect within an hour but could take up to 48 hours to update globally."

### Namecheap
- Nameservers (updated 4/3/2025): https://www.namecheap.com/support/knowledgebase/article.aspx/767/10/how-to-change-dns-for-a-domain/
- DNSSEC: https://www.namecheap.com/support/knowledgebase/article.aspx/9723/2232/managing-dnssec-for-domains-pointed-to-premium-or-basicdns/
- Redirects/forwarding limits: https://www.namecheap.com/support/knowledgebase/article.aspx/323/46/why-cant-i-modify-email-domain-redirect-and-host-records-in-my-namecheap-account/
- Private Email with third-party DNS: https://www.namecheap.com/support/knowledgebase/article.aspx/1340/2176/namecheap-private-email-records-for-domains-with-thirdparty-dns/
- Steps:
  1. DNSSEC off (best practice): **Domain List** > **Manage** > **"Advanced DNS"** tab > **"DNSSEC"** > "toggle the button to the left" (allow 60 minutes).
  2. "From the left sidebar, select **Domain List** and click on the **Manage** button next to your domain."
  3. **"Nameservers"** section > choose **"CustomDNS"** (screen may read "Custom DNS") > enter Cloudflare's > "click on the **green checkmark**".
- Gotchas:
  - "the host records will not be added to the new nameservers automatically": copy everything.
  - Free URL redirect and email forwarding stop: "available only if you use our Namecheap BasicDNS, PremiumDNS or FreeDNS nameservers." (Cloudflare Email Routing / Redirect Rules can replace them.)
  - Private Email records for Cloudflare: `MX @ 10 mx1.privateemail.com`, `MX @ 10 mx2.privateemail.com`, `TXT @ v=spf1 include:spf.privateemail.com ~all`, DKIM TXT `privateemail._domainkey` (subscriptions before 2 Jun 2026: `default._domainkey`; value from Private Email panel), `_dmarc`; optional CNAMEs `mail`/`autodiscover`/`autoconfig` -> `privateemail.com`, SRV `_autodiscover._tcp 0 0 443 privateemail.com`.
  - PremiumDNS subscription is left behind (auto-cancel/refund UNVERIFIED). `.cm`: 3 NS changes in 28 days triggers a permanent registry lock.
- Time: "It may take up to 24 hours (more, in rare cases)."

### Squarespace Domains (incl. ex-Google Domains)
- Nameservers + DNSSEC (updated 2026-09-21): https://support.squarespace.com/hc/en-us/articles/4404183898125
- Email forwarding: https://support.squarespace.com/hc/en-us/articles/19000909092237 ; after Google move: https://support.squarespace.com/hc/en-us/articles/46213669097101
- Google Domains migration FAQ: https://support.squarespace.com/hc/en-us/articles/17131164996365 ; Google Workspace MX: https://support.squarespace.com/hc/en-us/articles/360001476528
- Steps: domains dashboard > click domain > **"DNS"** > **"Domain Nameservers"** > **"Use Custom Nameservers"** > password/2FA > **"Continue"** > "Click **Continue** when prompted to disable DNSSEC" (built into the flow) > **"Nameserver 1"** / **"Nameserver 2"** > **"Save"**. Ex-Google Domains users log in at squarespace.com/login with **"Continue with Google"**.
- Gotchas (quoted): "Your domain will disconnect from your site." "The records in your domain's Squarespace DNS settings won't apply… You'll have to re-add custom records, like MX or DKIM records controlling custom email." "PayPal Payment Links won't work." "Only use custom nameservers if you have experience managing domains."
  - **Squarespace website users: strongly consider NOT moving nameservers**: whether the site can be reconnected via DNS records while on Cloudflare is UNVERIFIED; Squarespace's own pointing article says to "switch to Squarespace nameservers".
  - Google Workspace: copy MX/SPF/DKIM/DMARC into Cloudflare first (see the email checklist below; copy the live values).
  - Squarespace email forwarding (Mailgun): an **"Action required"** banner > **"Review instructions"** shows 2 MX + 2 TXT to add in Cloudflare.
  - Ex-Google Domains: email/domain forwarding needs records per article 46213669097101; Dynamic DNS and ACME not supported; external verification records may need redoing.
- Time: "It can take up to 48 hours for the nameservers to start working properly."

### IONOS (1&1)
- Nameservers: https://www.ionos.com/help/domains/using-your-own-name-servers/using-your-own-name-servers-for-a-domain/
- DNSSEC: https://www.ionos.com/help/domains/dns-pro/setting-up-and-managing-dnssec/
- Domain Guard: https://www.ionos.com/help/domains/domain-guard/what-is-domain-guard/ ; disable: https://www.ionos.com/help/domains/domain-guard/enablingdisabling-domain-guard/
- Email: SPF https://www.ionos.com/help/domains/configuring-mail-servers-and-other-related-records/using-ionos-spf-to-improve-email-delivery/ ; DKIM https://www.ionos.com/help/domains/configuring-mail-servers-and-other-related-records/email-authentication-with-dkim/ ; autodiscover https://www.ionos.com/help/email/troubleshooting-mail-basicmail-business/checking-the-autodiscover-settings-of-your-domain/ ; MX https://www.ionos.com/help/email/troubleshooting-mail-basic-mail-business/adjusting-mx-records-for-receiving-email-via-ionos-mail-servers/
- Steps (near-verbatim; fetch tool paraphrases slightly):
  1. If on: disable **Domain Guard** ("Changing the name servers" is a locked action).
  2. DNSSEC (only exists with DNS Pro / Domain Guard): domain DNS settings > **DNSSEC** section > **Disable** ("at least 8 hours to update all systems").
  3. **"Domains & SSL"** > next to the domain "click on the **gear icon** under **Actions** and select **Name Server**".
  4. **"Use Custom Name Servers"** > **"Name Server 1"**, **"Name Server 2"** > **"Save"** (undo: **"Reset Settings"**).
- Gotchas: IONOS mail records for Cloudflare: MX `mx00.ionos.com`, `mx01.ionos.com` (priorities UNVERIFIED: copy live); SPF `v=spf1 include:_spf-us.ionos.com ~all` (US; other regions may differ: copy live); DKIM CNAMEs `s1-ionos._domainkey -> s1.dkim.ionos.com`, `s2-ionos._domainkey -> s2.dkim.ionos.com` plus one account-specific `s<number>._domainkey` (must copy from IONOS DNS page: quick scan will miss it); `autodiscover -> adsredir.ionos.info`. IONOS website/MyWebsite: copy A/AAAA from IONOS DNS page first (IP UNVERIFIED). Records left at IONOS "are not visible on the Internet" after the switch. Custom NS applies to root domains only.
- Time: "Up to 48 hours."

### Hostinger
- Nameservers: https://www.hostinger.com/support/1696789-how-to-change-nameservers-at-hostinger/
- DNSSEC: https://www.hostinger.com/support/3667267-how-to-use-dnssec-records-at-hostinger/
- Mail records for external DNS: https://www.hostinger.com/support/8671319-set-up-a-domain-for-hostinger-email-manually/
- AI Builder via Cloudflare: https://www.hostinger.com/support/6865646-how-to-point-a-domain-to-hostinger-ai-builder-via-cloudflare/
- Steps: Hostinger dashboard > "In the left sidebar, click **DNS** and select your domain" (or **"Manage"** next to the domain) > **"DNS / Nameservers"** tab > **"Change Nameservers"** > **"Change nameservers"** > enter (up to 4) > **"Save"**.
- Gotchas: DNSSEC "is not supported" on Hostinger nameservers: usually nothing to turn off. Mail (from **Emails** > **Mailboxes** > **Domain settings**): `MX @ 5 mx1.hostinger.com`, `MX @ 10 mx2.hostinger.com`, `TXT @ v=spf1 include:_spf.mail.hostinger.com ~all`, DKIM CNAMEs `hostingermail-a/-b/-c._domainkey` -> matching `….dkim.mail.hostinger.com`, `_dmarc`; email "may take up to 24 hours". AI/Website Builder: delete root A/AAAA; `CNAME @ -> connect.hostinger.com` and `CNAME www -> connect.hostinger.com`, **"DNS only"** (agentic-mode sites: `yourdomain.tld.cdn.hstgr.net` / `www.yourdomain.tld.cdn.hstgr.net`); Cloudflare SSL/TLS **"Full"**; A-record pointing for Builder unsupported since 20 May 2026. Web hosting A record IP: UNVERIFIED (copy live).
- Time: "Allow up to 24 hours… Typically, changes take effect within a few hours."
### Wix
- Nameservers: https://support.wix.com/en/article/changing-nameserver-ns-records-for-a-wix-domain
- Unassign from site: https://support.wix.com/en/article/unassigning-a-domain-from-your-site
- Cloudflare settings for a Wix site: https://support.wix.com/en/article/verifying-your-cloudflare-settings-for-connecting-a-domain-to-wix
- Steps (quoted): Before you begin: "Unassign the domain from your Wix site before changing nameservers. There is no need to reassign your domain after changing NS records." (Unassign path, from search summary only: **Domains** > **Domain Actions** icon > **Unassign from this site** > **Unassign Domain**: UNVERIFIED.)
  1. **Domains** in your Wix account > **Domain Actions** icon next to the domain > **Manage DNS records**.
  2. Scroll to **Nameservers** > **Use custom nameservers**.
  3. Enter Cloudflare's in **Nameserver 1** and **Nameserver 2** > **Continue**.
  4. "Review the important information on screen and select the checkbox to confirm" > **Switch nameservers**.
  5. Undo: **Manage DNS records** > **Nameservers** > **Reset to Wix**.
- Gotchas:
  - Wix site keeps working "only if your new DNS provider has records that point to Wix": copy Wix's A/CNAME records into Cloudflare first.
  - Proxy: Wix says records "must be set to DNS only… If your records are Proxied, you must update this to DNS Only." So on Cloudflare, Wix-pointing records = grey cloud (no Cloudflare caching/WAF for the Wix site).
  - "Wix can no longer renew your site's SSL certificate through your domain's DNS."
  - Email: "Wix mailboxes and email routing stop working unless your new DNS provider has the correct MX records." Google Workspace bought via Wix: copy MX + SPF/DKIM/verification TXT.
  - DNSSEC: paid add-on ("Private registration and DNSSEC"); no official page for turning it off: UNVERIFIED, contact Wix support. A Wix line that it "does not support the use of DNSSEC or DNS Proxies like Cloudflare when connecting domains via name servers" came from a search snippet only (UNVERIFIED).
- Time: "can take up to 48 hours to propagate".

### Porkbun
- Nameservers (updated 29 Apr 2026): https://kb.porkbun.com/article/22-how-to-change-nameservers
- Domain details / DNSSEC: https://kb.porkbun.com/article/175-how-to-use-the-domain-details-area
- Steps: Log in (Domain Management, or **ACCOUNT** > **Domain Management**) > **Details** drop-down right of the domain > **Nameservers** field > edit icon > "Remove all of the existing entries. Add the desired nameservers, one per line." > **Save Nameservers** > **Submit** if asked.
- Gotchas: "Changing nameservers from Porkbun to another DNS host will usually break any Porkbun-hosted services such as web hosting and email" (also parking/URL forwarding). DNSSEC: Details area has **PORKBUN DNSSEC** (Porkbun nameservers) and **REGISTRY DNSSEC** (DS records for third-party DNS); clear both before switching (my advice; exact removal steps UNVERIFIED).
- Time: "up to 48 hours… most places will see the change within a few hours."

### 123-reg
- Nameservers: https://www.123-reg.co.uk/support/domains/how-do-i-change-the-nameservers-for-my-domain-name/
- Lock: https://www.123-reg.co.uk/support/domains/how-do-i-lock-unlock-my-domain-name/
- Steps:
  1. Make sure the domain isn't locked: **123 Reg Control Panel** > **Manage All** (opposite **Domains**) > tick domain > **Lock** (or **More**) > **Turn Lock Off** > **Continue**.
  2. **123 Reg Control Panel** > **'My Products'** > Domains > **Manage**.
  3. **'Domain Portfolio'** page: **DNS** > **Nameservers** > **Change Nameservers**.
  4. **"I'll use my own nameservers"** > enter Cloudflare's > **Save**.
- Gotchas: once away, "you will be unable to manage your domain's nameserver records from your Control Panel"; 123-reg email/website records must be recreated in Cloudflare first. DNSSEC: official article no longer loads: UNVERIFIED. Whether lock blocks NS changes: UNVERIFIED (article only says check it isn't locked).
- Time: "between 24-48 hours".

### Network Solutions
- Nameservers + DNSSEC: https://www.networksolutions.com/help/article/manage-dns-adns-records
- Premium DNS: https://www.networksolutions.com/help/article/manage-premium-dns ; email: https://www.networksolutions.com/help/article/update-name-servers-for-email
- Steps: Log in (https://www.networksolutions.com/my-account/login) > **Domains** (left) > select domain > **Manage** > **Nameservers** tab > **Edit** > enter Cloudflare's > **Save**.
  - Do NOT use **Settings** > **Advanced Tools** > **Custom Nameservers** > **+ Nameserver** (asks for an IP; that's for creating host records).
- Gotchas: DNSSEC: "use the toggle located on the right-hand side of the DNS tab page" (.COM/.NET/.INFO/.ORG/.BIZ only): turn off first. "Managing your name servers will also disable the Premium DNS feature." Advanced DNS only works on default nameservers. Hosted site and NetSol email records must be copied (no record list published: UNVERIFIED values).
- Time: "24-48 hours" (another article: "up to 72 hours").

### Bluehost
- Nameservers (updated 18 Jun 2026): https://www.bluehost.com/help/article/custom-nameservers
- DNSSEC (updated 6 Oct 2026): https://www.bluehost.com/help/article/how-to-manage-dnssec-for-your-domain-on-bluehost
- Email DNS: https://www.bluehost.com/help/article/bh-email-dns-email-services
- Steps:
  1. DNSSEC off: **Bluehost Portal** > **Domains** > **DNS** tab > **DNSSEC** toggle > **DISABLE**. Official: "If you plan to change your nameservers or manage DNS with another provider, disable DNSSEC before making the change."
  2. **Bluehost Portal** > **Domains** (left menu) > choose domain > **Nameservers** tab > **Change Nameservers** > enter > **Save**. (Ignore "Custom Nameservers" **+Add**: that's private nameservers for VPS/Dedicated.)
- Gotchas: Bluehost: "Make sure all your DNS settings, like website and email directions, have been correctly moved" and "Test Email Services". Copy hosting A records, MX, SPF, DKIM, DMARC, autodiscover (no record list for external DNS: inferred).
- Time: "Allow 24-48 hours for propagation time."

### OVHcloud
- DNS servers: https://docs.ovhcloud.com/en/guides/web-cloud/domains/dns-server-edit
- DNSSEC: https://docs.ovhcloud.com/en/guides/web-cloud/domains/dns-dnssec
- MX for OVH email: https://docs.ovhcloud.com/en/guides/web-cloud/domains/dns-zone-mx
- Steps:
  1. DNSSEC off first: domain page > `Security` box ("Secured Delegation - DNSSEC") > activation button > confirm. "takes 24 hours to be effective". Guide: "The DNSSEC option must be disabled to combine the use of your own DNS servers with OVHcloud DNS."
  2. OVHcloud Control Panel: `Web Cloud` > `Domain names` > domain > `DNS servers` tab > `Modify DNS servers`.
  3. First Cloudflare NS in `DNS server` (leave `Associated IP (optional)` empty) > `+` > repeat.
  4. `Apply configuration` > check summary > `Apply`.
- Gotchas: "the content of the old configuration/DNS zone is not automatically replicated to the new one"; mistakes "can make your website inaccessible or prevent your email addresses from receiving new emails". OVH email MX (TTL 3600): `mx0.mail.ovh.net` (1), `mx1.mail.ovh.net` (5), `mx2.mail.ovh.net` (50), `mx3.mail.ovh.net` (100), `mx4.mail.ovh.net` (200). SPF/DKIM: copy from the current zone (official SPF value UNVERIFIED). Lock behaviour UNVERIFIED.
- Time: "a maximum of 48 hours"; 48-72h if DNSSEC was still on.

### Gandi
- Nameservers: https://docs.gandi.net/en/domain_names/common_operations/changing_nameservers.html
- DNSSEC: https://docs.gandi.net/en/domain_names/advanced_users/dnssec.html
- SPF: https://docs.gandi.net/en/domain_names/faq/record_types/spf_record.html
- Steps: "**Domain**" (left menu) > domain name > "**Nameservers**" tab (live page typo "Namservers") > **Change** > "**External**" > enter Cloudflare's > "**Save**".
- Gotchas: DNSSEC: same tab > **"Disable DNSSEC"**; Gandi: "Please don't change your nameservers until the propagation has been completed, from 12-24 hours, or it may become unreachable": so disable, wait 12-24h, then switch. External = Gandi LiveDNS stops serving your records; "make sure any important DNS records are duplicated correctly on the new nameserver". Changing NS turns off Premium DNS. Gandi Mail: SPF `v=spf1 include:_mailcust.gandi.net ~all` (official); MX `spool.mail.gandi.net` (10) / `fb.mail.gandi.net` (50) from old wiki only (UNVERIFIED current): copy the live values. DKIM: copy from LiveDNS.
- Time: "wait 12-24 hours".

### Dynadot
- Nameservers: https://www.dynadot.com/help/question/set-name-servers
- Delete DNSSEC: https://www.dynadot.com/help/question/delete-DNSSEC
- Steps: "My Domains" (left menu) > "Manage Domains" > tick domain > "Action" > "DNS Settings" > top drop-down "Name Servers" > "Enter new or existing Name Servers" > enter > "Save Name Server".
- Gotchas: DNSSEC: My Domains > Manage Domains > click the domain name (blue link) > **DNSSEC** section > "Clear DNSSEC". Website builder / email hosting: "ensure that the necessary DNS records are added to your servers beforehand." Abnormal domain status blocks saving. Parking/forwarding/lock: UNVERIFIED.
- Time: "might take some time" (no figure).

### Name.com
- Nameservers: https://www.name.com/support/articles/205934547-changing-nameservers-for-dns-management (live page updated 30 Dec 2025 is JS-rendered; steps from archived 30 Jul 2025 copy: labels may have changed)
- DNSSEC FAQ: https://www.name.com/support/articles/360011979333-dnssec-faq
- Steps: **My Domains** (top right) > domain > **Manage Nameservers** (Nameservers column) > **Delete All** (or **Delete** each) > type one NS in **Add Nameserver** > blue **Add** > repeat > **Save Changes**.
- Gotchas: "If you do not delete the old nameservers before adding the new, it will create conflicts and the associated website/email will not work." "If you do not use name.com's nameservers then we do NOT manage your DNS." DNSSEC: DS records stored at Name.com have a "Remove" button (exact path UNVERIFIED). Titan email/forwarding: UNVERIFIED.
- Time: "roughly 48 hours".

### Crazy Domains (AU)
- Change NS: https://www.crazydomains.com/help/article/error-displays-invalid-name-servers (`.com.au` mirror blocked bots; content identical)
- Access domain: https://www.crazydomains.com/help/article/access-your-domain ; Lock: https://www.crazydomains.com/help/article/what-is-domain-lock ; DS: https://www.crazydomains.com/help/article/how-to-set-up-and-publish-ds-records-for-dnssec
- Steps: Log in, find domain > Domain Registration row **MANAGE** (opens Domain Manager) > **Name Servers** tab > **ADD** ("Add or Edit Name Servers") > replace with Cloudflare's (field validates "after a short pause in typing": paste from a text editor) > **SAVE RECORD**.
- Gotchas: Domain Lock row on **Overview**: unlock if saving fails ("to transfer and update name servers" per meta description), relock after. "DNSSEC is not supported on our name servers": default NS domains have none; DS records added for other hosts must be removed (steps UNVERIFIED). Crazy Domains email (Titan/cPanel/Plesk), site builder, parking depend on its DNS: copy records (values UNVERIFIED).
- Time: "24 to 72 hours".

### VentraIP (AU)
- Nameservers: https://ventraip.com.au/support-centre/modifying-the-nameservers-on-a-domain-name-registration/
- DNS options (names Cloudflare): https://ventraip.com.au/faq/article/manage-dns-options/
- DNSSEC removal: https://ventraip.com.au/support-centre/removing-dnssec-data-from-your-domain/
- Email records: https://ventraip.com.au/support-centre/mx-records-required-for-dedicated-email-hosting-services
- Steps:
  1. DNSSEC: **VIPcontrol** > **'My Services' → 'Domains'** > **'DNS'** next to domain > bottom "DNSSEC heading" > "click on 'Remove' next to each entry."
  2. **VIPcontrol** > **My Services** > **Domains** tab > **DNS** > **Custom Nameservers** tab > **Enable** > enter (min 2) > **Set Custom Nameservers**.
- Gotchas: DNSSEC left on → "DNS resolution to stop". Switching "will immediately replace all existing DNS records (A, CNAME, MX records)"; email/hosting "will stop working until you have either prefilled the existing records or recreate them". Forwarding/Park Domain stop (inference). VentraIP email: MX `mx1.email-hosting.net.au` (10), `mx2.email-hosting.net.au` (10), `mx3.email-hosting.net.au` (20), `mx4.email-hosting.net.au` (30); SPF `v=spf1 +a +mx +include:spf.email-hosting.net.au ~all`; DKIM values UNVERIFIED (copy live).
- Time: "up to 24 hours" (other page: "2-6 hours").

### Hover (Tucows)
- Nameservers: https://support.hover.com/support/solutions/articles/201000064742
- DNSSEC: https://support.hover.com/support/solutions/articles/201000064716 ; MX: .../201000064756 ; SPF: .../201000064663 ; DKIM: .../201000130364 (all under https://support.hover.com/support/solutions/articles/)
- Steps: Sign in (2FA) > domain **Overview** (click domain if several) > **Nameservers** (left side) > **Edit** > enter > **Save nameservers**. Bulk: **Nameservers** in nav bar > tick domains > **Bulk edit: select** > **Edit nameservers**.
- Gotchas: "Once you save a nameserver change, Hover cannot stop it from taking effect." "Hover's Connect or forwarding tools … require your domain's nameservers to point to Hover" (Connect site links and forwarding stop). DNSSEC: DS records only allowed for non-Hover-NS domains; if present: **Overview** > **DNSSEC** > select record > **Delete**. Hover email: MX `@` priority 10 `mx.hover.com.cust.hostedemail.com` (ex-VistaPrint: `mx.yourdomain.com.cust.b.hostedemail.com`); SPF `v=spf1 include:_spf.hostedemail.com ~all`; DKIM is "enabled by a Hover support advisor on the backend": ask Hover support for values.
- Time: "24 to 48 hours".
- Other Tucows (OpenSRS/Enom resellers): changed in the reseller's own panel; menus vary (UNVERIFIED).

### Strato (DE)
- German: https://www.strato.de/faq/domains/wie-kann-ich-bei-strato-meine-dns-eintraege-verwalten/
- English: https://www.strato-hosting.co.uk/faq/domain/can-i-manage-my-own-dns-entries-at-strato/
- DNSSEC: https://www.strato.de/faq/domains/sichern-sie-ihre-webseite-mit-dnssec/
- Steps: Customer login > **Domains → Domainverwaltung** (EN: **Domain management**) > cogwheel (**Zahnrad**) next to domain > **DNS** tab > **NS-Record verwalten** (EN: manage NS record) > **Eigene Nameserver** (EN: **Your name server**), up to 4, format `name1.beispiel.de.` > **Einstellungen übernehmen** (EN: **Accept settings**).
- Gotchas:
  - NS record greyed out if "ein eigener MX-Record, ein eigener A-Record, ein SPF-Record oder ein DynDNS-Account zugewiesen wurde": reset those first.
  - .es, .fr, .be cannot change NS at Strato.
  - Domain Guard active → 2FA required. DNSSEC lives in Domain Guard: Zahnrad > **»DNS«** > **»DNSSEC«** > **»verwalten«**; DNSSEC only works with Strato nameservers; turning off steps UNVERIFIED.
  - Strato mail: MX `smtpin.rzone.de`; SPF `v=spf1 redirect=_spf.strato.com`; DKIM CNAMEs `strato-dkim-0002._domainkey` and `strato-dkim-0003._domainkey`: official DE/EN pages disagree on target (`…rzone.de.` vs `…rzone.com.`), so copy the live value via DoH.
  - Package restrictions on external NS: UNVERIFIED.
- Time: "bis zu 24 Stunden" / "up to 24 hours".

### one.com
- Nameservers: https://help.one.com/hc/en-us/articles/360000841638-How-do-I-change-the-name-servers (read via proxy; help.one.com blocks bots; published 22 Oct 2026)
- DNSSEC: https://help.one.com/hc/en-us/articles/14484128113041-What-is-DNSSEC
- Mail with external NS: https://help.one.com/hc/en-us/articles/17038200070545-Why-do-my-emails-end-up-in-spam-when-using-external-name-servers
- Steps: **one.com Control Panel** > "**Domain**" (left) > "**DNS settings**" > "**Nameservers**" tab > **Change to custom name servers** > NS1 (IP optional) > NS2 > **Save**. (Old "Advanced settings tile" path is outdated.)
- Gotchas: "all features included with your web hosting subscription will stop working - for example, the Website Builder, Online shop and email." (Domain-only subscriptions lose nothing.) DNSSEC "is automatically disabled if you change to external name servers" (manual: **Domain** > **DNS settings** > **Name servers** > **DNSSEC** > **Deactivate**). If registrant ≠ subscription owner, approval email goes to registrant. .dk/.es use a different process. Expired subscription → PDF form, up to 3 working days. one.com mail can still work with external NS if you add: MX `domain.tld.mx.one.com` (non-migrated) or `cluster.mx.service.one` (migrated; ask support); SPF `v=spf1 include:_custspf.one.com ~all`; DKIM "4 specific CNAME records" from support. (Conflicts with the NS article saying email "will stop working": get support to confirm.)
- Time: "changed within 5 minutes. However, it can take up to 24 hours".

## Pre-switch email safety checklist

Cloudflare's own warnings:
- "the quick scan is not guaranteed to find all existing DNS records": https://developers.cloudflare.com/dns/zone-setups/full-setup/setup/
- Quick scan is pattern-based; it misses "very custom hostnames (like `my-store1900.example.com`) or non-standard DKIM record names (like `this._domainkey` instead of `default._domainkey`)"; "You should always review your DNS records and manually add any missing ones before changing your nameservers.": https://developers.cloudflare.com/dns/zone-setups/reference/dns-quick-scan/
- Zone file import (BIND, FQDNs with trailing dot): https://developers.cloudflare.com/dns/manage-dns-records/how-to/import-and-export/

Checklist (every item must exist in Cloudflare, identical, before nameservers change):
1. **MX** at the apex (all of them, with the same priorities).
   - Microsoft 365: `<token>.mail.protection.outlook.com` (priority lowest number). Domains added to M365 after 1 July 2026 get the newer `<domain-with-dashes>.<x>.mx.microsoft` form instead; existing ones keep working. (MS Learn https://learn.microsoft.com/en-us/microsoft-365/enterprise/external-domain-name-system-records ; mx.microsoft change per Microsoft Message Center MC1048624 via secondary sources: copy whatever value is live rather than typing it.)
   - Google Workspace: `smtp.google.com` (single record, current) or legacy `aspmx.l.google.com`/`alt1..alt4.aspmx.l.google.com` set: "legacy MX record values are still supported." https://knowledge.workspace.google.com/admin/domains/set-up-mx-records-for-google-workspace
2. **SPF**: exactly ONE apex TXT starting `v=spf1`. M365: `include:spf.protection.outlook.com`; Google: `v=spf1 include:_spf.google.com ~all` (https://knowledge.workspace.google.com/admin/security/set-up-spf). Keep every other include (Mailchimp, website contact-form sender, invoicing tools).
3. **DKIM**
   - M365: two CNAMEs `selector1._domainkey` and `selector2._domainkey` -> either `selector1-<domain-dashes>._domainkey.<tenant>.onmicrosoft.com` (older) or `selector1-<domain-dashes>._domainkey.<tenant>.<x>-v1.dkim.mail.microsoft` (newer). https://learn.microsoft.com/en-us/defender-office-365/email-authentication-dkim-configure
   - Google: TXT at `google._domainkey` (default selector "google"; can be custom).
   - Others: any `*._domainkey` name. These are the records the quick scan most often misses.
4. **DMARC** TXT at `_dmarc`.
5. **Autodiscover / client config**
   - M365: CNAME `autodiscover` -> `autodiscover.outlook.com` (required). Optional/legacy: `lyncdiscover` -> `webdir.online.lync.com`, `sip` -> `sipdir.online.lync.com`, SRV `_sipfederationtls._tcp` -> `sipfed.online.lync.com` port 5061 (Teams federation), `enterpriseregistration` -> `enterpriseregistration.windows.net`, `enterpriseenrollment` -> `enterpriseenrollment.manage.microsoft.com` (Intune). Copy only those that exist today.
   - Google Workspace has no autodiscover CNAME requirement; check for custom `mail.`/`calendar.` CNAMEs to `ghs.googlehosted.com`.
   - Registrar-hosted email (IONOS, GoDaddy, Hostinger, one.com, Strato…): often `autoconfig`/`autodiscover`/`imap`/`smtp`/`mail`/`webmail` CNAME/A records: copy as-is.
6. **Verification TXT** records (`MS=ms…`, `google-site-verification=…`, Facebook, Apple, etc.): losing them can break admin consoles later.
7. **Proxy status**: in Cloudflare set every mail-related A/CNAME (`mail`, `autodiscover`, `smtp`, `imap`, `webmail`, DKIM CNAMEs) to **DNS only** (grey cloud). Cloudflare's proxy only carries HTTP/HTTPS; MX targets must resolve to real IPs. Same for anything Wix says must be DNS only.
8. **CAA** records, if present, must allow Cloudflare's CAs or Cloudflare cannot issue certificates (Pages doc notes this).
9. **Lower risk timing**: switch on a quiet day; have the old registrar's DNS page open (don't delete the old records there) so you can revert nameservers if mail breaks.
10. After switching: send a test email in and out; check `MX`, `TXT` and the DKIM names via DoH again; check the registrar didn't silently delete email hosting that depended on its DNS.


## After activation: re-enable DNSSEC (optional but recommended)
Cloudflare: **DNS > Settings** > DNSSEC card > **Enable DNSSEC** > copy the DS record values > "Add the **DS** record to your registrar." (Algorithm 13; some registrars don't support it.) Cloudflare also states DNSSEC must be disabled at the registrar before the move. https://developers.cloudflare.com/dns/dnssec/: The agent must walk the user back to the registrar's DNSSEC page from its section above.
