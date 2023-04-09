import os
import shutil
import hashlib
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
import datetime

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
            try:
                if file.lower().endswith(extensions):
                    images.append(os.path.join(root, file))
            except Exception:
                pass
    return images


def copy_image_if_unique(image, target_folder, target_hashes):
    image_hash = md5(image)
    if image_hash not in target_hashes:
        shutil.copy2(image, target_folder)
        target_hashes.add(image_hash) # Update the hash list
        return True
    return False


def browse_source():
    source_folder = filedialog.askdirectory()
    source_folder_var.set(source_folder)

def browse_target():
    target_folder = filedialog.askdirectory()
    target_folder_var.set(target_folder)


def start_copy():

    source_folder = source_folder_var.get()
    target_folder = target_folder_var.get()
    extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')

    images = find_images_in_folder(source_folder, extensions)
    progress_bar['maximum'] = len(images)
    copied_count = 0
    target_hashes = {md5(os.path.join(target_folder, f)) for f in os.listdir(target_folder)}

    # Log the image list to a file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_name = f"Images_processed_{timestamp}.txt"
    log_file_path = os.path.join(target_folder, log_file_name)  # Save the log file in the target folder
    with open(log_file_path, "w") as log_file:
        for image in images:
            log_file.write(f"{image}\n")

    # Copy the images
    for i, image in enumerate(images):
        copied = copy_image_if_unique(image, target_folder, target_hashes) # Copy the image if it's unique
        if copied:
            copied_count += 1
        progress_bar['value'] = i + 1
        root.update_idletasks()

    result_text_var.set(f"Copied {copied_count} new images to {target_folder}")


root = tk.Tk()
root.title(r"jl{ImageCollector} v0.1")

source_folder_var = tk.StringVar()
target_folder_var = tk.StringVar()
result_text_var = tk.StringVar()

frame = tk.Frame(root, padx=10, pady=10)
frame.pack()

tk.Label(frame, text="Source Folder:").grid(row=0, column=0, sticky=tk.W)
tk.Entry(frame, textvariable=source_folder_var, width=60).grid(row=0, column=1, padx=5)
tk.Button(frame, text="Browse", command=browse_source).grid(row=0, column=2)

tk.Label(frame, text="Target Folder:").grid(row=1, column=0, sticky=tk.W)
tk.Entry(frame, textvariable=target_folder_var, width=60).grid(row=1, column=1, padx=5)
tk.Button(frame, text="Browse", command=browse_target).grid(row=1, column=2)

tk.Button(frame, text="Start Copy", command=start_copy).grid(row=2, column=1, pady=10)
tk.Label(frame, textvariable=result_text_var).grid(row=3, column=0, columnspan=3)

progress_bar = ttk.Progressbar(frame, orient=tk.HORIZONTAL, mode='determinate')
progress_bar.grid(row=4, column=0, columnspan=3, pady=0, sticky=tk.W+tk.E)


root.mainloop()