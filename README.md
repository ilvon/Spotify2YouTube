# Spotify2YouTube

A simple command-line tool to Spotify playlists to local csv files or transfer to YouTube playlist.

This python script uses [spotipy](https://github.com/spotipy-dev/spotipy) and [ytmusicapi](https://github.com/sigma67/ytmusicapi)

## Features

- Transfer Spotify playlists to YouTube playlist
- Import playlist from local csv file to create YouTube playlist
- Export Spotify playlist to csv file with tracks' metadata

## Remarks

- YouTube playlist name will be set as the same in Spotify in default (csv file name if is imported from local csv file)
- Require access to Spotify Web API (Instructions can be found in [Spotify API Documentation](https://developer.spotify.com/documentation/web-api) under "Getting started" section)
- Require the use of request header to mimic a browser session (Instruction can be found in [ytmusicapi doc](https://ytmusicapi.readthedocs.io/en/stable/setup/browser.html) under the "Browser authentication" section)
  
  - You can copy the request header from any HTTP request that in `Status` = 200, `Method` = POST, `Domain` = music.youtube.com

- Import results (in YouTube) depends on the YouTube Music search, you should always verify the results after running the script