import sys
from spotify_utils import (
    create_spotify_client,
    get_top_tracks,
    get_or_create_playlist,
    validate_track_params,
    get_time_range_for_days,
    print_track_list
)

def main():
    if len(sys.argv) != 3:
        print("Usage: python spotify_playlist_creator.py <number_of_songs> <days>")
        print("Example: python spotify_playlist_creator.py 20 30")
        sys.exit(1)
    
    try:
        num_songs = int(sys.argv[1])
        days = int(sys.argv[2])
    except ValueError:
        print("Error: Both arguments must be numbers")
        sys.exit(1)
    
    try:
        # Validate parameters
        num_songs, days = validate_track_params(num_songs, days)
        
        # Get Spotify client
        sp = create_spotify_client()
        
        # Get top tracks
        time_range = get_time_range_for_days(days)
        top_tracks = get_top_tracks(sp, limit=num_songs, time_range=time_range)
        track_uris = [track['uri'] for track in top_tracks]
        
        # Create playlist name based on parameters
        playlist_name = f"Top {num_songs} Songs - Past {days} Days"
        
        # Create playlist and add tracks
        playlist_id = get_or_create_playlist(sp, playlist_name)
        sp.playlist_add_items(playlist_id, track_uris)
        
        # Get playlist URL
        playlist = sp.playlist(playlist_id)
        playlist_url = playlist['external_urls']['spotify']
        
        print(f"\nSuccess! Your playlist has been created!")
        print(f"Playlist URL: {playlist_url}")
        
        # Print track list
        print_track_list(top_tracks, "Tracks added:")
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
