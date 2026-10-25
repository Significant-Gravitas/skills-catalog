#!/usr/bin/env bash
# Screenshot a page at phone and desktop sizes, sized so read_file can show it.
# Usage: bash shoot.sh <url-or-dist-folder> [out-folder] [page-path]
#   bash shoot.sh dist                 serves the built site locally and shoots /
#   bash shoot.sh dist shots /contact/ shoots one page of the built site
#   bash shoot.sh https://x.workers.dev shoots a live or preview address
# Prints the PNG paths. Each image is at most 2000 px tall and under 3 MiB.
# Uses shoot.mjs (full page, real phone emulation) and falls back to Chrome's
# --screenshot mode, then Firefox.
set -uo pipefail

TARGET="${1:?give a URL or a dist folder}"
OUT="${2:-shots}"
PAGE="${3:-/}"
mkdir -p "$OUT"

SERVER_PID=""
cleanup() { [[ -n "$SERVER_PID" ]] && kill "$SERVER_PID" 2>/dev/null; }
trap cleanup EXIT

if [[ -d "$TARGET" ]]; then
  PORT=$(( 4300 + RANDOM % 600 ))
  python3 -m http.server "$PORT" --bind 127.0.0.1 --directory "$TARGET" >/dev/null 2>&1 &
  SERVER_PID=$!
  for _ in $(seq 1 20); do
    curl -s -o /dev/null "http://127.0.0.1:$PORT/" && break
    sleep 0.3
  done
  URL="http://127.0.0.1:$PORT${PAGE}"
else
  URL="${TARGET%/}${PAGE}"
fi

BROWSER=""
for b in google-chrome google-chrome-stable chromium chromium-browser; do
  if command -v "$b" >/dev/null 2>&1; then BROWSER="$b"; break; fi
done

NAME="$(printf '%s' "$PAGE" | tr -c 'a-zA-Z0-9' '-' | sed 's/^-*//; s/-*$//')"
NAME="${NAME:-home}"

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
QUIET_FLAGS=(--disable-features=Translate,OptimizationHints,MediaRouter,DialMediaRouteProvider,CalculateNativeWinOcclusion,InterestFeedContentSuggestions,CertificateTransparencyComponentUpdater,AutofillServerCommunication,PrivacySandboxSettings4
  --disable-extensions --disable-component-extensions-with-background-pages --disable-background-networking
  --disable-component-update --disable-sync --disable-default-apps --mute-audio --disable-domain-reliability
  --password-store=basic --use-mock-keychain)

shot() { # width height label
  local w="$1" h="$2" label="$3" file="$OUT/${NAME}-$3.png"
  rm -f "$OUT/${NAME}-${label}"*.png
  if [[ -n "$BROWSER" ]] && command -v node >/dev/null 2>&1 && [[ -f "$HERE/shoot.mjs" ]]; then
    CHROME_PATH="$(command -v "$BROWSER")" timeout 100 node "$HERE/shoot.mjs" "$URL" "$OUT/${NAME}" "$label" >/dev/null 2>&1
  fi
  if ! ls "$OUT/${NAME}-${label}"*.png >/dev/null 2>&1 && [[ -n "$BROWSER" ]]; then
    timeout 45 "$BROWSER" --headless=new --no-sandbox --disable-gpu --hide-scrollbars \
      --no-first-run --disable-dev-shm-usage --force-device-scale-factor=1 "${QUIET_FLAGS[@]}" \
      --user-data-dir="/tmp/shoot-profile-$$" --virtual-time-budget=4000 \
      --window-size="$w,$h" --screenshot="$file" "$URL" >/dev/null 2>&1
  fi
  if ! ls "$OUT/${NAME}-${label}"*.png >/dev/null 2>&1 && command -v firefox >/dev/null 2>&1; then
    timeout 60 firefox --headless --window-size="$w,$h" --screenshot "$file" "$URL" >/dev/null 2>&1
  fi
  local found=0
  for f in "$OUT/${NAME}-${label}"*.png; do
    [[ -s "$f" ]] || continue
    found=1
    # read_file refuses images over 2000 px per side or 3 MiB.
    if command -v convert >/dev/null 2>&1; then
      convert "$f" -resize '2000x2000>' -strip "$f"
      [[ $(stat -c %s "$f") -gt 3000000 ]] && convert "$f" -resize 60% "$f"
    fi
    echo "$f"
  done
  if (( ! found )); then
    echo "FAILED $label: no browser produced a screenshot of $URL" >&2
    return 1
  fi
}

# Phone first: most small-business visitors are on a phone.
shot 390 844 phone
shot 1440 900 desktop
