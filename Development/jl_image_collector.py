import os
import shutil
import hashlib
import threading
import datetime
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from Helpers.byte_unit_converter import format_unit_4_byte_size

# This is a simple script to copy images from a source folder and all its subfolders
# to a target folder without the subfolders (all collected in only one target folder).
# The script will skip images that are already in the target folder, even if they
# have a different name. This is useful if you have a folder with a lot of images and 
# you want to copy them to another folder, but you don't want to copy duplicates.
#
# Usage:
# 1. Run the python file: jl_image_collector.py
# 2. In the user interface:
# 	a. Select the source folder (the folder with the images you want to copy)
# 	b. Select the target folder (the folder where you want to copy the images)
# 	c. Click "Start Copy"
# 4. Wait for the script to finish and close the window
# 5. The copied images, together with a log file with all the images initially 
#    found, is now in the target folder.
#
# This code is made in cooperation with GPT-4 and GitHub Copilot.
# This code is released under the MIT license.
#
# Author: Jan Lægreid, CPT-4, GitHub Copilot - 2023


class FileTypes2Copy:
    # This class is used to store the file types that can be selected.

    def __init__(self):
        super().__init__()

        # Define the possible file extensions.

        images = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.esp', '.raw', '.cr2', '.nef', '.orf', '.sr2')

        videos = ('.mp4', '.avi', '.mov', '.thm', '.wmv', '.flv', '.webm', '.mkv', '.m4v', '.mpg', '.mpeg', '.3gp', '.3g2', '.mxf', 
                '.mts', '.m2ts', '.ts', '.vob', '.m2v', '.asf', '.rm', '.rmvb', '.ogv', '.ogm', '.ogx', '.qt', '.divx', '.xvid')
        
        # Define the possible file types.
        types_texts = ('images', 'videos', 'images and videos')

        # Define the file type dictionary.
        file_type_dict = {
                            types_texts[0] : images,
                            types_texts[1] : videos,
                            types_texts[2] : images + videos
                        }

        # Set the values for the class properties.
        self._file_types = types_texts
        self._file_types_extentions = file_type_dict

    @property
    def file_types(self) -> tuple:
        return self._file_types

    @property
    def file_types_extentions(self) -> dict:
        return self._file_types_extentions

class FileCopyingCurrentStatusTextDict():
    # This class is used to store the current status text for the file copying process.

    def __init__(self, status_text="", folder_text="", file_text=""):
        super().__init__()
        self._status_text = status_text
        self._folder_text = folder_text
        self._file_text = file_text

    @property
    def status_text(self):
        return self._status_text

    @status_text.setter
    def status_text(self, value):
        self._status_text = value

    @property
    def folder_text(self):
        return self._folder_text
    
    @folder_text.setter
    def folder_text(self, value):
        self._folder_text = value

    @property
    def file_text(self):
        return self._file_text
    
    @file_text.setter
    def file_text(self, value):
        self._file_text = value



def md5(file_path: str) -> str:
    # Calculate the MD5 hash of a file.
    # Return the MD5 hash as a string.

    hash_md5 = hashlib.md5()
    try:

        with open(file_path, "rb") as f:

            if os.path.getsize(file_path) == 0:
                return hash_md5.hexdigest()

            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)

    except Exception as e:

        print(f"Error reading file: {e}")
        return hashlib.md5().hexdigest()
    
    return hash_md5.hexdigest()


def read_hashes_from_file(file_path: str) -> set:
    # Read the hashes from a file.
    # Return a set with the hashes.
    hashes = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                hashes.add(line.strip())
    except FileNotFoundError:
        print(f"Warning: Hash file not found: {file_path}")
    except PermissionError as e:
        print(f"Warning: Could not read hashes from file '{file_path}'. Error: {e}")
    return hashes


def save_hashes_to_file(file_path: str, hashes: set) -> bool:
    # Save the hashes to a file.
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            for h in hashes:
                f.write(f"{h}\n")
    except PermissionError as e:
        print(f"Warning: Could not save hashes to file '{file_path}'. Error: {e}")
        return False
    return True


        
