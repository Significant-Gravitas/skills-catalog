#!/usr/bin/env bash
# After launch, check that every old URL still lands somewhere useful.
# Usage: bash check-redirects.sh https://newdomain.com old-urls.txt
# Each line: OK (200 directly, or a redirect chain ending in 200) or BROKEN.
# Exit code 1 if anything is broken.
set -uo pipefail
BASE="${1:?give the live site, e.g. https://example.com}"; LIST="${2:?give the file of old paths}"
BASE="${BASE%/}"; bad=0; n=0
while IFS= read -r path; do
  [[ -z "$path" || "$path" == \#* ]] && continue
  n=$((n+1))
  note=""; [[ "$path" == *\?* ]] && note=" (query URL: only a wildcard rule can catch it)"
  path="${path// /%20}"
  read -r code final hops < <(curl -s -o /dev/null -L --max-redirs 5 --max-time 20 \
    -w '%{http_code} %{url_effective} %{num_redirects}\n' "$BASE$path")
  if [[ "$code" == "200" ]]; then
    if [[ "$hops" == "0" ]]; then echo "OK      $path$note"; else echo "OK      $path -> ${final#$BASE} ($hops redirect)$note"; fi
  else
    echo "BROKEN  $path -> HTTP $code (${final#$BASE})$note"; bad=$((bad+1))
  fi
done < "$LIST"
echo "$n checked, $bad broken"
exit $(( bad > 0 ))
