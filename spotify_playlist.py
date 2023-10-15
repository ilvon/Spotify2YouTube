import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import csv

class SpotifyExport():
    def __init__(self, config_file=False):
        if not config_file:
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope='playlist-read-private'))
        else:
            with open('config.json', 'r') as jsonf:
                cfg = json.load(jsonf)
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=cfg['spotify']['SPOTIPY_CLIENT_ID'],
                client_secret=cfg['spotify']['SPOTIPY_CLIENT_SECRET'],
                redirect_uri=cfg['spotify']['SPOTIPY_REDIRECT_URI'],
                scope='playlist-read-private'))
            
        self.playlists = self.sp.current_user_playlists()
        self.all_playlist_title = []

        for playlist_item in self.playlists['items']:
            self.all_playlist_title.append(playlist_item['name'])

    def print_all_playlist(self):
        for i, list_name in enumerate(self.all_playlist_title):
            print(f"{i}. {list_name}")
    
    def _prompt_playlist_selection(self):
        while True:
            index = int(input(f'Playlist to be exported (0-{len(self.all_playlist_title)-1}): ')) 
            if (index <= len(self.all_playlist_title) - 1) and index >= 0:
                break
            print('Invalid choice.')
        return self.all_playlist_title[index]
    
    def export_simplified_tracks_info(self, encoding_mode='utf-8-sig'):
        self.print_all_playlist()
        target_playlist_name = self._prompt_playlist_selection()
        playlist_id = [(target['id'], target['tracks']['total']) for target in self.playlists['items'] if target['name'] == target_playlist_name]
        
        with open(f'{target_playlist_name}.txt', 'w', encoding=encoding_mode) as txtf:
            offset = 0
            if len(playlist_id):
                for id, track_count in playlist_id:
                    while True:
                        if offset > track_count:
                            break
                        
                        tracks = self.sp.playlist_tracks(id, limit=100, offset=offset)['items']
                        for song in tracks:
                            info = song['track']
                            trackname = info['name']
                            artists = ', '.join([ppl['name'] for ppl in info['artists']])
                            album_title = info['album']['name']
                            
                            crucial_track_info = f'{trackname} - {artists} - {album_title}'
                            txtf.write(crucial_track_info + '\n')
                        offset += 100
    
    def export_detailed_tracks_info(self, encoding_mode='utf-8-sig'):
        csvHeader = ['Title', 'Artist', 'Album', 'Released Date', 'Tracknumber', 'Duration', 'Date added']
        self.print_all_playlist()
        target_playlist_name = self._prompt_playlist_selection()
        playlist_id = [(target['id'], target['tracks']['total']) for target in self.playlists['items'] if target['name'] == target_playlist_name]
        
        with open(f'{target_playlist_name}.csv', 'w', newline='', encoding=encoding_mode) as csvf:
            csvwriter = csv.writer(csvf)
            csvwriter.writerow(csvHeader)
            offset = 0
            if len(playlist_id):
                for id, track_count in playlist_id:
                    while True:
                        if offset > track_count:
                            break
                        tracks = self.sp.playlist_tracks(id, limit=100, offset=offset)['items']
                        for song in tracks:
                            dat = song['track']
                            duration_mins = int(dat['duration_ms']/1000/60)
                            duration_secs = int(dat['duration_ms']/1000%60)
                            
                            detail_info = [
                                dat['name'],
                                ', '.join([ppl['name'] for ppl in dat['artists']]),
                                dat['album']['name'],
                                dat['album']['release_date'],
                                f"{dat['track_number']}//{dat['album']['total_tracks']}",
                                f'{duration_mins}:{duration_secs}',
                                song['added_at'].replace('T', ' ').replace('Z', '')
                            ]
                            csvwriter.writerow(detail_info)
                        offset += 100
    

if __name__ == '__main__':
    process = SpotifyExport(config_file=True)
    process.export_detailed_tracks_info()
