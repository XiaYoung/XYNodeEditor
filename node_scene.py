import json
from collections import OrderedDict
from node_scene_clipboard import SceneClipboard
from node_serializable import Serializable
from node_graphics_scene import QDMGraphicsScene
from node_node import Node
from node_edge import Edge
from node_scene_history import SceneHistory


class Scene(Serializable):
    def __init__(self):
        super().__init__()
        self.nodes = []
        self.edges = []
        self.scene_width = 64000
        self.scence_height = 64000

        self.initUI()
        self.history = SceneHistory(self)
        self.clipboard = SceneClipboard(self)

    def initUI(self):
        self.grScene = QDMGraphicsScene(self)
        self.grScene.setGrScene(self.scene_width, self.scence_height)

    def addNode(self, node):
        self.nodes.append(node)

    def addEdge(self, edge):
        self.edges.append(edge)

    def removeNode(self, node):
        if node in self.nodes:
            self.nodes.remove(node)

    def removeEdge(self, edge):
        # 防止重复删除
        if edge in self.edges:
            self.edges.remove(edge)

    def saveToFile(self, filename):
        with open(filename, "w") as file:
            file.write(json.dumps(self.serialize(), indent=4))
        print("saving to", filename, "was successfull.")

    def loadFromFile(self, filename):
        with open(filename, "r") as file:
            raw_data = file.read()
            data = json.loads(raw_data, encoding='utf-8')
            self.deserialize(data)
        self.history.storeHistory("load from file")

    def clear(self):
        while len(self.nodes) > 0:
            self.nodes[0].remove()

    def serialize(self):
        nodes, edges = [], []
        for node in self.nodes:
            nodes.append(node.serialize())
        for edge in self.edges:
            edges.append(edge.serialize())
        return OrderedDict([
            ('id', self.id),
            ('scene_width', self.scene_width),
            ('scene_height', self.scence_height),
            ('nodes', nodes),
            ('edges', edges),
        ])

    def deserialize(self, data, hashmap={}, restore_id=True):
        self.clear()
        hashmap = {}

        if restore_id:
            self.id = data['id']

        # create nodes
        for node_data in data['nodes']:
            Node(self).deserialize(node_data, hashmap, restore_id)
        # TODO: 为什么hashmap 的值传出来了？？
        # print(hashmap)

        # create edges
        for edge_data in data['edges']:
            Edge(self).deserialize(edge_data, hashmap, restore_id)

        return
