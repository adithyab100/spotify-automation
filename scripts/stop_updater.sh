#!/bin/bash

# Get the directory of this script and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
PID_FILE="$PROJECT_ROOT/logs/spotify_updater.pid"

stopped=false

# First try using the PID file
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null; then
        echo "Stopping Spotify playlist updater (PID: $PID)..."
        kill "$PID" 2>/dev/null && stopped=true
        rm "$PID_FILE"
    fi
fi

# If PID file method didn't work, try finding the process by name
if [ "$stopped" = false ]; then
    PIDS=$(pgrep -f "python.*auto_update_daemon\.py")
    if [ -n "$PIDS" ]; then
        echo "Found running updater processes with PIDs: $PIDS"
        for PID in $PIDS; do
            echo "Stopping process $PID..."
            kill "$PID" 2>/dev/null
            stopped=true
        done
    fi
fi

if [ "$stopped" = true ]; then
    echo "Successfully stopped Spotify playlist updater(s)."
else
    echo "No running updater found."
fi
