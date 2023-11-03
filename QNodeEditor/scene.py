"""Scene container storing all node editor elements"""
# pylint: disable = no-name-in-module
import json
from typing import TYPE_CHECKING, Iterable, Type, overload, Optional
from functools import partial

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from networkx import DiGraph, find_cycle, NetworkXNoCycle

from QNodeEditor.graphics.scene import NodeSceneGraphics
from QNodeEditor.graphics.view import NodeView
from QNodeEditor.metas import ObjectMeta
from QNodeEditor.node import Node
from QNodeEditor.edge import Edge
from QNodeEditor.entry import Entry
from QNodeEditor.clipboard import Clipboard
if TYPE_CHECKING:
    from QNodeEditor.socket import Socket


class NodeScene(QObject, metaclass=ObjectMeta):
    """Scene container holding nodes, sockets, layouts, edges, etc..."""

    # Create scene signals
    evaluated: pyqtSignal = pyqtSignal(dict)     # emits evaluation result
    errored: pyqtSignal = pyqtSignal(Exception)  # emits error if one occurs during evaluation

    # Create scene thread reference
    _thread: QThread = None
    _worker: 'Worker' = None

    def __init__(self, parent: QWidget = None):
        """
        Initialise scene with empty lists of nodes and edges
        :param parent: parent widget
        """
        super().__init__()
        self.nodes: list['Node'] = []
        self.edges: list['Edge'] = []
        self.available_nodes: dict[str, Type[Node] or dict] = {}

        # Create scene graphics
        self._width, self._height = 64000, 64000
        self.graphics: NodeSceneGraphics = NodeSceneGraphics(self, parent)
        self.graphics.set_size(self._width, self._height)

        # Create scene management
        self.clipboard: Clipboard = Clipboard(self)
        self.output_node: Optional[Type[Node]] = None
        self.has_cycles: bool = False

    def add_node(self, node: 'Node') -> None:
        """
        Add a new node to the scene
        :param node: new node
        :return: None
        """
        self.nodes.append(node)
        self.graphics.addItem(node.graphics)
        node.scene = self
        self.has_cycles = self._check_cycles()

    def add_nodes(self, nodes: Iterable['Node']) -> None:
        """
        Add new nodes to the scene
        :param nodes: iterable of nodes
        :return: None
        """
        for node in nodes:
            self.add_node(node)

    def remove_node(self, node: 'Node') -> None:
        """
        Remove a node from the scene
        :param node: node to remove
        :return: None
        """
        if node in self.nodes:
            self.nodes.remove(node)
            self.has_cycles = self._check_cycles()

    def clear(self) -> None:
        """
        Remove all nodes (and thus all edges) from the scene
        :return: None
        """
        while len(self.nodes) > 0:
            self.nodes[0].remove()
        self.has_cycles = self._check_cycles()

    def set_editing_flag(self, editing: bool) -> None:
        """
        Set a flag showing that content is being edited (to prevent undesired event effects)
        :param editing: whether content is being edited
        :return: None
        """
        for view in self.graphics.views():
            if isinstance(view, NodeView):
                view.set_editing_flag(editing)

    def __str__(self) -> str:
        """
        Get a string representation of the scene
        :return: str: string representation of the scene
        """
        return f"<NodeScene with {len(self.nodes)} nodes and {len(self.edges)} edges>"

    @property
    def output_node(self) -> Type[Node]:
        """
        Get the type of node that is considered the scene output node
        :return: Type[Node]: type of node that is used for output
        """
        return self._output_node

    @output_node.setter
    @overload
    def output_node(self, code: int) -> None:
        """
        Set the node to use as output by its unique code
        :param code: unique code for node to use as output node
        :return: None
        """

    @output_node.setter
    @overload
    def output_node(self, node_class: Type[Node]) -> None:
        """
        Set the node to use as output by its class definition
        :param node_class: class definition of node to use as output node
        :return: None
        """

    @output_node.setter
    @overload
    def output_node(self, node: Node) -> None:
        """
        Set the node to use as output by an instance of the node
        :param node: node instance for which class to use as output node
        :return: None
        """

    @output_node.setter
    def output_node(self, node: Node or Type[Node] or int or None) -> None:
        """
        Set the type of node to use as the output node
        :param node: code, class definition, or node instance from which to derive output node
        :return: None
        """
        # Clear output node if argument is None
        if node is None:
            self._output_node = None
            return

        # Get the node class definition if argument is node code or instance of node
        if isinstance(node, int):
            node = self.get_node_class(node)
        if isinstance(node, Node):
            node = type(node)

        # Ensure node definition is known in scene
        if node not in self.available_classes():
            raise ValueError(f"Node '{node}' is not in the available nodes for this scene")
        self._output_node = node

    @property
    def available_nodes(self) -> dict[str, Type['Node'] or dict]:
        """
        Get the (nested) dictionary defining the names and classes
        of the available nodes in the scene
        :return: dict[str, Type[Node] or dict]: (nested) dictionary of (name, Node class) items
        """
        return self._available_nodes

    @available_nodes.setter
    def available_nodes(self, new_available_nodes: dict[str, Type['Node'] or dict]) -> None:
        """
        Set the available nodes in the scene using a (nested) dictionary of (name, Node class) items
        :param new_available_nodes: (nested) dictionary of (name, Node class) items
        :return: None
        """
        # Helper funtion that recursively parses a nested dictionary
        def _parse(section: dict[str, Type['Node'] or dict], known_codes: list[int] = None) -> None:
            if known_codes is None:
                known_codes = []

            # Check key and value types and ensure all node codes are unique
            for key, value in section.items():
                if not isinstance(key, str):
                    raise TypeError(f"Name '{key}' not a string")
                if isinstance(value, dict):
                    _parse(value, known_codes)
                    continue
                if not issubclass(value, Node) or value is Node:
                    raise TypeError(f"Node item '{value}' does not inherit from Node")
                if value.code in known_codes:
                    raise ValueError(f'A node with code {value.code} '
                                     f'was already defined (must be unique)')
                known_codes.append(value.code)
        _parse(new_available_nodes)

        self._available_nodes = new_available_nodes

    def available_codes(self) -> list[int]:
        """
        Get a list of the codes of nodes that are available in the scene
        :return: list[int]: list of unique codes available in the scene
        """
        return [node_class.code for node_class in self.available_classes()]

    def available_classes(self) -> list[Type[Node]]:
        """
        Get a list of the class definition of nodes that are available in the scene
        :return: list[Type[Node]]: list of class definitions of available nodes
        """
        # Helper function that recursively parses a nested dictionary
        def _parse(section: dict[str, Type['Node']] or dict) -> list[Type[Node]]:
            classes: list[Type[Node]] = []
            for value in section.values():
                if isinstance(value, dict):
                    classes += _parse(value)
                else:
                    classes.append(value)
            return classes
        return _parse(self.available_nodes)

    def get_node_class(self, code: int) -> Type['Node']:
        """
        Get a node class definition by its unique code (if it is in the scene available nodes)
        :param code: unique node code
        :return: Type[Node]: node class definition
        """
        # Helper function that recursively parses a nested dictionary
        def _parse(section: dict[str, Type['Node'] or dict], searched: int) -> list[Type['Node']]:
            result: list[Type['Node']] = []
            for value in section.values():
                if isinstance(value, dict):
                    result += _parse(value, searched)
                elif value.code == searched:
                    result.append(value)
            return result
        classes = _parse(self.available_nodes, code)

        # Raise error if the node definition was not found, otherwise return the definition
        if len(classes) == 0:
            raise ValueError(f"Could not find node with code '{code}'")
        return classes[0]

    def socket_instances(self) -> dict[str, 'Socket']:
        """
        Get a dictionary of ids and associated socket instances
        :return: dict[str, Socket]: (id, Socket) pairs
        """
        result: dict[str, 'Socket'] = {}
        for node in self.nodes:
            for socket in node.sockets():
                result[socket.id] = socket
        return result

    def find_output_node(self) -> Node:
        """
        Find the output node in the scene (must be exactly one)
        :return: Node: output node
        """
        # Check if an output node has been set in the scene
        if self.output_node is None:
            raise ValueError('No output node has been set in this scene')

        # Find all nodes with the output node type in this scene
        output_nodes = []
        for node in self.nodes:
            if type(node) is self.output_node:
                output_nodes.append(node)

        # Make sure there is exactly one output node
        if len(output_nodes) == 0:
            raise ValueError('There is no output node in the scene')
        if len(output_nodes) > 1:
            raise ValueError('There are multiple output nodes in the scene')
        return output_nodes[0]

    def evaluate(self) -> None:
        """
        Evaluate the scene by traversing the nodes and return the calculated output value(s)
        :return: dict[str, Any]: name and calculated value of all output node sockets
        """
        # Create a QThread and place a worker on it
        self._thread = QThread()
        self._worker = Worker()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(partial(self._worker.run, self))

        # Connect finished and errored signals to handlers
        self._worker.finished.connect(self.evaluated.emit)
        self._worker.errored.connect(self.errored.emit)
        self._worker.done.connect(self._handle_done)

        # Move worker to thread and start it
        self._thread.start()

    def _handle_done(self) -> None:
        """
        Close and clean up the thread and worker
        :return: None
        """
        # Stop the thread if it is still running
        if self._thread.isRunning():
            self._thread.quit()

        # Wait for thread to close then delete it and the worker
        self._thread.wait()
        self._worker.deleteLater()
        self._thread.deleteLater()

    def _digraph(self) -> DiGraph:
        """
        Create a directional graph for that represents the node scene
        :return: DiGraph: directional graph representation
        """
        graph = DiGraph()

        # Add all nodes to the graph
        for node in self.nodes:
            graph.add_node(id(node))

        # Add all edges to the graph
        for edge in self.edges:
            if edge.start is None or edge.end is None:
                continue
            if edge.start.entry.entry_type == Entry.TYPE_INPUT:
                graph.add_edge(id(edge.end.entry.node), id(edge.start.entry.node))
            elif edge.end.entry.entry_type == Entry.TYPE_INPUT:
                graph.add_edge(id(edge.start.entry.node), id(edge.end.entry.node))
        return graph

    def _check_cycles(self) -> bool:
        """
        Check if the node scene nodes and edges contain cycles
        :return: bool: whether the scene graph contains cycles
        """
        try:
            graph = self._digraph()
            find_cycle(graph)
            return True
        except NetworkXNoCycle:
            return False

    def save(self, filepath: str) -> None:
        """
        Save the scene to a file
        :param filepath: filepath to save scene to
        :return: None
        """
        with open(filepath, 'w', encoding='utf-8') as file:
            state = json.dumps(self.get_state())
            file.write(state)

    def load(self, filepath: str) -> None:
        """
        Load the scene from a file
        :param filepath: filepath to load scene from
        :return: None
        """
        with open(filepath, 'r', encoding='utf-8') as file:
            state = json.loads(file.read())
            self.set_state(state, True)

    def get_state(self) -> dict:
        """
        Get the state of the scene as a dictionary
        :return: dict: representation of the scene state
        """
        return {
            'nodes': [node.get_state() for node in self.nodes],
            'edges': [edge.get_state() for edge in self.edges]
        }

    def set_state(self, state: dict, restore_id: bool = True) -> bool:
        """
        Set the state of the scene from a dictionary
        :param state: representation of the scene state
        :param restore_id: whether to restore the object id from state
        :return: bool: whether setting state succeeded
        """
        # Clear the current scene
        self.clear()
        result = True

        # Restore nodes
        socket_lookup: dict[str, str] = {}
        for node_state in state.get('nodes', []):

            # Instantiate node from the available nodes in the scene
            code = node_state.get('code', None)
            if code is None:
                continue  # TODO: logging warning
            node = self.get_node_class(code)()
            self.add_node(node)

            # Set the node state
            result &= node.set_state(node_state, restore_id)

            # Store the socket ids in the lookup (used when restore_id is False)
            for entry, entry_state in zip(node.entries, node_state.get('entries', [])):
                if (entry.socket is not None
                        and 'socket' in entry_state and 'id' in entry_state['socket']):
                    socket_lookup[entry_state['socket']['id']] = entry.socket.id

        # Restore edges
        for edge_state in state.get('edges', []):

            # Get start and end sockets from the scene
            edge = Edge(scene=self)
            result &= edge.set_state(edge_state, socket_lookup)

        self.has_cycles = self._check_cycles()
        return result


class Worker(QObject):
    """Worker class that runs on a thread to evaluate the node scene"""

    finished: pyqtSignal = pyqtSignal(dict)      # emits result when evaluation is finished
    errored: pyqtSignal = pyqtSignal(Exception)  # emits error when evaluation has errored
    done: pyqtSignal = pyqtSignal()              # emits once worker is done

    def run(self, scene: NodeScene) -> None:
        """
        Evaluate the node scene (or catch any exception that is thrown)
        :return:
        """
        try:
            # Prevent infinite recursion when cycles exist in the scene
            if scene.has_cycles:
                raise ValueError('Cannot evaluate scene since there are cycles in the connections')

            # Rest all node outputs
            for node in scene.nodes:
                node.output = None

            # Get the value for each input socket of the output node
            output_node = scene.find_output_node()
            result = {}
            for entry in output_node.entries:
                if entry.entry_type == Entry.TYPE_INPUT:
                    result[entry.name] = entry.calculate_value()

            # Emit signal with evaluation result
            self.finished.emit(result)

        # Catch any exceptions and emit it through the errored signal
        except Exception as err:
            self.errored.emit(err)

        # Emit signal upon completion
        finally:
            self.done.emit()
