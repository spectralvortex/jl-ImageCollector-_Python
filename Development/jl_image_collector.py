import os
import shutil
import hashlib
import threading
import datetime
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox

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

def md5(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def find_images_in_folder(source_folder, extensions):
    images = []
    for root, _, files in os.walk(source_folder):
        for file in files:
            if file.lower().endswith(extensions):
                images.append(os.path.join(root, file))
    return images


def copy_image_if_unique(image, target_folder, target_hashes) -> str:

    image_hash = md5(image)

    if image_hash not in target_hashes:
        # Generate a unique destination filename
        basename = os.path.basename(image)
        filename, extension = os.path.splitext(basename)
        destination_image = os.path.join(target_folder, basename)

        index = 1
        while os.path.exists(destination_image):
            new_basename = f"{filename}({index}){extension}"
            destination_image = os.path.join(target_folder, new_basename)
            index += 1 
        try:
            # Copy the image and update the hash list.
            shutil.copy2(image, destination_image)
            target_hashes.add(image_hash) # Update the hash list
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


def start_copy():

    global progress_value

    timestamp_start = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    timestamp_start_text.set(f"Start time: {timestamp_start}")

    source_folder = source_folder_var.get()
    target_folder = target_folder_var.get()

    if not os.path.isdir(source_folder) or not os.path.isdir(target_folder):
        messagebox.showerror("Error", "Both source and target folders must be valid directories.")
        return

    progress_value.set(0)
    progress_bar["maximum"] = 100  # Set maximum progress value

    # Copy in a separate thread.
    def copy_thread():
        extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.esp', '.raw', '.cr2', '.nef', '.orf', '.sr2')
        images = find_images_in_folder(source_folder, extensions)

        result_text_var.set(f"Found {len(images)} images in {source_folder}.\nCopying images to {target_folder}...")

        target_hashes = { md5(os.path.join(target_folder, f)) for f in os.listdir(target_folder) if f.lower().endswith(extensions) }

        copied_ok_count = 0
        copied_skipped_count = 0
        copy_error_count = 0
  
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_name = f"Images_processed_{timestamp}.txt"
        log_file_path = os.path.join(target_folder, log_file_name)  # Save the log file in the target folder
       
        with open(log_file_path, "w", encoding='utf-8', newline='') as log_file:

            for index, image in enumerate(images):

                # Copy the image if it is unique, and write to the log file.
                copy_result = copy_image_if_unique(image, target_folder, target_hashes)
                if copy_result == 'Copied':
                    log_file.write(f"{image} --> OK\n".encode('utf-8').decode('utf-8'))
                    copied_ok_count += 1
                elif copy_result == 'Duplicate':
                    log_file.write(f"{image} --> Skipped (duplicate)\n".encode('utf-8').decode('utf-8'))
                    copied_skipped_count += 1
                else:
                    # Error copying image
                    log_file.write(f"{image} --> !{copy_result}\n".encode('utf-8').decode('utf-8')) # Write error message to log file
                    copy_error_count += 1

                progress_value.set(int((index + 1) / len(images) * 100))  # Update progress value (0-100) -> in percent.
                root.update_idletasks()  # Update progress bar

        progress_value.set(100)  # Set progress value to 100

        update_text(f"Copied {copied_ok_count} new images to the target folder.\n\n" +
                    f"Skipped {copied_skipped_count} images that already existed in the target folder.\n\n" +
                    f"Error copying {copy_error_count} images.\n\n" +
                    f"Log file saved to the following file in the target folder:\n--> {log_file_name}.")

        timestamp_finnished = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        timestamp_finnished_text.set(f"End time:  {timestamp_finnished}")

        # Re-enable the Start Copy button at the end of the thread.
        start_copy_button.config(state=tk.NORMAL)

    # Start the copy thread.
    threading.Thread(target=copy_thread).start()
    # Disable the Start Copy button while the thread is running.
    start_copy_button.config(state=tk.DISABLED)


# Update the content of the Text widget
def update_text(content):
    text_widget.config(state=tk.NORMAL) # Enable editing
    text_widget.delete(1.0, tk.END) # Clear the existing content
    text_widget.insert(tk.END, content)
    text_widget.config(state=tk.DISABLED) # Disable editing


# GUI ---------------------------------------------------------------------------------------------

root = tk.Tk()
root.title(r"jl{ImageCollector} v0.1")


source_folder_var = tk.StringVar()
target_folder_var = tk.StringVar()
result_text_var = tk.StringVar()
timestamp_start_text = tk.StringVar()
timestamp_finnished_text = tk.StringVar()
progress_value = tk.IntVar()

frame = tk.Frame(root, padx=10, pady=10)
frame.pack()


tk.Label(frame, text="Source Folder:").grid(row=0, column=0, sticky=tk.W)
tk.Entry(frame, textvariable=source_folder_var, width=100).grid(row=0, column=1, padx=5)
tk.Button(frame, text="Browse", command=browse_source).grid(row=0, column=2)

tk.Label(frame, text="Target Folder:").grid(row=1, column=0, sticky=tk.W)
tk.Entry(frame, textvariable=target_folder_var, width=100).grid(row=1, column=1, padx=5)
tk.Button(frame, text="Browse", command=browse_target).grid(row=1, column=2)


start_copy_button = tk.Button(frame, text="Start Copy", command=start_copy)
start_copy_button.grid(row=2, column=1, pady=10)
start_copy_button.config(state=tk.NORMAL) # Disable the Start Copy button until source and target folders are selected.

text_widget = tk.Text(frame, wrap=tk.WORD, width=90, height=8, font=("Arial", 9))
text_widget.grid(row=3, column=0, columnspan=3, pady=10, sticky=tk.W+tk.E) # Adjust row and column as needed
text_widget.config(state=tk.DISABLED) # Disable editing

progress_bar = ttk.Progressbar(frame, orient=tk.HORIZONTAL, mode='determinate', variable=progress_value)
progress_bar.grid(row=4, column=0, columnspan=3, pady=0, sticky=tk.W+tk.E)

tk.Label(frame, textvariable=timestamp_start_text).grid(row=5, column=0, columnspan=3, sticky=tk.W)
tk.Label(frame, textvariable=timestamp_finnished_text).grid(row=6, column=0, columnspan=3, sticky=tk.W)


root.mainloop()