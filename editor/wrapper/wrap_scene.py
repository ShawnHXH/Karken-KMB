from editor.graphic.node_scene import KMBNodeGraphicScene
from editor.wrapper.serializable import Serializable
from cfg import DEBUG


class KMBNodeScene(Serializable):

    def __init__(self):
        super().__init__()

        self.edges = []  # saving wrapper edges
        self.nodes = []  # saving wrapper nodes

        self.scene_width = 16000
        self.scene_height = 16000
        self.graphic_scene = KMBNodeGraphicScene(self)
        self.graphic_scene.set_graphic_scene(self.scene_width,
                                             self.scene_height)

    def check_edge(self, edge):
        """ Check edge valid. """
        for e in self.edges:
            if e.start_item == edge.start_item and e.end_item is edge.end_item:
                return False
        return True

    def add_edge(self, edge):
        self.edges.append(edge)
        if DEBUG:
            print("*[E_ADD_%d]" % len(self.edges), self.edges)

    def remove_edge(self, edge):
        self.edges.remove(edge)
        if DEBUG:
            print("*[E_DEL_%d]" % len(self.edges), self.edges)

    def add_node(self, node):
        self.nodes.append(node)
        if DEBUG:
            print("*[N_ADD_%d]" % len(self.nodes), self.nodes)

    def remove_node(self, node):
        self.nodes.remove(node)
        self._remove_relative_edges(node)
        if DEBUG:
            print("*[N_DEL_%d]" % len(self.nodes), self.nodes)

    def _remove_relative_edges(self, node):
        # removing node also remove edge that connected to it.
        edges = self.edges.copy()
        # cannot iter self.edges directly that's ...
        for edge in edges:
            if node == edge.start_item or node == edge.end_item:
                self.graphic_scene.removeItem(edge.gr_edge)
                self.remove_edge(edge)  # ... because of this

    def serialize(self):
        pass

    def deserialize(self):
        pass