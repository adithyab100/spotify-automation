import sys
import os
import time
from datetime import datetime
import argparse
import logging
from spotify_utils import (
    create_spotify_client,
    get_top_tracks,
    get_or_create_playlist,
    update_playlist,
    validate_track_params,
    get_time_range_for_days
)

# Get the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')

# Ensure logs directory exists
os.makedirs(LOGS_DIR, exist_ok=True)

# Set up logging
log_file = os.path.join(LOGS_DIR, 'spotify_updater.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

def update_playlist_with_retry(playlist_name, num_songs, days, max_retries=3, retry_delay=60):
    """Update playlist with retry logic."""
    sp = None
    for attempt in range(max_retries):
        try:
            # Validate parameters
            num_songs, days = validate_track_params(num_songs, days)
            
            # Get Spotify client
            sp = create_spotify_client()
            
            # Get or create playlist
            playlist_id = get_or_create_playlist(sp, playlist_name, auto_update=True)
            
            # Get top tracks
            time_range = get_time_range_for_days(days)
            top_tracks = get_top_tracks(sp, limit=num_songs, time_range=time_range)
            track_uris = [track['uri'] for track in top_tracks]
            
            # Update playlist
            update_playlist(sp, playlist_id, track_uris)
            
            logging.info(f"Successfully updated playlist '{playlist_name}' with {len(track_uris)} tracks")
            logging.info("Tracks:")
            for i, track in enumerate(top_tracks, 1):
                artists = ", ".join([artist['name'] for artist in track['artists']])
                logging.info(f"{i}. {track['name']} - {artists}")
            
            return True
            
        except Exception as e:
            logging.error(f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                logging.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logging.error("Max retries reached. Update failed.")
                return False
        finally:
            # Close the Spotify client to free up the port
            if sp is not None:
                try:
                    sp._auth_manager.cache_handler.save_token_to_cache(None)
                    sp = None
                except:
                    pass

def main():
    parser = argparse.ArgumentParser(description='Auto-update Spotify playlist daemon')
    parser.add_argument('playlist_name', help='Name of the playlist to update')
    parser.add_argument('num_songs', type=int, help='Number of songs to include')
    parser.add_argument('days', type=int, help='Time range in days')
    parser.add_argument('--interval', type=int, default=3600,
                      help='Update interval in seconds (default: 3600 = 1 hour)')
    parser.add_argument('--retry-delay', type=int, default=60,
                      help='Delay between retries in seconds (default: 60)')
    parser.add_argument('--max-retries', type=int, default=3,
                      help='Maximum number of retry attempts (default: 3)')
    
    args = parser.parse_args()
    
    logging.info(f"Starting Spotify playlist updater daemon")
    logging.info(f"Playlist: {args.playlist_name}")
    logging.info(f"Number of songs: {args.num_songs}")
    logging.info(f"Time range: {args.days} days")
    logging.info(f"Update interval: {args.interval} seconds")
    
    consecutive_failures = 0
    while True:
        try:
            logging.info("\n" + "="*50)
            logging.info(f"Starting playlist update at {datetime.now()}")
            
            success = update_playlist_with_retry(
                args.playlist_name,
                args.num_songs,
                args.days,
                args.max_retries,
                args.retry_delay
            )
            
            if success:
                consecutive_failures = 0
                logging.info(f"Update completed successfully. Next update in {args.interval} seconds.")
            else:
                consecutive_failures += 1
                logging.error(f"Update failed. Consecutive failures: {consecutive_failures}")
                
                # If we've failed too many times, increase the interval temporarily
                if consecutive_failures > 3:
                    temp_interval = args.interval * 2
                    logging.warning(f"Too many consecutive failures. Increasing interval to {temp_interval} seconds.")
                    time.sleep(temp_interval)
                    continue
            
            time.sleep(args.interval)
            
        except KeyboardInterrupt:
            logging.info("\nStopping Spotify playlist updater daemon")
            sys.exit(0)
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            logging.info("Continuing in 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    main()
