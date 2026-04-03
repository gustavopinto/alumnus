#!/usr/bin/env bash
# Conta linhas de código ignorando pastas ocultas (que começam com .)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

EXCLUDE_HIDDEN_DIRS="$(find "$ROOT" -maxdepth 2 -name '.*' -type d -exec basename {} \; | sort -u | tr '\n' ',' | sed 's/,$//')"
EXCLUDE_DIRS="${EXCLUDE_HIDDEN_DIRS:+${EXCLUDE_HIDDEN_DIRS},}htmlcov,coverage_html"

cloc "$ROOT" \
  --exclude-dir="$EXCLUDE_DIRS" \
  --not-match-d='^\.' \
  "$@"
