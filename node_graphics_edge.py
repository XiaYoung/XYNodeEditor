import math

from PySide2.QtCore import QPointF, Qt
from PySide2.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide2.QtWidgets import QGraphicsPathItem

from node_socket import LEFT_BOTTOM, LEFT_TOP, RIGHT_BOTTOM, RIGHT_TOP

EDGE_CP_ROUNDNESS = 100


class QDMGraphicsEdge(QGraphicsPathItem):
    def __init__(self, edge, parent=None):
        super().__init__(parent)

        self.edge = edge

        self._color = QColor("#001000")  # 多一位都不显示 #00100000 错误
        self._pen = QPen(self._color)
        self._pen.setWidthF(2.0)

        self._color_selected = QColor("#00ff00")
        self._pen_selected = QPen(self._color_selected)
        self._pen_selected.setWidthF(2.0)

        self._pen_dragging = QPen(self._color)
        self._pen_dragging.setWidthF(2.0)
        self._pen_dragging.setStyle(Qt.DashLine)

        self.setFlag(QGraphicsPathItem.ItemIsSelectable)

        self.setZValue(-1)

        self.posSource = [0, 0]
        self.posDestination = [200, 100]

    def setSource(self, x, y):
        self.posSource = [x, y]

    def setDestination(self, x, y):
        self.posDestination = [x, y]

    def paint(self, painter: QPainter, option, widget=None):
        self.setPath(self.calcPath())

        if self.edge.end_socket is None:
            painter.setPen(self._pen_dragging)
        else:
            painter.setPen(self._pen_selected if self.isSelected() else self._pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.path())

    def intersectsWith(self, p1, p2):
        cutpath = QPainterPath(p1)
        cutpath.lineTo(p2)
        path = self.calcPath()
        return cutpath.intersects(path)

    def calcPath(self):
        ''' Will handle drawing QPainterPath from Point A to B'''
        raise NotImplementedError("This method has to be overriden in a child class")


class QDMGraphicsEdgeDirect(QDMGraphicsEdge):
    def calcPath(self):
        path = QPainterPath(QPointF(self.posSource[0], self.posSource[1]))
        path.lineTo(self.posDestination[0], self.posDestination[1])
        return path


class QDMGraphicsEdgeBezier(QDMGraphicsEdge):
    def calcPath(self):
        s = self.posSource
        d = self.posDestination
        dist = (d[0] - s[0]) * 0.5

        # control points
        cpx_s = +dist
        cpx_d = -dist
        cpy_s = 0
        cpy_d = 0

        sspos = self.edge.start_socket.position

        if (s[0] > d[0] and sspos in (RIGHT_TOP, RIGHT_BOTTOM)) or (s[0] < d[0] and sspos in (LEFT_TOP, LEFT_BOTTOM)):
            cpx_d *= -1
            cpx_s *= -1

            cpy_d = ((s[1] - d[1]) / math.fabs((s[1] - d[1]) if (s[1] - d[1]) != 0 else 0.000001)) * EDGE_CP_ROUNDNESS
            cpy_s = ((d[1] - s[1]) / math.fabs((d[1] - s[1]) if (d[1] - s[1]) != 0 else 0.000001)) * EDGE_CP_ROUNDNESS

        path = QPainterPath(QPointF(self.posSource[0], self.posSource[1]))
        path.cubicTo(s[0] + cpx_s, s[1] + cpy_s,
                     d[0] + cpx_d, d[1] + cpy_d,
                     self.posDestination[0], self.posDestination[1])
        return path
