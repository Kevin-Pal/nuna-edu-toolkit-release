#!/bin/bash
set -euo pipefail

# Purpose: Attach to logs for all project containers without rebuilding images.
# Usage: ./scripts/attach.sh

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_ENV_FILE="$PROJECT_ROOT/compose/.env"
COMPOSE_FILE="$PROJECT_ROOT/compose/docker-compose.all.yml"

if [ ! -f "$COMPOSE_ENV_FILE" ]; then
	echo "Error: compose env file not found: $COMPOSE_ENV_FILE"
	exit 1
fi

cd "$PROJECT_ROOT"
docker compose --env-file "$COMPOSE_ENV_FILE" -f "$COMPOSE_FILE" up --no-build --no-recreate