def find_files_in_folder(source_folder: str, extensions, forbidden_paths_file: str, folders_2_avoid: list=[], min_file_size_kb: int=0) -> tuple:
    # Find all files in a folder and its subfolders that match the specified extensions.
    # Avoid folders that are in the folders_2_avoid list.
    # Avoid files that have a path starting with any of the forbidden paths in the database file.
    # Return a tuple with a list of all files found and the total size of all files found.

    
    # Read the forbidden paths from the database file and store them in a set.
    forbidden_paths = set()
    try:
        with open(forbidden_paths_file, 'r', encoding='utf-8') as f:
            
            for line in f:
                forbidden_paths.add(line.strip().replace('\\', '/'))

    except (FileNotFoundError, PermissionError) as e:
        print(f"Warning: Could not read forbidden paths from file '{forbidden_paths_file}'. Error: {e}")


    files_found = []
    total_files_size_bytes = 0
    file_count = 0
    files_found_count = 0
    progress_text = FileCopyingCurrentStatusTextDict()

    # Loop through all files in the source folder and its subfolders
    for root, _, files in os.walk(source_folder):

        for file in files:

            file_count += 1

            # Set some status text to give feedback to the user.
            progress_text.status_text = f"Number of files investegated: {file_count}"
            
            if os.path.basename(root) in folders_2_avoid:
                continue

            file_path = os.path.join(root, file)
            
            # Check if the file's path starts with any of the forbidden paths, and if so, skip the file
            if any(file_path.replace('\\', '/').startswith(forbidden_path) for forbidden_path in forbidden_paths):
                continue

            # Check if the file's extension is in the list of extensions to look for.
            if os.path.splitext(file)[1].lower() in extensions:
                
                file_size_bytes = os.path.getsize(file_path)
                total_files_size_bytes += file_size_bytes

                file_size_kb = file_size_bytes / 1024
                
                # Check if the file is larger than the minimum file size.
                if (min_file_size_kb > 0 and file_size_kb >= min_file_size_kb) or (min_file_size_kb == 0 and file_size_kb > 0):
                    # Add the file to the list of files found, since it is larger than the minimum file size.
                    files_found.append(file_path)
                    files_found_count += 1
                else:
                    # Add the file to the list of files found, but with a note that it is too small.
                    files_found.append( f"{file_path} --> Too small ({file_size_kb} kb)" )
                    # Because of the note "--> Too small", the file is not counted as found, allthough it is added to the list of files found.

            # Update the status text to give feedback to the user.
            progress_text.folder_text = f"Files found: {files_found_count}"
            progress_text.file_text = ""

            # Yield the current status text to the caller.
            set_current_status_text(progress_text)
            

    # Format the total size of all files found, so that it is easier to read.
    # The format_unit_4_byte_size function returns a tuple with the formatted size and the unit used.
    total_files_size_formatted = format_unit_4_byte_size(total_files_size_bytes)

    # Return the list of files found and the total size of all files found as a tuple.
    return (files_found, total_files_size_formatted)


def copy_file_if_unique(file, target_folder: str, target_hashes: set, hash_file_path: str) -> str:
    # Check if the file is unique (not already in the target folder) and copy it if it is.
    # Return a string with the status of the copy operation.

    # Get the MD5 hash of the file.
    file_hash = md5(file)

    # Check if the file is unique - if it is, copy it to the target folder.
    if file_hash not in target_hashes:
        # Generate a unique destination filename
        basename = os.path.basename(file)
        filename, extension = os.path.splitext(basename)
        destination_file = os.path.join(target_folder, basename)

        index = 1
        while os.path.exists(destination_file):
            new_basename = f"{filename}({index}){extension}"
            destination_file = os.path.join(target_folder, new_basename)
            index += 1 
        try:
            # Copy the image and update the hash list.
            shutil.copy2(file, destination_file)
            target_hashes.add(file_hash) # Update the hash list
            save_hashes_to_file(hash_file_path, target_hashes)  # Save the target hashes to a file.
            return 'Copied'
        except Exception as e:
            return f"Error copying: {e}"
    else:
        return 'Duplicate'


def browse_source():
    source_folder = filedialog.askdirectory()
    source_folder_var.set(source_folder)

def browse_target():
    target_folder = filedialog.askdirectory()
    target_folder_var.set(target_folder)

def browse_forbidden_paths_file():
    forbidden_paths_file = filedialog.askopenfilename()
    forbidden_paths_file_var.set(forbidden_paths_file)


# Update the content of the Text widget used for displaying the log.
def set_current_status_text(progress_info_text: FileCopyingCurrentStatusTextDict):
    progress_bar_info_text_current_status.set(progress_info_text.status_text)
    progress_bar_info_text_current_folder.set(progress_info_text.folder_text)
    progress_bar_info_text_current_file.set(progress_info_text.file_text)
    root.update_idletasks()


