---
name: "website-hosting-setup"
description: "Put a website online for the first time, on the owner's own free GitHub and Cloudflare accounts. Covers the GitHub connection, the repo, the one-time Cloudflare import (automatic deploys and public preview links for every change), and the first live workers.dev address. Use for 'put my website online', 'host my site', 'set up hosting', 'deploy the site'."
triggers: ["put my website online", "host my website", "set up hosting", "deploy my website", "publish the site", "connect cloudflare", "website hosting", "get the site live", "connect github", "free hosting"]
version: "1"
---

# Website hosting setup

The result of this skill: the site's code is in a GitHub repo the owner controls, Cloudflare builds it automatically on every push, and the site is live at a free address like `https://harbour-bakery.<their-subdomain>.workers.dev`. Every branch also gets its own public preview address. After this, all changes go through `website-preview-publish`, and the custom domain through `website-custom-domain`.

Cost to the owner: nothing. GitHub Free and Cloudflare's free Workers plan cover a business site (static files are served free and without limit; builds have 3,000 minutes a month). A domain, when they want one, costs about $10 a year.

Package files: `/home/user/skills/website-hosting-setup/scripts/deploy-status.sh` and `/home/user/skills/website-hosting-setup/reference/accounts.md` (account ownership for owners and for agencies: read it if the user builds sites for clients).

## Before you start

- The site exists in `~/workspace/sites/<slug>/`, builds cleanly, and has been through QA (`website-build`). Its `wrangler.jsonc` `name` equals `<slug>`.
- Read `SITE.md`. If it already lists a GitHub repo and a workers.dev address, hosting is done. Load `website-preview-publish` instead.
- Decide whose accounts these are (see `reference/accounts.md`). For a business owner: their own GitHub and Cloudflare. For an agency: usually the agency's, with each client's domain and handover planned.

Tell the owner the plan in two or three lines before the first step, for example: "To put it online I'll keep the code in a private repo in your GitHub and connect it to a free Cloudflare account. You'll sign in to each once, then click through a short Cloudflare setup with my steps (about five minutes). Until launch it sits at a free, unlisted address that search engines ignore." Their yes to this covers the pushes in this skill: the repo is private, and before launch the site is in pre-launch mode (noindex, robots blocked; see `website-build`).

## Step 1. GitHub

1. Run `gh auth status`. If it says logged in, note the account (`gh api user --jq .login`) and go to step 3.
2. If not, connect: `run_capability(id="tool:connect_integration", input={"provider": "github"})`. A sign-in card appears. Tell the owner in one line to use it, and stop the turn there. If they have no GitHub account, give them three lines: go to https://github.com/signup, use the business email, choose the Free plan, then press the card.
3. Set the commit identity so new commits show their name. Earlier commits stay as "Website build", which is fine.
   ```bash
   cd ~/workspace/sites/<slug>
   git config user.name "$(gh api user --jq '.name // .login')"
   git config user.email "$(gh api user --jq '.id|tostring')+$(gh api user --jq .login)@users.noreply.github.com"
   gh auth setup-git
   ```
4. Create the private repo and push. For an agency organisation, use `<org>/<slug>` as the name.
   ```bash
   gh repo create <slug> --private --source . --remote origin --push
   ```
   If the name is taken in that account, choose a new slug and change it in `wrangler.jsonc` (`name`), `package.json` (`name`) and SITE.md before creating the repo. The repo name, the Worker name and the `wrangler.jsonc` name must all be the same.
   The push may show an approval card. That's expected; the owner approves it.
   For an agency organisation, the push may fail with "OAuth App access restrictions" or a 403. The organisation then blocks third-party apps. Ask an organisation owner to approve AutoGPT: GitHub shows a request link, or they go to organisation **Settings > Third-party access > OAuth application policy**. Or create the repo in the user's personal account now and transfer it to the organisation later (repo **Settings > Transfer ownership**).

## Step 2. Cloudflare account

Ask once whether they already have a Cloudflare account. If not: https://dash.cloudflare.com/sign-up with the business email and a strong password, then click the verification link in the email Cloudflare sends. No card is needed for the free plan.

An agency with an existing Cloudflare account uses that one (see `reference/accounts.md`).

## Step 3. The one-time Cloudflare import (the owner clicks; you guide)

This is the only step you can't do for them, because it installs Cloudflare's GitHub app with their GitHub login. Send these steps as one short numbered message, with the exact values filled in:

1. Open https://dash.cloudflare.com and go to **Workers & Pages** in the left menu.
2. Click **Create application**, then choose **GitHub** (Connect GitHub / Import a repository; the wording varies).
3. If asked, sign in to GitHub and install **Cloudflare Workers and Pages**. Choose **Only select repositories** and pick `<slug>`. An agency building many sites can choose **All repositories** to skip this step next time.
4. Pick the `<slug>` repository.
5. On the setup screen check: **Project name** (or Worker name) is exactly `<slug>`; **Build command** is `npm run build`; **Deploy command** is `npx wrangler deploy`. If there is a **Preview command** it should be `npx wrangler preview`, and if there's a box for preview or non-production branch builds, tick it. Leave everything else as it is.
6. Click **Deploy** (it may say **Save and Deploy**). Wait about two minutes for the first build.
7. If Cloudflare asks you to choose a workers.dev subdomain, use something short like the business name. That becomes part of your free address.
8. When it's done, copy the address it shows ending in `.workers.dev` and send it to me.

