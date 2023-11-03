"""Container storing socket properties"""
# pylint: disable = no-name-in-module
from __future__ import annotations
from typing import TYPE_CHECKING, Type

from PyQt5.QtCore import QObject, pyqtSignal

from QNodeEditor.graphics.socket import SocketGraphics
from QNodeEditor.metas import ObjectMeta
if TYPE_CHECKING:
    from QNodeEditor.edge import Edge
    from QNodeEditor.entry import Entry


class Socket(QObject, metaclass=ObjectMeta):
    """Class housing socket properties and connections"""

    # Create socket signals
    connected: pyqtSignal = pyqtSignal()
    disconnected: pyqtSignal = pyqtSignal()

    def __init__(self, entry: 'Entry', value_type: Type = int):
        """
        Initialise by storing properties and creating graphics
        :param entry: entry this socket belongs to
        :param value_type: type of the value of the socket (determines color)
        """
        super().__init__()
        self.id: str = str(id(self))
        self.entry: 'Entry' = entry
        self.value_type: Type = value_type

        self.edges: list['Edge'] = []
        self.graphics: SocketGraphics = SocketGraphics(self)

    def add_edge(self, edge: 'Edge') -> None:
        """
        Connect a new edge to the socket
        :param edge: edge to connect to the socket
        :return: None
        """
        self.edges.append(edge)
        self.connected.emit()

    def remove_edge(self, edge: 'Edge') -> None:
        """
        Remove an edge from the socket
        :param edge: edge to remove from the socket
        :return: None
        """
        if edge in self.edges:
            self.edges.remove(edge)
            self.disconnected.emit()

    def remove_all_edges(self) -> None:
        """
        Remove all edges from the socket
        :return: None
        """
        while len(self.edges) > 0:
            edge = self.edges.pop(0)
            edge.remove()

    def update_edges(self) -> None:
        """
        Update all edges connected to the socket
        :return: None
        """
        for edge in self.edges:
            edge.update_positions()

    def __str__(self) -> str:
        """
        Get a string representation of the socket
        :return: str: string representation of the socket
        """
        return f"<Socket for entry '{self.entry.name}' ({len(self)} connections)>"

    def __len__(self) -> int:
        """
        Get the number of edges connected to this socket
        :return: int: number of connected edges
        """
        return len(self.edges)

    def get_state(self) -> dict:
        """
        Get the state of the socket as a dictionary
        :return: dict: representation of the socket state
        """
        return {
            'id': self.id
        }

    def set_state(self, state: dict, restore_id: bool = True) -> bool:
        """
        Set the state of the socket from a dictionary
        :param state: representation of the socket state
        :param restore_id: whether to restore the object id from state
        :return: bool: whether setting state succeeded
        """
        if restore_id:
            self.id = state.get('id', self.id)
        return True
