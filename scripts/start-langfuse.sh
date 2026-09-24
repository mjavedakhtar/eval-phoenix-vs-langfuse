#!/usr/bin/env bash
# Clone the official Langfuse stack (once) and start it locally.
# UI default: http://localhost:3000  — if that port is busy, binds 3001.
# Creates a local project on first boot so you do not need cloud signup.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$ROOT/.local/langfuse"
HOST_PORT=3000

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required to self-host Langfuse." >&2
  exit 1
fi

if lsof -nP -iTCP:3000 -sTCP:LISTEN >/dev/null 2>&1; then
  HOST_PORT=3001
  echo "Port 3000 is in use; Langfuse UI will be http://localhost:${HOST_PORT}"
fi

if [[ ! -d "$DEST/.git" ]]; then
  mkdir -p "$ROOT/.local"
  git clone --depth=1 https://github.com/langfuse/langfuse.git "$DEST"
fi

COMPOSE_ENV="$DEST/.env"
if [[ ! -f "$COMPOSE_ENV" ]]; then
  PK="pk-lf-$(openssl rand -hex 16)"
  SK="sk-lf-$(openssl rand -hex 16)"
  cat >"$COMPOSE_ENV" <<EOF
NEXTAUTH_URL=http://localhost:${HOST_PORT}
LANGFUSE_INIT_ORG_ID=lab
LANGFUSE_INIT_ORG_NAME=lab
LANGFUSE_INIT_PROJECT_ID=data-fabric-agent
LANGFUSE_INIT_PROJECT_NAME=data-fabric-agent
LANGFUSE_INIT_PROJECT_PUBLIC_KEY=${PK}
LANGFUSE_INIT_PROJECT_SECRET_KEY=${SK}
LANGFUSE_INIT_USER_EMAIL=lab@example.com
LANGFUSE_INIT_USER_NAME=lab
LANGFUSE_INIT_USER_PASSWORD=lab-local-only
EOF
  echo "Wrote first-boot keys to ${COMPOSE_ENV}"
else
  # Keep NEXTAUTH_URL aligned with the port we actually bind.
  if grep -q '^NEXTAUTH_URL=' "$COMPOSE_ENV"; then
    sed -i.bak "s|^NEXTAUTH_URL=.*|NEXTAUTH_URL=http://localhost:${HOST_PORT}|" "$COMPOSE_ENV"
    rm -f "$COMPOSE_ENV.bak"
  else
    echo "NEXTAUTH_URL=http://localhost:${HOST_PORT}" >>"$COMPOSE_ENV"
  fi
fi

cat >"$DEST/docker-compose.override.yml" <<EOF
services:
  langfuse-web:
    ports: !override
      - "${HOST_PORT}:3000"
EOF

# Mirror keys into the lab .env (gitignored).
PK="$(awk -F= '/^LANGFUSE_INIT_PROJECT_PUBLIC_KEY=/{print $2}' "$COMPOSE_ENV")"
SK="$(awk -F= '/^LANGFUSE_INIT_PROJECT_SECRET_KEY=/{print $2}' "$COMPOSE_ENV")"
LAB_ENV="$ROOT/.env"
touch "$LAB_ENV"
python3 - "$LAB_ENV" "$HOST_PORT" "$PK" "$SK" <<'PY'
from pathlib import Path
import sys
path, port, pk, sk = Path(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
text = path.read_text() if path.exists() else ""
replacements = {
    "LANGFUSE_BASE_URL": f"http://localhost:{port}",
    "LANGFUSE_HOST": f"http://localhost:{port}",
    "LANGFUSE_PUBLIC_KEY": pk,
    "LANGFUSE_SECRET_KEY": sk,
}
lines = text.splitlines() if text else []
seen = set()
out = []
for line in lines:
    key = line.split("=", 1)[0] if "=" in line and not line.strip().startswith("#") else None
    if key in replacements:
        out.append(f"{key}={replacements[key]}")
        seen.add(key)
    else:
        out.append(line)
for key, value in replacements.items():
    if key not in seen:
        out.append(f"{key}={value}")
path.write_text("\n".join(out) + "\n")
PY

cd "$DEST"
if docker compose version >/dev/null 2>&1; then
  docker compose up -d
else
  docker-compose up -d
fi
echo
echo "Langfuse is starting. Open http://localhost:${HOST_PORT}"
echo "Local login: lab@example.com / lab-local-only  (this machine only)"
echo "Then: uv run python experiments/run_langfuse.py"
