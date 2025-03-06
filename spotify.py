import requests
import base64
import time

class SpotifyAPI:
    def __init__(self, client_id, client_secret, refresh_token):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.token = self.refresh_access_token()

    def refresh_access_token(self):
        token_url = 'https://accounts.spotify.com/api/token'
        headers = {
            'Authorization': 'Basic ' + base64.b64encode(f'{self.client_id}:{self.client_secret}'.encode()).decode(),
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'grant_type': 'refresh_token',
            'refresh_token': self.refresh_token
        }
        response = requests.post(token_url, headers=headers, data=data)
        response.raise_for_status()
        token_data = response.json()
        return token_data['access_token']

    def fetch_web_api(self, endpoint, method='GET', body=None):
        url = f'https://api.spotify.com/v1/{endpoint}'
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        response = requests.request(method, url, json=body, headers=headers)
        if response.status_code == 401:  # Token expired, refresh it
            print('Refreshing access token...')
            self.token = self.refresh_access_token()
            headers['Authorization'] = f'Bearer {self.token}'
            response = requests.request(method, url, json=body, headers=headers)
        response.raise_for_status()
        
        # Handle empty responses (like playlist updates)
        if response.status_code == 200 and not response.content.strip():
            return None  # No JSON to parse

        return response.json()

    def get_playlists(self, user_id):
        endpoint = f'users/{user_id}/playlists'
        data = self.fetch_web_api(endpoint)
        return data.get('items', [])

    def get_playlist_tracks(self, playlist_id):
        fields = 'items(track(id,uri,name,artists(name),album(release_date),popularity),added_at)'
        endpoint = f'playlists/{playlist_id}/tracks?fields={fields}'
        data = self.fetch_web_api(endpoint)
        return [
            {
                'id': item['track']['id'],
                'uri': item['track']['uri'],
                'song_name': item['track']['name'],
                'artists': ', '.join(artist['name'] for artist in item['track']['artists']),
                'date_added': item['added_at'],
                'release_date': item['track']['album']['release_date'],
                'popularity': item['track']['popularity']
            }
            for item in data.get('items', [])
        ]
     
    def search_song(self, query, limit=5):
        # Debug: Print the search query
        endpoint = f'search?q={query}&type=track&limit={limit}'
        data = self.fetch_web_api(endpoint)
        tracks = data.get('tracks', {}).get('items', [])

        if not tracks:
            return None

        # Debug: Print all search results
        for i, track in enumerate(tracks):
            track_artists = ', '.join(artist['name'] for artist in track['artists'])

        # Iterate through the tracks to find the best match
        for track in tracks:
            track_artists = ', '.join(artist['name'] for artist in track['artists'])
            track_name = track['name']

            # Check if the query is a close match to the track name or artists
            if query.lower() in track_name.lower() or query.lower() in track_artists.lower():
                return {
                    'id': track['id'],
                    'uri': track['uri'],
                    'song_name': track_name,
                    'artists': track_artists,
                    'album': track['album']['name'],
                    'release_date': track['album']['release_date'],
                    'popularity': track['popularity']
                }

        # If no matching track is found, return the first result
        return {
            'id': tracks[0]['id'],
            'uri': tracks[0]['uri'],
            'song_name': tracks[0]['name'],
            'artists': ', '.join(artist['name'] for artist in tracks[0]['artists']),
            'album': tracks[0]['album']['name'],
            'release_date': tracks[0]['album']['release_date'],
            'popularity': tracks[0]['popularity']
        }

    def search_song_strict(self, query, limit=5):
        # Debug: Print the search query
        endpoint = f'search?q={query}&type=track&limit={limit}'
        data = self.fetch_web_api(endpoint)
        tracks = data.get('tracks', {}).get('items', [])

        if not tracks:
            return None  # No tracks found at all

        # Iterate through the search results and look for close matches
        for track in tracks:
            track_artists = ', '.join(artist['name'] for artist in track['artists'])
            track_name = track['name']

            # Match if the query closely matches the song name or artist names
            if query.lower() in track_name.lower() or query.lower() in track_artists.lower():
                return {
                    'id': track['id'],
                    'uri': track['uri'],
                    'song_name': track_name,
                    'artists': track_artists,
                    'album': track['album']['name'],
                    'release_date': track['album']['release_date'],
                    'popularity': track['popularity']
                }

        # If no close match is found, return None
        print(f"No strict match found for query: {query}")
        return None

    def add_tracks_to_playlist(self, playlist_id, track_uris):
        endpoint = f'playlists/{playlist_id}/tracks'
        batch_size = 100

        # Get current playlist tracks
        existing_tracks = self.get_playlist_tracks(playlist_id)
        existing_uris = {track['uri'] for track in existing_tracks}

        # Filter out duplicates
        unique_uris = [uri for uri in track_uris if uri not in existing_uris]

        total_tracks = len(unique_uris)
        # print(f"Adding {total_tracks} new tracks to playlist...")

        for i in range(0, total_tracks, batch_size):
            batch = unique_uris[i:i + batch_size]
            body = {'uris': batch}
            response = self.fetch_web_api(endpoint, method='POST', body=body)

            if response.get('snapshot_id'):
                print(f"Added {len(batch)} tracks — {i + len(batch)}/{total_tracks} complete.")
            else:
                print(f"Failed to add batch starting at {i}. Response: {response}")

            # time.sleep(1)

        print(f"Finished adding all {total_tracks} tracks.")

    def remove_tracks_from_playlist(self, playlist_id, track_uris):
        endpoint = f'playlists/{playlist_id}/tracks'
        batch_size = 100
        for i in range(0, len(track_uris), batch_size):
            batch = [{'uri': uri} for uri in track_uris[i:i + batch_size]]
            body = {'tracks': batch}
            response = self.fetch_web_api(endpoint, method='DELETE', body=body)
            print(f"Removed {len(batch)} tracks from playlist.")
        return response
    
    def reorder_playlist_tracks(self, playlist_id, track_uris):
        endpoint = f'playlists/{playlist_id}/tracks'
        current_tracks = self.get_playlist_tracks(playlist_id)
        current_uris = [track['uri'] for track in current_tracks]

        # Only update if the order has changed
        if current_uris == track_uris:
            print("☑️ Playlist order is already correct. No update needed.")
            return

        # Prepare the request body
        batches = [track_uris[i:i + 100] for i in range(0, len(track_uris), 100)]
        for batch in batches:
            body = {'uris': batch}
            response = self.fetch_web_api(endpoint, method='PUT', body=body)
            print(f"✅ Updated playlist order for {len(batch)} tracks.")
        
        return response
    
    def reorder_playlist_many_tracks(self, playlist_id, ordered_uris):
        # Fetch current tracks from the playlist
        existing_tracks = self.get_playlist_tracks(playlist_id)
        existing_uris = [track['uri'] for track in existing_tracks]

        # Ensure we include all tracks currently in the playlist
        final_order = [uri for uri in ordered_uris if uri in existing_uris]
        missing_uris = [uri for uri in existing_uris if uri not in final_order]
        final_order.extend(missing_uris)  # Add any tracks that weren't in ordered_uris

        print(f"🔃Reordering {len(final_order)} tracks...")

        # Reorder in batches
        for i, uri in enumerate(final_order):
            current_index = existing_uris.index(uri)
            if current_index != i:
                body = {
                    "range_start": current_index,
                    "insert_before": i
                }
                response = self.fetch_web_api(f'playlists/{playlist_id}/tracks', method='PUT', body=body)
                # if response.get('snapshot_id'):
                    # print(f"✅ Reordered track {i + 1}/{len(final_order)}")
                # else:
                    # print(f"❌ Failed to reorder track {uri}")

        print(f"✅Finished reordering {len(final_order)} tracks.")

    def update_playlist_description(self, playlist_id, playlist_name, base_description):
        print(f"Updating Playlist Description for {playlist_name}")

        # Get tracks based on playlist order
        top_tracks = self.get_playlist_tracks(playlist_id)
        artist_names = []
        genres = []

        # Collect artists and genres from top tracks
        for track in top_tracks[:20]:
            try:
                track_id = track['id']
            except KeyError:
                continue  # Skip invalid tracks
            
            track_info = self.fetch_web_api(f'tracks/{track_id}')
            artists = track_info.get('artists', [])

            for artist in artists:
                artist_name = artist['name']
                if artist_name not in artist_names:
                    artist_names.append(artist_name)

                artist_id = artist.get('id')
                if artist_id:
                    artist_info = self.fetch_web_api(f'artists/{artist_id}')
                    for genre in artist_info.get('genres', []):
                        if genre not in genres:
                            genres.append(genre)

        # Format artist and genre strings
        artist_str = ', '.join(artist_names[:5])
        genre_str = ', '.join(genres[:2])

        # Replace placeholders in the base description
        new_description = base_description.replace("{artists}", artist_str).replace("{genres}", genre_str)

        # Adjust description length dynamically
        # Case 1: Add more artists/genres if the description is too short
        artist_index = 5
        genre_index = 2

        while len(new_description) < 300:
            added = False

            if artist_index < len(artist_names):
                artist_str = ', '.join(artist_names[:artist_index + 1])
                artist_index += 1
                added = True

            if genre_index < len(genres):
                genre_str = ', '.join(genres[:genre_index + 1])
                genre_index += 1
                added = True

            new_description = base_description.replace("{artists}", artist_str).replace("{genres}", genre_str)

            if not added:
                break  # Stop if we've used all artists and genres

        # Case 2: Remove artists/genres if the description is too long
        while len(new_description) > 300:
            if len(artist_names) > 1:
                artist_names.pop()
                artist_str = ', '.join(artist_names)
            elif len(genres) > 1:
                genres.pop()
                genre_str = ', '.join(genres)

            new_description = base_description.replace("{artists}", artist_str).replace("{genres}", genre_str)

            if len(artist_names) <= 1 and len(genres) <= 1:
                break  # Can't shrink further, prevent infinite loop

        # Final cut-off to guarantee max 300 characters
        new_description = new_description[:300]

        # Update playlist description via Spotify API
        endpoint = f'playlists/{playlist_id}'
        body = {'description': new_description}
        self.fetch_web_api(endpoint, method='PUT', body=body)

        print(f"✅ Updated playlist {playlist_name} Description: {new_description}")
        print("_____________________________________________________________________")

    def reorder_playlist_by_track_popularity(self, playlist_id):
        tracks = self.get_playlist_tracks(playlist_id)
        # Sort tracks by track popularity (descending)
        sorted_tracks = sorted(tracks, key=lambda x: x['popularity'], reverse=True)
        sorted_uris = [track['uri'] for track in sorted_tracks]
        self.reorder_playlist_tracks(playlist_id, sorted_uris)

    def reorder_playlist_by_artist_popularity(self, playlist_id):
            sorted_tracks = self.get_top_artists_by_popularity(playlist_id)
            sorted_uris = [track['uri'] for track in sorted_tracks]
            self.reorder_playlist_tracks(playlist_id, sorted_uris)

    def get_playlist_names_and_ids(self, user_id):
        playlists = self.get_playlists(user_id)
        return [{'name': playlist['name'], 'id': playlist['id']} for playlist in playlists]

    def get_top_tracks_by_popularity(self, playlist_id):
        tracks = self.get_playlist_tracks(playlist_id)
        # Sort tracks by popularity (descending)
        return sorted(tracks, key=lambda x: x['popularity'], reverse=True)
    
    def get_top_artists_by_popularity(self, playlist_id):
        tracks = self.get_playlist_tracks(playlist_id)
        artist_popularity = {}

        for track in tracks:
            track_id = track['id']
            # print(track_id)
            track_info = self.fetch_web_api(f'tracks/{track_id}')
            artist_info = track_info['artists']

            for artist in artist_info:
                try:
                    artist_id = artist_info[0]['id']
                except:
                    artist_id = artist_info['id']         
                try:
                    artist_info = self.fetch_web_api(f'artists/{artist_id}')
                    artist_popularity[artist_info['uri']] = artist_info['popularity']
                except:
                    print(f"FAILED TO FETCH DETAILS FOR ARTIST: {artist_info[0]['name']}")

        # Sort artists by popularity
        sorted_artists = sorted(tracks, key=lambda x: artist_popularity.get(x['uri'], 0), reverse=True)
        return sorted_artists






