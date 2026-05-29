#!/bin/bash
set -euo pipefail

PLIST_NAME="com.llmwiki.bridge.plist"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLIST_SRC="$SCRIPT_DIR/$PLIST_NAME"
AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_DEST="$AGENTS_DIR/$PLIST_NAME"

echo "Installing LLMwiki bridge server..."

# Unload existing service if already installed
if launchctl list | grep -q "com.llmwiki.bridge" 2>/dev/null; then
    echo "  Unloading existing service..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
fi

mkdir -p "$AGENTS_DIR"
cp "$PLIST_SRC" "$PLIST_DEST"
launchctl load "$PLIST_DEST"

echo "  Plist loaded from $PLIST_DEST"

# Give the server a moment to start
sleep 2

# Verify the server is reachable
if curl -s --max-time 3 -X POST "http://localhost:7842/ingest" \
    -H "Content-Type: application/json" \
    -d '{"title":"ping","url":"ping://health","content":"health check"}' \
    -o /dev/null -w "%{http_code}" | grep -qE "^(200|409)$"; then
    echo "  Bridge server is running on localhost:7842."
else
    echo "  Warning: could not reach localhost:7842 — check ~/LLMwiki/bridge-error.log"
    exit 1
fi

echo "Done. The bridge server will start automatically at login."
