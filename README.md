# Playlist Manager for Spotify

This Python project helps automate the management of Spotify playlists, including reordering playlists based on track popularity, updating playlist descriptions for better SEO, and syncing playlists with YouTube. The script uses the [Spotify Web API](https://developer.spotify.com/documentation/web-api/) and [YouTube API](https://developers.google.com/youtube/v3) to perform these tasks efficiently.

## Features

- **Reorder Playlists by Track Popularity:** Reorders all playlists based on track popularity, excluding the special playlist "Top 100 Songs In Zimbabwe".
- **Update Playlist Descriptions:** Updates playlist descriptions to include trending artists and genres to improve SEO and engagement.
- **Sync with YouTube:** Syncs Spotify playlists with their corresponding YouTube playlists, adding or removing tracks as necessary.

## Functions

### `re_order_playlists(my_playlists, spotify_api)`

Reorders all playlists by track popularity, except for "Top 100 Songs In Zimbabwe".

**Parameters:**

- `my_playlists`: List of playlists to be reordered.
- `spotify_api`: Spotify Web API instance for interacting with Spotify.

### `update_playlists_descriptions(my_playlists, spotify_api)`

Updates the descriptions of the playlists based on their names and trending artists/genres for SEO purposes.

**Parameters:**

- `my_playlists`: List of playlists to be updated.
- `spotify_api`: Spotify Web API instance for interacting with Spotify.

### `update_playlist_from_youtube(playlist_id, youtube_playlist_id, spotify_api, youtube_api, remove=False)`

Syncs a Spotify playlist with its corresponding YouTube playlist, either adding or removing tracks based on the `remove` flag.

**Parameters:**

- `playlist_id`: ID of the Spotify playlist.
- `youtube_playlist_id`: ID of the YouTube playlist.
- `spotify_api`: Spotify Web API instance.
- `youtube_api`: YouTube API instance.
- `remove`: Boolean flag to indicate whether to remove tracks from Spotify that are no longer in the YouTube playlist.

## Requirements

- Python 3.x
- [Spotipy](https://pypi.org/project/spotipy/) library for Spotify API integration.
- [google-api-python-client](https://pypi.org/project/google-api-python-client/) library for YouTube API integration.

## Setup

1. Install the required dependencies:

   ```bash
   pip install spotipy google-api-python-client
   ```
