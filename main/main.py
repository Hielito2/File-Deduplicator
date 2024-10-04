import os
import threading
import hashlib
import FreeSimpleGUI as sg
from pathlib import Path
from send2trash import send2trash

def main():
    # Primary window used to select directory to be scanned for duplicate files
    btn_pad = ((6, 0), (10, 0))
    sg.theme('LightGreen5')
    layout1 = [
        [sg.Input('Select or enter a folder to scan ',key='selected_folder')],
        [sg.Button('Scan',pad=btn_pad),sg.FolderBrowse(target='selected_folder',pad=btn_pad)]
    ]

    layout2 = [
        [sg.CB('Subfolders',key='sub_folder')],
        [sg.Text('File ext.')],
        [sg.Multiline(default_text='', size=(9, 3),key='-ext-')]
    ]

    #https://stackoverflow.com/questions/71721158/how-do-i-add-elements-horizontally-instead-of-vertically-in-pysimplegui
    layout = [
    [sg.Column(layout1, vertical_alignment='top'), sg.VSeparator(), sg.Column(layout2, vertical_alignment='top')],
]   

    window = sg.Window('File Deduplicator', layout, grab_anywhere=True)    
    while True:
        event, values = window.read()
        if event in (None, 'Exit'):
            window.close()
            break
        elif event in ('Scan'):
            extension_custom = tuple(values['-ext-'].splitlines())
            if not os.path.exists(values['selected_folder']):
                sg.popup_error('Invalid path/folder')
            else:
                scan_dupe(values['selected_folder'],values['sub_folder'],extension_custom)
                


    window.close()


def scan_progress_bar(file_num):
    # Simple progress bar to monitor scan progress
    layout = [
        [sg.Text('Scanning...')],
        [sg.ProgressBar(max_value=file_num, orientation='h', size=(20,20), key='-PBAR-')],
        [sg.Cancel()]#Currently it does not cancel, idk how to make it to cancel the scan
    ]
    
    window = sg.Window('Scan Progress', layout, grab_anywhere=True, keep_on_top=True)   
        
    return window


def get_hash_file(path):
    with open(path, 'rb') as f:
        hasher = hashlib.md5()
        blocksize = 65536
        buffer = f.read(blocksize)
        while len(buffer) > 0:
            hasher.update(buffer)
            buffer = f.read(blocksize)
    
    return hasher.hexdigest()


def scan_dupe(directory_path, sub_f, tuple_exten):   
    # Setup values for our progress bar
    scan_prog, total = 0, len(os.listdir(directory_path))
    # Setup our progress bar window
    prog_window = scan_progress_bar(total)
    progress_bar = prog_window['-PBAR-']

    unique_files = {}; dupe_files = []
    
    # Loop over our target directory and resident files
    for root, dirs, files in os.walk(directory_path):
        prog_window.read(timeout=0)  # Establish and update our progress bar
        if not sub_f and root != directory_path:
            continue
        for file in files:
            #sort by only the file extension, if are
            if tuple_exten and not file.endswith(tuple_exten):
                continue  
            # Update progress bar for each file
            scan_prog += 1
            progress_bar.update_bar(scan_prog, total)              
            # Get the full file path and hash the file accordingly
            file_path = Path(os.path.join(root, file))            
            file_hash = get_hash_file(file_path)
            # Add unique files to our unique_files Dict
            # As duplicate files are encountered, add them to the dupe_file List
            if file_hash not in unique_files:
                unique_files[file_hash] = file_path
            else:
                dupe_files.append(file_path)

    prog_window.close()  # Close the progress bar window

    if len(dupe_files) > 0: 
        yes_or_no = sg.popup_ok_cancel(f"{len(dupe_files)} files appears to be duplicated.\nWant to delete them?")

        match yes_or_no:
            case 'OK':
                #threadingn to delete files faster and so the main gui doesnt crash (don't respond)
                thread1 = threading.Thread(target=send2trash, args=(dupe_files,))
                thread1.start()
                thread1.join()
                sg.popup(f'{len(dupe_files)} files have been moved to the trash.')
            case _:
                sg.popup_timed('0 files have been moved to the trash.')
    else:
        sg.popup('There are no duplicate items in this folder')


if __name__ == '__main__':
    main()
    