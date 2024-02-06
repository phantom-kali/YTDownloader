import tkinter as tk
from tkinter import ttk, Entry, Label
from pytube import YouTube
from pathlib import Path
from threading import Thread
import platform
import os

os_type = platform.system()

downloads_path = ""  # Define downloads_path as a global variable
new_name = ""  # Define new_name as a global variable

def video_downloader():
    global downloads_path, new_name  # Use the global variables

    url = link_entry.get().strip()

    if not url:
        status_label.config(text="Please enter a YouTube link.", fg="red", font=16)
        return

    downloads_path = str(Path.home() / 'Videos/YouTube')
    video = YouTube(url)
    name = video.title
    name = name.replace('\\', '').replace('/', '')

    new_name = f'{name}.mp4'

    # Update status label before download
    status_label.config(text="Downloading Video...", fg="green", font=16)

    def download_video():
        global downloads_path, new_name  # Use the global variables
        video.streams.get_highest_resolution().download(filename=new_name, output_path=downloads_path)
        status_label.config(text=f"Downloaded: {new_name}")
        open_button.config(state=tk.NORMAL)  # Enable the open button

    # Run download in a separate thread to avoid GUI freezing
    download_thread = Thread(target=download_video)
    download_thread.start()

def audio_downloader():
    global downloads_path, new_name  # Use the global variables

    url = link_entry.get().strip()

    if not url:
        status_label.config(text="Please enter a YouTube link.", fg="red", font=16)
        return

    downloads_path = str(Path.home() / 'Music/YouTube')
    video = YouTube(url)
    name = video.title
    name = name.replace('\\', '').replace('/', '')

    new_name = f'{name}.mp3'

    # Update status label before download
    status_label.config(text="Downloading Audio...", fg="green", font=16)

    def download_audio():
        global downloads_path, new_name  # Use the global variables
        video.streams.get_audio_only().download(filename=new_name, output_path=downloads_path)
        status_label.config(text=f"Downloaded: {new_name}")
        open_button.config(state=tk.NORMAL)  # Enable the open button

    # Run download in a separate thread to avoid GUI freezing
    download_thread = Thread(target=download_audio)
    download_thread.start()

def open_file():
    global downloads_path, new_name  # Use the global variables

    if not downloads_path or not new_name:
        status_label.config(text="No file has been downloaded yet.", fg="red", font=16)
        return

    # Get the path of the downloaded file
    file_path = os.path.join(downloads_path, new_name)

    # Open the file using the default system application
    if os_type.lower() == "linux":
        try:    
            os.system(f"xdg-open '{file_path}'")
        except:
            pass
    elif os_type.lower() == "windows":
        try:
            os.system(f"start '{file_path}'")
        except:
            pass

# GUI setup
root = tk.Tk()
root.title("YouTube Downloader")
root.resizable(False, False)  # Set resizable to False

# Set dark background color for the window
root.configure(bg="#333333")

# Create a ttk style for rounded buttons with dark colors
style = ttk.Style()
style.configure("Rounded.TButton",
                borderwidth=1,
                relief="flat",
                foreground="white",
                background="#00008B",  # Dark blue color
                font=('Helvetica', 10, 'bold'),
                highlightbackground="#00004B",  # Adjust this to a darker shade
                highlightcolor="#00004B")  # Adjust this to a darker shade

# Link Entry
link_label = Label(root, text="Enter YouTube Link:", bg="#333333", fg="white")
link_label.pack(pady=5)

link_entry = Entry(root, width=50, font=('Helvetica', 10), borderwidth=5, relief="groove")
link_entry.pack(pady=5)

# Video Download Button
video_button = ttk.Button(root, text="Download Video", command=video_downloader, style="Rounded.TButton")
video_button.pack(pady=10)

# Audio Download Button
audio_button = ttk.Button(root, text="Download Audio", command=audio_downloader, style="Rounded.TButton")
audio_button.pack(pady=10)

# Open Button
open_button = ttk.Button(root, text="Open Downloaded File", command=open_file, state=tk.DISABLED, style="Rounded.TButton")
open_button.pack(pady=10)

# Status Label
status_label = Label(root, text="", bg="#333333", fg="white")
status_label.pack(pady=10)

root.mainloop()
