# script.py
from spotify import SpotifyAPI
from youtube import YouTubeAPI
from urllib.parse import urlencode
from dotenv import load_dotenv
import os

def main():
    # Load environment variables from .env file
    load_dotenv()

    # Access Spotify credentials
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    refresh_token = os.getenv('REFRESH_TOKEN')
    redirect_uri = os.getenv('REDIRECT_URI')
    user_name = os.getenv('USER_NAME')
    top_100_spotify_playlist_id = os.getenv('TOP_100_SPOTIFY_PLAYLIST_ID')
    eighties_pop_rock_spotify_playlist_id = os.getenv('EIGHTIES_POP_ROCK_HITS_SPOTIFY_PLAYLIST_ID')
    eighties_pop_rock_youtube_playlist_id = os.getenv('EIGHTIES_POP_ROCK_HITS_YOUTUBE_PLAYLIST_ID')
    eighties_pop_rock_youtube_playlist_id_1 = os.getenv('EIGHTIES_POP_ROCK_HITS_YOUTUBE_PLAYLIST_ID_1')
    zim_old_school_spotify_playlist = os.getenv('ZIM_OLD_SCHOOL_SPOTIFY_PLAYLIST')
    zim_old_school_youtube_playlist = os.getenv('ZIM_OLD_SCHOOL_YOUTUBE_PLAYLIST')
    scopes = os.getenv('SCOPES')

    # Access YouTube credentials
    api_key = os.getenv('API_KEY')
    top_100_youtube_playlist_id = os.getenv('TOP_100_YOUTUBE_PLAYLIST_ID')

    # Initialize APIs
    spotify_api = spotify_api = SpotifyAPI(client_id, client_secret, refresh_token)
    youtube_api = YouTubeAPI(api_key)

    # get all playlist names and ids
    my_playlists = spotify_api.get_playlist_names_and_ids(user_name)

    update_playlist_from_youtube(zim_old_school_spotify_playlist, 
                                 zim_old_school_youtube_playlist, 
                                 spotify_api, youtube_api,
                                 remove=False, strict_search=False)
    return

    #Re-Order all playlists by popularity except for current Top 100
    re_order_playlists(my_playlists, spotify_api)
  
    # Update Playlist Descriptions based on Top Artists and Genre for SEO 
    update_playlists_descriptions(my_playlists, spotify_api)
    
    # Update Top 100 Songs In Zimbabwe from youtube
    update_playlist_from_youtube(top_100_spotify_playlist_id, 
                                 top_100_youtube_playlist_id, 
                                 spotify_api, youtube_api,
                                 remove=True, strict_search=False)

def re_order_playlists(my_playlists, spotify_api):
    #Re-Order all playlists by popularity except for current Top 100
    for playlist in my_playlists:
        if "Top 100 Songs In Zimbabwe" not in playlist['name']:
            print("----------------------------------------------------------------------------")
            print(f"Playlist: {playlist['name']}  ID: {playlist['id']}")
            spotify_api.reorder_playlist_by_track_popularity(playlist['id'])

def update_playlists_descriptions(my_playlists, spotify_api):
    # Update Playlist Descriptions based on Top Artists and Genre for SEO          
    for playlist in my_playlists:
        playlist_name = playlist['name']

        if "Top 100 Songs In Zimbabwe" not in playlist_name and "Zimbabwe Trending Hits" not in playlist_name:
            spotify_api.update_playlist_description(playlist['id'], 
                                                    playlist_name, 
                                                    playlist_name + " {artists}. {genres}")

        elif "Top 100 Songs In Zimbabwe" in playlist_name:
            print(f"Updating Description for {playlist_name}")
            base_description = "🔥 Zimbabwe Top 100 Music Hits 2025!  {artists}. {genres}. New, YouTube Trends, Playlists. #Hot100"
            spotify_api.update_playlist_description(playlist['id'], "", base_description)

        elif "Zimbabwe Trending Hits" in playlist_name:
            print(f"Updating Description for {playlist_name}")
            base_description = "Top Fresh Music in Zimbabwe 2025. {artists}. {genres}"
            spotify_api.update_playlist_description(playlist['id'], "", base_description)

