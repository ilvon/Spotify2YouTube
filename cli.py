from Spotify_to_YouTube import Spotify2Youtube
import os

OPTION_MENU = '''
1. Transfer Spotify playlist to YouTube
2. Import Spotify playlist from local csv file to YouTube
3. Export Spotify playlist (simplified info) to local file (.csv)
4. Export Spotify playlist (detailed info) to local file (.csv)
5. Update YouTube playlist with Spotify playlist
'''

def get_user_choice():
    while True:
        print(OPTION_MENU)
        try:
            user_option = int(input('Option (1-5): '))
            if user_option < 1 or user_option > 5:
                print('Please input valid number between 1-5.')
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
            print('\nTransfer process finished.')
        elif process_opt == 2:
            main.init_transfer_fromLocal()
            print('\nTransfer process finished.')
        elif process_opt == 3:
            main.sp.export_simplified_tracks_info()
            print('\nPlaylist with simplified track info exported to local csv file.')
        elif process_opt == 4:
            main.sp.export_detailed_tracks_info()
            print('\nPlaylist with detailed track info exported to local csv file.')
        elif process_opt == 5:
            main.init_update_ytlist()
        
        export_more = input('Continue to transfer/export Spotify playlist? (Y / Any key to exit): ')
        if export_more not in ['Y', 'y']:
            if os.path.exists('browser.json'):
                os.remove('browser.json')
            return
        
if __name__ == '__main__':
    cli_init()