#!/bin/bash

# Get the directory of this script and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
PID_FILE="$PROJECT_ROOT/logs/spotify_updater.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "Stopping Spotify playlist updater (PID: $PID)..."
    kill "$PID" 2>/dev/null || true
    rm "$PID_FILE"
    echo "Stopped."
else
    echo "No running updater found."
fi
