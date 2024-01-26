import tkinter as tk
from tkinter import Entry, Button, Label
from pytube import YouTube
from pathlib import Path
from threading import Thread

class YouTubeDownloaderApp:
    def __init__(self, master):
        self.master = master
        master.title("YouTube Downloader")

        # Link Entry
        self.link_label = Label(master, text="Enter YouTube Link:")
        self.link_label.pack(pady=10)

        self.link_entry = Entry(master, width=50)
        self.link_entry.pack(pady=10)

        # Video Download Button
        self.video_button = Button(master, text="Download Video", command=self.video_downloader)
        self.video_button.pack(pady=10)

        # Audio Download Button
        self.audio_button = Button(master, text="Download Audio", command=self.audio_downloader)
        self.audio_button.pack(pady=10)

        # Status Label
        self.status_label = Label(master, text="")
        self.status_label.pack(pady=10)

    def video_downloader(self):
        url = self.link_entry.get()
        downloads_path = str(Path.home() / 'Videos/YouTube')
        video = YouTube(url)
        name = self.clean_filename(video.title)
        new_name = f'{name}.mp4'

        # Update status label before download
        self.status_label.config(text="Downloading Video...")

        # Run download in a separate thread to avoid GUI freezing
        download_thread = Thread(target=self.download_video, args=(video, new_name, downloads_path))
        download_thread.start()

    def audio_downloader(self):
        url = self.link_entry.get()
        downloads_path = str(Path.home() / 'Music/YouTube')
        video = YouTube(url)
        name = self.clean_filename(video.title)
        new_name = f'{name}.mp3'

        # Update status label before download
        self.status_label.config(text="Downloading Audio...")

        # Run download in a separate thread to avoid GUI freezing
        download_thread = Thread(target=self.download_audio, args=(video, new_name, downloads_path))
        download_thread.start()

    def download_video(self, video, new_name, downloads_path):
        video.streams.get_highest_resolution().download(filename=new_name, output_path=downloads_path)
        self.status_label.config(text=f"Downloaded: {new_name}")

    def download_audio(self, video, new_name, downloads_path):
        video.streams.get_audio_only().download(filename=new_name, output_path=downloads_path)
        self.status_label.config(text=f"Downloaded: {new_name}")

    @staticmethod
    def clean_filename(name):
        return name.replace('\\', '').replace('/', '')

# GUI setup
root = tk.Tk()
app = YouTubeDownloaderApp(root)
root.mainloop()
