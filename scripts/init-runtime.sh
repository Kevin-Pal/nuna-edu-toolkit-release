#!/bin/bash
set -euo pipefail

# Purpose: Initialize runtime directories and default env files after a fresh clone.
# Usage: ./scripts/init-runtime.sh [--skip-chmod]

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_ROOT="$PROJECT_ROOT/runtime"
SKIP_CHMOD=0

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    echo "Usage: $0 [--skip-chmod]"
    echo "Create runtime paths and default env files if missing."
    exit 0
fi

if [ "${1:-}" = "--skip-chmod" ]; then
    SKIP_CHMOD=1
elif [ "${1:-}" != "" ]; then
    echo "Error: unknown argument: ${1}"
    echo "Usage: $0 [--skip-chmod]"
    exit 1
fi

echo "Initializing runtime directory at $RUNTIME_ROOT..."

# Create runtime directories required by app, snapshot, and logs.
mkdir -p "$RUNTIME_ROOT/env"
mkdir -p "$RUNTIME_ROOT/data/db"
mkdir -p "$RUNTIME_ROOT/data/audio"
mkdir -p "$RUNTIME_ROOT/logs"
mkdir -p "$RUNTIME_ROOT/snapshots"

if [ ! -f "$RUNTIME_ROOT/env/app.env" ]; then
    echo "Creating runtime/env/app.env..."
    cat > "$RUNTIME_ROOT/env/app.env" <<EOL
APP_ENV=dev
DB_URL=sqlite:////runtime/data/db/app.sqlite
RUNTIME_AUDIO_DIR=/runtime/data/audio
SESSION_SECRET=dev_secret_please_change
ASR_PROVIDER=none
PRELABEL_SERVICE_URL=http://prelabel-service:8100
PRELABEL_PIPELINE_VERSION=mvp-mock-v1
EOL
fi

if [ ! -f "$RUNTIME_ROOT/env/prelabel.env" ]; then
    echo "Creating runtime/env/prelabel.env..."
    cat > "$RUNTIME_ROOT/env/prelabel.env" <<EOL
PRELABEL_PIPELINE_VERSION=mvp-mock-v1
EOL
fi

if [ ! -f "$RUNTIME_ROOT/env/stack.env" ]; then
    echo "Creating runtime/env/stack.env..."
    cat > "$RUNTIME_ROOT/env/stack.env" <<EOL
APP_PORT=8000
DATA_PORT=9000
PRELABEL_PORT=8100
EOL
fi

if [ ! -f "$PROJECT_ROOT/compose/.env" ]; then
    echo "Creating compose/.env..."
    cat > "$PROJECT_ROOT/compose/.env" <<EOL
APP_PORT=80
DATA_PORT=9000
PRELABEL_PORT=8100
EOL
fi

# Some host-mounted files may not support chmod; allow non-fatal fallback.
if [ "$SKIP_CHMOD" = "1" ]; then
    echo "Skipping runtime chmod (--skip-chmod)."
else
    chmod -R 777 "$RUNTIME_ROOT" || \
        echo "Warning: chmod -R on runtime had permission errors; continuing."
fi

echo "Runtime initialization complete."
