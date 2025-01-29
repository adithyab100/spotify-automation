#!/usr/bin/env python3
import sys
import argparse
from datetime import datetime
from spotify_utils import (
    create_spotify_client,
    get_top_tracks,
    get_or_create_playlist,
    update_playlist,
    validate_track_params,
    get_time_range_for_days,
    print_track_list
)

def main():
    parser = argparse.ArgumentParser(description='Create a Spotify playlist with your top tracks')
    parser.add_argument('num_songs', type=int, help='Number of songs to include (max 50)')
    parser.add_argument('days', type=int, help='Time range in days')
    parser.add_argument('-n', '--name', type=str, default=None,
                      help='Name of the playlist (default: "Top Songs [timeframe] - [date]")')
    
    args = parser.parse_args()
    
    try:
        # Validate parameters
        num_songs, days = validate_track_params(args.num_songs, args.days)
        
        # Get Spotify client
        sp = create_spotify_client()
        
        # Generate default playlist name if not provided
        if args.name is None:
            timeframe = "4 weeks" if days <= 28 else "6 months" if days <= 180 else "all time"
            current_date = datetime.now().strftime("%Y-%m-%d")
            playlist_name = f"Top Songs ({timeframe}) - {current_date}"
        else:
            playlist_name = args.name
        
        # Get or create playlist
        playlist_id = get_or_create_playlist(sp, playlist_name)
        
        # Get top tracks
        time_range = get_time_range_for_days(days)
        top_tracks = get_top_tracks(sp, limit=num_songs, time_range=time_range)
        track_uris = [track['uri'] for track in top_tracks]
        
        # Update playlist
        update_playlist(sp, playlist_id, track_uris)
        
        print(f"\nCreated playlist: {playlist_name}")
        print(f"URL: https://open.spotify.com/playlist/{playlist_id}")
        
        print_track_list(top_tracks)
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
