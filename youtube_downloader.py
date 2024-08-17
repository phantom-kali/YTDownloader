import sys
<<<<<<< HEAD
import json
=======
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QFileDialog, QProgressBar, QMenu,
    QMenuBar, QMessageBox, QDialog, QRadioButton, QButtonGroup, QDialogButtonBox
)
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pytube import YouTube, Search
from PIL import Image
>>>>>>> b98ede6228e89a59929ef604bb754902d607a19e
import requests
import io
import platform
from pathlib import Path
import urllib.parse
import subprocess
import os
from pathlib import Path
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QFileDialog, QProgressBar, QMenu,
    QMenuBar, QMessageBox, QDialog, QRadioButton, QButtonGroup, QDialogButtonBox
)
from PyQt6.QtGui import QPixmap, QAction
from PyQt6.QtCore import Qt, QRunnable, QThreadPool, QObject, pyqtSignal, pyqtSlot
from pytube import YouTube, Search
from PIL import Image

os_type = platform.system()

<<<<<<< HEAD
class Cache:
    def __init__(self, cache_file, expiration_time=timedelta(hours=1)):
        self.cache_file = cache_file
        self.expiration_time = expiration_time
        self.cache = self.load_cache()

    def load_cache(self):
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f)

    def get(self, key):
        if key in self.cache:
            timestamp, value = self.cache[key]
            if datetime.now() - datetime.fromisoformat(timestamp) < self.expiration_time:
                return value
        return None

    def set(self, key, value):
        self.cache[key] = (datetime.now().isoformat(), value)
        self.save_cache()

class WorkerSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)

class SearchWorker(QRunnable):
    def __init__(self, query, cache):
        super().__init__()
        self.query = query
        self.cache = cache
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            cached_results = self.cache.get(self.query)
            if cached_results:
                for result in cached_results:
                    self.signals.result.emit(result)
            else:
                search = Search(self.query)
                results = []
                for i, result in enumerate(search.results):
                    if i >= 10:
                        break
                    results.append(result)
                    self.signals.result.emit(result)
                self.cache.set(self.query, results)
            self.signals.finished.emit()
        except Exception as e:
            self.signals.error.emit(str(e))

class ThumbnailWorker(QRunnable):
    def __init__(self, thumbnail_url, cache):
        super().__init__()
        self.thumbnail_url = thumbnail_url
        self.cache = cache
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            cached_thumbnail = self.cache.get(self.thumbnail_url)
            if cached_thumbnail:
                self.signals.result.emit(cached_thumbnail)
            else:
                response = requests.get(self.thumbnail_url)
                self.cache.set(self.thumbnail_url, response.content)
                self.signals.result.emit(response.content)
            self.signals.finished.emit()
        except Exception as e:
            self.signals.error.emit(str(e))

