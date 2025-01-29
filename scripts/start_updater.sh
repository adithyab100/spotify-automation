#!/bin/bash

# Get the directory of this script and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Create necessary directories
mkdir -p "$PROJECT_ROOT/logs"

# Default values
PLAYLIST_NAME="My Auto-Updated Top Songs"
NUM_SONGS=20
DAYS=30
UPDATE_INTERVAL=3600  # 1 hour in seconds

# Help message
show_help() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -p, --playlist NAME    Playlist name (default: '$PLAYLIST_NAME')"
    echo "  -n, --num-songs NUM    Number of songs (default: $NUM_SONGS)"
    echo "  -d, --days NUM         Time range in days (default: $DAYS)"
    echo "  -i, --interval SEC     Update interval in seconds (default: $UPDATE_INTERVAL)"
    echo "  -h, --help            Show this help message"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--playlist)
            PLAYLIST_NAME="$2"
            shift 2
            ;;
        -n|--num-songs)
            NUM_SONGS="$2"
            shift 2
            ;;
        -d|--days)
            DAYS="$2"
            shift 2
            ;;
        -i|--interval)
            UPDATE_INTERVAL="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Change to the project root directory
cd "$PROJECT_ROOT"

# Start the updater in the background
nohup python3 src/auto_update_daemon.py "$PLAYLIST_NAME" "$NUM_SONGS" "$DAYS" --interval "$UPDATE_INTERVAL" > logs/spotify_updater.out 2>&1 &

# Save the process ID
echo $! > logs/spotify_updater.pid

echo "Spotify playlist updater started with PID $(cat logs/spotify_updater.pid)"
echo "Playlist: $PLAYLIST_NAME"
echo "Number of songs: $NUM_SONGS"
echo "Time range: $DAYS days"
echo "Update interval: $UPDATE_INTERVAL seconds"
echo
echo "Log files:"
echo "- Main log: logs/spotify_updater.log"
echo "- Output log: logs/spotify_updater.out"
echo "To stop the updater, run: scripts/stop_updater.sh"
