import spotipy
from spotipy.oauth2 import SpotifyOAuth
import ytmusicapi
from ytmusicapi import YTMusic
import csv, json, logging, re
import os, sys

class Spotify2Youtube():
    def __init__(self, init_with_config=True):
        self.__log_name__ = 'Spotify2YouTube.log'
        self.sp = self.SpotifyExport(init_with_config)
        self.yt = self.YoutubeImport(log_name=self.__log_name__)
        
    @staticmethod
    def terminate(message, exit_code:int = 1):
        if message:
            print(message)
        input('Press any key to exit...')
        sys.exit(exit_code)
    
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
            with open(self.__log_name__, 'a', encoding='utf-8-sig') as logf:
                logf.write(f'\n\"{sp_playlist_title}\" created successfully, URL = https://www.youtube.com/playlist?list={ytlist_id}')
            print(f'\"{sp_playlist_title}\" created successfully, URL = https://www.youtube.com/playlist?list={ytlist_id}')
        except Exception as err:
            Spotify2Youtube.terminate(f'Error occurred: {str(err)}')
    
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
                Spotify2Youtube.terminate('Unsupported file type!')              
        except OSError:
            Spotify2Youtube.terminate('Failed to read the targeted file!')
            
        ytlist_desc = input('\nPlaylist description: ')
        ytlist_visibility = input('Playlist privacy status (PUBLIC / PRIVATE / UNLISTED): ').upper()
        if ytlist_visibility not in ['PUBLIC', 'PRIVATE', 'UNLISTED']:
            ytlist_visibility = 'PRIVATE'
            
        print(f'\n{len(parsed_tracks)} tracks will be imported from \"{parsed_title}\" to YouTube')
        ytlist_id = self.yt.import_tracks(parsed_title, parsed_tracks,
                                          ytlist_desc, ytlist_visibility)
        with open(self.__log_name__, 'a', encoding='utf-8-sig') as logf:
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
                    Spotify2Youtube.terminate('\"config.json\" does not exist / failed to open!')
                except Exception as err:
                    Spotify2Youtube.terminate(f'Error occurred: {str(err)}')
                           
                self.sp_client = spotipy.Spotify(auth_manager=SpotifyOAuth(
                    client_id=cfg['spotify']['SPOTIPY_CLIENT_ID'],
                    client_secret=cfg['spotify']['SPOTIPY_CLIENT_SECRET'],
                    redirect_uri=cfg['spotify']['SPOTIPY_REDIRECT_URI'],
                    scope='playlist-read-private'))
            else:
                self.sp_client = spotipy.Spotify(auth_manager=SpotifyOAuth(scope='playlist-read-private'))
                
            self.playlists = self.sp_client.current_user_playlists()
            self.all_playlist_info = self.playlists['items']


        def chk_create_JSON(self):
            if os.path.exists('config.json'):
                return
            
            create_cfg = input('\"config.json\" does not exist. Create it? (Y/N): ')
            if create_cfg not in ['y', 'Y']:
                Spotify2Youtube.terminate('Script exited.', 0)
                
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
                Spotify2Youtube.terminate(f'Error occurred when creating \"config.json\": {str(err)}')
         
        def _prompt_SPplaylist_selection(self): # return playlist ID in list & playlist title 
            print('\n') 
            for i, list_info in enumerate(self.playlists['items']):
                print(f"{i}. {list_info['name']}")
            while True:
                index = int(input(f'Playlist to be exported (0-{len(self.all_playlist_info)-1}): ')) 
                if (index <= len(self.all_playlist_info) - 1) and index >= 0:
                    break
                print('Invalid choice.')
            Id = self.playlists['items'][index]['id']
            title = self.all_playlist_info[index]['name']
            no_of_track = self.playlists['items'][index]['tracks']['total']
            return Id, title, no_of_track
        
        def get_playlist_tracks_info(self): # return detailed track info
            all_track_attrs = []
            playlist_id, playlist_title, track_count = self._prompt_SPplaylist_selection()
            offset = 0
            while True:
                if offset > track_count:
                    break
                tracks = self.sp_client.playlist_tracks(playlist_id, limit=100, offset=offset)['items']
                
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
            return playlist_title, all_track_attrs
        
        def export_simplified_tracks_info(self, encoding_mode='utf-8-sig'): # output .csv
            title, track_info = self.get_playlist_tracks_info()
            title = self.sanitize(title)
            try:
                with open(f'{title}.csv', 'w', newline='', encoding=encoding_mode) as export:
                    csvwriter = csv.DictWriter(export, fieldnames=['Title', 'Artist', 'Album'])
                    csvwriter.writeheader()
                    for aud in track_info:
                        csvwriter.writerow({
                            'Title': aud['Title'], 
                            'Artist': aud['Artist'], 
                            'Album': aud['Album']})
            except PermissionError:
                Spotify2Youtube.terminate('\nYou do not have the permission to write the csv file / the exisiting file is in use!')
            except OSError:
                Spotify2Youtube.terminate('\nFailed to export the csv file!')
            except Exception as err:
                Spotify2Youtube.terminate(f'\nError occurred: {str(err)}')

        def export_detailed_tracks_info(self, encoding_mode='utf-8-sig'):
            title, track_info = self.get_playlist_tracks_info()
            title = self.sanitize(title)
            try:
                with open(f'{title}.csv', 'w', newline='', encoding=encoding_mode) as export:
                    csvwriter = csv.DictWriter(export, fieldnames=track_info[0].keys())
                    csvwriter.writeheader()
                    for aud in track_info:
                        csvwriter.writerow(aud)
            except PermissionError:
                Spotify2Youtube.terminate('\nYou do not have the permission to write the csv file / the exisiting file is in use!')
            except OSError:
                Spotify2Youtube.terminate('\nFailed to export the csv file!')
            except Exception as err:
                Spotify2Youtube.terminate(f'\nError occurred: {str(err)}')
            
        def sanitize(self, title):
            invalid_chars = r'[\\\/\:\*\?\'\"\<\>\|]'  
            return re.sub(invalid_chars, ' ', title)  
            
 
    class YoutubeImport():
        def __init__(self, log_name):     
            if not os.path.exists('browser.json'):
                print('\nVisit https://music.youtube.com/ and get the access header.')
                try:
                    ytmusicapi.setup(filepath='browser.json')          
                except Exception as err:
                    Spotify2Youtube.terminate(f'Error occurred: {str(err)}', 1)
            self.yt_client = YTMusic('browser.json') 
            self.__log_name__ = log_name    
                             
        # imported_tracks: list containing dict
        def import_tracks(self, new_playlist_name, imported_tracks: list, desc, privacy):
            imported_tracks_ID = []
            total_track_no = len(imported_tracks)
            logging.basicConfig(level=logging.INFO, filename=self.__log_name__, filemode='a', encoding='utf-8-sig', format='%(levelname)s: %(message)s')
            with open(self.__log_name__, 'w', encoding='utf-8-sig') as logf:
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
                Spotify2Youtube.terminate('', 0)
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
    main_process = Spotify2Youtube(init_with_config=True) 