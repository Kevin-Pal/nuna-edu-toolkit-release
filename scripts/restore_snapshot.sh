#!/bin/sh
set -eu

# Purpose: Restore runtime/data from a snapshot in runtime/snapshots.
# Usage: ./scripts/restore_snapshot.sh <snapshot_name>

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/compose/docker-compose.all.yml"
COMPOSE_ENV_FILE="$PROJECT_ROOT/compose/.env"
RUNTIME_DIR="$PROJECT_ROOT/runtime"
DATA_DIR="$RUNTIME_DIR/data"
SNAPSHOT_ROOT="$RUNTIME_DIR/snapshots"

usage() {
    echo "Usage: $0 <snapshot_name>"
    echo "Example: $0 before-auth-test"
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    usage
    exit 0
fi

if [ "$#" -lt 1 ]; then
    usage
    exit 1
fi

SNAPSHOT_NAME="$1"
SNAPSHOT_DIR="$SNAPSHOT_ROOT/$SNAPSHOT_NAME"
SNAPSHOT_DATA_DIR="$SNAPSHOT_DIR/data"

check_root_owned_paths_in_data_dir() {
    if [ ! -d "$DATA_DIR" ]; then
        return 0
    fi

    # When running as root, ownership will not block delete operations.
    if [ "$(id -u)" -eq 0 ]; then
        return 0
    fi

    root_owned_path=$(find "$DATA_DIR" -xdev -user root -print -quit 2>/dev/null || true)
    if [ -n "$root_owned_path" ]; then
        current_user=$(id -un 2>/dev/null || echo "current-user")
        echo "Error: found root-owned files under runtime/data."
        echo "Restore would fail with 'Permission denied' during rm -rf."
        echo "Example path: $root_owned_path"
        echo "Please fix ownership first:"
        echo "  sudo chown -R $current_user:$current_user runtime/data"
        echo "Then rerun:"
        echo "  ./scripts/restore_snapshot.sh $SNAPSHOT_NAME"
        exit 1
    fi
}

if ! command -v docker >/dev/null 2>&1; then
    echo "Error: docker command not found"
    exit 1
fi

if [ ! -f "$COMPOSE_ENV_FILE" ]; then
    echo "Error: compose env file not found: $COMPOSE_ENV_FILE"
    exit 1
fi

running_services=$(docker compose --env-file "$COMPOSE_ENV_FILE" -f "$COMPOSE_FILE" ps --status running --services 2>/dev/null | grep -E '^(app|receiver|prelabel-service)$' || true)
if [ -n "$running_services" ]; then
    echo "Error: app/receiver/prelabel-service are running. Restore is blocked."
    echo "Please stop services first:"
    echo "  docker compose --env-file compose/.env -f compose/docker-compose.all.yml stop app receiver prelabel-service"
    exit 1
fi

if [ ! -d "$SNAPSHOT_DATA_DIR" ]; then
    echo "Error: snapshot not found: $SNAPSHOT_DATA_DIR"
    echo "Available snapshots:"
    ls -1 "$SNAPSHOT_ROOT" 2>/dev/null || true
    exit 1
fi

check_root_owned_paths_in_data_dir

echo "Restoring snapshot: $SNAPSHOT_NAME"
rm -rf "$DATA_DIR"
cp -a "$SNAPSHOT_DATA_DIR" "$DATA_DIR"
chmod -R 777 "$DATA_DIR"

echo "Restore complete: runtime/data <= runtime/snapshots/$SNAPSHOT_NAME/data"
