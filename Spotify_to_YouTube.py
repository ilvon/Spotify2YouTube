import spotipy
from spotipy.oauth2 import SpotifyOAuth
import ytmusicapi
from ytmusicapi import YTMusic
import json
import csv
import os

class Spotify2Youtube():
    def __init__(self, config_file=True):
        self.sp = self.SpotifyExport(config_file)
        self.yt = self.YoutubeImport()
    
    def init_transfer(self):
        sp_playlist_title, sp_playlist_tracks = self.sp.get_playlist_tracks_info()
        ytlist_desc = input('\nPlaylist description: ')
        ytlist_visibility = input('Playlist privacy status (PUBLIC / PRIVATE / UNLISTED): ')
        print(f'\n{len(sp_playlist_tracks)} tracks will be imported from \"{sp_playlist_title}\" to YouTube')
        ytlist_id = self.yt.import_tracks(sp_playlist_title, sp_playlist_tracks,
                                          ytlist_desc, ytlist_visibility)
        print(f'\"{sp_playlist_title}\" created successfully, URL = https://www.youtube.com/playlist?list={ytlist_id}')
        
        os.remove('browser.json')
    
    class SpotifyExport():
        def __init__(self, config_file: bool):
            if config_file:
                with open('config.json', 'r') as jsonf:
                    cfg = json.load(jsonf)
                self.sp_client = spotipy.Spotify(auth_manager=SpotifyOAuth(
                    client_id=cfg['spotify']['SPOTIPY_CLIENT_ID'],
                    client_secret=cfg['spotify']['SPOTIPY_CLIENT_SECRET'],
                    redirect_uri=cfg['spotify']['SPOTIPY_REDIRECT_URI'],
                    scope='playlist-read-private'))
            else:
                self.sp_client = spotipy.Spotify(auth_manager=SpotifyOAuth(scope='playlist-read-private'))
                
            self.playlists = self.sp_client.current_user_playlists()
            self.all_playlist_title = []

            for playlist_item in self.playlists['items']:
                self.all_playlist_title.append(playlist_item['name'])

        def print_all_playlist(self):
            for i, list_name in enumerate(self.all_playlist_title):
                print(f"{i}. {list_name}")
                
        def _prompt_playlist_selection(self):   # return playlist ID in list & playlist title 
            self.print_all_playlist()
            while True:
                index = int(input(f'Playlist to be exported (0-{len(self.all_playlist_title)-1}): ')) 
                if (index <= len(self.all_playlist_title) - 1) and index >= 0:
                    break
                print('Invalid choice.')
            title = self.all_playlist_title[index]
            id = [(target['id'], target['tracks']['total']) for target in self.playlists['items'] if target['name'] == title]
            return id, title    # id = [id , track_numbers]
        
        def get_playlist_tracks_info(self): # return simplified track info only
            tracks_basic_info = []
            playlist_id, playlist_title = self._prompt_playlist_selection()
            offset = 0
            if len(playlist_id):
                for id, track_count in playlist_id:
                    while True:
                        if offset > track_count:
                            break
                        tracks = self.sp_client.playlist_tracks(id, limit=100, offset=offset)['items']
                        for song in tracks:
                            info = song['track']
                            trackname = info['name']
                            artists = ', '.join([ppl['name'] for ppl in info['artists']])
                            album_title = info['album']['name']
                            # tracks_basic_info.append(f'{trackname} - {artists} - {album_title}')
                            tracks_basic_info.append({
                                'title': trackname,
                                'artist': artists,
                                'album': album_title
                            })
                        offset += 100
            return playlist_title, tracks_basic_info    # info->[{title,artist,album}, {x,x,x}, ...]
        
        def export_simplified_tracks_info(self, encoding_mode='utf-8-sig'):
            title, track_info = self.get_playlist_tracks_info()
            with open(f'{title}.txt', 'w', encoding=encoding_mode) as txtf:
                for aud in track_info:
                    txtf.write('-'.join(aud.values()) + '\n')

        def export_detailed_tracks_info(self, encoding_mode='utf-8-sig'):
            playlist_id, target_playlist_name = self._prompt_playlist_selection()
            csvHeader = ['Title', 'Artist', 'Album', 'Released Date', 'Tracknumber', 'Duration', 'Date added']
            
            with open(f'{target_playlist_name}.csv', 'w', newline='', encoding=encoding_mode) as csvf:
                csvwriter = csv.writer(csvf)
                csvwriter.writerow(csvHeader)
                offset = 0
                if len(playlist_id):
                    for id, track_count in playlist_id:
                        while True:
                            if offset > track_count:
                                break
                            tracks = self.sp_client.playlist_tracks(id, limit=100, offset=offset)['items']
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
    
    class YoutubeImport():
        def __init__(self):     
            if not os.path.exists('browser.json'):
                ytmusicapi.setup(filepath='browser.json')          
            self.yt_client = YTMusic('browser.json')    
            # self.fun_test()     
            
        def fun_test(self):
            results = self.yt_client.search('I miss you, I’m sorry - Gracie Abrams - minor', filter='songs')
            with open('gracie_songs.json', 'w', encoding='utf-8-sig') as resultjson:
                json.dump(results, resultjson)
                
        
        # imported_tracks: list containing dict
        def import_tracks(self, new_playlist_name, imported_tracks: list, desc, privacy):
            imported_tracks_ID = []
            total_track_no = len(imported_tracks)
            
            for idx, metadata in enumerate(imported_tracks):    # metadata : dict->{title, artist, album}
                trackID = self.search_tracks(metadata)
                imported_tracks_ID.append(trackID)
                if idx == (total_track_no - 1):
                    print(f'{idx+1}/{total_track_no} exported.\n')
                else:
                    print(f'{idx+1}/{total_track_no} exported.', end='\r')
                
            new_playlist_id = self.yt_client.create_playlist(title=new_playlist_name,
                                                             description=desc,
                                                             privacy_status=privacy, 
                                                             video_ids=imported_tracks_ID)
            return new_playlist_id


        def search_tracks(self, target_track_metadata):
            target_track_id = ''
            search_str = '-'.join(target_track_metadata.values())
            results = self.yt_client.search(search_str)
            
            for info in results:
                if target_track_id:
                    break
                if info['category'] == 'More from YouTube':
                    continue
                    
                if info['category'] == 'Top result' and info['resultType'] == 'song':
                    target_track_id = info['videoId']
                if info['category'] == 'Songs':
                    if target_track_metadata['title'] in info['title']:
                        target_track_id = info['videoId']
            if target_track_id == '':
                # target_track_id = results[0]['videoId']
                target_track_id = next((info['videoId'] for info in results if info['category'] == 'Songs'), None)
            return target_track_id
        
        def search_tracks2(self, target_track_metadata):
            search_str = '-'.join(target_track_metadata.values())
            results = self.yt_client.search(search_str)
            
            for info in results:
                if info['category'] == 'More from YouTube':
                    continue
                
                if info['category'] == 'Top result' and info['resultType'] == 'song':
                    return info['videoId']
                if info['category'] == 'Songs':
                    if target_track_metadata['title'] == info['title']:
                        return info['videoId']
            
            return results[0]['videoID']    # id of Top result
                

if __name__ == '__main__':
    main_process = Spotify2Youtube(config_file=True) 
    main_process.init_transfer()
    # main_process.sp.export_simplified_tracks_info()