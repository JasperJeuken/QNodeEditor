"""Class handling clipboard interaction for node scenes"""
# pylint: disable = no-name-in-module
from typing import TYPE_CHECKING
import json

from PyQt5.QtWidgets import QApplication

from QNodeEditor.graphics.node import NodeGraphics
from QNodeEditor.graphics.edge import EdgeGraphics
from QNodeEditor.graphics.view import NodeView
from QNodeEditor.edge import Edge
if TYPE_CHECKING:
    from QNodeEditor.scene import NodeScene
    from QNodeEditor.node import Node


class Clipboard:
    """Class that handles cutting/copying/pasting for node scenes"""

    def __init__(self, scene: 'NodeScene'):
        """
        Store the scene the clipboard is associated with
        :param scene: node scene clipboard management is for
        """
        self.scene: 'NodeScene' = scene

    def copy(self) -> None:
        """
        Store the state of the selected items in the clipboard
        :return: None
        """
        state = self.get_selected_state()
        state_str = json.dumps(state, indent=1)
        QApplication.clipboard().setText(state_str)

    def cut(self) -> None:
        """
        Store the state of the selected items in the clipboard and remove them
        :return: None
        """
        state = self.get_selected_state(True)
        state_str = json.dumps(state, indent=1)
        QApplication.clipboard().setText(state_str)

    def paste(self) -> None:
        """
        Try pasting items from the clipboard into the scene
        :return: None
        """
        state_str = QApplication.clipboard().text()
        try:
            state = json.loads(state_str)
        except json.JSONDecodeError:
            return

        # Check if state is valid:
        try:
            if 'nodes' not in state or 'edges' not in state:
                return
        except (TypeError, KeyError):
            return

        self.add_state(state)

    def _get_view(self) -> NodeView:
        """
        Get the node view graphics object of the scene
        :return: NodeView: view graphics object
        """
        for view in self.scene.graphics.views():
            if isinstance(view, NodeView):
                return view
        raise ValueError('Could not find NodeView in node scene')

    def get_selected_state(self, remove_after: bool = False) -> dict:
        """
        Get the state of the selected items
        :param remove_after: whether to remove selected items after reading state
        :return: dict: selected items state
        """
        # Get the selected nodes and edges from the scene and create a socket lookup table
        node_states = []
        edges = []
        socket_lookup = {}
        for item in self.scene.graphics.selectedItems():

            # Store the state of all nodes and add the node sockets to the lookup table
            if isinstance(item, NodeGraphics):
                node_states.append(item.node.get_state())
                for socket in item.node.sockets():
                    socket_lookup[socket.id] = socket

            # Store the state of all edges
            elif isinstance(item, EdgeGraphics):
                edges.append(item.edge)

        # Ignore edges that are connected to non-selected edges
        edge_states = []
        for edge in edges:
            if edge.start.id in socket_lookup and edge.end.id in socket_lookup:
                edge_states.append(edge.get_state())

        # Remove selected items (if specified)
        if remove_after:
            self._get_view().remove_selected()

        # Return state dictionary for clipboard
        return {
            'nodes': node_states,
            'edges': edge_states
        }

    def add_state(self, state: dict) -> None:
        """
        Set a state loaded from the clipboard to the scene
        :param state: state to add to scene
        :return: None
        """
        view = self._get_view()
        mouse_pos = view.mapToScene(view.prev_mouse_pos)
        self.scene.graphics.clearSelection()

        # Add nodes
        added_nodes: list['Node'] = []
        socket_lookup: dict[str, str] = {}
        for node_state in state['nodes']:

            # Instantiate node from the available nodes in the scene
            code = node_state.get('code', None)
            if code is None or code not in self.scene.available_codes():
                continue
            node = self.scene.get_node_class(code)()

            # Add the node to the scene and set its state
            self.scene.add_node(node)
            node.set_state(node_state, False)
            added_nodes.append(node)
            node.graphics.setSelected(True)

            # Store the socket ids in the lookup
            for entry, entry_state in zip(node.entries, node_state.get('entries', [])):
                if (entry.socket is not None
                        and 'socket' in entry_state and 'id' in entry_state['socket']):
                    socket_lookup[entry_state['socket']['id']] = entry.socket.id

        # Stop further adding if no nodes were added
        if len(added_nodes) == 0:
            return

        # Calculate the coordinate of the center of the added nodes
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')
        for node in added_nodes:
            x, y = node.graphics.pos().x(), node.graphics.pos().y()
            min_x, max_x = min(min_x, x), max(max_x, x + node.graphics.width)
            min_y, max_y = min(min_y, y), max(max_y, y + node.graphics.height)
        center_x = (max_x - min_x) / 2 + min_x
        center_y = (max_y - min_y) / 2 + min_y

        # Move all nodes such that the mouse position is the center of the added nodes
        offset_x, offset_y = mouse_pos.x() - center_x, mouse_pos.y() - center_y
        for node in added_nodes:
            node.graphics.moveBy(offset_x, offset_y)

        # Add edges
        for edge_state in state['edges']:
            edge = Edge(scene=self.scene)
            edge.set_state(edge_state, socket_lookup)
            edge.graphics.setSelected(True)
