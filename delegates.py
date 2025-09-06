from PyQt6.QtWidgets import QStyledItemDelegate, QStyleOptionViewItem, QStyle
from PyQt6.QtGui import QPainter, QPixmap, QImage
from PyQt6.QtCore import QSize, Qt, QModelIndex


# --- 2. Custom Item Delegate (Where Poweramp's list styling would happen) ---
class PowerampLikeDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.album_art_size = QSize(64, 64) # Example size for album art thumbnail

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
        if not index.isValid():
            return

        song = index.data(Qt.ItemDataRole.UserRole)
        if not song:
            return

        painter.save()
        rect = option.rect

        # Highlight selection
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(rect, option.palette.highlight())

        # Draw album art
        album_art_rect = rect.adjusted(5, 5, -5 - self.album_art_size.width(), -5) # Adjust for padding
        album_art_rect.setSize(self.album_art_size)
        
        pixmap = QPixmap()
        if song.album_art_bytes:
            image = QImage.fromData(song.album_art_bytes)
            pixmap = QPixmap.fromImage(image).scaled(self.album_art_size, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        else:
            # Placeholder for no album art
            pixmap = QPixmap(":/icons/default_album_art.png") # You'd need a default icon
            if pixmap.isNull(): # Fallback if resource is not found
                pixmap = QPixmap(self.album_art_size)
                pixmap.fill(Qt.GlobalColor.darkGray)

        painter.drawPixmap(album_art_rect, pixmap)

        # Draw text (title, artist, album, duration)
        text_rect = rect.adjusted(album_art_rect.width() + 15, 5, -5, -5) # Adjust position relative to album art

        # Title
        painter.setFont(option.font) # Use default font for now
        title_font = painter.font()
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.drawText(text_rect.x(), text_rect.y(), text_rect.width(), text_rect.height() // 3,
                         Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                         song.title)

        # Artist
        artist_font = painter.font()
        artist_font.setBold(False)
        artist_font.setPointSize(int(artist_font.pointSize() * 0.9)) # Slightly smaller
        painter.setFont(artist_font)
        painter.drawText(text_rect.x(), text_rect.y() + text_rect.height() // 3, text_rect.width(), text_rect.height() // 3,
                         Qt.AlignmentFlag.AlignLeft,
                         song.artist)
        
        # Duration (right aligned)
        duration_text = song.get_duration_string()
        duration_rect = rect.adjusted(rect.width() - 60, 5, -5, -5) # Right side of item
        painter.drawText(duration_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop, duration_text)


        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex):
        # This is crucial for custom drawn items to have the correct height
        return QSize(option.rect.width(), self.album_art_size.height() + 10) # Album art height + padding
