from Spotify_to_YouTube import Spotify2Youtube
import os

OPTION_MENU = '''
1. Transfer Spotify playlist to YouTube
2. Update YouTube playlist with Spotify playlist
3. Import Spotify playlist from local csv file to YouTube
4. Export Spotify playlist (simplified info) to local file (.csv)
5. Export Spotify playlist (detailed info) to local file (.csv)
6. Export ALL Spotify playlist (detailed info) to local file (.csv)
7. Terminate the script
'''
OPTION_CNT = 7

def get_user_choice():
    while True:
        print(OPTION_MENU)
        try:
            user_option = int(input(f'Option (1-{OPTION_CNT}): '))
            if user_option < 1 or user_option > OPTION_CNT:
                print(f'Please input valid number between 1-{OPTION_CNT}.')
            else: 
                return user_option
        except ValueError:
            print('Please input valid intger value.')
 
def cli_init(): 
    main = Spotify2Youtube(init_with_config=True)
    
    while True:  
        process_opt = get_user_choice() 
        if process_opt == 1:
            main.init_transfer()
            print('\nTransfer completed.')
        elif process_opt == 2:
            main.init_update_ytlist()
            print('\nUpdate finished.')
        elif process_opt == 3:
            main.init_transfer_fromLocal()
            print('\nTransfer completed.')
        elif process_opt == 4:
            main.sp.export_simplified_tracks_info()
            print('\nPlaylist (simplified info) export completed.')
        elif process_opt == 5:
            main.sp.export_detailed_tracks_info()
            print('\nPlaylist (detailed info) export completed.')
        elif process_opt == 6:
            main.sp.export_all_playlist_local()
            print('\nAll playlist exports completed.')
        elif process_opt == 7:
            if os.path.exists('browser.json'):
                os.remove('browser.json')
            print('Script terminated.')
            return
            
        export_more = input('Continue to transfer/export Spotify playlist? (Y / Any key to exit): ')
        if export_more not in ['Y', 'y']:
            if os.path.exists('browser.json'):
                os.remove('browser.json')
            return
        os.system('clear')
        
if __name__ == '__main__':
    try:
        cli_init()
    except KeyboardInterrupt:
        print('\nScript terminated.')