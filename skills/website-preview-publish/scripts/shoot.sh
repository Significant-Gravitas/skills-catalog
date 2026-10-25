#!/usr/bin/env bash
# Screenshot a page at phone and desktop sizes, sized so read_file can show it.
# Usage: bash shoot.sh <url-or-dist-folder> [out-folder] [page-path] [frames]
#   bash shoot.sh dist                 serves the built site locally and shoots /
#   bash shoot.sh dist shots /contact/ shoots one page of the built site
#   bash shoot.sh https://x.workers.dev shoots a live or preview address
#   bash shoot.sh dist shots / frames  motion frames: load sequence + scroll positions
#                                      (desktop and phone), to judge motion from stills
# Env (passed through to shoot.mjs): SHOOT_WAIT=6000 for sites with preloaders,
# SHOOT_EVAL='document.querySelector(".menu-toggle").click()' to capture a state,
# FRAMES_AT=0.2,0.22,0.24 to land frames inside a pinned section.
# Prints the PNG paths. Each image is at most 2000 px tall and under 3 MiB.
# Uses shoot.mjs (full page, real phone emulation) and falls back to Chrome's
# --screenshot mode, then Firefox. Full-page shots render with reduced motion, so
# they show the finished composition; use the frames mode to see the motion.
set -uo pipefail

TARGET="${1:?give a URL or a dist folder}"
OUT="${2:-shots}"
PAGE="${3:-/}"
MODE="${4:-}"
mkdir -p "$OUT"

SERVER_PID=""
cleanup() { [[ -n "$SERVER_PID" ]] && kill "$SERVER_PID" 2>/dev/null; rm -rf "/tmp/shoot-profile-$$"; }
trap cleanup EXIT

if [[ -d "$TARGET" ]]; then
  PORT="$(python3 -c 'import socket; s = socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')"
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
    for attempt in 1 2; do
      CHROME_PATH="$(command -v "$BROWSER")" timeout 140 node "$HERE/shoot.mjs" "$URL" "$OUT/${NAME}" "$label" 2>&1 >/dev/null | grep -E "TRUNCATED" >&2; [[ ${PIPESTATUS[0]} -eq 0 ]] && break
    done
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

if [[ "$MODE" == "frames" ]]; then
  [[ -z "$BROWSER" ]] && { echo "FAILED: no Chrome/Chromium for motion frames" >&2; exit 1; }
  rm -f "$OUT/${NAME}-frames-"*.png
  CHROME_PATH="$(command -v "$BROWSER")" timeout 180 node "$HERE/shoot.mjs" "$URL" "$OUT/${NAME}" frames >/dev/null 2>&1
  CHROME_PATH="$(command -v "$BROWSER")" timeout 180 node "$HERE/shoot.mjs" "$URL" "$OUT/${NAME}" frames-phone >/dev/null 2>&1
  # Contact sheets: all frames of one device in a single image, labelled, so the
  # whole motion sequence can be read in one read_file call.
  for dev in desktop phone; do
    frames=( "$OUT/${NAME}-frames-${dev}-"*.png )
    [[ -e "${frames[0]}" ]] || continue
    abs="$(cd "$OUT" && pwd)"
    sheet_html="$abs/${NAME}-frames-${dev}-sheet.html"
    if [[ "$dev" == desktop ]]; then cols=3; w=640; else cols=9; w=212; fi
    {
      echo "<!doctype html><html><body style='margin:0;background:#222;font:14px monospace;color:#eee'><div style='display:grid;grid-template-columns:repeat($cols,${w}px);gap:8px;padding:8px'>"
      for f in "${frames[@]}"; do
        label="$(basename "$f" .png | sed "s/^${NAME}-frames-${dev}-//")"
        echo "<figure style='margin:0'><img src='file://$abs/$(basename "$f")' style='width:${w}px;display:block'><figcaption>$label</figcaption></figure>"
      done
      echo "</div></body></html>"
    } > "$sheet_html"
    CHROME_PATH="$(command -v "$BROWSER")" timeout 90 node "$HERE/shoot.mjs" "file://$sheet_html" "$OUT/${NAME}-frames-${dev}" sheet >/dev/null 2>&1 \
      && mv "$OUT/${NAME}-frames-${dev}-sheet.png" "$OUT/${NAME}-frames-${dev}-contact-sheet.png" 2>/dev/null
    rm -f "$sheet_html"
  done
  ls "$OUT/${NAME}-frames-"*contact-sheet.png 2>/dev/null
  echo "(single frames are in $OUT/${NAME}-frames-*.png if you need a closer look)"
  exit 0
fi

# Phone first: most small-business visitors are on a phone.
shot 390 844 phone
shot 1440 900 desktop
