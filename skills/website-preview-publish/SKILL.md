---
name: "website-preview-publish"
description: "Changes to a website that's already online: opening hours, prices, phone number, text, photos, new sections. Make the change on a branch, get Cloudflare's public preview link, show the owner or client a screenshot and the link, publish on approval, roll back if anything goes wrong. Use for 'update my website', 'change our hours', 'update prices', 'show me a preview', 'publish the changes', 'undo the last change'."
triggers: ["update my website", "change our hours", "update prices on the website", "website preview link", "publish the changes", "change my website", "edit the site", "roll back the website", "undo website change", "show the client a preview"]
version: "1"
---

# Website preview and publish

Every change to a live site goes the same way: a branch, a preview link, an approval, then live. The owner never sees broken work on their real site, every change is recorded on GitHub, and anything can be undone.

Requires hosting to be set up (`SITE.md` has a GitHub repo and a production workers.dev address). If not, load `website-hosting-setup` first.

Package files: `/home/user/skills/website-preview-publish/scripts/deploy-status.sh` (build checks, preview addresses, waiting for a deploy) and `scripts/shoot.sh` (phone and desktop screenshots of any URL).

## Before launch vs after launch

- **Before launch** (`launched: false` in `src/site.config.mjs`), the production workers.dev address is the owner's unlisted staging site: noindex, and blocked to search engines. Push finished work straight to `main` and send that address as the preview link. Branches are optional. QA still runs before every push.
- **After launch**, everything below applies.
- **Going live for the first time** (attaching the domain, flipping `launched`) is not a merge. If the owner says "go live" and SITE.md shows no launched domain, load `website-launch-care` and follow its launch checklist.

## The rules (after launch)

- **`main` is the live site.** Merging to `main` publishes it. Nothing reaches `main` without the owner's explicit OK for that change ("go live", "publish", "yes"), unless SITE.md records a standing permission ("small text fixes can go live directly").
- **Work happens on branches.** Every branch gets a public preview at `https://<branch>-<slug>.<subdomain>.workers.dev`. Preview pages are hidden from search engines automatically.
- **Pushing to a preview branch is part of the job.** The first time, get the owner's agreement in one line ("I'll push work-in-progress to preview links without asking each time; going live always needs your OK") and record it in SITE.md. The platform may still show an approval card on pushes. If cards on every push annoy the owner, they can choose "approve from now on" for you on the card. Tell them that allows all your shell commands, not just pushes.
- **Never tell anyone a change is live or previewable until `deploy-status.sh wait` has printed LIVE for that address.**

## Branch names

Lowercase letters, digits and hyphens only, no slashes, under 25 characters, saying what the change is: `new-menu`, `spring-offer`, `fix-phone`. The branch name becomes part of the preview address, and Cloudflare limits that part (branch plus Worker name) to 63 characters.

## The loop

### 1. Start from the latest live code

```bash
cd ~/workspace/sites/<slug>
git fetch -q origin && git switch main -q && git pull -q --ff-only
git switch -c <branch>
```

If the repo isn't in `~/workspace/sites/` (a new computer), clone it first: `cd ~/workspace/sites && gh repo clone <owner>/<slug> && cd <slug> && npm ci`. Run npm with `timeout: 300`.

If the owner has a change already waiting on a preview branch, keep working on that branch instead of starting a new one.

### 2. Make the change and check it

Edit (load `website-build` for anything beyond small edits), then:

```bash
npm run build 2>&1 | tail -10 && node /home/user/skills/website-build/scripts/qa.mjs
```

If `/home/user/skills/website-build/` isn't present, load `website-build` to get the QA script. Fix every ERROR before pushing.

### 3. Push and open a pull request

```bash
git add -A && git commit -q -m "<plain description>"
git push -q -u origin <branch>
gh pr create --title "<plain description>" --body "<two or three lines: what changed and why>" --head <branch> --base main
```

The pull request is the change record. Cloudflare comments on it with the build status and the preview addresses.

### 4. Wait for the preview and check it yourself

```bash
S=/home/user/skills/website-preview-publish/scripts/deploy-status.sh
$S preview-url <branch>                                  # expected address
$S wait "$($S preview-url <branch>)" "$(git rev-parse HEAD)"   # timeout: 480
```