def update_playlist_from_youtube(playlist_id, youtube_playlist_id, spotify_api,
                                 youtube_api, remove=False, strict_search=False):
    # Fetch YouTube videos and search on spotify
    print("\nYouTube Playlist Tracks:")
    youtube_videos = youtube_api.get_playlist_items(youtube_playlist_id)

    # Search for Spotify tracks
    found_tracks = []
    not_found_count = 0
    
    count = 1
    for title, url in youtube_videos:
        # Step 1: Extract song and artist from the original title
        (song_first, artist_first), (song_second, artist_second) = youtube_api.extract_song_and_artist(title)

        # Step 2: Clean the extracted song and artist names
        cleaned_song_first = youtube_api.clean_title(song_first)
        cleaned_artist_first = youtube_api.clean_title(artist_first)
        cleaned_song_second = youtube_api.clean_title(song_second)
        cleaned_artist_second = youtube_api.clean_title(artist_second)

        # Step 3: Try both formats
        query1 = f"{cleaned_song_first} {cleaned_artist_first}" if cleaned_artist_first else cleaned_song_first
        query2 = f"{cleaned_song_second} {cleaned_artist_second}" if cleaned_artist_second else cleaned_song_second

        # Debug: Print the queries
        print("----------------------------------------------------------------------------")
        print(f"Search Query: {query1}")
        # print(f"Query 2: {query2}")

        # Choose search method based on strict_search flag
        search_method = spotify_api.search_song_strict if strict_search else spotify_api.search_song

        # Search Spotify
        result = search_method(query1)
        if not result:
            result = search_method(query2)

        # Skip songs with "deleted" or "private" in the title
        if any(word in title.lower() for word in ["deleted", "private"]):
            print(f"{count}. ⏩ Skipped (Deleted/Private): {title}")
            continue

        # Track found or not
        if result:
            found_tracks.append(result['uri'])
            print(f"{count}. ✅ Found: {result['song_name']} by {result['artists']}")
        else:
            not_found_count += 1
            print(f"{count}. ❌ Song Not Found: {title}")

        count += 1
    
    # Get current Spotify playlist tracks
    spotify_tracks = spotify_api.get_playlist_tracks(playlist_id)
    spotify_track_uris = [track['uri'] for track in spotify_tracks]

    # Add new tracks if needed
    tracks_to_add = set(found_tracks) - set(spotify_track_uris)
    if tracks_to_add:
        print(f"\nAdding {len(tracks_to_add)} new tracks to Spotify playlist...")
        spotify_api.add_tracks_to_playlist(playlist_id, list(tracks_to_add))

    if remove:
        # Remove old tracks if needed
        tracks_to_remove = set(spotify_track_uris) - set(found_tracks)
        if tracks_to_remove:
            print(f"\nRemoving {len(tracks_to_remove)} tracks from Spotify playlist...")
            spotify_api.remove_tracks_from_playlist(playlist_id, list(tracks_to_remove))
        
    # Ensure playlist order matches YouTube
    print(f"\nUpdating playlist order...")
    
    if len(youtube_videos) > 100:
        spotify_api.reorder_playlist_many_tracks(playlist_id, found_tracks)
    else: 
        spotify_api.reorder_playlist_tracks(playlist_id, found_tracks)

    # Summary
    print("\nSummary:")
    print(f"Total YouTube songs: {len(youtube_videos)}")
    print(f"Found on Spotify: {len(found_tracks)}")
    print(f"Not Found on Spotify: {not_found_count}")
    print(f"Added to playlist: {len(tracks_to_add)}")
    if remove:
        print(f"Removed from playlist: {len(tracks_to_remove)}")
 
if __name__ == '__main__':
    main()