# Update progress bar value and progress bar info text.
def update_progress(progress_index, total, info_text_ending, file) -> int:
    progress_text = FileCopyingCurrentStatusTextDict()
    progress_index += 1
    progress_percent = (progress_index) / total * 100
    progress_text.status_text = f"{progress_percent:.2f}% ({progress_index}/{total}) {info_text_ending}"
    progress_text.folder_text = f"-> Folder: {os.path.dirname(file)}"
    progress_text.file_text = f"-> File: {os.path.basename(file)}"

    progress_bar_value.set(progress_percent)  # Update progress value (0-100) -> in percent.
    set_current_status_text(progress_text)  # Update progress bar info text
    
    root.update_idletasks()  # Update progress bar
    return progress_index


# Update the content of the Text widget
def update_log_text_panel(text_content: str):
    text_widget.config(state=tk.NORMAL) # Enable editing
    text_widget.delete(1.0, tk.END) # Clear the existing content
    text_widget.insert(tk.END, text_content)
    text_widget.config(state=tk.DISABLED) # Disable editing



def start_copy():

    # Get start time and update the start time text.
    timestamp_start = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    timestamp_start_text.set(f"Start time: {timestamp_start}")

    # Get source and target folder.
    source_folder = source_folder_var.get()
    target_folder = target_folder_var.get()
    forbidden_paths_file = forbidden_paths_file_var.get()

    # Check if source and target folder are valid directories.
    if not os.path.isdir(source_folder) or not os.path.isdir(target_folder):
        messagebox.showerror("Error", "Both source and target folders must be valid directories.")
        return

    # Initialize progress bar and progress bar info text.
    progress_bar_value.set(0)
    progress_bar["maximum"] = 100  # Set maximum progress value
    progress_bar_info_text_current_status.set("Initializing...")

    # Copy in a separate thread.
    def copy_thread():

        hash_file_folder_name = "hashes"
        hash_file_path = os.path.join(target_folder, hash_file_folder_name )
        os.makedirs(hash_file_path, exist_ok=True)  # Create the log_files folder if it doesn't exist
        hash_file_path = os.path.join(hash_file_path, "hashes.jllog") # Path to the file containing the hashes of the files in the target folder.

        # Define the folders to avoid.
        folders_2_avoid = ('__pycache__', 'node_modules', 'venv', '.git', '.vscode', '.idea', 'dist', 'build', 'cache', 'logs', 'temp',
                            'tmp', 'temp', 'tmp', 'thumbs', 'thumbnails', 'thumbs.db', 'desktop.ini', 'thumbs.db:encryptable', 'thumbs.db:encryptable$')
        
        # Get the file types to copy as string from the format selector combobox and
        # get the proper file extensions from the selected file types to copy ('images', 'videos', 'images and videos')
        # to use for the file search.
        selected_file_types_to_copy = format_selector_var.get()
        extensions = FileTypes2Copy().file_types_extentions[selected_file_types_to_copy]
        
        # Get all files in the source folder and calculate the total number of files and the total file size -> to be used for the progress bar.
        files, total_files_size_formated = find_files_in_folder(source_folder, extensions, forbidden_paths_file, folders_2_avoid)
        # total_files_size_mb = round(total_files_size  / 1024, 2) # files_and_total_files_sizes[1] contains the total file sizes in kb -> convert to MB and round to 2 decimals.
        
        # Update the log text panel with the initial status text.
        initial_status_log_text = (f"Found {len(files)} {selected_file_types_to_copy} in {source_folder}.\n" \
                                   f"Total of {total_files_size_formated['value']} {total_files_size_formated['unit']}.\n" \
                                   f"Harvesting file hashes for files already in the target folder...")
        update_log_text_panel(initial_status_log_text)
        
        progress_index= 0
        target_hashes = set()

        # Check if the user wants to update the hash list from scratch.
        if update_hash_list_from_scratch_var.get() == False:
            # Read the target hashes from the file with the saved hashes.
            target_hashes = read_hashes_from_file(hash_file_path)
        
        if not target_hashes:
            # Get all files in the target folder and calculate the total number of files -> to be used for the progress bar.
            target_files = [f for f in os.listdir(target_folder) if f.lower().endswith(extensions)]
            total_target_files = len(target_files)
            # Calculate the md5 hash for each file in the target folder and store it in a set while updating the progress bar.
            target_hashes = set()
            for f in target_files:
                file_path = os.path.join(target_folder, f)
                target_hashes.add(md5(file_path)) # Add the md5 hash to the set.
                save_hashes_to_file(hash_file_path, target_hashes)  # Save the target hashes to a file.
                progress_index = update_progress(progress_index, total_target_files, "- md5 hash",f)
        
        # Create a log folder in the target folder
        log_folder_name = "log_files"
        log_folder_path = os.path.join(target_folder, log_folder_name )
        os.makedirs(log_folder_path, exist_ok=True)  # Create the log_files folder if it doesn't exist
        # Create a log file name with a timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_name = f"Files_processed_{timestamp}.txt"
        # Save the log file in the log_files folder
        log_file_path = os.path.join(log_folder_path, log_file_name)  

        # Update the log text panel
        initial_status_log_text += (f"\nCopying files...")
        update_log_text_panel(initial_status_log_text)

        # Initialize counters.
        copied_ok_count = 0
        copied_skipped_count = 0
        copy_error_count = 0
        file_size_copied_sum = 0
        
        # Iteriate through the files and copy them to the target folder while logging the results.
        with open(log_file_path, "w", encoding='utf-8', newline='') as log_file:
            
            # Iterate through the files
            for index, f in enumerate(files):

                # Copy the image if it is actually on the disk and unique, 
                # and write to the log file.

                #Check if file_name/path contains "--> Too small" at the end, and logs it and skip if it does.
                if "--> Too small" in f:
                    log_file.write(f"{f}\n".encode('utf-8').decode('utf-8'))
                    copied_skipped_count += 1
                    continue #Skips to the next iteration of the loop.

                #Copy the file if it is unique, and write to the log file.
                copy_result = copy_file_if_unique(f, target_folder, target_hashes, hash_file_path)
                if copy_result == 'Copied':
                    log_file.write(f"{os.path.normpath(f)} --> OK\n".encode('utf-8').decode('utf-8'))
                    copied_ok_count += 1
                    file_size_copied_sum += os.path.getsize(f)
                elif copy_result == 'Duplicate':
                    log_file.write(f"{os.path.normpath(f)} --> Skipped (duplicate)\n".encode('utf-8').decode('utf-8'))
                    copied_skipped_count += 1
                else:
                    # Error copying file
                    log_file.write(f"{os.path.normpath(f)} --> !{copy_result}\n".encode('utf-8').decode('utf-8')) # Write error message to log file
                    copy_error_count += 1
                
                # Update the progress bar and status text.
                update_progress(index, len(files), "copying", f)

            # Set progress bar to 100% and update status text to "Finished!"
            progress_bar_value.set(100)  # Set progress value to 100
            set_current_status_text(FileCopyingCurrentStatusTextDict(status_text="Finished!"))

            total_bytes_copied = format_unit_4_byte_size(file_size_copied_sum)

            # Create the summary text and update the log text panel.
            initial_status_log_text += f"\nCopied {copied_ok_count} new {selected_file_types_to_copy} to the target folder" + \
                                      f" --> {total_bytes_copied['value']} {total_bytes_copied['unit']} total.\n" + \
                                      f"Skipped {copied_skipped_count} {selected_file_types_to_copy} duplicates.\n" + \
                                      f"Error copying {copy_error_count} {selected_file_types_to_copy}.\n" + \
                                      f"Log file saved to the following file in the target folder --> \{log_folder_name}\{log_file_name}."
            
            update_log_text_panel(initial_status_log_text)

        # Read the log file and add the summary to the top of the file.
        with open(log_file_path, "r", encoding='utf-8' ) as log_file:
            log_file_content = log_file.read()

        timestamp_finished = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        # Create the summary text.
        process_summary_text = f"Summary:\n------------------------------\n{initial_status_log_text}\n\n" + \
                                f"Start of process: {timestamp_start}\n" + \
                                f"End of process: {timestamp_finished}\n------------------------------\n\n"
        # Add the summary to the top of the log file.
        log_file_content = process_summary_text + log_file_content
        
        # Write the log file with the summary added to the top.
        with open(log_file_path, "w", encoding='utf-8', newline='') as log_file:
            log_file.write(log_file_content.encode('utf-8').decode('utf-8'))

        # Update the timestamp_finished_text variable.
        timestamp_finished_text.set(f"End time:  {timestamp_finished}")

        # Re-enable the Start Copy button at the end of the thread.
        start_copy_button.config(state=tk.NORMAL)

    # Start the copy thread.
    threading.Thread(target=copy_thread).start()
    # Disable the Start Copy button while the thread is running.
    start_copy_button.config(state=tk.DISABLED)