- A build usually takes 1 to 3 minutes.
- If `wait` times out, run `$S checks` to see Cloudflare's check, and `$S urls` to see the addresses Cloudflare posted on the PR. If Cloudflare's address differs from the expected one, use Cloudflare's and fix the pattern in SITE.md.
- **NO CLOUDFLARE CHECK** for several minutes on a branch, while `main` builds fine, means preview builds are switched off. Ask the owner to switch them on: Cloudflare dashboard > **Workers & Pages** > `<slug>` > **Settings** > **Build** > **Branch control** > tick **Enable Preview Builds** (sometimes labelled for non-production branches) > **Save**. Then push an empty commit to trigger it: `git commit --allow-empty -m "Trigger preview" && git push -q`.
- Failed check: follow "Fixing a failed build" in `website-hosting-setup` (reproduce with a clean `npm ci && npm run build` first).

Then screenshot the preview and look at it, phone first:

```bash
bash /home/user/skills/website-preview-publish/scripts/shoot.sh "<preview-url>" shots <page-path>
```

Use `read_file` on the PNGs. If something is off, fix it, push again (same branch, same preview address), and wait again.

### 5. Show the owner

Upload the phone screenshot slice that shows the change (`write_workspace_file(source_path=...)`; short pages give one file, long pages come as `-part0`, `-part1`... top to bottom), then send a short message:

```
Preview of the new menu page: <preview-url>/menu/
![Menu page on a phone](workspace://<id>#image/png)
Prices are from your September list; the seasonal section is new.
Say "go live" when you're happy, or tell me what to change.
```

For an agency's client, the preview link can go straight to the client. It's public, works on any phone, and needs no login. If a preview must stay private (an unannounced launch), protect previews with Cloudflare Access: dashboard > **Workers & Pages** > `<slug>` > **Access** (or Settings) > protect **Previews only**, allowing the client's email addresses. It's free for up to 50 users. Cloudflare may ask the owner to set up Zero Trust the first time.

### 6. Go live (only on approval)

If the site hasn't launched yet (see "Before launch vs after launch"), stop here and load `website-launch-care` instead.

```bash
gh pr merge <number> --squash --delete-branch
git switch main -q && git pull -q --ff-only
S=/home/user/skills/website-preview-publish/scripts/deploy-status.sh
$S wait "<production url from SITE.md>" "$(git rev-parse HEAD)"      # timeout: 480
```

If a custom domain is live, also wait on it: `$S wait https://<domain> "$(git rev-parse HEAD)"`. Then reply in one or two lines: it's live, with the link. Close any related to-dos.

### 7. Undo (rollback)

First look at what's actually wrong: screenshot the live site (`shoot.sh https://<domain>`) and check the latest Cloudflare build (`deploy-status.sh checks`). Revert only if the last change caused the problem; if something else is wrong (a third-party embed, the domain, the form service), say what it is and fix that instead.

- **A published change needs undoing:** revert it through git, so the live site and the code stay in step.
  ```bash
  git switch main -q && git pull -q --ff-only
  git revert --no-edit <merge-commit-sha>
  git push -q origin main
  ```
  Then `wait` on the production address and on the domain. Reverting restores the live site, so tell the owner what you're doing before you push; that one sentence is the approval moment.
- **Emergency (site broken right now, and the git route is too slow):** the owner opens Cloudflare dashboard > **Workers & Pages** > `<slug>` > **Deployments**, then on the previous good version **...** > **Rollback**. Then you revert in git anyway, because the next push to `main` would otherwise re-deploy the broken version.

## Small requests from non-technical owners

Opening hours, a price, a phone number, a new photo:
- Make the change in `src/site.config.mjs` or the data file, so it updates everywhere at once.
- Preview it and show the owner. When they confirm, publish.
- If the owner says "for tiny fixes like this, just do it", record that in SITE.md and from then on publish typo-level fixes directly after QA, telling them afterwards with the link.
- After a change to hours, phone, address or prices, remind them in one line to make the same change on their Google Business Profile (and Facebook) so they match. Mismatches confuse customers and Google.

## Housekeeping

- Delete merged branches (`--delete-branch` does it). Previews of deleted branches stay until Cloudflare's limit of 100 removes the oldest. That's fine.
- Keep SITE.md's "Recent changes" list to the last ten items, with dates.
- If a preview branch is abandoned, close its PR with a one-line reason.
