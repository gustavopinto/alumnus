#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

stop() {
  echo "Parando containers..."
  docker compose -f "$ROOT/docker-compose.yml" down
}

run_migrations() {
  echo "Aguardando PostgreSQL..."
  until docker compose -f "$ROOT/docker-compose.yml" exec -T db \
    pg_isready -U alumnus -q 2>/dev/null; do
    sleep 1
  done
  echo "Aplicando migrations..."
  docker compose -f "$ROOT/docker-compose.yml" exec -T backend \
    python3 /app/migrate.py
}

if [ "${1}" = "stop" ]; then
  stop
  echo "App parada."
  exit 0
fi

if [ "${1}" = "migrate" ]; then
  run_migrations
  exit 0
fi

# Para o que estiver rodando antes de subir
docker compose -f "$ROOT/docker-compose.yml" down 2>/dev/null || true

# Builda e sobe tudo
echo "Buildando e subindo containers..."
docker compose -f "$ROOT/docker-compose.yml" up --build -d

run_migrations

echo ""
echo "App rodando:"
echo "  Frontend → http://localhost:5173"
echo "  Backend  → http://localhost:8000"
echo ""
echo "Logs:       docker compose logs -f"
echo "Para parar: bash dev.sh stop"
