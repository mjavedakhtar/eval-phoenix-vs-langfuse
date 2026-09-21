#!/usr/bin/env bash
# Clone the official Langfuse stack (once) and start it locally.
# UI: http://localhost:3000  — create a project, copy keys into .env
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/.local/langfuse"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required to self-host Langfuse." >&2
  exit 1
fi

if [[ ! -d "$DEST/.git" ]]; then
  mkdir -p "$ROOT/.local"
  git clone --depth=1 https://github.com/langfuse/langfuse.git "$DEST"
fi

cd "$DEST"
docker compose up -d
echo
echo "Langfuse is starting. Open http://localhost:3000"
echo "Sign up locally, create project 'data-fabric-agent',"
echo "then paste LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY into .env"
echo "and run: python experiments/run_langfuse.py"
