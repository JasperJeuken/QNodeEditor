"""
Scene containing nodes, edges, and utility functions

This module contains a class derived from QObject. The object contains a list of nodes and edges
that make up a node scene.
"""
# pylint: disable = no-name-in-module
import json
from typing import TYPE_CHECKING, Iterable, Type, overload, Optional
from functools import partial

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from networkx import DiGraph, find_cycle, NetworkXNoCycle, has_path

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
    """
    Scene container holding nodes, sockets, layouts, edges, and utility functions.

    This class represents a scene containing nodes connected by edges. The scene has a set number
    of nodes that can be used in the scene, with one being the dedicated output node.

    See the :py:attr:`available_nodes` property for details on how to set the nodes that can be used
    in the scene, and see :py:attr:`output_node` for setting the dedicated output node.

    Examples
    --------
    To create a new scene and add some nodes to it:

    .. code-block:: python

        # Create a scene
        scene = NodeScene()

        # Set the nodes that can be used in the scene
        scene.available_nodes = {
            'Some node': SomeNode,
            'Another node': AnotherNode
        }

        # Set the node that is used as the output
        scene.output_node = SomeNode

        # Create two nodes and add them to the scene
        node1 = SomeNode()
        node2 = AnotherNode()
        scene.addNodes([node1, node2])

    To display a node scene, use a :py:class:`~.graphics.view.NodeView` instance.

    Attributes
    ----------
    nodes : list[:py:class:`~.node.Node`]
        List of nodes that are present in the scene
    edges : list[:py:class:`~.edge.Edge`]
        List of edges that are present in the scene
    """

    # Create scene signals
    evaluated: pyqtSignal = pyqtSignal(dict)
    """pyqtSignal -> dict: Signal that emits a dictionary with the result of evaluating the scene"""
    errored: pyqtSignal = pyqtSignal(Exception)
    """pyqtSignal -> Exception: Signal that emits the error if once occurs during evaluation"""
    progress: pyqtSignal = pyqtSignal()
    """pyqtSignal -> Signal that is emitted when a node has been evaluated"""

    # Create scene thread reference
    _thread: QThread = None
    """QThread: Thread used for scene evaluation (or None when not evaluating)"""
    _worker: 'Worker' = None
    """:py:class:`Worker`: Worker used to perform scene evaluation (or None when not evaluating)"""

    def __init__(self, parent: QWidget = None):
        """
        Create a new node scene.

        Parameters
        ----------
        parent : QWidget, optional
            Parent object for the node scene (if any)
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

    def add_node(self, node: 'Node') -> None:
        """
        Add a new node to the scene.

        Parameters
        ----------
        node : :py:class:`~.node.Node`
            Node to add to the scene

        Returns
        -------
            None
        """
        self.nodes.append(node)
        self.graphics.addItem(node.graphics)
        node.scene = self

    def add_nodes(self, nodes: Iterable['Node']) -> None:
        """
        Add multiple new nodes to the scene.

        Parameters
        ----------
        nodes : Iterable[:py:class:`~.node.Node`]
            Iterable of nodes to add to the scene

        Returns
        -------
            None
        """
        for node in nodes:
            self.add_node(node)

    def remove_node(self, node: 'Node') -> None:
        """
        Remove a node from the scene.

        Does not raise an error if the node does not exist.

        Parameters
        ----------
        node : :py:class:`~.node.Node`
            Node to remove from the scene

        Returns
        -------
            None
        """
        if node in self.nodes:
            self.nodes.remove(node)

    def clear(self) -> None:
        """
        Remove all nodes (and thus all edges) from the scene.

        Returns
        -------
            None
        """
        while len(self.nodes) > 0:
            self.nodes[0].remove()

    def set_editing_flag(self, editing: bool) -> None:
        """
        Set a flag showing that content is being edited in a node.

        When this flag is set to ``True``, nodes will not be deleted when pressing the ``Delete``
        key.

        This flag is automatically set when a :py:class:`~.widgets.value_box.ValueBox` is edited, as
        well as for select other widgets (see :py:meth:`~.entry.Entry.connect_signal`).

        Parameters
        ----------
        editing : bool
            Whether  content is being edited in a node.

        Returns
        -------
            None
        """
        for view in self.graphics.views():
            if isinstance(view, NodeView):
                view.set_editing_flag(editing)

    def __str__(self) -> str:
        """
        Get a string representation of the node scene

        Returns
        -------
        str:
            Representation of the node scene
        """
        return f"<NodeScene with {len(self.nodes)} nodes and {len(self.edges)} edges>"

    @property
    def output_node(self) -> Type[Node]:
        """
        Get or set the type of node that is considered the scene output.

        The node that is set will not be evaluated. Instead, all inputs of this node will be
        collected by traversing through the node scene. This is then collected and emitted as the
        result of the scene through the :py:attr:`evaluated` signal.

        The output node can be set by either passing the class type, its unique
        :py:attr:`~.node.Node.code` property, or an instance of that node.

        Examples
        --------
        .. code-block:: python

            # Create a scene and set the available nodes and output node
            scene = NodeScene()
            scene.available_nodes = {'Some node': SomeNode}
            scene.output_node = SomeNode

            # Create an instance of the output node and add it to the scene
            node = SomeNode()  # Node with two inputs, 'Value 1' and 'Value 2'
            scene.addNode(node)

            # Evaluate the scene (without any connections to the output node)
            scene.evaluated.connect(print)  # Give the scene result to the 'print' function
            scene.evaluate()                # Start the evaluation

        The output of this script looks like this:

        .. code-block:: bash

            $ python test.py

            {'Value 1': None, 'Value 2': None}

        The values for both items are ``None`` since nothing is wired into them.

        If the input entries in ``SomeNode`` had widgets such as a
        :py:class:`~.widgets.value_box.ValueBox`, its value would be used instead.

        If the input entries were wired to another node, it would be evaluated and that result would
        be used instead.
        """
        return self._output_node

    @output_node.setter
    @overload
    def output_node(self, code: int) -> None:
        pass

    @output_node.setter
    @overload
    def output_node(self, node_class: Type[Node]) -> None:
        pass

    @output_node.setter
    @overload
    def output_node(self, node: Node) -> None:
        pass

    @output_node.setter
    def output_node(self, node: Node or Type[Node] or int or None) -> None:
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
        Get or set the nodes that can be used in the scene.

        Setting the available nodes is done using a (nested) dictionary. The keys are used as names
        in the node editor context menu, and the corresponding values are types of a node that are
        placed when a name is selected.

        You can only add nodes to the scene that are in the :py:attr:`available_nodes` property.
        This is to keep track of the nodes such that they can be saved and loaded.

        Nodes may only appear once in the (nested) dictionary.

        Examples
        --------
        A scene with two nodes:

        .. code-block:: python

            scene.available_nodes = {
                'Name 1': SomeNode,
                'Name 2': AnotherNode
            }

        The resulting context menu would have the following structure:

        .. code-block::

            Add node
             ├─ Name 1
             └─ Name 2

        Choosing either option results in placing a new instance of the corresponding node type.

        A more complicated menu can be created like this:

        .. code-block:: python

            scene.available_nodes = {
                'Name 1': SomeNode,
                'Group 1': {
                    'Name 2': AnotherNode,
                    'Name 3': YetAnotherNode
                },
                'Name 4': FinalNode
            }

        The resulting context menu would now have the following structure:

        .. code-block::

            Add node
             ├─ Name 1
             ├─ Group 1
             │   ├─ Name 2
             │   └─ Name 3
             └─ Name 4
        """
        return self._available_nodes

    @available_nodes.setter
    def available_nodes(self, new_available_nodes: dict[str, Type['Node'] or dict]) -> None:
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
        Get a list of the unique codes of all nodes that are available in the scene.

        Examples
        --------
        With the following value for the :py:attr:`available_nodes` property:

        .. code-block:: python

            scene.available_nodes = {
                'Name 1': SomeNode,           # Unique code: 0
                'Group 1': {
                    'Name 2': AnotherNode,    # Unique code: 1
                    'Name 3': YetAnotherNode  # Unique code: 2
                },
                'Name 4': FinalNode           # Unique code: 3
            }

        This function would return:

        .. code-block:: python

            [0, 1, 2, 3]

        Returns
        -------
        list[int]
            List of unique codes for all available nodes
        """
        return [node_class.code for node_class in self.available_classes()]

    def available_classes(self) -> list[Type[Node]]:
        """
        Get a list of the class definitions of nodes that are available in the scene.

        Examples
        --------
        With the following value for the :py:attr:`available_nodes` property:

        .. code-block:: python

            scene.available_nodes = {
                'Name 1': SomeNode,
                'Group 1': {
                    'Name 2': AnotherNode,
                    'Name 3': YetAnotherNode
                },
                'Name 4': FinalNode
            }

        This function would return:

        .. code-block:: python

            [SomeNode, AnotherNode, YetAnotherNode, FinalNode]

        Returns
        -------
        list[Type[:py:class:`~.node.Node`]]
            List of node classes for all available nodes
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
        Get a node class definition by its unique code

        This only works for nodes that are set in the :py:attr:`available_nodes` property.

        Parameters
        ----------
        code : int
            Unique code of node class definition to retrieve

        Returns
        -------
        Type[:py:class:`~.node.Node`]
            Node class definition matching the unique code

        Raises
        ------
        ValueError
            If no node with the specified unique code exists
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
        Get a dictionary of all sockets and their IDs in this scene

        The returned dictionaries has the socket ID (string) and socket instance as keys and values
        respectively.

        Returns
        -------
        dict[str, :py:class:`.socket.Socket`]
            Dictionary of (ID, instance) pairs for all sockets in the scene
        """
        result: dict[str, 'Socket'] = {}
        for node in self.nodes:
            for socket in node.sockets():
                result[socket.id] = socket
        return result

    def find_output_node(self) -> Node:
        """
        Find the instance of the output node in the scene (if any)

        This function raises an error if the output node could not be found. This can be due to
        one of the following reasons:

        - No output node has been set through the :py:attr:`output_node` property
        - There is no instance of the specified output node in the scene
        - There is more than one instances of the specified output node in the scene

        Returns
        -------
        :py:class:`~.node.Node`
            Output node instance

        Raises
        ------
        ValueError
            If the node could not be found, or there is more than one output node instance
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

    def evaluate(self) -> int:
        """
        Evaluate the scene by traversing the nodes and their connections.

        This starts the asynchronous evaluation of the scene. All nodes leading up to the output
        node are evaluated, and the final result is emitted through the :py:attr:`evaluated` signal.

        If an error occurs during the evaluation, it is emitted through the :py:attr:`errored`
        signal (and nothing through the :py:attr:`evaluated` signal).

        Returns
        -------
        int
            Number of nodes that will be evaluated asynchronously
        """
        # Count the number of nodes that have to be evaluated
        n_nodes = len(self.simplified_digraph().nodes) - 1

        # Connect node evaluation signals
        for node in self.nodes:
            node.evaluated.connect(self.progress.emit)

        # Disable view while calculating
        self._disable_view(True)

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
        return n_nodes

    def _handle_done(self) -> None:
        """
        If the scene evaluation is completed, close all asynchronous elements.

        Returns
        -------
            None
        """
        # Stop the thread if it is still running
        if self._thread.isRunning():
            self._thread.quit()

        # Wait for thread to close then delete it and the worker
        self._thread.wait()
        self._worker.deleteLater()
        self._thread.deleteLater()

        # Enable view
        self._disable_view(False)

    def _disable_view(self, disabled: bool) -> None:
        """
        Enable/disable the :py:class:`~.graphics.view.NodeView` (during scene evaluation).

        Parameters
        ----------
        disabled : bool
            Whether the view should be disabled

        Returns
        -------
            None
        """
        for view in self.graphics.views():
            view.setDisabled(disabled)

    def digraph(self) -> DiGraph:
        """
        Create a directional graph that represents the node scene.

        This graph is used to check for cycles in the graph to prevent infinite recursion when
        evaluating.

        Returns
        -------
        DiGraph
            Directional graph object representing the nodes and connections in the scene.
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

    def simplified_digraph(self) -> DiGraph:
        """
        Get a directional graph representing the scene with only nodes connected to the output.

        This graph is used to determine how many nodes will have to be calculated during scene
        evaluation.

        Returns
        -------
        DiGraph
            Directional graph object representing the nodes connected to the output node.
        """
        # Create graph from scene and find the output node
        graph = self.digraph()
        output = id(self.find_output_node())

        # Create new graph with only nodes that connect to the output
        simple_graph = DiGraph()
        for node in graph.nodes:
            if has_path(graph, node, output):
                simple_graph.add_node(node)

        # Add back the edges that are part of the simplified graph
        for edge in graph.edges:
            if simple_graph.has_node(edge[0]) and simple_graph.has_node(edge[1]):
                simple_graph.add_edge(edge[0], edge[1])

        return simple_graph

    def has_cycles(self) -> bool:
        """
        Check if the nodes and edges in the scene form a cycle.

        Returns
        -------
        bool
            Whether a cycle is present in the node scene
        """
        try:
            graph = self.digraph()
            find_cycle(graph)
            return True
        except NetworkXNoCycle:
            return False

    def save(self, filepath: str) -> None:
        """
        Save the scene state to a file.

        Parameters
        ----------
        filepath : str
            Path to file to save scene state to

        Returns
        -------
            None
        """
        with open(filepath, 'w', encoding='utf-8') as file:
            state = json.dumps(self.get_state())
            file.write(state)

    def load(self, filepath: str) -> None:
        """
        Load the scene state from a file

        Parameters
        ----------
        filepath : str
            Path to file to load scene state from

        Returns
        -------
            None
        """
        with open(filepath, 'r', encoding='utf-8') as file:
            state = json.loads(file.read())
            self.set_state(state, True)

    def get_state(self) -> dict:
        """
        Get the state of this scene as a (JSON-safe) dictionary.

        The dictionary contains:

        - ``'nodes'``: list of node states
        - ``'edges'``: list of edge states

        Returns
        -------
        dict
            JSON-safe dictionary representing scene state
        """
        return {
            'nodes': [node.get_state() for node in self.nodes],
            'edges': [edge.get_state() for edge in self.edges]
        }

    def set_state(self, state: dict, restore_id: bool = True) -> bool:
        """
        Set the state of this scene from a state dictionary.

        The dictionary contains:

        - ``'nodes'``: list of node states
        - ``'edges'``: list of edge states

        Parameters
        ----------
        state : dict
            Dictionary representation of the desired scene state
        restore_id : bool
            Whether to restore the internal IDs of the entry sockets (used to reconnect saved edges)

        Returns
        -------
        bool
            Whether setting the scene state succeeded
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

        return result


