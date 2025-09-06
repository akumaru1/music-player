from PyQt6.QtCore import Qt, QAbstractListModel, QModelIndex
import os

# --- 1. Custom Data Model for Songs ---
class Song:
    def __init__(self, file_path, title, artist, album, duration_seconds, album_art_bytes=None):
        self.file_path = file_path
        self.title = title if title else os.path.basename(file_path)
        self.artist = artist if artist else "Unknown Artist"
        self.album = album if album else "Unknown Album"
        self.duration_seconds = duration_seconds
        self.album_art_bytes = album_art_bytes

    def get_duration_string(self):
        minutes = self.duration_seconds // 60
        seconds = self.duration_seconds % 60
        return f"{int(minutes):02d}:{int(seconds):02d}"

class SongListModel(QAbstractListModel):
    def __init__(self, songs=None, parent=None):
        super().__init__(parent)
        self._songs = songs if songs is not None else []

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        song = self._songs[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            # Default display role (what the list item will show by default)
            return f"{song.title} - {song.artist}"
        elif role == Qt.ItemDataRole.UserRole:
            # Custom role to retrieve the full Song object
            return song
        # You could add other roles here for different data, e.g., Qt.DecorationRole for album art
        return None

    def rowCount(self, parent=QModelIndex()):
        return len(self._songs)

    def add_song(self, song):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._songs.append(song)
        self.endInsertRows()

    def get_song_at_index(self, index):
        if index.isValid() and 0 <= index.row() < len(self._songs):
            return self._songs[index.row()]
        return None
