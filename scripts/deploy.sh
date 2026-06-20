#!/bin/bash
set -euo pipefail

# Purpose: Build and start all project containers with one command.
# Usage: ./scripts/deploy.sh [--detach|-d]

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_ENV_FILE="$PROJECT_ROOT/compose/.env"
COMPOSE_FILE="$PROJECT_ROOT/compose/docker-compose.all.yml"
DETACH=0

usage() {
    echo "Usage: $0 [--detach|-d]"
    echo "Build and start all services defined in compose/docker-compose.all.yml."
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    usage
    exit 0
fi

if [ "${1:-}" = "-d" ] || [ "${1:-}" = "--detach" ]; then
    DETACH=1
elif [ "${1:-}" != "" ]; then
    echo "Error: unknown argument: ${1}"
    usage
    exit 1
fi

if ! command -v docker >/dev/null 2>&1; then
    echo "Error: docker command not found"
    exit 1
fi

if [ ! -f "$PROJECT_ROOT/scripts/init-runtime.sh" ]; then
    echo "Error: scripts/init-runtime.sh not found"
    exit 1
fi

# Deploy path skips recursive chmod to avoid permission errors on host-mounted files.
bash "$PROJECT_ROOT/scripts/init-runtime.sh" --skip-chmod

if [ ! -f "$COMPOSE_ENV_FILE" ]; then
    echo "Error: compose env file not found: $COMPOSE_ENV_FILE"
    exit 1
fi

echo "Building and starting services..."
COMPOSE_CMD=(docker compose --env-file "$COMPOSE_ENV_FILE" -f "$COMPOSE_FILE" up --build --remove-orphans)
if [ "$DETACH" -eq 1 ]; then
    COMPOSE_CMD+=( -d )
fi
"${COMPOSE_CMD[@]}"

echo "Deployment successful."
echo "Port mappings loaded from compose/.env (APP_PORT/DATA_PORT/PRELABEL_PORT)."
if [ "$DETACH" -eq 1 ]; then
    echo "Tip: docker compose --env-file \"$COMPOSE_ENV_FILE\" -f \"$COMPOSE_FILE\" logs -f"
fi