# GUI ---------------------------------------------------------------------------------------------

root = tk.Tk()
root.title(r"jl{ImageCollector} v0.2")
root.geometry("820x420")  # Set the window size
root.resizable(False, False)  # Disable resizing

frame = tk.Frame(root, padx=10, pady=10)
frame.pack()

# Source folder
source_folder_var = tk.StringVar()
tk.Label(frame, text="Source Folder:").grid(row=0, column=0, sticky=tk.W)
tk.Entry(frame, textvariable=source_folder_var, width=90).grid(row=0, column=1, padx=5)
tk.Button(frame, text="Browse", command=browse_source).grid(row=0, column=2)

# Target folder
target_folder_var = tk.StringVar()
tk.Label(frame, text="Target Folder:").grid(row=1, column=0, sticky=tk.W)
tk.Entry(frame, textvariable=target_folder_var, width=90).grid(row=1, column=1, padx=5)
tk.Button(frame, text="Browse", command=browse_target).grid(row=1, column=2)

# Forbidden pats file
forbidden_paths_file_var = tk.StringVar()
tk.Label(frame, text="File containg forbidden paths:").grid(row=2, column=0, sticky=tk.W)
tk.Entry(frame, textvariable=forbidden_paths_file_var, width=90).grid(row=2, column=1, padx=5)
tk.Button(frame, text="Browse", command=browse_forbidden_paths_file).grid(row=2, column=2)

