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

def get_top_tracks(sp, limit=50, time_range='short_term', genre=None):
    """Get user's top tracks, optionally filtered by genre.
    time_range options: short_term (4 weeks), medium_term (6 months), long_term (all time)
    """
    all_tracks = []
    offset = 0
    max_tracks = 50  # Spotify API limit is 50 tracks per request
    max_attempts = 10  # Maximum number of attempts to find enough tracks
    
    # If genre filter is specified, get more tracks initially
    target_tracks = limit * 3 if genre else limit
    
    while len(all_tracks) < target_tracks:
        try:
            results = sp.current_user_top_tracks(
                limit=max_tracks,
                offset=offset,
                time_range=time_range
            )
            
            if not results['items']:
                break
                
            all_tracks.extend(results['items'])
            offset += max_tracks
            
            # Stop if we've made too many attempts
            if offset >= max_tracks * max_attempts:
                break
                
        except Exception as e:
            print(f"Warning: Error fetching tracks at offset {offset}: {str(e)}")
            break
    
    # Apply genre filter if specified
    if genre:
        filtered_tracks = filter_tracks_by_genre(sp, all_tracks, genre)
        
        # If we don't have enough tracks and there might be more available,
        # keep fetching until we do or run out of tracks
        while (len(filtered_tracks) < limit and 
               offset < max_tracks * max_attempts):
            try:
                results = sp.current_user_top_tracks(
                    limit=max_tracks,
                    offset=offset,
                    time_range=time_range
                )
                
                if not results['items']:
                    break
                    
                new_tracks = filter_tracks_by_genre(sp, results['items'], genre)
                filtered_tracks.extend(new_tracks)
                offset += max_tracks
                
            except Exception as e:
                print(f"Warning: Error fetching tracks at offset {offset}: {str(e)}")
                break
        
        tracks = filtered_tracks[:limit]  # Trim to requested limit
    else:
        tracks = all_tracks[:limit]
    
    return tracks

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

def get_artist_genres(sp, artist_id):
    """Get genres for a specific artist."""
    try:
        artist = sp.artist(artist_id)
        return set(artist['genres'])
    except:
        return set()

def get_track_genres(sp, track):
    """Get all genres associated with a track's artists."""
    genres = set()
    for artist in track['artists']:
        artist_genres = get_artist_genres(sp, artist['id'])
        genres.update(artist_genres)
    return genres

def filter_tracks_by_genre(sp, tracks, genre=None):
    """Filter tracks by genre. If genre is None, return all tracks."""
    if not genre:
        return tracks
    
    filtered_tracks = []
    genre = genre.lower()
    
    # Define genre variations and related genres
    genre_variations = {
        'pop': {'pop', 'dance pop', 'pop dance', 'electropop'},  # but not k-pop
        'rock': {'rock', 'modern rock', 'alternative rock', 'indie rock'},
        'rap': {'rap', 'melodic rap', 'hip hop', 'trap', 'drill', 'brooklyn drill', 'new york drill'},
        'hip hop': {'hip hop', 'rap', 'melodic rap', 'trap'},
        'electronic': {'electronic', 'edm', 'electro', 'dance'},
    }
    
    print(f"\nDebug: Looking for genre '{genre}'")
    for track in tracks:
        track_genres = get_track_genres(sp, track)
        artists = ", ".join(artist['name'] for artist in track['artists'])
        print(f"\nTrack: {track['name']} - {artists}")
        print(f"Genres: {sorted(track_genres)}")
        
        # Check if any of the track's genres match our criteria
        matched = False
        for g in track_genres:
            g_lower = g.lower()
            
            # Exact match
            if g_lower == genre:
                matched = True
                break
                
            # Check variations for single-word genres
            if genre in genre_variations and g_lower in genre_variations[genre]:
                matched = True
                break
                
            # For compound genres (e.g., "pop rock"), allow partial matches
            # but ensure it's not matching substrings of other genres (e.g., "pop" shouldn't match "k-pop")
            if (genre.count(' ') > 0 and 
                genre in g_lower and 
                not any(x in g_lower for x in ['k-pop', 'j-pop'])):  # exclude specific genres
                matched = True
                break
        
        if matched:
            filtered_tracks.append(track)
            print("✓ Match found!")
    
    return filtered_tracks

def get_available_genres(sp, tracks):
    """Get a list of all available genres from the tracks."""
    all_genres = set()
    for track in tracks:
        track_genres = get_track_genres(sp, track)
        all_genres.update(track_genres)
    return sorted(all_genres)

# Create necessary directories
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)
