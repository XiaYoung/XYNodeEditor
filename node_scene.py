from node_graphics_scene import QDMGraphicsScene


class Scene:

    def __init__(self):
        self.nodes = []
        self.edges = []
        self.scene_width = 64000
        self.scence_height = 64000

        self.initUI()

    def initUI(self):
        self.grScence = QDMGraphicsScene(self)
        self.grScence.setGrScene(self.scene_width, self.scence_height)

    def addNode(self, node):
        self.nodes.append(node)

    def addEdge(self, edge):
        self.edges.append(edge)

    def removeNode(self, node):
        self.nodes.remove(node)

    def removeEdge(self, edge):
        self.edges.remove(edge)