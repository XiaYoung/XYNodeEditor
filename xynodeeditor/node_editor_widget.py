import os

from PySide2.QtGui import QBrush, QColor, QPen
from PySide2.QtCore import QFile, Qt
from PySide2.QtWidgets import QApplication, QGraphicsItem, QPushButton, QTextEdit, QVBoxLayout, QWidget

from xynodeeditor.node_node import Node
from xynodeeditor.node_scene import Scene
from xynodeeditor.node_edge import EDGE_TYPE_BEZIER, EDGE_TYPE_DIRECT, Edge
from xynodeeditor.node_graphics_view import QDMGraphicsView


class NodeEditorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.filename = None
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        # create graphics scene
        self.scene = Scene()
        # self.grScene = self.scene.grScence

        self.addNodes()

        # create grphic view
        self.view = QDMGraphicsView(self.scene.grScene, self)
        self.layout.addWidget(self.view)

        # self.addDebugContent()

    def isModified(self):
        return self.scene.has_been_modified

    def isFilenameSet(self):
        return self.filename is not None

    def getUserFriendlyFilename(self):
        name = os.path.basename(self.filename) if self.isFilenameSet() else "New Graph"
        return name + ("*" if self.isModified() else "")


    def addNodes(self):
        node1 = Node(self.scene, "My new Nd",
                     inputs=[0, 2, 3],
                     outputs=[4])
        node2 = Node(self.scene, "My new Nd",
                     inputs=[5, 2, 4],
                     outputs=[4])
        node3 = Node(self.scene, "My new Nd",
                     inputs=[1, 5, 3],
                     outputs=[5])

        node1.setPos(-350, -250)
        node2.setPos(-75, 0)
        node3.setPos(200, -150)

        edge1 = Edge(self.scene, node1.outputs[0], node2.inputs[0], edge_type=EDGE_TYPE_BEZIER)
        edge2 = Edge(self.scene, node2.outputs[0], node3.inputs[0], edge_type=EDGE_TYPE_BEZIER)
        self.scene.history.storeHistory("Init add nodes")

    def addDebugContent(self):
        greenBrush = QBrush(Qt.green)
        outlinePen = QPen(Qt.black)
        outlinePen.setWidth(2)

        rect = self.grScene.addRect(-100, -100, 80, 100, outlinePen, greenBrush)
        rect.setFlag(QGraphicsItem.ItemIsMovable)

        text = self.grScene.addText("this is my awesome text")
        text.setFlag(QGraphicsItem.ItemIsSelectable)
        text.setFlag(QGraphicsItem.ItemIsMovable)
        text.setDefaultTextColor(QColor.fromRgbF(1.0, 0.0, 0.0))

        widget1 = QPushButton("Hello world")
        proxy1 = self.grScene.addWidget(widget1)
        proxy1.setFlag(QGraphicsItem.ItemIsMovable)
        proxy1.setPos(0, 30)

        widget2 = QTextEdit()
        proxy2 = self.grScene.addWidget(widget2)
        proxy2.setFlag(QGraphicsItem.ItemIsSelectable)
        proxy2.setFlag(QGraphicsItem.ItemIsMovable)
        proxy2.setPos(0, 60)

        line = self.grScene.addLine(-200, -100, 400, 200, outlinePen)
        line.setFlag(QGraphicsItem.ItemIsMovable)
        line.setFlag(QGraphicsItem.ItemIsSelectable)
