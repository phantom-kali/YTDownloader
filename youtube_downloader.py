import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QFileDialog, QProgressBar, QMenu,
    QMenuBar, QMessageBox
)
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pytube import YouTube, Search
from PIL import Image
import requests
import io
import platform
from pathlib import Path
import os
import subprocess

os_type = platform.system()

class YouTubeDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Downloader")
        self.setGeometry(100, 100, 800, 600)

        self.quality = "720p"
        self.theme = "Light"
        self.download_location = str(Path.home() / 'Downloads/YouTube')

        self.initUI()
        self.create_menu()

        self.search_thread = None
        self.download_threads = []
        self.thumbnail_threads = []
        self.current_progress_bars = {}  # Dictionary to keep track of progress bars by frame

    def initUI(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        search_layout = QHBoxLayout()
        self.search_bar = QLineEdit(self)
        self.search_bar.setPlaceholderText("Search YouTube")
        self.search_bar.returnPressed.connect(self.search_videos)
        search_layout.addWidget(self.search_bar)

        self.search_button = QPushButton("Search", self)
        self.search_button.clicked.connect(self.search_videos)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)
        self.scroll_area.setWidget(self.results_widget)
        layout.addWidget(self.scroll_area)

    def create_menu(self):
        menu_bar = self.menuBar()
        settings_menu = menu_bar.addMenu("Settings")

        theme_menu = QMenu("Theme", self)
        light_action = QAction("Light", self)
        dark_action = QAction("Dark", self)
        light_action.triggered.connect(lambda: self.change_theme("Light"))
        dark_action.triggered.connect(lambda: self.change_theme("Dark"))
        theme_menu.addAction(light_action)
        theme_menu.addAction(dark_action)

        quality_menu = QMenu("Video Quality", self)
        qualities = ["1080p", "720p", "480p", "360p", "240p"]
        for quality in qualities:
            action = QAction(quality, self)
            action.triggered.connect(lambda checked, q=quality: self.set_quality(q))
            quality_menu.addAction(action)

        download_location_action = QAction("Set Download Location", self)
        download_location_action.triggered.connect(self.set_download_location)

        settings_menu.addMenu(theme_menu)
        settings_menu.addMenu(quality_menu)
        settings_menu.addAction(download_location_action)

    def change_theme(self, theme):
        self.theme = theme
        if theme == "Dark":
            self.setStyleSheet("background-color: #1e1e1e; color: #ffffff;")
        else:
            self.setStyleSheet("")

    def set_quality(self, quality):
        self.quality = quality

    def set_download_location(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Download Location")
        if directory:
            self.download_location = directory

    def search_videos(self):
        query = self.search_bar.text()
        self.search_button.setText("Loading...")
        self.search_button.setEnabled(False)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.terminate()
            self.search_thread.wait()

        self.search_thread = SearchThread(query)
        self.search_thread.results_found.connect(self.display_result)
        self.search_thread.finished.connect(lambda: self.search_button.setText("Search"))
        self.search_thread.finished.connect(lambda: self.search_button.setEnabled(True))
        self.search_thread.start()

    def display_result(self, video):
        frame = QWidget()
        layout = QHBoxLayout(frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        thumbnail_thread = ThumbnailThread(video.thumbnail_url)
        thumbnail_thread.finished.connect(lambda img_data, f=frame, v=video: self.add_video_frame(img_data, f, v))
        thumbnail_thread.start()
        self.thumbnail_threads.append(thumbnail_thread)

    def add_video_frame(self, img_data, frame, video):
        img = Image.open(io.BytesIO(img_data))
        img = img.resize((120, 90), Image.Resampling.LANCZOS)
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        pixmap = QPixmap()
        pixmap.loadFromData(img_byte_arr.getvalue())

        thumbnail_label = QLabel()
        thumbnail_label.setPixmap(pixmap)
        layout = frame.layout()
        layout.addWidget(thumbnail_label)

        meta_layout = QVBoxLayout()
        title_label = QLabel(video.title)
        title_label.setWordWrap(True)
        meta_layout.addWidget(title_label)
        meta_layout.setSpacing(10)

        download_button = QPushButton("Download")
        download_button.setFixedWidth(100)
        download_button.clicked.connect(lambda checked, v=video, f=frame, b=download_button: self.download_options(v, f, b))
        meta_layout.addWidget(download_button)

        layout.addLayout(meta_layout)
        self.results_layout.addWidget(frame)

    def download_options(self, video, frame, download_button):
        # Remove download button
        layout = frame.layout()
        meta_layout = layout.itemAt(1).layout()
        meta_layout.removeWidget(download_button)
        download_button.deleteLater()

        # Create progress bar immediately after selection
        progress_bar = QProgressBar()
        progress_bar.setValue(0)
        layout.addWidget(progress_bar)
        self.current_progress_bars[frame] = progress_bar

        # Start the download thread
        download_thread = DownloadThread(video.watch_url, audio=False, download_location=self.download_location)
        download_thread.progress.connect(progress_bar.setValue)
        download_thread.finished.connect(lambda: self.download_complete(video.title, frame))
        download_thread.start()
        self.download_threads.append(download_thread)

    def download_complete(self, video_title, frame):
        progress_bar = self.current_progress_bars.get(frame)
        if progress_bar:
            frame.layout().removeWidget(progress_bar)
            progress_bar.deleteLater()

        # Show a popup notification
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("Download Complete")
        msg_box.setText(f"Download of '{video_title}' complete.")
        open_button = msg_box.addButton("Open", QMessageBox.ButtonRole.AcceptRole)
        msg_box.addButton("Close", QMessageBox.ButtonRole.RejectRole)
        msg_box.exec()

        if msg_box.clickedButton() == open_button:
            download_path = Path(self.download_location) / video_title
            open_thread = OpenFileThread(download_path)
            open_thread.start()

        download_button = QPushButton("Download")
        download_button.setFixedWidth(100)
        download_button.clicked.connect(lambda checked, v=None, f=frame, b=download_button: self.download_options(v, f, b))
        frame.layout().addWidget(download_button)

    def closeEvent(self, event):
        if self.search_thread and self.search_thread.isRunning():
            self.search_thread.terminate()
            self.search_thread.wait()
        
        for thread in self.thumbnail_threads:
            if thread.isRunning():
                thread.terminate()
                thread.wait()

        for thread in self.download_threads:
            if thread.isRunning():
                thread.terminate()
                thread.wait()
        event.accept()

class OpenFileThread(QThread):
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def run(self):
        if os_type == "Windows":
            subprocess.Popen(['start', self.file_path], shell=True)
        elif os_type == "Darwin":  # macOS
            subprocess.Popen(['open', self.file_path])
        else:  # Linux
            subprocess.Popen(['xdg-open', self.file_path])

class SearchThread(QThread):
    results_found = pyqtSignal(object)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        search = Search(self.query)
        for i, result in enumerate(search.results):
            if i >= 10:  # Limit results to 10
                break
            self.results_found.emit(result)

class ThumbnailThread(QThread):
    finished = pyqtSignal(bytes)

    def __init__(self, thumbnail_url):
        super().__init__()
        self.thumbnail_url = thumbnail_url

    def run(self):
        response = requests.get(self.thumbnail_url)
        self.finished.emit(response.content)

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, video_url, audio, download_location):
        super().__init__()
        self.video_url = video_url
        self.audio = audio
        self.download_location = download_location

    def run(self):
        yt = YouTube(self.video_url, on_progress_callback=self.update_progress)
        if self.audio:
            stream = yt.streams.get_audio_only()
        else:
            stream = yt.streams.get_highest_resolution()
        stream.download(output_path=self.download_location)
        self.finished.emit()

    def update_progress(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage = (bytes_downloaded / total_size) * 100
        self.progress.emit(int(percentage))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    downloader = YouTubeDownloader()
    downloader.show()
    sys.exit(app.exec())
