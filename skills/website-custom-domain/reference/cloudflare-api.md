# Cloudflare API recipes (through the Cloudflare integration)

These run through Cloudflare's official server, `https://mcp.cloudflare.com/mcp`, after the owner connects it (`website-hosting-setup`, step 5). It has four tools:
- `search`: query Cloudflare's API spec with JavaScript. Read-only, so it runs without an approval card. Use it to confirm a path or body before you `execute`.
- `execute`: run JavaScript that calls `cloudflare.request({ method, path, body })`. Each call may show an approval card, so do a whole step in one script and return a short summary.
- `whoami`: who the connection belongs to.
- `docs`: search Cloudflare's documentation.

Call shape: `run_capability(id="https://mcp.cloudflare.com/mcp", input={"tool": "execute", "arguments": {"code": "async () => { ... }"}})`. For a user login (OAuth), pass `"account_id": "<id>"` in `arguments` once you know it; the code can then use `accountId`. Responses are `{ success, errors, result }`. Return only what you need: the server cuts results at about 6,000 tokens.

If an execute call fails with a missing-permission (scope) error, run the connect card again (`input={"connect": true}`) and ask the owner to allow the extra permission. Never ask for an API token.

If the integration isn't available, every recipe below has a dashboard equivalent in SKILL.md.

## 0. Find the account, zone and Worker (one call)

```js
async () => {
  const accounts = (await cloudflare.request({ method: "GET", path: "/accounts" })).result
    .map(a => ({ id: a.id, name: a.name }));
  const zones = (await cloudflare.request({ method: "GET", path: "/zones?per_page=50" })).result
    .map(z => ({ id: z.id, name: z.name, status: z.status, name_servers: z.name_servers, account: z.account?.id }));
  const out = { accounts, zones, workers: {} };
  for (const a of accounts) {
    const r = await cloudflare.request({ method: "GET", path: `/accounts/${a.id}/workers/scripts` });
    out.workers[a.id] = (r.result || []).map(s => ({ name: s.id, tag: s.tag }));
    const sub = await cloudflare.request({ method: "GET", path: `/accounts/${a.id}/workers/subdomain` });
    out.workers[a.id + ":subdomain"] = sub.result?.subdomain;
  }
  return out;
}
```

Write the account id, zone id and workers.dev subdomain into SITE.md. Recipes 1 and 3 can find the account and zone themselves, so you don't need to run this first; it's for when you need the overview.

## 1. Add an existing domain as a zone and copy its records (one call)