class Worker(QObject):
    """
    Worker class that runs on a thread to evaluate the node scene.

    When run, traverses through a node scene starting from the output node and moving backwards
    until all inputs have been determined.
    """

    finished: pyqtSignal = pyqtSignal(dict)
    """pyqtSignal: Signal that emits result of scene evaluation if successful"""
    errored: pyqtSignal = pyqtSignal(Exception)
    """pyqtSignal: Signal that emits the exception if one occurred during evaluation"""
    done: pyqtSignal = pyqtSignal()
    """pyqtSignal: Signal that is emitted when the scene evaluation completed"""

    def run(self, scene: NodeScene) -> None:
        """
        Evaluate a node scene (or catch any exception that is thrown).

        Goes through all output node inputs and traverses the scene until all of their inputs have
        been calculated. This is collected in a dictionary and emitted as the result through the
        :py:attr:`finished` signal.

        If an error occurred at some point, it is caught and emitted through the :py:attr:`errored`
        signal.

        Finally, whether successful or not, the :py:attr:`done` signal is emitted to signal that
        the worker has completed the evaluation.

        Parameters
        ----------
        scene : :py:class:`NodeScene`
            Scene to evaluate

        Returns
        -------
            None
        """
        try:
            # Prevent infinite recursion when cycles exist in the scene
            if scene.has_cycles():
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
