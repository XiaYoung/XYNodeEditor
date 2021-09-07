from collections import OrderedDict
from xynodeeditor.node_serializable import Serializable
from PySide2.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget


class QDMNodeContentWidget(QWidget, Serializable):
    def __init__(self, node, parent=None):
        super().__init__(parent)

        self.node = node

        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.wdg_label = QLabel("Some Title")
        self.layout.addWidget(self.wdg_label)
        self.layout.addWidget(QDMTextEdit("foo"))

    def setEditingFlag(self, value):
        self.node.scene.grScene.views()[0].editingFlag = value

    def serialize(self):
        return OrderedDict([

            ])

    def deserialize(self, data, hashmap={}):
        return False


class QDMTextEdit(QTextEdit):
    def focusInEvent(self, event):
        self.parentWidget().setEditingFlag(True)
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        self.parentWidget().setEditingFlag(False)
        super().focusOutEvent(event)
