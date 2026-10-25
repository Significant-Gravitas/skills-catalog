#!/usr/bin/env bash
# Find and wait for Cloudflare Workers Builds deployments without any Cloudflare
# login: it reads GitHub check runs and PR comments, and fetches the site itself.
#
#   bash deploy-status.sh checks [sha]          build checks for a commit (default HEAD)
#   bash deploy-status.sh urls [pr-number]      workers.dev addresses Cloudflare posted on a PR
#   bash deploy-status.sh wait <url> [sha] [s]  wait until <url> serves commit <sha>
#                                               (default HEAD, up to s seconds, default 420)
#   bash deploy-status.sh preview-url <branch>  the expected preview address for a branch
#
# Run from inside the site's git repo. Needs gh to be logged in for checks/urls.
# The site must render <meta name="build" content="..."> (the starter's Base.astro
# does, from WORKERS_CI_COMMIT_SHA), which is how `wait` knows the new build is live.
set -uo pipefail

cmd="${1:-}"; shift || true
repo() { if [[ -n "${REPO:-}" ]]; then echo "$REPO"; else gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null; fi; }

case "$cmd" in
  checks)
    sha="${1:-$(git rev-parse HEAD)}"
    r="$(repo)"; [[ -z "$r" ]] && { echo "ERROR: no GitHub remote or gh not logged in"; exit 2; }
    # Cloudflare names its check "Workers Builds: <worker-name>".
    gh api "repos/$r/commits/$sha/check-runs" --jq '
      [.check_runs[] | select(.name | startswith("Workers Builds"))] as $cf
      | if ($cf | length) == 0 then "NO CLOUDFLARE CHECK YET for '"${sha:0:7}"' (still queued, preview builds switched off, or the repo is not connected in Cloudflare)"
        else $cf[] | "\(.name) | status: \(.status) | result: \(.conclusion // "pending") | logs: \(.details_url // "-")" end'
    ;;
  urls)
    r="$(repo)"; pr="${1:-}"
    [[ -z "$pr" ]] && pr="$(gh pr view --json number --jq .number 2>/dev/null)"
    [[ -z "$pr" ]] && { echo "ERROR: give a PR number (no PR for this branch)"; exit 2; }
    { gh api "repos/$r/issues/$pr/comments" --jq '.[].body'; gh pr view "$pr" --json body --jq .body; } 2>/dev/null \
      | grep -oE 'https://[a-zA-Z0-9.-]+\.workers\.dev' | sort -u
    # Branch aliases (<branch>-<worker>.<sub>.workers.dev) stay the same across
    # pushes; the 8-hex-digit ones are single deployments.
    ;;
  wait)
    url="${1:?give the URL to watch}"; sha="${2:-$(git rev-parse HEAD)}"; limit="${3:-420}"
    start=$(date +%s); last=""
    while :; do
      body="$(curl -sL --max-time 20 -H 'Cache-Control: no-cache' "$url?cb=$(date +%s)" || true)"
      code="$(curl -sL -o /dev/null -w '%{http_code}' --max-time 20 "$url?cb=$(date +%s)" || true)"
      live="$(printf '%s' "$body" | grep -oE '<meta name="build" content="[^"]*"' | sed -E 's/.*content="([^"]*)"/\1/' | head -1)"
      if [[ "$live" == "$sha" ]]; then echo "LIVE: $url is serving ${sha:0:7} (HTTP $code)"; exit 0; fi
      now=$(date +%s)
      if (( now - start >= limit )); then
        echo "NOT YET after ${limit}s: $url gives HTTP $code, serving build '${live:-unknown}', want ${sha:0:7}"
        exit 1
      fi
      status="HTTP $code build ${live:0:7}"
      [[ "$status" != "$last" ]] && echo "waiting: $status" && last="$status"
      sleep 15
    done
    ;;
  preview-url)
    branch="${1:?give the branch name}"
    prod="$(grep -iE '^\s*[-*]?\s*Production:' SITE.md 2>/dev/null | grep -oE 'https://[a-z0-9-]+\.[a-z0-9-]+\.workers\.dev' | head -1)"
    [[ -z "$prod" ]] && { echo "ERROR: SITE.md has no line like \"Production: https://<slug>.<subdomain>.workers.dev\""; exit 2; }
    host="${prod#https://}"; worker="${host%%.*}"; rest="${host#*.}"
    echo "https://${branch}-${worker}.${rest}"
    ;;
  *)
    sed -n '2,14p' "$0"; exit 2 ;;
esac
