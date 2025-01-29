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
    print_track_list,
    get_available_genres
)

def main():
    parser = argparse.ArgumentParser(description='Create a Spotify playlist with your top tracks')
    parser.add_argument('num_songs', type=int, help='Number of songs to include (max 50)')
    parser.add_argument('days', type=int, help='Time range in days')
    parser.add_argument('-n', '--name', type=str, default=None,
                      help='Name of the playlist (default: "Top Songs [timeframe] - [date]")')
    parser.add_argument('-g', '--genre', type=str, default=None,
                      help='Filter songs by genre (e.g., "rock", "pop", "hip hop")')
    parser.add_argument('-l', '--list-genres', action='store_true',
                      help='List all available genres in your top tracks')
    
    args = parser.parse_args()
    
    try:
        # Validate parameters
        num_songs, days = validate_track_params(args.num_songs, args.days)
        
        # Get Spotify client
        sp = create_spotify_client()
        
        # Get time range
        time_range = get_time_range_for_days(days)
        
        # If --list-genres is specified, show available genres and exit
        if args.list_genres:
            print("\nFetching your top tracks to analyze available genres...")
            top_tracks = get_top_tracks(sp, limit=50, time_range=time_range)
            genres = get_available_genres(sp, top_tracks)
            print("\nAvailable genres in your top tracks:")
            for genre in genres:
                print(f"- {genre}")
            sys.exit(0)
        
        # Get top tracks with genre filter to validate genre before creating playlist
        if args.genre:
            print(f"\nValidating genre '{args.genre}'...")
            test_tracks = get_top_tracks(sp, limit=num_songs, time_range=time_range, genre=args.genre)
            if not test_tracks:
                print(f"\nNo tracks found matching the genre '{args.genre}'.")
                print("Try using --list-genres to see available genres.")
                sys.exit(1)
        
        # Generate default playlist name if not provided
        if args.name is None:
            timeframe = "4 weeks" if days <= 28 else "6 months" if days <= 180 else "all time"
            genre_text = f" ({args.genre})" if args.genre else ""
            current_date = datetime.now().strftime("%Y-%m-%d")
            playlist_name = f"Top Songs{genre_text} ({timeframe}) - {current_date}"
        else:
            playlist_name = args.name
        
        # Get or create playlist
        playlist_id = get_or_create_playlist(sp, playlist_name)
        
        # Get top tracks (we already have them if genre was specified)
        if not args.genre:
            print("\nFetching your top tracks...")
            top_tracks = get_top_tracks(sp, limit=num_songs, time_range=time_range)
        else:
            top_tracks = test_tracks
        
        if args.genre and len(top_tracks) < num_songs:
            print(f"\nNote: Only found {len(top_tracks)} tracks matching the genre '{args.genre}'")
        
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