# Checkbox for if the hash list of the target folder should be updated.
update_hash_list_from_scratch_var = tk.IntVar()
update_hash_list_from_scratch_checkbox = tk.Checkbutton(frame, text="Update the hash list from scratch.", variable=update_hash_list_from_scratch_var)
update_hash_list_from_scratch_checkbox.grid(row=3, column=0, columnspan=2, sticky=tk.W)

# File format selector
format_selector_var = tk.StringVar()
format_selector = ttk.Combobox(frame, values=FileTypes2Copy().file_types, textvariable=format_selector_var, width=20)
format_selector.grid(row=3, column=1, padx=5, sticky=tk.E)
format_selector.current(0)

# Start Copy button
start_copy_button = tk.Button(frame, text="Start Copy", command=start_copy)
start_copy_button.grid(row=3, column=2, pady=10)
start_copy_button.config(state=tk.NORMAL) # Disable the Start Copy button until source and target folders are selected.

# Text info panel
text_widget = tk.Text(frame, wrap=tk.WORD, width=90, height=8, font=("Arial", 9))
text_widget.grid(row=4, column=0, columnspan=3, pady=0, sticky=tk.W+tk.E) # Adjust row and column as needed
text_widget.config(state=tk.DISABLED) # Disable editing

# Progress bar
progress_bar_value = tk.IntVar()
progress_bar_info_text_current_status = tk.StringVar()
progress_bar_info_text_current_folder = tk.StringVar()
progress_bar_info_text_current_file = tk.StringVar()
progress_bar = ttk.Progressbar(frame, orient=tk.HORIZONTAL, length= 100, mode='determinate', variable=progress_bar_value)
progress_bar.grid(row=5, column=0, columnspan=3, pady=10, sticky=tk.E+tk.W)
tk.Label(frame, textvariable=progress_bar_info_text_current_status).grid(row=6, column=0, columnspan=3, sticky=tk.W)
tk.Label(frame, textvariable=progress_bar_info_text_current_folder).grid(row=7, column=0, columnspan=3, sticky=tk.W)
tk.Label(frame, textvariable=progress_bar_info_text_current_file).grid(row=8, column=0, columnspan=3, sticky=tk.W)

# Timestamps
timestamp_start_text = tk.StringVar()
timestamp_finished_text = tk.StringVar()
tk.Label(frame, textvariable=timestamp_start_text).grid(row=9, column=0, columnspan=3, sticky=tk.W)
tk.Label(frame, textvariable=timestamp_finished_text).grid(row=10, column=0, columnspan=3, sticky=tk.W)


root.mainloop()