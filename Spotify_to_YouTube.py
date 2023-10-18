import spotipy
from spotipy.oauth2 import SpotifyOAuth
import ytmusicapi
from ytmusicapi import YTMusic
import csv, json
import os, sys
import logging

class Spotify2Youtube():
    def __init__(self, config_file=True):
        self.__log_filename__ = 'Spotify2YouTube.log'
        self.sp = self.SpotifyExport(config_file)
        self.yt = self.YoutubeImport(log_name=self.__log_filename__)
    
    def init_transfer(self):
        try:
            sp_playlist_title, sp_playlist_tracks = self.sp.get_playlist_tracks_info()
            ytlist_desc = input('\nPlaylist description: ')
            ytlist_visibility = input('Playlist privacy status (PUBLIC / PRIVATE / UNLISTED): ').upper()
            if ytlist_visibility not in ['PUBLIC', 'PRIVATE', 'UNLISTED']:
                ytlist_visibility = 'PRIVATE'
                
            print(f'\n{len(sp_playlist_tracks)} tracks will be imported from \"{sp_playlist_title}\" to YouTube')
            ytlist_id = self.yt.import_tracks(sp_playlist_title, sp_playlist_tracks,
                                            ytlist_desc, ytlist_visibility)
            with open(self.__log_filename__, 'a', encoding='utf-8-sig') as logf:
                logf.write(f'\n\"{sp_playlist_title}\" created successfully, URL = https://www.youtube.com/playlist?list={ytlist_id}')
            print(f'\"{sp_playlist_title}\" created successfully, URL = https://www.youtube.com/playlist?list={ytlist_id}')
        except Exception as err:
            print('Error occurred: ' + str(err))
            sys.exit(1)
    
    def init_transfer_fromLocal(self):
        file_import = input('File to be imported: ').strip('"\'')
        csvfields = ['Title', 'Artist', 'Album', 'Release_date', 'Tracknumber', 'Duration', 'Date_added']
        try:
            if os.path.splitext(file_import)[1] == '.csv':
                with open(file_import, 'r', newline='', encoding='utf-8-sig') as local_import:
                    parsed_title = os.path.splitext(os.path.basename(file_import))[0]
                    parsed_tracks = csv.DictReader(local_import, fieldnames=csvfields)
                    next(parsed_tracks)
                    parsed_tracks = [{'Title': track['Title'], 
                                     'Artist':track['Artist'], 
                                     'Album':track['Album']} for track in parsed_tracks]   # -> [{},{},{}]
            else:
                print('Unsupported file type!') 
                sys.exit(1)               
        except OSError:
            print('Failed to read the targeted file!')
            sys.exit(1)
            
        ytlist_desc = input('\nPlaylist description: ')
        ytlist_visibility = input('Playlist privacy status (PUBLIC / PRIVATE / UNLISTED): ').upper()
        if ytlist_visibility not in ['PUBLIC', 'PRIVATE', 'UNLISTED']:
            ytlist_visibility = 'PRIVATE'
            
        print(f'\n{len(parsed_tracks)} tracks will be imported from \"{parsed_title}\" to YouTube')
        ytlist_id = self.yt.import_tracks(parsed_title, parsed_tracks,
                                          ytlist_desc, ytlist_visibility)
        with open(self.__log_filename__, 'a', encoding='utf-8-sig') as logf:
            logf.write(f'\n\"{parsed_title}\" created successfully, URL = https://www.youtube.com/playlist?list={ytlist_id}')
        print(f'\"{parsed_title}\" created successfully, URL = https://www.youtube.com/playlist?list={ytlist_id}')
                
    class SpotifyExport():
        def __init__(self, config_file: bool):
            if config_file:
                self.chk_create_JSON()
                try:
                    with open('config.json', 'r') as jsonf:
                        cfg = json.load(jsonf)
                except(FileNotFoundError):
                    print('\"config.json\" does not exist / failed to open!')
                    sys.exit(1)
                except Exception as err:
                    print('An error occurred:', str(err))      
                    sys.exit(1) 
                           
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

        def chk_create_JSON(self):
            if os.path.exists('config.json'):
                return
            
            create_cfg = input('\"config.json\" does not exist. Create it? (Y/N): ')
            if create_cfg not in ['y', 'Y']:
                print('Script exited.')
                sys.exit(0)
                
            print('Please visit https://developer.spotify.com/ to create your app and obtain WebAPI credentials.')
            api_client_id = input('Client ID: ')
            api_client_secret = input('Client Secret: ')
            api_client_uri = input('Redirect URI: ')
            SPOTIFY_CFG_TEMPLATE = {
                'spotify':{
                    'SPOTIPY_CLIENT_ID': api_client_id,
                    'SPOTIPY_CLIENT_SECRET': api_client_secret,
                    'SPOTIPY_REDIRECT_URI': api_client_uri
                }
            }
            try:
                with open('config.json', 'w') as ojson:
                    json.dump(SPOTIFY_CFG_TEMPLATE, ojson)
            except Exception as err:
                print('An error occurred when creating \"config.json\": ', str(err))
                sys.exit(1)

        def print_all_playlist(self):
            for i, list_name in enumerate(self.all_playlist_title):
                print(f"{i}. {list_name}")
                
        def _prompt_playlist_selection(self): # return playlist ID in list & playlist title 
            print('\n') 
            self.print_all_playlist() 
            while True:
                index = int(input(f'Playlist to be exported (0-{len(self.all_playlist_title)-1}): ')) 
                if (index <= len(self.all_playlist_title) - 1) and index >= 0:
                    break
                print('Invalid choice.')
            title = self.all_playlist_title[index]
            id = [(target['id'], target['tracks']['total']) for target in self.playlists['items'] if target['name'] == title]
            return id, title    # id = [id , track_numbers]
        
        def get_playlist_tracks_info(self): # return detailed track info
            all_track_attrs = []
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
                            artists = ', '.join([ppl['name'] for ppl in info['artists']])
                            duration_mins = int(info['duration_ms']/1000/60)
                            duration_secs = int(info['duration_ms']/1000%60)
                            if song['added_at'] == '1970-01-01T00:00:00Z':
                                dateAdd = 'Generated by Spotify'
                            else:
                                dateAdd = song['added_at'].replace('T', ' ').replace('Z', '')
                            all_track_attrs.append({
                                'Title': info['name'],
                                'Artist': artists,
                                'Album': info['album']['name'],
                                'Release_date': info['album']['release_date'],
                                'Tracknumber': f"{info['track_number']}//{info['album']['total_tracks']}",
                                'Duration': f'{duration_mins}:{duration_secs}',
                                'Date_added': dateAdd
                            })
                            
                        offset += 100
            return playlist_title, all_track_attrs  # all_track_attrs->[{attr}, {attr}, {attr}]
        
        def export_simplified_tracks_info(self, encoding_mode='utf-8-sig'): # output .csv
            title, track_info = self.get_playlist_tracks_info()
            try:
                with open(f'{title}.csv', 'w', newline='', encoding=encoding_mode) as export:
                    csvwriter = csv.DictWriter(export, fieldnames=['Title', 'Artist', 'Album'])
                    csvwriter.writeheader()
                    for aud in track_info:  # aud is a dict
                        csvwriter.writerow({
                            'Title': aud['Title'], 
                            'Artist': aud['Artist'], 
                            'Album': aud['Album']})
            except PermissionError:
                print('\nYou do not have the permission to write the csv file / the exisiting file is in use!')    
                sys.exit(1)
            except OSError:
                print('\nFailed to export the csv file!')
                sys.exit(1)
            except Exception as err:
                print(f'\nError occurred: {str(err)}')
                sys.exit(1)

        def export_detailed_tracks_info(self, encoding_mode='utf-8-sig'):
            title, track_info = self.get_playlist_tracks_info()
            try:
                with open(f'{title}.csv', 'w', newline='', encoding=encoding_mode) as export:
                    csvwriter = csv.DictWriter(export, fieldnames=track_info[0].keys())
                    csvwriter.writeheader()
                    for aud in track_info:
                        csvwriter.writerow(aud)
            except PermissionError:
                print('\nYou do not have the permission to write the csv file / the exisiting file is in use!')    
                sys.exit(1)
            except OSError:
                print('\nFailed to export the csv file!')
                sys.exit(1)
            except Exception as err:
                print(f'\nError occurred: {str(err)}')
                sys.exit(1)
            
 
    class YoutubeImport():
        def __init__(self, log_name):     
            if not os.path.exists('browser.json'):
                print('\nVisit https://music.youtube.com/ and get the access header.')
                ytmusicapi.setup(filepath='browser.json')          
            self.yt_client = YTMusic('browser.json') 
            self.__log_filename__ = log_name    
                             
        # imported_tracks: list containing dict
        def import_tracks(self, new_playlist_name, imported_tracks: list, desc, privacy):
            imported_tracks_ID = []
            total_track_no = len(imported_tracks)
            logging.basicConfig(level=logging.INFO, filename=self.__log_filename__, filemode='a', encoding='utf-8-sig', format='%(levelname)s: %(message)s')
            with open(self.__log_filename__, 'w', encoding='utf-8-sig') as logf:
                logf.write(f'Transfer {total_track_no} tracks from \"{new_playlist_name}\" to YouTube\n')
                logf.write(f'Description: {desc}\nPrivacy Status: {privacy}\n')
            
            for idx, metadata in enumerate(imported_tracks):    # metadata : dict->{Title, Artist, Album, ... more}
                trackID = self.search_tracks(metadata, idx + 1)
                imported_tracks_ID.append(trackID)
                if idx == (total_track_no - 1):
                    print(f'{idx+1}/{total_track_no} exported.\n')
                else:
                    print(f'{idx+1}/{total_track_no} exported.', end='\r')
            try:                
                new_playlist_id = self.yt_client.create_playlist(title=new_playlist_name,
                                                                description=desc,
                                                                privacy_status=privacy, 
                                                                video_ids=imported_tracks_ID)
            except Exception as autherr:
                print(str(autherr) + '\nTry to delete \"browser.json\" and restart the process!')
                del_req_header = input('Delete \"browser.json\"? (Y/N): ')
                if del_req_header in ['Y', 'y']:
                    os.remove('browser.json')
                sys.exit(0)
            return new_playlist_id

        def search_tracks(self, target_attrs: dict, iter_idx: int = 1):
            search_str = f"{target_attrs['Title']}-{target_attrs['Artist']}-{target_attrs['Album']}"
            results = self.yt_client.search(search_str)
            
            for info in results:
                if info['category'] == 'More from YouTube':
                    continue
                if info['category'] == 'Top result' and info['resultType'] == 'song':
                    return info['videoId']
                if info['category'] == 'Songs':
                    if target_attrs['Title'] == info['title']:
                        return info['videoId']
                if info['category'] == 'Videos':    # prefer video if no exact match (title) song being found
                    if target_attrs['Title'] in info['title']:
                        logging.info(f"#{iter_idx} {target_attrs['Title']}: Added track is in form of video(https://www.youtube.com/watch?v={info['videoId']}).")
                        return info['videoId']
            
            alt_track_id = next((info['videoId'] for info in results if info['resultType'] == 'song'), None)
            logging.warning(f"#{iter_idx} {target_attrs['Title']}: Failed to find song with matching title. Alternative track added(https://www.youtube.com/watch?v={alt_track_id}).")
            return alt_track_id
                       

if __name__ == '__main__':
    main_process = Spotify2Youtube(config_file=True) 