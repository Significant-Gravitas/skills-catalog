#!/usr/bin/env bash
# Lighthouse scores (mobile) for a live URL: performance, accessibility,
# best practices, SEO, plus the top problems to fix.
# Usage: bash speed.sh https://example.com/     (a live or preview address)
#        bash speed.sh dist                     (the local build, served for the test)
# Tries local Lighthouse with the sandbox's Chrome first (about 1-2 minutes on a
# small machine, so its performance score is a little pessimistic), then
# Google's PageSpeed API, then prints a link the owner can open.
set -uo pipefail
URL="${1:?give a full https:// URL or a dist folder}"
OUT="/tmp/lh-$$.json"
SERVER_PID=""
trap '[[ -n "$SERVER_PID" ]] && kill "$SERVER_PID" 2>/dev/null' EXIT
if [[ -d "$URL" ]]; then
  PORT=$(( 4900 + RANDOM % 500 ))
  python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$URL" >/dev/null 2>&1 &
  SERVER_PID=$!
  for _ in $(seq 1 20); do curl -s -o /dev/null "http://127.0.0.1:$PORT/" && break; sleep 0.3; done
  URL="http://127.0.0.1:$PORT/"
  echo "(local build: performance is indicative; SEO reads low before launch because of the pre-launch noindex)"
fi

summarise() { # json file, source label
  node -e '
    const r = JSON.parse(require("fs").readFileSync(process.argv[1], "utf8"));
    const lh = r.lighthouseResult || r;
    const c = lh.categories;
    const pct = k => c[k] ? Math.round(c[k].score * 100) : "-";
    console.log(`Scores (${process.argv[2]}, mobile): performance ${pct("performance")}, accessibility ${pct("accessibility")}, best practices ${pct("best-practices")}, SEO ${pct("seo")}`);
    const a = lh.audits;
    for (const k of ["largest-contentful-paint", "cumulative-layout-shift", "total-blocking-time"]) if (a[k]) console.log(`  ${a[k].title}: ${a[k].displayValue || "-"}`);
    const bad = Object.values(a).filter(x => x.score !== null && x.score < 0.9 && x.scoreDisplayMode !== "informative" && x.scoreDisplayMode !== "notApplicable" && x.scoreDisplayMode !== "manual")
      .sort((x, y) => x.score - y.score).slice(0, 10);
    if (bad.length) console.log("Fix first:");
    for (const x of bad) console.log(`  - ${x.title}${x.displayValue ? " (" + x.displayValue + ")" : ""}`);
  ' "$1" "$2"
}

CHROME=""
for b in google-chrome google-chrome-stable chromium chromium-browser; do
  command -v "$b" >/dev/null 2>&1 && CHROME="$(command -v "$b")" && break
done
if [[ -n "$CHROME" ]]; then
  CHROME_PATH="$CHROME" timeout 300 npx -y lighthouse@13 "$URL" --quiet \
    --chrome-flags="--headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage --disable-extensions --disable-background-networking --disable-component-update" \
    --only-categories=performance,accessibility,best-practices,seo --form-factor=mobile \
    --output=json --output-path="$OUT" >/dev/null 2>&1
  if [[ -s "$OUT" ]]; then summarise "$OUT" "Lighthouse in the sandbox"; rm -f "$OUT"; exit 0; fi
fi

API="https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=$(node -e 'console.log(encodeURIComponent(process.argv[1]))' "$URL")&strategy=mobile&category=performance&category=accessibility&category=best-practices&category=seo"
if curl -s --max-time 120 "$API" -o "$OUT" && node -e 'process.exit(JSON.parse(require("fs").readFileSync(process.argv[1])).lighthouseResult ? 0 : 1)' "$OUT" 2>/dev/null; then
  summarise "$OUT" "PageSpeed Insights"; rm -f "$OUT"; exit 0
fi
rm -f "$OUT"
echo "Could not run Lighthouse here. Open https://pagespeed.web.dev/analysis?url=$(node -e 'console.log(encodeURIComponent(process.argv[1]))' "$URL") or ask the owner to, and read the scores from a screenshot."
exit 1
