#!/usr/bin/env bash
# Create Sofia's durable hiring folder. Idempotent: never overwrites a file.
#
# Usage:  cd ~/skills/sofia-getting-started && bash scripts/init_hiring_folder.sh
# Env:    HIRING_DIR  (default: $HOME/workspace/hiring)
# Output: one line per created item, then a tree of the folder.
# Exit:   0 ok; 2 if the templates folder cannot be found (run from the package dir).
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATES="$HERE/templates"
HIRING_DIR="${HIRING_DIR:-$HOME/workspace/hiring}"

if [ ! -d "$TEMPLATES/tracker-headers" ]; then
  echo "error: $TEMPLATES/tracker-headers not found; run from ~/skills/sofia-getting-started" >&2
  exit 2
fi

if [ ! -d "$HOME/workspace" ]; then
  echo "warning: $HOME/workspace does not exist (no durable volume mounted)." >&2
  echo "         Creating it anyway; tell the owner files may not survive this chat." >&2
fi

for d in "" roles tracker packets debriefs offers reports flags screens; do
  if [ ! -d "$HIRING_DIR/$d" ]; then
    mkdir -p "$HIRING_DIR/$d"
    echo "created dir  $HIRING_DIR/$d"
  fi
done

copy_if_absent() {
  local src="$1" dest="$2"
  if [ ! -f "$dest" ]; then
    cp "$src" "$dest"
    echo "created file $dest"
  fi
}

for f in roles candidates loops; do
  copy_if_absent "$TEMPLATES/tracker-headers/$f.csv" "$HIRING_DIR/tracker/$f.csv"
done
for f in shortlist outreach-log dnc searches; do
  copy_if_absent "$TEMPLATES/tracker-headers/$f.csv" "$HIRING_DIR/$f.csv"
done
copy_if_absent "$TEMPLATES/preferences.md" "$HIRING_DIR/preferences.md"

echo "--- $HIRING_DIR"
if command -v find >/dev/null 2>&1; then
  (cd "$HIRING_DIR" && find . -maxdepth 2 | sort)
fi
