# script.py
from spotify import SpotifyAPI
from youtube import YouTubeAPI
# from urllib.parse import urlencode
from dotenv import load_dotenv
import os

def main():
    load_dotenv()

    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    refresh_token = os.getenv('REFRESH_TOKEN')
    top_100_spotify_playlist_id = os.getenv('TOP_100_SPOTIFY_PLAYLIST_ID')
    api_key = os.getenv('API_KEY')
    top_100_youtube_playlist_id = os.getenv('TOP_100_YOUTUBE_PLAYLIST_ID')

    required = {
        'CLIENT_ID': client_id,
        'CLIENT_SECRET': client_secret,
        'REFRESH_TOKEN': refresh_token,
        'TOP_100_SPOTIFY_PLAYLIST_ID': top_100_spotify_playlist_id,
        'API_KEY': api_key,
        'TOP_100_YOUTUBE_PLAYLIST_ID': top_100_youtube_playlist_id,
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

    spotify_api = SpotifyAPI(client_id, client_secret, refresh_token)
    youtube_api = YouTubeAPI(api_key)

    # my_playlists = spotify_api.get_playlist_names_and_ids(user_name)
    # re_order_playlists(my_playlists, spotify_api)
    # update_playlists_descriptions(my_playlists, spotify_api)

    update_playlist_from_youtube(top_100_spotify_playlist_id,
                                 top_100_youtube_playlist_id,
                                 spotify_api, youtube_api,
                                 remove=True, strict_search=False)

# def re_order_playlists(my_playlists, spotify_api):
#     for playlist in my_playlists:
#         if "Top 100 Songs In Zimbabwe" not in playlist['name']:
#             print("----------------------------------------------------------------------------")
#             print(f"Playlist: {playlist['name']}  ID: {playlist['id']}")
#             spotify_api.reorder_playlist_by_track_popularity(playlist['id'])

# def update_playlists_descriptions(my_playlists, spotify_api):
#     for playlist in my_playlists:
#         playlist_name = playlist['name']

#         if "Top 100 Songs In Zimbabwe" not in playlist_name and "Zimbabwe Trending Hits" not in playlist_name:
#             spotify_api.update_playlist_description(playlist['id'],
#                                                     playlist_name,
#                                                     playlist_name + " {artists}. {genres}")

#         elif "Top 100 Songs In Zimbabwe" in playlist_name:
#             print(f"Updating Description for {playlist_name}")
#             base_description = "🔥 Zimbabwe Top 100 Music Hits 2025!  {artists}. {genres}. New, YouTube Trends, Playlists. #Hot100"
#             spotify_api.update_playlist_description(playlist['id'], "", base_description)

#         elif "Zimbabwe Trending Hits" in playlist_name:
#             print(f"Updating Description for {playlist_name}")
#             base_description = "Top Fresh Music in Zimbabwe 2025. {artists}. {genres}"
#             spotify_api.update_playlist_description(playlist['id'], "", base_description)

def update_playlist_from_youtube(playlist_id, youtube_playlist_id, spotify_api,
                                 youtube_api, remove=False, strict_search=False):
    print("\nYouTube Playlist Tracks:")
    youtube_videos = youtube_api.get_playlist_items(youtube_playlist_id)

    found_tracks = []
    not_found_count = 0

    count = 1
    for title, url in youtube_videos:
        (song_first, artist_first), (song_second, artist_second) = youtube_api.extract_song_and_artist(title)

        cleaned_song_first = youtube_api.clean_title(song_first)
        cleaned_artist_first = youtube_api.clean_title(artist_first)
        cleaned_song_second = youtube_api.clean_title(song_second)
        cleaned_artist_second = youtube_api.clean_title(artist_second)

        query1 = f"{cleaned_song_first} {cleaned_artist_first}" if cleaned_artist_first else cleaned_song_first
        query2 = f"{cleaned_song_second} {cleaned_artist_second}" if cleaned_artist_second else cleaned_song_second

        print("----------------------------------------------------------------------------")
        print(f"Search Query: {query1}")

        search_method = spotify_api.search_song_strict if strict_search else spotify_api.search_song

        result = search_method(query1)
        if not result:
            result = search_method(query2)

        if any(word in title.lower() for word in ["deleted", "private"]):
            print(f"{count}. ⏩ Skipped (Deleted/Private): {title}")
            continue

        if result:
            found_tracks.append(result['uri'])
            print(f"{count}. ✅ Found: {result['song_name']} by {result['artists']}")
        else:
            not_found_count += 1
            print(f"{count}. ❌ Song Not Found: {title}")

        count += 1

    spotify_tracks = spotify_api.get_playlist_tracks(playlist_id)
    spotify_track_uris = [track['uri'] for track in spotify_tracks]

    tracks_to_add = set(found_tracks) - set(spotify_track_uris)
    if tracks_to_add:
        print(f"\nAdding {len(tracks_to_add)} new tracks to Spotify playlist...")
        spotify_api.add_tracks_to_playlist(playlist_id, list(tracks_to_add))

    if remove:
        tracks_to_remove = set(spotify_track_uris) - set(found_tracks)
        if tracks_to_remove:
            print(f"\nRemoving {len(tracks_to_remove)} tracks from Spotify playlist...")
            spotify_api.remove_tracks_from_playlist(playlist_id, list(tracks_to_remove))

    print(f"\nUpdating playlist order...")

    if len(youtube_videos) > 100:
        spotify_api.reorder_playlist_many_tracks(playlist_id, found_tracks)
    else:
        spotify_api.reorder_playlist_tracks(playlist_id, found_tracks)

    print("\nSummary:")
    print(f"Total YouTube songs: {len(youtube_videos)}")
    print(f"Found on Spotify: {len(found_tracks)}")
    print(f"Not Found on Spotify: {not_found_count}")
    print(f"Added to playlist: {len(tracks_to_add)}")
    if remove:
        print(f"Removed from playlist: {len(tracks_to_remove)}")

if __name__ == '__main__':
    main()
