#!/usr/bin/env bash
# Create the durable folder for one role and a blank hiring plan.
#
# Usage:  bash scripts/init_role.sh <role-slug> [--root DIR]
#   <role-slug>  lowercase letters, digits and hyphens, e.g. billing-ops-lead
#   --root DIR   parent folder (default: $HOME/workspace/hiring)
#
# Creates <root>/<role-slug>/{screens,scorecards,debriefs,drafts} and copies
# templates/hiring-plan.md to <root>/<role-slug>/hiring-plan.md with the slug
# and today's date filled in. Never overwrites anything.
#
# Exit codes: 0 created; 2 the role folder already exists (open it instead);
#             3 bad arguments; 4 the root is not writable.
# No network, no secrets.
set -u

here="$(cd "$(dirname "$0")/.." && pwd)"
template="$here/templates/hiring-plan.md"
root="${HOME}/workspace/hiring"
slug=""

while [ $# -gt 0 ]; do
  case "$1" in
    --root) root="${2:-}"; shift 2 ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    *) if [ -z "$slug" ]; then slug="$1"; shift; else echo "error: unexpected argument '$1'" >&2; exit 3; fi ;;
  esac
done

if [ -z "$slug" ]; then
  echo "error: give a role slug, e.g. bash scripts/init_role.sh billing-ops-lead" >&2
  exit 3
fi
if ! printf '%s' "$slug" | grep -Eq '^[a-z0-9]([a-z0-9-]{0,62}[a-z0-9])?$'; then
  echo "error: '$slug' is not a valid slug; use lowercase letters, digits and single hyphens" >&2
  exit 3
fi
if [ ! -f "$template" ]; then
  echo "error: template missing at $template; re-run read_skill to re-sync the package" >&2
  exit 3
fi

mkdir -p "$root" 2>/dev/null
if [ ! -w "$root" ]; then
  echo "error: $root is not writable; the plan will not persist. Deliver files with write_workspace_file instead." >&2
  exit 4
fi

dir="$root/$slug"
if [ -d "$dir" ]; then
  echo "role folder exists, open it instead: $dir"
  ls -1 "$dir"
  exit 2
fi

mkdir -p "$dir/screens" "$dir/scorecards" "$dir/debriefs" "$dir/drafts"
today="$(date -u +%Y-%m-%d)"
sed -e "s/<role-slug>/$slug/g" -e "s/<YYYY-MM-DD>/$today/g" "$template" > "$dir/hiring-plan.md"

echo "created: $dir/hiring-plan.md"
echo "roles already set up under $root:"
ls -1 "$root"
exit 0
