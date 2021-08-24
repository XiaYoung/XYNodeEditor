from PySide2.QtCore import QRect
from PySide2.QtGui import QBrush, QColor, QPainter, QPen
from PySide2.QtWidgets import QGraphicsItem


class QDMGraphicsSocket(QGraphicsItem):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.radius = 6.0
        self.outline_width = 1.0
        self._color_bacground = QColor("#FFFF7700")
        self._color_outline = QColor("#FF000000")

        self._pen = QPen(self._color_outline)
        self._pen.setWidthF(self.outline_width)
        self._brush = QBrush(self._color_bacground)

    def paint(self, painter: QPainter, option, widget=None):

        # painting circle
        painter.setBrush(self._brush)
        painter.setPen(self._pen)
        painter.drawEllipse(-self.radius, -self.radius,
                            2 * self.radius, 2 * self.radius)

    def boundingRect(self):
        return QRect(
            - self.radius - self.outline_width,
            - self.radius - self.outline_width,
            2 * (self.radius + self.outline_width),
            2 * (self.radius + self.outline_width),
        )
