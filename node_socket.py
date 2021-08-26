from collections import OrderedDict
from node_serializable import Serializable
from node_graphics_socket import QDMGraphicsSocket


LEFT_TOP = 1
LEFT_BOTTOM = 2
RIGHT_TOP = 3
RIGHT_BOTTOM = 4


class Socket(Serializable):
    def __init__(self, node, index=0, position=LEFT_TOP, socket_type=1):
        super().__init__()
        self.node = node
        self.index = index
        self.position = position
        self.socket_type = socket_type

        self.grSocket = QDMGraphicsSocket(self, self.socket_type)  # must give a parent

        self.grSocket.setPos(*self.node.getSocketPosition(index, position))

        # self.edge = None
        self.edges = []

    def __str__(self):
        return "<Socket %s..%s>" % (hex(id(self))[2:5], hex(id(self))[-3:])

    def getSocketPosition(self):
        return self.node.getSocketPosition(self.index, self.position)

    def setConnectedEdge(self, edge=None):
        # self.edge = edge
        self.edges.append(edge)

    def hasEdge(self):
        return self.edges

    def serialize(self):
        return OrderedDict([
            ('id', self.id),
            ('index', self.index),
            ('position', self.position),
            ('socket_type', self.socket_type),
        ])

    def deserialize(self, data, hashmap={}):
        self.id = data["id"]
        hashmap[data['id']] = self

        return True
