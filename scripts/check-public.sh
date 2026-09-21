#!/usr/bin/env bash
# Fail if employer-specific strings leaked into files that would be published.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

hits="$(
  grep -RInE 'Siemens|Amberg|SODF|Opcenter|Insights Hub|ontology\.siemens|BOMBOP|siemens\.com' \
    --exclude-dir=.git --exclude-dir=.venv --exclude-dir=.local --exclude-dir=internal \
    --exclude-dir=__pycache__ --exclude=check-public.sh . || true
)"

if [[ -n "$hits" ]]; then
  echo "Public tree still contains strings that should not go to personal GitHub:"
  echo "$hits"
  exit 1
fi

echo "Public tree looks clean."
