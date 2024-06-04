import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pytube import YouTube, Search
from PIL import Image, ImageTk
import requests
import io
import threading
import platform
import os
from pathlib import Path

os_type = platform.system()

class YouTubeDownloader(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Downloader")
        self.geometry("800x600")
        self.configure(bg="#ffffff")

        self.style = ttk.Style(self)
        self.quality_var = tk.StringVar(value="720p")
        self.theme_var = tk.StringVar(value="Light")
        self.download_location = tk.StringVar(value=str(Path.home() / 'Downloads/YouTube'))

        self.create_widgets()
        self.create_menu()
        self.current_options_frame = None  # Track the current download options frame

    def create_widgets(self):
        # Search bar
        self.search_var = tk.StringVar()
        search_frame = ttk.Frame(self, padding="10")
        search_frame.pack(fill=tk.X)

        # YouTube-like search bar style
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=70)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.search_entry.bind("<Return>", lambda event: self.search_videos())

        self.search_button = ttk.Button(search_frame, text="Search", command=self.search_videos)
        self.search_button.pack(side=tk.RIGHT)

        # Results frame with scrollbar
        self.canvas = tk.Canvas(self)
        self.results_frame = ttk.Frame(self.canvas)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.create_window((0, 0), window=self.results_frame, anchor="nw")

        self.results_frame.bind("<Configure>", lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

    def create_menu(self):
        self.menu = tk.Menu(self)
        self.config(menu=self.menu)

        settings_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Settings", menu=settings_menu)

        theme_menu = tk.Menu(settings_menu, tearoff=0)
        settings_menu.add_cascade(label="Theme", menu=theme_menu)
        theme_menu.add_command(label="Light", command=lambda: self.change_theme("Light"))
        theme_menu.add_command(label="Dark", command=lambda: self.change_theme("Dark"))

        quality_menu = tk.Menu(settings_menu, tearoff=0)
        settings_menu.add_cascade(label="Video Quality", menu=quality_menu)
        qualities = ["1080p", "720p", "480p", "360p", "240p"]
        for quality in qualities:
            quality_menu.add_command(label=quality, command=lambda q=quality: self.set_quality(q))

        settings_menu.add_command(label="Set Download Location", command=self.set_download_location)

    def change_theme(self, theme):
        self.theme_var.set(theme)
        if theme == "Dark":
            self.configure(bg="#1e1e1e")
            self.style.configure("TFrame", background="#1e1e1e")
            self.style.configure("TLabel", background="#1e1e1e", foreground="#ffffff")
            self.style.configure("TButton", background="#333333", foreground="#ffffff")
        else:
            self.configure(bg="#ffffff")
            self.style.configure("TFrame", background="#ffffff")
            self.style.configure("TLabel", background="#ffffff", foreground="#000000")
            self.style.configure("TButton", background="#ffffff", foreground="#000000")

    def set_quality(self, quality):
        self.quality_var.set(quality)

    def set_download_location(self):
        directory = filedialog.askdirectory()
        if directory:
            self.download_location.set(directory)

    def search_videos(self):
        query = self.search_var.get()
        threading.Thread(target=self.search_thread, args=(query,)).start()

    def search_thread(self, query):
        self.search_button.config(text="Loading...", state="disabled")
        try:
            search = Search(query)
            self.display_results(search.results)
        finally:
            self.search_button.config(text="Search", state="normal")

    def display_results(self, results):
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        for video in results:
            frame = ttk.Frame(self.results_frame)
            frame.pack(fill=tk.X, padx=20, pady=10)

            # Thumbnail
            thumbnail_url = video.thumbnail_url
            response = requests.get(thumbnail_url)
            img_data = response.content
            img = Image.open(io.BytesIO(img_data))
            img = img.resize((120, 90), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            thumbnail_label = ttk.Label(frame, image=photo)
            thumbnail_label.image = photo  # keep a reference
            thumbnail_label.pack(side=tk.LEFT)

            # Meta-data
            meta_frame = ttk.Frame(frame)
            meta_frame.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
            title_label = ttk.Label(meta_frame, text=video.title, wraplength=400)
            title_label.pack(anchor=tk.W, fill=tk.X, expand=True)

            # Fixed position download button
            download_button = ttk.Button(meta_frame, text="Download", command=lambda v=video, f=frame: self.download_options(v, f))
            download_button.pack(anchor=tk.E)

            # Store video URL in metadata
            meta_frame.video_url = video.watch_url

    def download_options(self, video, frame):
        # Close the previous options frame if any
        if self.current_options_frame:
            self.current_options_frame.destroy()

        options = ttk.Frame(frame)
        options.pack(anchor=tk.E)
        self.current_options_frame = options  # Track the current options frame

        audio_button = ttk.Button(options, text="Audio", command=lambda: self.download_video(video, audio=True, options=options, frame=frame))
        audio_button.pack(side=tk.LEFT, padx=5)

        video_button = ttk.Button(options, text="Video", command=lambda: self.download_video(video, audio=False, options=options, frame=frame))
        video_button.pack(side=tk.LEFT, padx=5)

        frame.video_url = video.watch_url

    def download_video(self, video, audio=False, options=None, frame=None):
        if options:
            options.destroy()
            self.current_options_frame = None  # Reset current options frame
        threading.Thread(target=self.download_thread, args=(video, audio, frame)).start()

    def download_thread(self, video, audio, frame):
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(frame, variable=progress_var, maximum=100)
        progress_bar.pack(fill=tk.X, padx=5, pady=5)

        def update_progress(stream, chunk, bytes_remaining):
            total_size = stream.filesize
            bytes_downloaded = total_size - bytes_remaining
            percentage = (bytes_downloaded / total_size) * 100
            progress_var.set(percentage)

        video_url = frame.video_url  # Get video URL from frame's metadata

        try:
            yt = YouTube(video_url, on_progress_callback=update_progress)
            if audio:
                self.audio_downloader(yt, progress_var)
            else:
                self.video_downloader(yt, progress_var)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def audio_downloader(self, yt, progress_var):
        downloads_path = self.download_location.get()
        name = yt.title
        name = name.replace('\\', '').replace('/', '')
        new_name = f'{name}.mp3'

        def download_audio():
            yt.streams.get_audio_only().download(filename=new_name, output_path=downloads_path)
            messagebox.showinfo("Download Complete", f"Downloaded: {new_name}")

        download_thread = threading.Thread(target=download_audio)
        download_thread.start()

    def video_downloader(self, yt, progress_var):
        downloads_path = self.download_location.get()
        name = yt.title
        name = name.replace('\\', '').replace('/', '')
        new_name = f'{name}.mp4'

        def download_video():
            yt.streams.get_highest_resolution().download(filename=new_name, output_path=downloads_path)
            messagebox.showinfo("Download Complete", f"Downloaded: {new_name}")

        download_thread = threading.Thread(target=download_video)
        download_thread.start()

if __name__ == "__main__":
    app = YouTubeDownloader()
    app.mainloop()
