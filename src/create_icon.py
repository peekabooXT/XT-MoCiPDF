from pathlib import Path
import struct
import os
os.environ['QT_QPA_PLATFORM']='offscreen'
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QByteArray,QBuffer,QIODevice,QRectF,Qt
from PySide6.QtGui import QPixmap,QPainter,QColor,QFont,QFontDatabase
PACKAGE=Path(__file__).resolve().parents[1]
app = QApplication([])
QFontDatabase.addApplicationFont('C:/Windows/Fonts/segoeuib.ttf')
images = []
for size in (16, 32, 48, 64, 128, 256):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.scale(size / 256, size / 256)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor('#087f73'))
    painter.drawRoundedRect(QRectF(8, 8, 240, 240), 48, 48)
    painter.setBrush(QColor('#d7eee8'))
    painter.drawRoundedRect(QRectF(40, 42, 176, 174), 13, 13)
    painter.setBrush(QColor('white'))
    painter.drawRoundedRect(QRectF(48, 34, 168, 172), 12, 12)
    painter.setPen(QColor('#087f73'))
    font = QFont('Segoe UI', 66, QFont.Weight.Bold)
    font.setPixelSize(91)
    painter.setFont(font)
    painter.drawText(QRectF(48, 38, 168, 140), Qt.AlignmentFlag.AlignCenter, 'XT')
    painter.setBrush(QColor('#e2b85d'))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(QRectF(76, 181, 112, 8), 4, 4)
    painter.end()
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    pixmap.save(buffer, 'PNG')
    images.append((size, bytes(data)))
offset = 6 + len(images) * 16
entries, payload = [], []
for size, data in images:
    entries.append(struct.pack('<BBBBHHII', size % 256, size % 256, 0, 0, 1, 32, len(data), offset))
    payload.append(data)
    offset += len(data)
(PACKAGE / 'icon.ico').write_bytes(struct.pack('<HHH', 0, 1, len(images)) + b''.join(entries + payload))
pixmap.save(str(PACKAGE / 'icon-preview.png'))
print('XT icon generated')