class DownloadWorker(QRunnable):
    def __init__(self, video_url, audio_only, download_location):
        super().__init__()
        self.video_url = video_url
        self.audio_only = audio_only
        self.download_location = download_location
        self.signals = WorkerSignals()

    @pyqtSlot()
    def run(self):
        try:
            yt = YouTube(self.video_url, on_progress_callback=self.update_progress)
            if self.audio_only:
                stream = yt.streams.get_audio_only()
            else:
                stream = yt.streams.get_highest_resolution()
            stream.download(output_path=self.download_location)
            self.signals.finished.emit()
        except Exception as e:
            self.signals.error.emit(str(e))

    def update_progress(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage = (bytes_downloaded / total_size) * 100
        self.signals.progress.emit(int(percentage))

class YouTubeDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Downloader")
        self.setGeometry(100, 100, 800, 600)

        self.quality = "240p"
        self.theme = "Light"
        self.download_location = str(Path.home() / 'Downloads/YouTube')

        self.search_cache = Cache('search_cache.json')
        self.thumbnail_cache = Cache('thumbnail_cache.json')

        self.initUI()
        self.create_menu()

        self.current_progress_bars = {}

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
        if not query:
            self.show_error("Please enter a search query.")
            return

        self.search_button.setText("Loading...")
        self.search_button.setEnabled(False)
        self.results_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        worker = SearchWorker(query, self.search_cache)
        worker.signals.result.connect(self.display_result)
        worker.signals.finished.connect(lambda: self.search_button.setText("Search"))
        worker.signals.finished.connect(lambda: self.search_button.setEnabled(True))
        worker.signals.error.connect(self.show_error)

        QThreadPool.globalInstance().start(worker)

    def display_result(self, video):
        frame = QWidget()
        layout = QHBoxLayout(frame)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        worker = ThumbnailWorker(video.thumbnail_url, self.thumbnail_cache)
        worker.signals.result.connect(lambda img_data, f=frame, v=video: self.add_video_frame(img_data, f, v))
        worker.signals.error.connect(self.show_error)
        QThreadPool.globalInstance().start(worker)

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
        dialog = QDialog(self)
        dialog.setWindowTitle("Download Options")

        layout = QVBoxLayout(dialog)
        audio_button = QRadioButton("Audio Only")
        video_button = QRadioButton("Video")
        video_button.setChecked(True)

        button_group = QButtonGroup(dialog)
        button_group.addButton(audio_button)
        button_group.addButton(video_button)

        layout.addWidget(audio_button)
        layout.addWidget(video_button)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

=======
class YouTubeDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Downloader")
        self.setGeometry(100, 100, 800, 600)

        self.quality = "240p"
        self.theme = "Light"
        self.download_location = str(Path.home() / 'Downloads/YouTube')

        self.initUI()
        self.create_menu()

        self.search_thread = None
        self.download_threads = []
        self.thumbnail_threads = []
        self.current_progress_bars = {}

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
        dialog = QDialog(self)
        dialog.setWindowTitle("Download Options")

        layout = QVBoxLayout(dialog)
        audio_button = QRadioButton("Audio Only")
        video_button = QRadioButton("Video")
        video_button.setChecked(True)

        button_group = QButtonGroup(dialog)
        button_group.addButton(audio_button)
        button_group.addButton(video_button)

        layout.addWidget(audio_button)
        layout.addWidget(video_button)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

>>>>>>> b98ede6228e89a59929ef604bb754902d607a19e
        if dialog.exec() == QDialog.DialogCode.Accepted:
            download_audio = audio_button.isChecked()
            self.start_download(video, frame, download_button, download_audio)

    def start_download(self, video, frame, download_button, download_audio):
        layout = frame.layout()
        meta_layout = layout.itemAt(1).layout()
        meta_layout.removeWidget(download_button)
        download_button.deleteLater()

        progress_bar = QProgressBar()
        progress_bar.setValue(0)
        layout.addWidget(progress_bar)
        self.current_progress_bars[frame] = progress_bar

<<<<<<< HEAD
        worker = DownloadWorker(video.watch_url, download_audio, self.download_location)
        worker.signals.progress.connect(progress_bar.setValue)
        worker.signals.finished.connect(lambda: self.download_complete(video.title, frame, ".mp4" if not download_audio else ".mp3"))
        worker.signals.error.connect(self.show_error)
        QThreadPool.globalInstance().start(worker)
=======
        download_thread = DownloadThread(video.watch_url, download_audio, self.download_location)
        download_thread.progress.connect(progress_bar.setValue)
        download_thread.finished.connect(lambda: self.download_complete(video.title, frame, ".mp4" if not download_audio else ".mp3"))
        download_thread.start()
        self.download_threads.append(download_thread)

>>>>>>> b98ede6228e89a59929ef604bb754902d607a19e

    def download_complete(self, video_title, frame, extension):
        progress_bar = self.current_progress_bars.get(frame)
        if progress_bar:
            frame.layout().removeWidget(progress_bar)
            progress_bar.deleteLater()

        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("Download Complete")
        msg_box.setText(f"Download of '{video_title}' complete.")
        open_button = msg_box.addButton("Open", QMessageBox.ButtonRole.AcceptRole)
        msg_box.addButton("Close", QMessageBox.ButtonRole.RejectRole)
        msg_box.exec()

        if msg_box.clickedButton() == open_button:
            download_path = Path(self.download_location) / (video_title + extension)
<<<<<<< HEAD
            self.open_file(download_path)
=======
            open_thread = OpenFileThread(download_path)
            open_thread.start()
>>>>>>> b98ede6228e89a59929ef604bb754902d607a19e

        download_button = QPushButton("Download")
        download_button.setFixedWidth(100)
        download_button.clicked.connect(lambda checked, v=None, f=frame, b=download_button: self.download_options(v, f, b))
        frame.layout().addWidget(download_button)

<<<<<<< HEAD
    def open_file(self, file_path):
        if not os.path.exists(file_path):
            self.show_error(f"File not found: {file_path}")
            return

        if os_type == "Windows":
            os.startfile(str(file_path))
        elif os_type == "Darwin":  # macOS
            os.system(f"open {str(file_path)}")
        else:  # Linux
            os.system(f"xdg-open {str(file_path)}")

    def show_error(self, message):
        error_box = QMessageBox(self)
        error_box.setIcon(QMessageBox.Icon.Critical)
        error_box.setText("Error")
        error_box.setInformativeText(message)
        error_box.setWindowTitle("Error")
        error_box.exec()
=======

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
        if not os.path.exists(self.file_path):
            print(f"File not found: {self.file_path}")
            return

        if os_type == "Windows":
            subprocess.Popen(['start', str(self.file_path)], shell=True)
        elif os_type == "Darwin":  # macOS
            subprocess.Popen(['open', str(self.file_path)])
        else:  # Linux
            subprocess.Popen(['xdg-open', str(self.file_path)])


class SearchThread(QThread):
    results_found = pyqtSignal(object)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        search = Search(self.query)
        for i, result in enumerate(search.results):
            if i >= 10:
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
>>>>>>> b98ede6228e89a59929ef604bb754902d607a19e

if __name__ == "__main__":
    app = QApplication(sys.argv)
    downloader = YouTubeDownloader()
    downloader.show()
<<<<<<< HEAD
    sys.exit(app.exec())
=======
    sys.exit(app.exec())
>>>>>>> b98ede6228e89a59929ef604bb754902d607a19e
