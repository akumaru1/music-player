import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout,
    QWidget, QPushButton, QListView, QLabel, QSlider,
    QFileDialog
)
from PyQt6.QtCore import (
    Qt, QUrl, QModelIndex, QStandardPaths
)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from mutagen import File
from mutagen.flac import FLAC
from models import Song, SongListModel
from delegates import PowerampLikeDelegate



# --- 3. Main Application Window ---
class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt Poweramp-Lite Player")
        self.setGeometry(100, 100, 800, 600)

        self.current_song_index = -1
        self.playlist_songs = [] # This will hold Song objects
        self.audio_output = QAudioOutput()
        self.media_player = QMediaPlayer()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.playbackStateChanged.connect(self.handle_playback_state_changed)
        self.media_player.positionChanged.connect(self.update_position)
        self.media_player.durationChanged.connect(self.update_duration)

        self.init_ui()
        self.scan_music_directory(os.path.join(os.getcwd(), "/mnt/hdd1tb/ablume")) # Scan default 'music' folder

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Top section: Library controls
        library_layout = QHBoxLayout()
        self.scan_button = QPushButton("Scan Music Folder")
        self.scan_button.clicked.connect(self.select_and_scan_music_directory)
        library_layout.addWidget(self.scan_button)
        main_layout.addLayout(library_layout)

        # Song List View
        self.song_list_model = SongListModel()
        self.song_list_view = QListView()
        self.song_list_view.setModel(self.song_list_model)
        self.song_list_view.clicked.connect(self.play_selected_song)

        # Apply the custom delegate for Poweramp-like look
        self.song_list_view.setItemDelegate(PowerampLikeDelegate(self.song_list_view))

        main_layout.addWidget(self.song_list_view)

        # Current Song Display
        self.current_song_label = QLabel("No song playing")
        self.current_song_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.current_song_label)

        # Playback controls
        controls_layout = QHBoxLayout()
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.play_pause_song)
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.stop_song)
        self.previous_button = QPushButton("Prev")
        self.previous_button.clicked.connect(self.play_previous_song)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.play_next_song)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(50) # Default volume
        self.volume_slider.valueChanged.connect(self.set_volume)

        controls_layout.addWidget(self.previous_button)
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.next_button)
        controls_layout.addWidget(QLabel("Vol:"))
        controls_layout.addWidget(self.volume_slider)

        main_layout.addLayout(controls_layout)

        # Seek Slider and Time Labels
        seek_layout = QHBoxLayout()
        self.position_label = QLabel("00:00")
        self.duration_label = QLabel("00:00")
        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 0)
        self.seek_slider.sliderMoved.connect(self.set_position)

        seek_layout.addWidget(self.position_label)
        seek_layout.addWidget(self.seek_slider)
        seek_layout.addWidget(self.duration_label)
        main_layout.addLayout(seek_layout)

        self.set_volume(self.volume_slider.value()) # Apply initial volume

    def select_and_scan_music_directory(self):
        # Open a dialog to let the user select a directory
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        
        # Get standard music location on Linux
        default_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.MusicLocation)
        if not default_dir:
            default_dir = os.getcwd() # Fallback to current directory

        dialog.setDirectory(default_dir)

        if dialog.exec() == QFileDialog.DialogCode.Accepted:
            selected_dir = dialog.selectedFiles()[0]
            print(f"Scanning: {selected_dir}")
            self.scan_music_directory(selected_dir)

    def scan_music_directory(self, directory):
        self.playlist_songs.clear()
        self.song_list_model._songs.clear() # Clear existing songs in the model
        self.song_list_model.layoutChanged.emit() # Notify view that data has changed

        supported_extensions = ('.mp3', '.flac', '.ogg', '.wav') # Add more as needed

        for root, _, files in os.walk(directory):
            for file in files:
                if file.lower().endswith(supported_extensions):
                    file_path = os.path.join(root, file)
                    song_title, artist, album, duration, album_art_bytes = self.read_metadata(file_path)
                    song = Song(file_path, song_title, artist, album, duration, album_art_bytes)
                    self.playlist_songs.append(song)
                    self.song_list_model.add_song(song) # Add to the model for display

        print(f"Found {len(self.playlist_songs)} songs.")
        if self.playlist_songs:
            self.song_list_view.setCurrentIndex(self.song_list_model.index(0, 0)) # Select first song

    def read_metadata(self, file_path):
        title = None
        artist = None
        album = None
        duration = 0
        album_art_bytes = None

        try:
            audio = File(file_path, easy=True)
            if audio is None:
                # If mutagen can't read it, we'll just use the filename and return.
                return title, artist, album, duration, album_art_bytes

            duration = audio.info.length

            # Mutagen's easy interface provides a consistent way to access tags
            if 'title' in audio:
                title = audio['title'][0]
            if 'artist' in audio:
                artist = audio['artist'][0]
            if 'album' in audio:
                album = audio['album'][0]

            # For album art, we need to access the full object, not the "easy" one
            audio_full = File(file_path)
            if audio_full:
                if isinstance(audio_full, FLAC) and audio_full.pictures:
                    album_art_bytes = audio_full.pictures[0].data
                elif 'APIC:' in audio_full: # For MP3
                    album_art_bytes = audio_full['APIC:'].data
                elif 'covr' in audio_full: # For M4A/MP4
                    album_art_bytes = audio_full['covr'][0]
        except Exception as e:
            print(f"Error reading metadata for {file_path}: {e}")
        
        return title, artist, album, duration, album_art_bytes

    def play_selected_song(self, index: QModelIndex):
        self.current_song_index = index.row()
        self.play_current_song()

    def play_current_song(self):
        if 0 <= self.current_song_index < len(self.playlist_songs):
            song = self.playlist_songs[self.current_song_index]
            self.current_song_label.setText(f"Playing: {song.title} - {song.artist}")
            self.media_player.setSource(QUrl.fromLocalFile(song.file_path))
            self.media_player.play()

            # Update selection in the list view
            index = self.song_list_model.index(self.current_song_index, 0)
            self.song_list_view.setCurrentIndex(index)
        else:
            self.current_song_label.setText("No song selected")
            self.media_player.stop()

    def play_pause_song(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_button.setText("Play")
        elif self.media_player.playbackState() == QMediaPlayer.PlaybackState.PausedState:
            self.media_player.play()
            self.play_button.setText("Pause")
        elif self.media_player.playbackState() == QMediaPlayer.PlaybackState.StoppedState:
            if self.current_song_index != -1:
                self.media_player.play()
                self.play_button.setText("Pause")
            elif self.playlist_songs:
                self.current_song_index = 0
                self.play_current_song()
                self.play_button.setText("Pause")

    def stop_song(self):
        self.media_player.stop()
        self.play_button.setText("Play")
        self.current_song_label.setText("No song playing")
        self.position_label.setText("00:00")
        self.duration_label.setText("00:00")
        self.seek_slider.setValue(0)

    def play_previous_song(self):
        if self.playlist_songs:
            self.current_song_index = (self.current_song_index - 1) % len(self.playlist_songs)
            self.play_current_song()

    def play_next_song(self):
        if self.playlist_songs:
            self.current_song_index = (self.current_song_index + 1) % len(self.playlist_songs)
            self.play_current_song()

    def set_volume(self, value):
        # QAudioOutput volume is 0.0 to 1.0
        self.audio_output.setVolume(value / 100.0)

    def set_position(self, position):
        self.media_player.setPosition(position)

    def update_position(self, position):
        self.seek_slider.setValue(position)
        self.position_label.setText(self.format_time(position))

    def update_duration(self, duration):
        self.seek_slider.setRange(0, duration)
        self.duration_label.setText(self.format_time(duration))

    def format_time(self, ms):
        seconds = ms // 1000
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes:02d}:{remaining_seconds:02d}"

    def handle_playback_state_changed(self, state):
        if state == QMediaPlayer.PlaybackState.StoppedState:
            # Auto-play next song when current one finishes
            if self.current_song_index != -1 and self.playlist_songs:
                self.play_next_song()
        elif state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setText("Pause")
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.play_button.setText("Play")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MusicPlayer()
    window.show()
    sys.exit(app.exec())