First, in the sandbox, generate the record list from the audit:
`python3 /home/user/skills/website-custom-domain/scripts/dnscheck.py cf-records <domain> > records.json`.
Paste its contents in place of `RECORDS`. Keep the old website records (don't use `--skip-web`) so the old site keeps working until launch day.

```js
async () => {
  const DOMAIN = "<domain>";
  const RECORDS = [ /* contents of records.json */ ];
  // Use the account id from SITE.md if you have it; otherwise take the only account.
  let ACCOUNT = "<account-id or empty>";
  if (!/^[0-9a-f]{32}$/.test(ACCOUNT)) {
    const accts = (await cloudflare.request({ method: "GET", path: "/accounts" })).result || [];
    if (accts.length !== 1) return { step: "pick account", accounts: accts.map(a => ({ id: a.id, name: a.name })) };
    ACCOUNT = accts[0].id;
  }
  let zone = (await cloudflare.request({ method: "GET", path: `/zones?name=${DOMAIN}` })).result?.[0];
  if (!zone) {
    const r = await cloudflare.request({ method: "POST", path: "/zones", body: { name: DOMAIN, account: { id: ACCOUNT }, type: "full" } });
    if (!r.success) return { step: "create zone", errors: r.errors };
    zone = r.result;
  }
  const existing = (await cloudflare.request({ method: "GET", path: `/zones/${zone.id}/dns_records?per_page=500` })).result || [];
  const key = r => `${r.type}|${r.name}|${r.content ?? JSON.stringify(r.data)}|${r.priority ?? ""}`.toLowerCase();
  const have = new Set(existing.map(key));
  const created = [], failed = [];
  for (const rec of RECORDS) {
    if (have.has(key(rec)) || have.has(key({ ...rec, content: (rec.content || "").replace(/^"|"$/g, "") }))) continue;
    const r = await cloudflare.request({ method: "POST", path: `/zones/${zone.id}/dns_records`, body: rec });
    (r.success ? created : failed).push(r.success ? `${rec.type} ${rec.name}` : { rec, errors: r.errors });
  }
  return { account_id: ACCOUNT, zone_id: zone.id, status: zone.status, name_servers: zone.name_servers, created: created.length, failed };
}
```

Then verify from the sandbox against one of the returned nameservers:
`python3 /home/user/skills/website-custom-domain/scripts/dnscheck.py compare <domain> <first-assigned-nameserver>`.
Fix anything it lists before the owner touches the registrar.

## 2. Check activation (free; no API needed)

`python3 .../dnscheck.py status <domain>` shows whether the nameservers are Cloudflare's. Cloudflare also re-checks by itself. To push a re-check through the API: `PUT /zones/{zone_id}/activation_check`.

## 3. Launch: point the domain at the site (one call)

Run this only after the zone is active, and the owner has said to go live on the domain.

What it does:
- Removes the old website records for the bare domain and www.
- Attaches the domain to the Worker. Cloudflare creates the DNS record and the certificate.
- Sends www to the bare domain with a 301.
- Turns on Always Use HTTPS.

Email records are untouched, and it refuses to run while mail still depends on the website address (see "Mail on the website address" in SKILL.md). If attaching fails, it puts the old records back and stops, so the old site keeps working.

The bodies below match Cloudflare's OpenAPI spec as of October 2026. If a call errors, check the current shape with `search` (for example the spec entry for `PUT /accounts/{account_id}/workers/domains`) and adjust.

```js
async () => {
  const DOMAIN = "<domain>", WORKER = "<slug>";
  const log = [];
  const zone = (await cloudflare.request({ method: "GET", path: `/zones?name=${DOMAIN}` })).result?.[0];
  if (!zone || zone.status !== "active") return { stop: `zone ${DOMAIN} is ${zone ? zone.status : "missing"}; it must be active first` };
  const ZONE = zone.id, ACCOUNT = zone.account.id;
  const recs = (await cloudflare.request({ method: "GET", path: `/zones/${ZONE}/dns_records?per_page=500` })).result || [];
  const webHosts = [DOMAIN, `www.${DOMAIN}`];
  // Guard: mail that points at the website address would break.
  const target = r => (r.content || "").replace(/\.$/, "").toLowerCase();
  const mailDeps = recs.filter(r => (r.type === "MX" && webHosts.includes(target(r))) ||
    (r.type === "CNAME" && !webHosts.includes(r.name) && webHosts.includes(target(r)) && /^(mail|smtp|imap|pop|webmail|autodiscover|autoconfig|email)\./.test(r.name)) ||
    (r.type === "TXT" && r.name === DOMAIN && /^"?v=spf1/i.test(r.content) && /\s\+?(a|mx)(\s|"|$)/i.test(r.content)));
  if (mailDeps.length) return { stop: "mail depends on the website address; fix first", records: mailDeps.map(r => `${r.name} ${r.type} ${r.content}`) };
  // 1. Remove old website records at the bare domain and www, remembering them.
  const removed = [];
  for (const r of recs) {
    if (webHosts.includes(r.name) && ["A", "AAAA", "CNAME"].includes(r.type)) {
      const d = await cloudflare.request({ method: "DELETE", path: `/zones/${ZONE}/dns_records/${r.id}` });
      if (d.success) removed.push({ type: r.type, name: r.name, content: r.content, proxied: r.proxied, ttl: r.ttl });
      log.push(`delete ${r.type} ${r.name} ${r.content}: ${d.success}`);
    }
  }
  // 2. Attach the bare domain to the Worker; on failure put the old records back and stop.
  const att = await cloudflare.request({ method: "PUT", path: `/accounts/${ACCOUNT}/workers/domains`,
    body: { hostname: DOMAIN, service: WORKER, zone_id: ZONE } });
  if (!att.success) {
    for (const r of removed) await cloudflare.request({ method: "POST", path: `/zones/${ZONE}/dns_records`, body: r });
    return { stop: "attach failed; old records restored", errors: att.errors, log };
  }
  log.push(`attach ${DOMAIN}: ok`);
  // 3. www placeholder record (proxied) so the redirect rule can catch it.
  const www = await cloudflare.request({ method: "POST", path: `/zones/${ZONE}/dns_records`,
    body: { type: "AAAA", name: `www.${DOMAIN}`, content: "100::", proxied: true, ttl: 1, comment: "www redirect to bare domain" } });
  log.push(`www placeholder: ${www.success ? "ok" : JSON.stringify(www.errors)}`);
  // 4. Redirect rule www -> bare domain, keeping any existing rules.
  const phase = `/zones/${ZONE}/rulesets/phases/http_request_dynamic_redirect/entrypoint`;
  const cur = await cloudflare.request({ method: "GET", path: phase });
  const rules = (cur.success && cur.result?.rules) ? cur.result.rules.map(({ id, version, last_updated, ref, categories, ...keep }) => keep) : [];
  if (!rules.some(r => (r.description || "").includes("www to bare domain"))) {
    rules.push({
      description: "www to bare domain",
      expression: `(http.host eq "www.${DOMAIN}")`,
      action: "redirect",
      action_parameters: { from_value: { status_code: 301, preserve_query_string: true,
        target_url: { expression: `concat("https://${DOMAIN}", http.request.uri.path)` } } },
      enabled: true,
    });
  }
  const put = await cloudflare.request({ method: "PUT", path: phase, body: { rules } });
  log.push(`redirect rule: ${put.success ? "ok" : JSON.stringify(put.errors)}`);
  // 5. Always use HTTPS.
  const https = await cloudflare.request({ method: "PATCH", path: `/zones/${ZONE}/settings/always_use_https`, body: { value: "on" } });
  log.push(`always https: ${https.success}`);
  return { account_id: ACCOUNT, zone_id: ZONE, log };
}
```

If the owner prefers www as the main address (for example the old site used it, and it's printed on their van), swap the roles: attach `www.<domain>` to the Worker, put the placeholder on the bare domain (`A` `192.0.2.1`, proxied), and redirect the bare domain to `https://www.<domain>`.

Then verify from the sandbox: `dnscheck.py status <domain>`. Both hosts should have a valid certificate; the bare domain answers 200 with the new site's title and build; www gives 301 to the bare domain. Certificates usually issue within minutes; allow up to 15. Then update `site.url` and publish (see SKILL.md).

## 4. Domain registration check (optional)

Price and availability for up to 20 names, from Cloudflare Registrar:

```js
async () => (await cloudflare.request({ method: "POST", path: `/accounts/${accountId}/registrar/domain-check`,
  body: { domains: ["harbourbakery.com", "harbourbakery.co.uk"] } })).result
```

Buying stays with the owner in the dashboard: it spends their money, needs their contact details, and the API (beta) defaults to auto-renew off.

## 5. Undo the launch

Detach the Worker domain (`DELETE /accounts/{account_id}/workers/domains/{domain_id}`; list ids with `GET /accounts/{account_id}/workers/domains`), then re-create the old website records from `dns-audit-<domain>.json` (`cf-records` without `--skip-web`). Keep the audit file until the new site has been live and stable for a few weeks.
