#!/usr/bin/env bash
# Create a new site from the starter, install dependencies and prove it builds.
# Usage: bash new-site.sh <slug> "<Business Name>"
#   slug: lowercase letters, digits and hyphens, 3-20 chars. It becomes the
#   folder, the GitHub repo name and the Cloudflare Worker name.
set -euo pipefail

SLUG="${1:-}"
NAME="${2:-}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STARTER="$HERE/../starter"
SITES="${SITES_DIR:-$HOME/workspace/sites}"
DEST="$SITES/$SLUG"

if [[ ! "$SLUG" =~ ^[a-z0-9]([a-z0-9-]{1,18})[a-z0-9]$ ]]; then
  echo "ERROR: slug must be 3-20 chars of a-z, 0-9 and hyphens, not starting or ending with a hyphen" >&2
  exit 2
fi
if [[ -z "$NAME" ]]; then
  echo "ERROR: give the business name as the second argument" >&2
  exit 2
fi
if [[ -e "$DEST" ]]; then
  echo "ERROR: $DEST already exists. Work in it, or choose another slug." >&2
  exit 3
fi

mkdir -p "$SITES"
cp -R "$STARTER" "$DEST"
cd "$DEST"
mv gitignore.txt .gitignore
mv node-version.txt .node-version

TODAY="$(date -u +%Y-%m-%d)"
sed -i "s|__SLUG__|$SLUG|g" package.json wrangler.jsonc src/site.config.mjs
sed -i "s|__DATE__|$TODAY|g" wrangler.jsonc
# Insert the business name as a properly quoted JS string (handles ' & " etc).
SITE_NAME="$NAME" node -e '
  const fs = require("fs");
  const p = "src/site.config.mjs";
  fs.writeFileSync(p, fs.readFileSync(p, "utf8").replace("\x27__NAME__\x27", JSON.stringify(process.env.SITE_NAME)));
'

OGTMP="$(mktemp -u /tmp/new-site-og-XXXXXX)"
# Placeholder favicon and social image so nothing 404s. Replace both with the
# owner's real logo and a designed 1200x630 image before launch (QA --launch checks).
SITE_NAME="$NAME" OGTMP="$OGTMP" node -e '
  const fs = require("fs");
  const name = process.env.SITE_NAME;
  const esc = (t) => t.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" }[c]));
  const initial = (name.match(/[A-Za-z0-9]/) || ["W"])[0].toUpperCase();
  fs.writeFileSync("public/favicon.svg", `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#141414"/><text x="32" y="44" font-family="Arial, sans-serif" font-size="36" font-weight="700" text-anchor="middle" fill="#ffffff">${initial}</text></svg>\n`);
  fs.writeFileSync(process.env.OGTMP + ".html", `<!doctype html><html><body style="margin:0;width:1200px;height:630px;display:flex;align-items:center;justify-content:center;background:#141414;color:#fff;font:700 64px/1.15 system-ui,Arial,sans-serif;text-align:center;padding:0 80px;box-sizing:border-box">${esc(name)}</body></html>`);
'
CHROME="$(command -v google-chrome || command -v google-chrome-stable || command -v chromium || command -v chromium-browser || true)"
if [[ -n "$CHROME" ]]; then
  CHROME_PATH="$CHROME" timeout 90 node "$HERE/shoot.mjs" "file://$OGTMP.html" "$OGTMP" og >/dev/null 2>&1 \
    && mv "$OGTMP-og.png" public/og.png
rm -f "$OGTMP.html"
fi
if [[ ! -s public/og.png ]] && command -v convert >/dev/null 2>&1; then
  convert -size 1200x630 xc:'#141414' public/og.png
fi
[[ -s public/og.png ]] || echo "WARN: could not make public/og.png; make a 1200x630 PNG before launch"
sha256sum public/favicon.svg public/og.png 2>/dev/null > starter-placeholders.txt || true

echo "== installing dependencies (about a minute)"
npm install --no-audit --no-fund --loglevel=error
echo "== building"
if ! npm run build --silent > /tmp/new-site-build.log 2>&1; then
  tail -30 /tmp/new-site-build.log; echo "ERROR: starter build failed (log above)" >&2; exit 4
fi
tail -3 /tmp/new-site-build.log
npx wrangler deploy --dry-run 2>&1 | grep -E "Read [0-9]+ files|ERROR|error" || true

git init -q -b main
# A local identity so commits work before GitHub is connected; website-hosting-setup
# switches it to the owner's GitHub identity.
git config user.name "Website build"
git config user.email "build@localhost"
git add -A
git commit -q -m "Start $NAME website from starter"
echo "== ready: $DEST"
