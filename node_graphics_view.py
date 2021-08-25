from PySide2.QtCore import QEvent, Qt
from PySide2.QtGui import QMouseEvent, QPainter
from PySide2.QtWidgets import QGraphicsView

from node_edge import EDGE_TYPE_BEZIER, Edge
from node_graphics_edge import QDMGraphicsEdge
from node_graphics_socket import QDMGraphicsSocket

MODE_NOOP = 1
MODE_EDGE_DRAG = 2
EDGE_DRAG_START_THRESHOLD = 10

DEBUG = True


class QDMGraphicsView(QGraphicsView):
    def __init__(self, grScene, parent=None):
        super().__init__(parent)
        self.grScene = grScene

        self.initUI()

        self.setScene(self.grScene)

        self.mode = MODE_NOOP

        self.zoomInFactor = 1.25
        self.zoomClamp = False
        self.zoom = 10
        self.zoomStep = 1
        self.zoomRange = [0, 20]

    def initUI(self):
        self.setRenderHints(QPainter.Antialiasing |
                            QPainter.HighQualityAntialiasing |
                            QPainter.TextAntialiasing |
                            QPainter.SmoothPixmapTransform)

        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.RubberBandDrag)

    def mousePressEvent(self, event):
        if event.button() == Qt.MidButton:
            self.middleMouseButtonPress(event)
        elif event.button() == Qt.LeftButton:
            self.leftMouseButtonPress(event)
        elif event.button() == Qt.RightButton:
            self.rightMouseButtonPress(event)
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MidButton:
            self.middleMouseButtonRelease(event)
        elif event.button() == Qt.LeftButton:
            self.leftMouseButtonRelease(event)
        elif event.button() == Qt.RightButton:
            self.rightMouseButtonRelease(event)
        else:
            super().mouseReleaseEvent(event)

    def middleMouseButtonPress(self, event):
        releaseEvent = QMouseEvent(QEvent.MouseButtonRelease, event.localPos(),
                                   event.screenPos(), Qt.LeftButton,
                                   Qt.NoButton, event.modifiers())
        super().mouseReleaseEvent(releaseEvent)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        fakeEvent = QMouseEvent(event.type(), event.localPos(),
                                event.screenPos(), Qt.LeftButton,
                                event.buttons() | Qt.LeftButton,
                                event.modifiers())
        super().mousePressEvent(fakeEvent)

    def middleMouseButtonRelease(self, event):
        fakeEvent = QMouseEvent(event.type(), event.localPos(),
                                event.screenPos(), Qt.LeftButton,
                                event.buttons() & ~Qt.LeftButton,  # not -
                                event.modifiers())
        super().mouseReleaseEvent(fakeEvent)
        self.setDragMode(QGraphicsView.NoDrag)

    def leftMouseButtonPress(self, event):
        item = self.getItemAtClick(event)
        if hasattr(item, "node") or isinstance(item, QDMGraphicsEdge) or item is None:
            if event.modifiers() & Qt.ShiftModifier:
                if DEBUG:
                    print("LMB Click on", item, self.debug_modifiers(event))
                event.ignore()
                fakeEvent = QMouseEvent(
                    QEvent.MouseButtonPress, event.localPos(),
                    event.screenPos(), Qt.LeftButton,
                    event.buttons() | Qt.LeftButton,
                    event.modifiers() | Qt.ControlModifier)
                super().mousePressEvent(fakeEvent)
                return

        if self.mode == MODE_NOOP:
            if type(item) is QDMGraphicsSocket:
                self.mode = MODE_EDGE_DRAG
                self.edgeDragStart(event)
                return

        super().mousePressEvent(event)

    def leftMouseButtonRelease(self, event):
        item = self.getItemAtClick(event)
        if hasattr(item, "node") or isinstance(item, QDMGraphicsEdge)  or item is None:
            if event.modifiers() & Qt.ShiftModifier:                   
                event.ignore()
                fakeEvent = QMouseEvent(
                    event.type(), event.localPos(), event.screenPos(),
                    Qt.LeftButton, Qt.NoButton,
                    event.modifiers() | Qt.ControlModifier)
                super().mouseReleaseEvent(fakeEvent)
                return

        if self.mode == MODE_EDGE_DRAG:
            # get item which we clicked on
            if type(item) is QDMGraphicsSocket:
                if self.distanceBetweenClickAndReleaseIsOff(event):
                    self.mode = MODE_NOOP
                    self.edgeDragEnd(item)
                    return
            else:
                self.mode = MODE_NOOP
                if DEBUG:
                    print("View::edgeDragEnd ~  NOT assign End socket")
                    print("View::edgeDragEnd ~ End dargging edge")
                self.dragEdge.remove()
                self.dragEdge = None

        super().mouseReleaseEvent(event)

    def rightMouseButtonPress(self, event):
        super().mousePressEvent(event)

        item = self.getItemAtClick(event)

        if DEBUG:
            if isinstance(item, QDMGraphicsEdge):
                print('RMD DEBUG', item.edge, ' connecting sockets:',
                      item.edge.start_socket, '<-->', item.edge.end_socket)
            if type(item) is QDMGraphicsSocket:
                print('RMD DEBUG', item.socket, 'has edg:', *item.socket.edges)
            if item is None:
                print('SCENE:')
                print(' Nodes')
                for node in self.grScene.scene.nodes:
                    print('  ', node)
                print(' Edges:')
                for edge in self.grScene.scene.edges:
                    print('  ', edge)

    def rightMouseButtonRelease(self, event):
        super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self.mode == MODE_EDGE_DRAG:
            pos = self.mapToScene(event.pos())
            self.dragEdge.grEdge.setDestination(pos.x(), pos.y())
            self.dragEdge.grEdge.update()

        super().mouseMoveEvent(event)

    def debug_modifiers(self, event):
        out = "MODS: "
        if event.modifiers() & Qt.ShiftModifier:
            out += " SHIFT"
        if event.modifiers() & Qt.ControlModifier:
            out += " CTRL"
        if event.modifiers() & Qt.AltModifier:
            out += " ALT"
        return out
    
    def getItemAtClick(self, event):
        pos = event.pos()
        obj = self.itemAt(pos)
        return obj

    def edgeDragStart(self, event):
        self.last_lmb_click_scene_pos = self.mapToScene(event.pos())
        item = self.getItemAtClick(event)
        if DEBUG:
            print("View::edgeDragStart ~ Start dragging edge")
            print("View::edgeDragStart ~   assign Start Socket to:", item.socket)

        self.dragEdge = Edge(self.grScene.scene, item.socket, None, EDGE_TYPE_BEZIER)
        if DEBUG:
            print("View::edgeDragStart ~ dragEdge:", self.dragEdge)

    def edgeDragEnd(self, item):
        if DEBUG:
            print("View::edgeDragEnd ~  assign End socket")
        # 检查是否已经存在重复的曲线，start end socket 相同
        other_edges = self.dragEdge.start_socket.edges
        for edge in other_edges:
            if edge.end_socket == item.socket:
                if DEBUG:
                    print("View::edgeDragEnd ~  already have a same edge")
                    print("View::edgeDragEnd ~ End dargging edge")
                self.dragEdge.remove()
                self.dragEdge = None
                return
        self.dragEdge.end_socket = item.socket
        self.dragEdge.end_socket.setConnectedEdge(self.dragEdge)
        if DEBUG:
            print("View::edgeDragEnd ~  assign start & end socket to drag edge")
            print("View::edgeDragEnd ~ End dargging edge")

    def distanceBetweenClickAndReleaseIsOff(self, event):
        ''' measures if we are too far from '''
        new_lmb_release_scene_pos = self.mapToScene(event.pos())
        dis_scene_pos = new_lmb_release_scene_pos - self.last_lmb_click_scene_pos
        dis_sq = dis_scene_pos.x()*dis_scene_pos.x()+dis_scene_pos.y()*dis_scene_pos.y()
        print(dis_sq)
        return dis_sq > EDGE_DRAG_START_THRESHOLD * EDGE_DRAG_START_THRESHOLD

    def wheelEvent(self, event):
        # calculate our zoom Facotr
        zoomOutFactor = 1 / self.zoomInFactor

        # calculate zoom
        if event.angleDelta().y() > 0:
            zoomFactor = self.zoomInFactor
            self.zoom += self.zoomStep
        else:
            zoomFactor = zoomOutFactor
            self.zoom -= self.zoomStep

        clamped = False

        if self.zoom < self.zoomRange[0]:
            self.zoom = self.zoomRange[0]
            clamped = True

        if self.zoom > self.zoomRange[1]:
            self.zoom = self.zoomRange[1]
            clamped = True

        # set scene scale
        if not clamped or self.zoomClamp is False:
            self.scale(zoomFactor, zoomFactor)
