#!/usr/bin/env bash
# Conta linhas de código ignorando pastas ocultas (que começam com .)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"

cloc "$ROOT" \
  --exclude-dir="$(find "$ROOT" -maxdepth 2 -name '.*' -type d -exec basename {} \; | sort -u | tr '\n' ',' | sed 's/,$//')" \
  --not-match-d='^\.' \
  "$@"
