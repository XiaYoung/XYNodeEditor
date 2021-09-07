from PySide2.QtCore import QEvent, Qt, Signal
from PySide2.QtGui import QKeyEvent, QMouseEvent, QPainter
from PySide2.QtWidgets import QApplication, QGraphicsView

from xynodeeditor.node_graphics_cutline import QDMCutLine
from xynodeeditor.node_edge import EDGE_TYPE_BEZIER, Edge
from xynodeeditor.node_graphics_edge import QDMGraphicsEdge
from xynodeeditor.node_graphics_socket import QDMGraphicsSocket

MODE_NOOP = 1
MODE_EDGE_DRAG = 2
MODE_EDGE_CUT = 3

EDGE_DRAG_START_THRESHOLD = 10

DEBUG = False


class QDMGraphicsView(QGraphicsView):
    # TODO: 这是什么用法？
    scenePosChangedSignal = Signal(int, int)

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
        self.setDragMode(QGraphicsView.RubberBandDrag)

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
            return

        if self.dragMode() == QGraphicsView.RubberBandDrag:
            self.grScene.scene.history.storeHistory("Selection changed")

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
            self.drag_edge.grEdge.setDestination(pos.x(), pos.y())
            self.drag_edge.grEdge.update()
        if self.mode == MODE_EDGE_CUT:
            pos = self.mapToScene(event.pos())
            self.cutline.line_points.append(pos)
            self.cutline.update()

        self.last_scene_mouse_position = self.mapToScene(event.pos())

        self.scenePosChangedSignal.emit(
            int(self.last_scene_mouse_position.x()), int(self.last_scene_mouse_position.y())
        )

        super().mouseMoveEvent(event)

    def keyPressEvent(self, event: QKeyEvent):
        # if event.key() == Qt.Key_Delete:
        #     if not self.editingFlag:
        #         self.deleteSelected()
        #     else:
        #         super().keyPressEvent(event)
        # elif event.key() == Qt.Key_S and event.modifiers() & Qt.ControlModifier:
        #     self.grScene.scene.saveToFile("graph.json.txt")
        # elif event.key() == Qt.Key_L and event.modifiers() & Qt.ControlModifier:
        #     self.grScene.scene.loadFromFile("graph.json.txt")
        # elif event.key() == Qt.Key_Z and event.modifiers() & Qt.ControlModifier and not event.modifiers() & Qt.ShiftModifier:
        #     self.grScene.scene.history.undo()
        # elif event.key() == Qt.Key_Z and event.modifiers() & Qt.ControlModifier and event.modifiers() & Qt.ShiftModifier:
        #     self.grScene.scene.history.redo()
        # elif event.key() == Qt.Key_H:
        #     print("HISTORY: len(%d)" % len(self.grScene.scene.history.history_stack),
        #           "-- current _step", self.grScene.scene.history.history_current_step)
        #     ix = 0
        #     for item in self.grScene.scene.history.history_stack:
        #         print("#", ix, "--", item['desc'])
        #         ix += 1
        # else:
        super().keyPressEvent(event)

    def cutIntersectingEdges(self):

        for ix in range(len(self.cutline.line_points) - 1):
            p1 = self.cutline.line_points[ix]
            p2 = self.cutline.line_points[ix + 1]

            for edge in self.grScene.scene.edges:
                if edge.grEdge.intersectsWith(p1, p2):
                    edge.remove()
        self.grScene.scene.history.storeHistory("Delete cutted edges", setModified=True)

    def deleteSelected(self):
        for item in self.grScene.selectedItems():
            if isinstance(item, QDMGraphicsEdge):
                item.edge.remove()
            elif hasattr(item, 'node'):
                item.node.remove()
        self.grScene.scene.history.storeHistory("Delete selected", setModified=True)

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
        # drag_edge 在非multi_edges模式下需要删掉
        self.drag_edge = Edge(self.grScene.scene, item.socket, None, EDGE_TYPE_BEZIER)
        self.drag_start_socket = item.socket
        if DEBUG:
            print("View::edgeDragStart ~ dragEdge:", self.drag_edge)
            print("View::edgeDragStart ~   assign Start Socket to:", item.socket)

    def edgeDragEnd(self, item):

        if type(item) is QDMGraphicsSocket:
            # check if start and end are same socket
            if item.socket == self.drag_edge.start_socket:
                if DEBUG:
                    print("View::edgeDragEnd ~  Start and End are same!")
                return True

            # check if already have a same edge
            other_edges = self.drag_edge.start_socket.edges
            for edge in other_edges:
                if edge.end_socket == item.socket:
                    if DEBUG:
                        print("View::edgeDragEnd ~  already have a same edge")
                    return True

            if not self.drag_edge.start_socket.is_multi_edges:
                self.drag_edge.start_socket.removeAllEdges()

            if not item.socket.is_multi_edges:
                item.socket.removeAllEdges()

            self.mode = MODE_NOOP
            # self.drag_edge.end_socket = item.socket
            # self.drag_edge.end_socket.addEdge(self.drag_edge)
            # self.drag_edge.start_socket = self.drag_start_socket
            # self.drag_edge.start_socket.addEdge(self.drag_edg)

            Edge(self.grScene.scene, self.drag_start_socket, item.socket, EDGE_TYPE_BEZIER)
            # self.drag_edge.updatePositions()

            if DEBUG:
                print("View::edgeDragEnd ~  assign End socket to:", item.socket)
                print("View::edgeDragEnd ~ End dargging edge")
            self.grScene.scene.history.storeHistory("Created new edge by dargging", setModified=True)

        else:
            self.mode = MODE_NOOP
            if DEBUG:
                print("View::edgeDragEnd ~  NOT assign End socket")
            self.drag_edge.remove()
            self.drag_edge = None
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
