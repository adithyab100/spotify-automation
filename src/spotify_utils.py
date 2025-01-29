import os
import json
from datetime import datetime
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from time import sleep

# Get the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Define paths
CONFIG_DIR = os.path.join(PROJECT_ROOT, 'config')
CACHE_DIR = os.path.join(PROJECT_ROOT, 'cache')
PLAYLIST_CACHE_FILE = os.path.join(CACHE_DIR, 'playlist_cache.json')
SPOTIFY_CACHE_FILE = os.path.join(CACHE_DIR, 'spotify_cache')
ENV_FILE = os.path.join(CONFIG_DIR, '.env')

def create_spotify_client():
    """Create and return an authenticated Spotify client."""
    load_dotenv(ENV_FILE)
    
    scope = "user-top-read playlist-modify-public playlist-modify-private"
    auth_manager = SpotifyOAuth(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
        scope=scope,
        open_browser=True,
        cache_path=SPOTIFY_CACHE_FILE,
        requests_timeout=10,
        requests_session=True  # Use a session to properly close connections
    )
    return spotipy.Spotify(auth_manager=auth_manager)

def get_top_tracks(sp, limit=50, time_range='short_term'):
    """Get user's top tracks.
    time_range options: short_term (4 weeks), medium_term (6 months), long_term (all time)
    """
    results = sp.current_user_top_tracks(limit=limit, offset=0, time_range=time_range)
    return results['items']

def get_time_range_for_days(days):
    """Convert number of days to Spotify time range."""
    time_range = 'short_term'  # 4 weeks
    if days > 180:
        time_range = 'long_term'  # all time
    elif days > 28:
        time_range = 'medium_term'  # 6 months
    return time_range

def validate_track_params(num_songs, days):
    """Validate and adjust track parameters."""
    if num_songs <= 0 or days <= 0:
        raise ValueError("Both number of songs and days must be positive numbers")
    
    if num_songs > 50:
        print("Warning: Maximum number of songs is 50. Setting to 50.")
        num_songs = 50
    
    return num_songs, days

def load_playlist_cache():
    """Load cached playlist ID from file."""
    if os.path.exists(PLAYLIST_CACHE_FILE):
        with open(PLAYLIST_CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_playlist_cache(cache):
    """Save playlist ID to cache file."""
    # Ensure cache directory exists
    os.makedirs(os.path.dirname(PLAYLIST_CACHE_FILE), exist_ok=True)
    with open(PLAYLIST_CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def get_or_create_playlist(sp, playlist_name, auto_update=False):
    """Get existing playlist or create a new one."""
    user_id = sp.current_user()['id']
    
    # Check cache first
    cache = load_playlist_cache()
    if playlist_name in cache:
        playlist_id = cache[playlist_name]
        try:
            # Verify the playlist still exists and we can modify it
            playlist = sp.playlist(playlist_id)
            if playlist['name'].lower() == playlist_name.lower():
                print(f"\nFound existing playlist: {playlist_name}")
                desc = "Auto-updated playlist of top songs" if auto_update else "Your top songs playlist"
                sp.playlist_change_details(playlist_id, 
                    description=f"{desc}. Last updated: {datetime.now().strftime('%Y-%m-%d')}")
                return playlist_id
        except:
            # If there's any error, remove from cache and continue
            del cache[playlist_name]
            save_playlist_cache(cache)
    
    # Search through user's playlists
    offset = 0
    limit = 50
    
    while True:
        results = sp.current_user_playlists(limit=limit, offset=offset)
        if not results['items']:
            break
            
        print(f"\nChecking playlists {offset+1} to {offset+len(results['items'])}")
        for playlist in results['items']:
            print(f"- {playlist['name']} (ID: {playlist['id']})")
            if playlist['name'].lower() == playlist_name.lower():
                print(f"\nFound existing playlist: {playlist_name}")
                try:
                    desc = "Auto-updated playlist of top songs" if auto_update else "Your top songs playlist"
                    sp.playlist_change_details(playlist['id'], 
                        description=f"{desc}. Last updated: {datetime.now().strftime('%Y-%m-%d')}")
                    # Save to cache
                    cache[playlist_name] = playlist['id']
                    save_playlist_cache(cache)
                    return playlist['id']
                except Exception as e:
                    print(f"Cannot modify playlist: {str(e)}")
                    continue
        
        if len(results['items']) < limit:
            break
        offset += limit
    
    # Create new playlist if not found or no writable playlist found
    print(f"\nCreating new playlist: {playlist_name}")
    desc = "Auto-updated playlist of top songs" if auto_update else "Your top songs playlist"
    playlist = sp.user_playlist_create(
        user_id,
        playlist_name,
        public=False,
        description=f"{desc}. Last updated: {datetime.now().strftime('%Y-%m-%d')}"
    )
    
    # Save to cache
    cache[playlist_name] = playlist['id']
    save_playlist_cache(cache)
    
    # Wait a moment for the playlist to be available
    sleep(2)
    
    return playlist['id']

def update_playlist(sp, playlist_id, track_uris):
    """Replace all tracks in the playlist with new ones."""
    sp.playlist_replace_items(playlist_id, track_uris)

def print_track_list(tracks, header="Tracks:"):
    """Print a formatted list of tracks."""
    print(f"\n{header}")
    for i, track in enumerate(tracks, 1):
        artists = ", ".join([artist['name'] for artist in track['artists']])
        print(f"{i}. {track['name']} - {artists}")

# Create necessary directories
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