Then stop the turn and wait. Tell them that if anything on screen looks different, a screenshot in the chat is the quickest way for you to help. If they send one, look at it with `read_workspace_file` and tell them exactly what to click.

Known screens and fixes:
- **No repositories listed:** the GitHub app was installed with "Only select repositories" without this repo. At https://github.com/settings/installations, Cloudflare Workers and Pages, **Configure**, add the repo, **Save**, then reload Cloudflare.
- **"This GitHub account is already connected to another Cloudflare account":** Cloudflare expects one GitHub account per Cloudflare account. Use the Cloudflare account that GitHub already points to, or remove the app from the other one first (`reference/accounts.md`).
- **The project name was changed:** set it back to `<slug>`, or change `wrangler.jsonc` `name` to match the Worker exactly, then commit and push. A mismatch fails the build with "The name in your Wrangler configuration file ... must match the name of your Worker". Cloudflare may also open a "name conflict" pull request; prefer fixing the name yourself.
- **Cloudflare opened a "configuration" pull request** that adds an adapter or changes `astro.config.mjs`: close it without merging. The repo already has a correct `wrangler.jsonc`; that PR only appears when the config is missing or unreadable, so check that `wrangler.jsonc` is committed.

## Step 4. Confirm the first deploy yourself

When they send the address (or if they say it's done without one):

```bash
cd ~/workspace/sites/<slug>
bash /home/user/skills/website-hosting-setup/scripts/deploy-status.sh checks
bash /home/user/skills/website-hosting-setup/scripts/deploy-status.sh wait https://<slug>.<subdomain>.workers.dev
```

- `checks` reads Cloudflare's GitHub check ("Workers Builds: <slug>") for the latest commit: queued, success or failure, plus a logs link.
- `wait` fetches the site until it serves the latest commit (the starter puts the commit in a `<meta name="build">` tag). Pass `timeout: 480` to `bash_exec`.
- No address from the owner yet? Wait for `checks` to show success, then ask for the address. You can't guess the subdomain.

If the build failed, see Fixing a failed build below.

Once it's live:
1. Set `site.url` in `src/site.config.mjs` to the workers.dev address (it becomes the custom domain later). Commit and push to `main` so canonical links and the sitemap are right. Before launch, `main` is the unlisted staging site, so this needs no extra OK.
2. Screenshot the live address on a phone and look at it (`bash /home/user/skills/website-preview-publish/scripts/shoot.sh https://...` if that skill's files are present, otherwise `/home/user/skills/website-build/scripts/shoot.sh`).
3. Update SITE.md:
   ```
   ## Hosting
   GitHub: <owner>/<slug> (private)
   Cloudflare account: <email or account name>; Worker: <slug>
   Production: https://<slug>.<subdomain>.workers.dev
   Preview pattern: https://<branch>-<slug>.<subdomain>.workers.dev
   Push approval: <what the owner agreed>
   ```
4. Tell the owner in two or three lines: their site is up at the address (a link) to open on their phone, it stays unlisted until launch, and the next step (more pages, their domain, or launch).

## Step 5. Connect the Cloudflare integration (when the domain step comes, or for diagnosis)

Normal changes don't need any Cloudflare login on your side: GitHub drives the builds, and you check results through GitHub and the public site. The Cloudflare integration is needed for domain and DNS work (`website-custom-domain`) and for reading build logs. Connect it when one of those comes up, not before.

1. `find_capability(query="Cloudflare")`. If a Cloudflare integration is listed, use that id.
2. Otherwise use Cloudflare's official server: `run_capability(id="https://mcp.cloudflare.com/mcp", input={"connect": true})`. A sign-in card appears. In one line, ask the owner to press it, sign in to Cloudflare, and allow the permissions it asks for. Then stop the turn.
3. After they connect, `run_capability(id="https://mcp.cloudflare.com/mcp", input={})` lists the tools: `search`, `execute`, `docs` and `whoami`. `search` is read-only and runs without an approval card, so use it to look up endpoints. Each `execute` call may show an approval card because this server isn't in the platform's catalog yet. So do several API calls in one `execute` script rather than many small calls.
4. If the connection fails or the owner would rather not connect it, every domain step has a click-by-click fallback in `website-custom-domain`.

Never ask for a Cloudflare API token in chat.

## Fixing a failed build

1. Reproduce exactly what Cloudflare runs, from a clean install:
   ```bash
   cd ~/workspace/sites/<slug> && rm -rf node_modules dist && npm ci 2>&1 | tail -5 && npm run build 2>&1 | tail -30 && npx wrangler deploy --dry-run 2>&1 | tail -5
   ```
   Pass `timeout: 400`. Most failures show up here: a missing dependency, a typo in a component, an import path with the wrong case (Linux is case-sensitive), or `package-lock.json` not committed or out of date. Run `npm install`, then commit the lockfile.
2. Name mismatch: see Step 3.
3. Node version: the repo pins Node 24 in `.node-version`, and Cloudflare honours it. Don't remove it.
4. Still failing and the Cloudflare integration is connected: read the log with one `execute` call. Find the build with `GET /accounts/{account_id}/builds/workers/{worker_tag}/builds`; the worker tag is the `tag` field of the script in `GET /accounts/{account_id}/workers/scripts`, not its name. Then fetch `GET /accounts/{account_id}/builds/builds/{build_uuid}/logs`. Return only the last 60 lines.
5. Not connected: give the owner the logs link from `checks`, and ask them to screenshot the red lines at the bottom.

Never tell the owner a deploy worked until `wait` has printed LIVE.
