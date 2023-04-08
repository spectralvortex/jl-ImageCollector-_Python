# jl-ImageCollector-_Python

A simple script to copy images from a source folder and all its subfolders to a target folder without the subfolders (all collected in only one target folder).

The script will skip images that are already in the target folder, even if they have a different name. This is useful if you have a folder with a lot of images and you want to copy them to another folder, but you don't want to copy duplicates.

Usage:
1. Run the python file: jl_image_collector.py
2. In the user interface:
	1. Select the source folder (the folder with the images you want to copy).
	2. Select the target folder (the folder where you want to copy the images).
	3. Click "Start Copy".
3. Wait for the script to finish and close the window.
4. The copied images, together with a log file with all the images initially found, is now in the target folder.

This code is made in cooperation with GPT-4 and GitHub Copilot.
This code is released under the MIT license.

Author: Jan Lægreid, CPT-4, GitHub Copilot - 2023
