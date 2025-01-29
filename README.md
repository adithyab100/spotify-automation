# Spotify Playlist Automation

This project helps you create and automatically update Spotify playlists with your top tracks.

## Project Structure

```
spotify-automation/
├── src/                    # Source code
│   ├── spotify_utils.py    # Core Spotify functionality
│   ├── auto_update_daemon.py    # Auto-update daemon
│   └── spotify_playlist_creator.py    # One-time playlist creator
├── scripts/                # Shell scripts
│   ├── start_updater.sh    # Start the auto-updater
│   └── stop_updater.sh     # Stop the auto-updater
├── logs/                   # Log files
│   ├── spotify_updater.log # Main log file
│   └── spotify_updater.out # Output log
├── config/                 # Configuration files
│   ├── .env               # Environment variables
│   └── requirements.txt    # Python dependencies
└── cache/                  # Cache files
    ├── .spotify_cache     # Spotify authentication cache
    └── playlist_cache.json # Playlist ID cache
```

## Setup

1. Install dependencies:
```bash
pip install -r config/requirements.txt
```

2. Create a Spotify Developer account and create a new application:
   - Go to https://developer.spotify.com/dashboard
   - Create a new application
   - Get your Client ID and Client Secret
   - Add `http://localhost:8888/callback` to your application's Redirect URIs in the settings

3. Create `config/.env` file with your Spotify API credentials:
```
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8888/callback
```

## Usage

### 1. Create a One-Time Playlist

Use `spotify_playlist_creator.py` to create a new playlist with your top tracks:

```bash
python src/spotify_playlist_creator.py <number_of_songs> <days>
```

Example:
```bash
python src/spotify_playlist_creator.py 20 30  # Creates a playlist with your top 20 songs from the last 30 days
```

### 2. Auto-Updating Playlist

Use the auto-updater to keep a playlist continuously updated with your latest top tracks:

1. Start the updater with default settings (updates every hour):
```bash
./scripts/start_updater.sh
```

2. Or customize the update settings:
```bash
./scripts/start_updater.sh --playlist "My Playlist" --num-songs 30 --days 60 --interval 7200
```

Available options:
- `-p, --playlist`: Playlist name (default: "My Auto-Updated Top Songs")
- `-n, --num-songs`: Number of songs (default: 20)
- `-d, --days`: Time range in days (default: 30)
- `-i, --interval`: Update interval in seconds (default: 3600 = 1 hour)

3. Stop the updater:
```bash
./scripts/stop_updater.sh
```

The auto-updater will:
- Create a playlist if it doesn't exist
- Update it at regular intervals
- Retry on failure
- Log all actions to `logs/spotify_updater.log`

## Time Ranges

The number of days you specify determines which Spotify time range is used:
- 1-28 days: short_term (approximately last 4 weeks)
- 29-180 days: medium_term (approximately last 6 months)
- 180+ days: long_term (calculated from several years of data)

## Logs

- `logs/spotify_updater.log`: Main log file with detailed information about updates
- `logs/spotify_updater.out`: Output log for the daemon process

## Cache

The application maintains two cache files:
- `cache/.spotify_cache`: Stores Spotify authentication tokens
- `cache/playlist_cache.json`: Stores playlist IDs for faster access

## Troubleshooting

If you encounter any issues:
1. Check the log files in the `logs` directory
2. Make sure your Spotify credentials are correct in `config/.env`
3. Verify that `http://localhost:8888/callback` is added to your Spotify app's Redirect URIs
4. Try stopping and restarting the updater
