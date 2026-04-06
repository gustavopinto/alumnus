#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
COMPOSE="docker compose -f $ROOT/docker-compose.yml"

stop() {
  echo "Parando containers..."
  $COMPOSE down
}

wait_for_db() {
  echo "Aguardando PostgreSQL..."
  until $COMPOSE exec -T db pg_isready -U alumnus -q 2>/dev/null; do
    sleep 1
  done
}

run_migrations() {
  echo "Verificando migrations pendentes..."
  $COMPOSE run --rm backend python migrate.py
}

if [ "${1}" = "stop" ]; then
  stop
  echo "App parada."
  exit 0
fi

if [ "${1}" = "migrate" ]; then
  wait_for_db
  run_migrations
  exit 0
fi

# Para o que estiver rodando antes de subir
$COMPOSE down 2>/dev/null || true

# Build das imagens
echo "Buildando imagens..."
$COMPOSE build

# Sobe só o banco primeiro
echo "Subindo banco de dados..."
$COMPOSE up -d db
wait_for_db

# Aplica migrations antes de subir o backend
run_migrations

# Sobe o resto
echo "Subindo backend e frontend..."
$COMPOSE up -d backend frontend

echo ""
echo "App rodando:"
echo "  Frontend → http://localhost:5173"
echo "  Backend  → http://localhost:8000"
echo ""
echo "Logs:       docker compose logs -f"
echo "Para parar: bash dev.sh stop"
