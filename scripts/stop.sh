#!/usr/bin/env bash
# Stop the Kanban Studio application
# Usage: ./scripts/stop.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "Stopping Kanban Studio..."

docker compose down

echo "Kanban Studio has been stopped."