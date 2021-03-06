from collections import OrderedDict
from xynodeeditor.node_graphics_edge import QDMGraphicsEdge
from xynodeeditor.node_node import Node
from xynodeeditor.node_edge import Edge

DEBUG = False


class SceneClipboard():
    def __init__(self, scene):
        self.scene = scene

    def serializeSelected(self, delete=False):
        if DEBUG:
            print("--COPY TO CLIPBOARD")

        sel_nodes, sel_edges, sel_sockets = [], [], {}

        # sort edges and nodes
        for item in self.scene.grScene.selectedItems():
            if hasattr(item, 'node'):
                sel_nodes.append(item.node.serialize())
                for socket in (item.node.inputs + item.node.outputs):
                    sel_sockets[socket.id] = socket
            elif isinstance(item, QDMGraphicsEdge):
                sel_edges.append(item.edge)

        # debug
        if DEBUG:
            print(" Nodes\n   ", sel_nodes)
            print(" Edges\n   ", sel_edges)
            print(" Sockets\n   ", sel_sockets)

        # remove all edges which are not connectd to a node in our list
        edges_to_remove = []
        for edge in sel_edges:
            if edge.start_socket.id not in sel_sockets or edge.end_socket.id not in sel_sockets:
                if DEBUG:
                    print("edge", edge, "is not connected")
                edges_to_remove.append(edge)
        for edge in edges_to_remove:
            sel_edges.remove(edge)

        # make final list of edges
        edges_final = []
        for edge in sel_edges:
            edges_final.append(edge.serialize())

        data = OrderedDict([
            ('nodes', sel_nodes),
            ('edges', edges_final),
        ])

        # if CUT (aka delete)
        if delete:
            self.scene.grScene.views()[0].deleteSelectd()
            # store our history
            self.scene.hitory.storeHistory("Cut out element from scene", setModified=True)

        return data

    def deserializeFromClipboard(self, data):
        hashmap = {}

        # calculate mous pointer - scene position
        view = self.scene.grScene.views()[0]
        mouse_scene_pos = view.last_scene_mouse_position

        # calculate selected objects bbox and center
        minx, maxx, miny, maxy = 0, 0, 0, 0
        for node_data in data['nodes']:
            x, y = node_data['pos_x'], node_data['pos_y'],
            if x < minx:
                minx = x
            if x > maxx:
                maxx = x
            if y < miny:
                miny = y
            if y > maxy:
                maxy = y
        bbox_center_x = (minx + maxx) / 2
        bbox_center_y = (miny + maxy) / 2

        # calculate the offset of the newly creating nodes
        offset_x = mouse_scene_pos.x() - bbox_center_x
        offset_y = mouse_scene_pos.y() - bbox_center_y

        # create each node

        for node_data in data['nodes']:
            new_node = Node(self.scene)
            new_node.deserialize(node_data, hashmap, restore_id=False)

            # readjust the new node's position
            pos = new_node.pos
            new_node.setPos(pos.x() + offset_x, pos.y() + offset_y)

        # create each edge
        if 'edges' in data:
            for edge_data in data['edges']:
                new_edge = Edge(self.scene)
                new_edge.deserialize(edge_data, hashmap, restore_id=False)

        # store history
        self.scene.history.storeHistory("Pasted items in scene", setModified=True)
