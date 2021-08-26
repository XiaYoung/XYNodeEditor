from node_graphics_cutline import QDMCutLine
from PySide2.QtCore import QEvent, Qt
from PySide2.QtGui import QKeyEvent, QMouseEvent, QPainter
from PySide2.QtWidgets import QApplication, QGraphicsView

from node_edge import EDGE_TYPE_BEZIER, Edge
from node_graphics_edge import QDMGraphicsEdge
from node_graphics_socket import QDMGraphicsSocket

MODE_NOOP = 1
MODE_EDGE_DRAG = 2
MODE_EDGE_CUT = 3

EDGE_DRAG_START_THRESHOLD = 10

DEBUG = False


class QDMGraphicsView(QGraphicsView):
    def __init__(self, grScene, parent=None):
        super().__init__(parent)
        self.grScene = grScene

        self.initUI()

        self.setScene(self.grScene)

        self.mode = MODE_NOOP
        self.editingFlag = False

        self.zoomInFactor = 1.25
        self.zoomClamp = False
        self.zoom = 10
        self.zoomStep = 1
        self.zoomRange = [0, 20]

        # cutline
        self.cutline = QDMCutLine()
        self.grScene.addItem(self.cutline)

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
        if self.mode == MODE_NOOP:
            # SHIFT select
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
            # drag edge start
            if type(item) is QDMGraphicsSocket:
                self.edgeDragStart(item)
                return

            if item is None:
                if event.modifiers() & Qt.ControlModifier:
                    self.mode = MODE_EDGE_CUT
                    fakeEvent = QMouseEvent(
                        QEvent.MouseButtonRelease, event.localPos(),
                        event.screenPos(), Qt.LeftButton, Qt.NoButton,
                        event.modifiers())
                    super().mouseReleaseEvent(fakeEvent)
                    QApplication.setOverrideCursor(Qt.CrossCursor)
                    return

        super().mousePressEvent(event)

    def leftMouseButtonRelease(self, event):
        item = self.getItemAtClick(event)
        # SHIFT select
        if hasattr(item, "node") or isinstance(item, QDMGraphicsEdge) or item is None:
            if event.modifiers() & Qt.ShiftModifier:
                event.ignore()
                fakeEvent = QMouseEvent(
                    event.type(), event.localPos(), event.screenPos(),
                    Qt.LeftButton, Qt.NoButton,
                    event.modifiers() | Qt.ControlModifier)
                super().mouseReleaseEvent(fakeEvent)
                return

        if self.mode == MODE_EDGE_DRAG:
            if self.edgeDragEnd(item):
                return

        if self.mode == MODE_EDGE_CUT:
            self.cutIntersectingEdges()
            self.cutline.line_points = []
            self.cutline.update()
            QApplication.setOverrideCursor(Qt.ArrowCursor)
            self.mode = MODE_NOOP

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
        if self.mode == MODE_EDGE_CUT:
            pos = self.mapToScene(event.pos())
            self.cutline.line_points.append(pos)
            self.cutline.update()

        super().mouseMoveEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Delete:
            if not self.editingFlag:
                self.deleteSelected()
            else:
                super().keyPressEvent(event)
        elif event.key() == Qt.Key_S and event.modifiers() & Qt.ControlModifier:
            self.grScene.scene.saveToFile("graph.json.txt")
        elif event.key() == Qt.Key_L and event.modifiers() & Qt.ControlModifier:
            self.grScene.scene.loadFromFile("graph.json.txt")
        else:
            super().keyPressEvent(event)

    def cutIntersectingEdges(self):

        for ix in range(len(self.cutline.line_points) - 1):
            p1 = self.cutline.line_points[ix]
            p2 = self.cutline.line_points[ix + 1]

            for edge in self.grScene.scene.edges:
                if edge.grEdge.intersectsWith(p1, p2):
                    edge.remove()

    def deleteSelected(self):
        for item in self.grScene.selectedItems():
            if isinstance(item, QDMGraphicsEdge):
                item.edge.remove()
            elif hasattr(item, 'node'):
                item.node.remove()

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

    def edgeDragStart(self, item):
        if DEBUG:
            print("View::edgeDragStart ~ Start dragging edge")
        self.mode = MODE_EDGE_DRAG
        self.dragEdge = Edge(self.grScene.scene, item.socket, None, EDGE_TYPE_BEZIER)
        if DEBUG:
            print("View::edgeDragStart ~ dragEdge:", self.dragEdge)
            print("View::edgeDragStart ~   assign Start Socket to:", item.socket)

    def edgeDragEnd(self, item):

        if type(item) is QDMGraphicsSocket:
            # check if start and end are same socket
            if item.socket == self.dragEdge.start_socket:
                if DEBUG:
                    print("View::edgeDragEnd ~  Start and End are same!")
                return True

            # check if already have a same edge
            other_edges = self.dragEdge.start_socket.edges
            for edge in other_edges:
                if edge.end_socket == item.socket:
                    if DEBUG:
                        print("View::edgeDragEnd ~  already have a same edge")
                    return True

            self.mode = MODE_NOOP
            self.dragEdge.end_socket = item.socket
            self.dragEdge.end_socket.setConnectedEdge(self.dragEdge)
            self.dragEdge.grEdge.update()
            if DEBUG:
                print("View::edgeDragEnd ~  assign End socket to:", item.socket)
                print("View::edgeDragEnd ~ End dargging edge")
        else:
            self.mode = MODE_NOOP
            if DEBUG:
                print("View::edgeDragEnd ~  NOT assign End socket")
            self.dragEdge.remove()
            self.dragEdge = None
            if DEBUG:
                print("View::edgeDragEnd ~  Remove Darg Edge")
                print("View::edgeDragEnd ~ End dargging edge")

        return False

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
