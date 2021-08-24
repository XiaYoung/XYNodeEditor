from node_socket import LEFT_BOTTOM, LEFT_TOP, RIGHT_BOTTOM, RIGHT_TOP, Socket
from node_content_widget import QDMNodeContentWidget
from node_graphics_node import QDMGraphicsNode


class Node():
    def __init__(self, scene, title="Undefined Node", inputs=[], outputs=[]):
        self.scene = scene

        self.title = title
        self.content = QDMNodeContentWidget()
        self.grNode = QDMGraphicsNode(self)

        self.scene.addNode(self)
        self.scene.grScene.addItem(self.grNode)

        self.socket_spacing = 22
        # create sockets for inputs and outputs
        self.inputs = []
        self.outputs = []

        counter = 0
        for item in inputs:
            socket = Socket(node=self, index=counter, position=LEFT_BOTTOM)
            counter += 1
            self.inputs.append(socket)

        counter = 0
        for item in outputs:
            socket = Socket(node=self, index=counter, position=RIGHT_TOP)
            self.outputs.append(socket)

    def getSocketPosition(self, index, position):
        x = 0 if position in [LEFT_TOP, LEFT_BOTTOM] else self.grNode.width

        if position in (LEFT_BOTTOM, RIGHT_BOTTOM):
            y = self.grNode.height - self.grNode.edge_size - self.grNode._padding - index * self.socket_spacing
        else:
            y = self.grNode.title_height + self.grNode._padding + self.grNode.edge_size + index * self.socket_spacing

        return x, y
