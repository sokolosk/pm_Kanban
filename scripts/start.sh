#!/usr/bin/env bash
# Start the Kanban Studio application
# Usage: ./scripts/start.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "Starting Kanban Studio..."
echo "Building and starting Docker container..."

docker compose up --build -d

echo ""
echo "Kanban Studio is running at http://localhost:8000"
echo ""
echo "To stop the application, run: ./scripts/stop.sh"