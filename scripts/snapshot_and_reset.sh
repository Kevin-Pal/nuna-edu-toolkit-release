#!/bin/sh
set -eu

# Purpose: Create a snapshot of runtime/data and optionally reset runtime/data.
# Usage: ./scripts/snapshot_and_reset.sh [snapshot_name] [--reset|reset|--no-reset]
# default: snapshot_name = timestamp-based, reset = false (keep data after snapshot)

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/compose/docker-compose.all.yml"
COMPOSE_ENV_FILE="$PROJECT_ROOT/compose/.env"
RUNTIME_DIR="$PROJECT_ROOT/runtime"
DATA_DIR="$RUNTIME_DIR/data"
SNAPSHOT_ROOT="$RUNTIME_DIR/snapshots"
DO_RESET=0
SNAPSHOT_NAME=""

check_root_owned_paths_before_reset() {
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
        echo "Reset would fail with 'Permission denied' during rm -rf."
        echo "Example path: $root_owned_path"
        echo "Please fix ownership first:"
        echo "  sudo chown -R $current_user:$current_user runtime/data"
        echo "Then rerun:"
        echo "  ./scripts/snapshot_and_reset.sh $SNAPSHOT_NAME --reset"
        exit 1
    fi
}

usage() {
    echo "Usage: $0 [snapshot_name] [--reset|reset|--no-reset]"
    echo "Examples:"
    echo "  $0"
    echo "  $0 before-auth-test"
    echo "  $0 before-auth-test --reset"
}

for arg in "$@"; do
    case "$arg" in
        -h|--help)
            usage
            exit 0
            ;;
        --reset|reset)
            DO_RESET=1
            ;;
        --no-reset)
            DO_RESET=0
            ;;
        *)
            if [ -z "$SNAPSHOT_NAME" ]; then
                SNAPSHOT_NAME="$arg"
            else
                echo "Error: unknown argument: $arg"
                usage
                exit 1
            fi
            ;;
    esac
done

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
    echo "Error: app/receiver/prelabel-service are running. Snapshot is blocked."
    echo "Please stop services first:"
    echo "  docker compose --env-file compose/.env -f compose/docker-compose.all.yml stop app receiver prelabel-service"
    exit 1
fi

if [ -z "$SNAPSHOT_NAME" ]; then
    SNAPSHOT_NAME="snapshot_$(date +%Y%m%d_%H%M%S)"
fi
SNAPSHOT_DIR="$SNAPSHOT_ROOT/$SNAPSHOT_NAME"

if [ -e "$SNAPSHOT_DIR" ]; then
    echo "Error: snapshot already exists: $SNAPSHOT_DIR"
    exit 1
fi

mkdir -p "$SNAPSHOT_ROOT"
mkdir -p "$DATA_DIR"

echo "Creating snapshot: $SNAPSHOT_DIR"
mkdir -p "$SNAPSHOT_DIR"
cp -a "$DATA_DIR" "$SNAPSHOT_DIR/data"

echo "Snapshot created: runtime/snapshots/$SNAPSHOT_NAME"

if [ "$DO_RESET" -eq 1 ]; then
    check_root_owned_paths_before_reset
    echo "Resetting runtime/data ..."
    rm -rf "$DATA_DIR"
    mkdir -p "$DATA_DIR/db" "$DATA_DIR/audio"
    touch "$DATA_DIR/db/.gitkeep" "$DATA_DIR/audio/.gitkeep"
    chmod -R 777 "$DATA_DIR"
    echo "Data reset complete: runtime/data"
else
    echo "Skipping reset. Use --reset (or reset) to clear runtime/data after snapshot."
fi

echo "To restore: ./scripts/restore_snapshot.sh $SNAPSHOT_NAME"
