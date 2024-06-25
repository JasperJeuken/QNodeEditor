"""
Socket containing a reference to all edges connected to it.

This module contains a class derived from QObject. The object contains a list of edges connected to
it.
"""
# pylint: disable = no-name-in-module
from __future__ import annotations
from typing import TYPE_CHECKING, Type

try:
    from PySide6.QtCore import Signal as pyqtSignal
    from PySide6.QtCore import QObject
except ImportError:
    from PyQt5.QtCore import pyqtSignal, QObject


from QNodeEditor.graphics.socket import SocketGraphics
from QNodeEditor.metas import ObjectMeta
if TYPE_CHECKING:
    from QNodeEditor.edge import Edge
    from QNodeEditor.entry import Entry


class Socket(QObject, metaclass=ObjectMeta):
    """
    Socket container holding a reference to all edges connected to it.

    This class should not be used since all socket instances are handled by
    :py:class:`~.entry.Entry` instances automatically.

    Attributes
    ----------
    entry : :py:class:`~.entry.Entry`
        Entry this socket belongs to
    edges : list[:py:class:`.edge.Edge`]
        List of edges connected to this socket
    graphics : :py:class:`.graphics.socket.SocketGraphics`
        Graphics object that is shown in the scene representing this socket
    """

    # Create socket signals
    connected: pyqtSignal = pyqtSignal()
    """pyqtSignal: Signal that is emitted when a new edge is connected to the socket"""
    disconnected: pyqtSignal = pyqtSignal()
    """pyqtSignal: Signal that is emitted when an edge is disconnected from the socket"""

    def __init__(self, entry: 'Entry', value_type: Type = int):
        """
        Create a new socket.

        Parameters
        ----------
        entry : :py:class:`~.entry.Entry`
            Entry this socket belongs to
        value_type : Type
            Type of the socket (not yet implemented)
        """
        super().__init__()
        self.id: str = str(id(self))
        self.entry: 'Entry' = entry
        self.value_type: Type = value_type

        self.edges: list['Edge'] = []
        self.graphics: SocketGraphics = SocketGraphics(self)

    def add_edge(self, edge: 'Edge') -> None:
        """
        Connect a new edge to the socket.

        Parameters
        ----------
        edge : :py:class:`.edge.Edge`
            Edge to connect to the socket

        Returns
        -------
            None
        """
        self.edges.append(edge)
        self.connected.emit()

    def remove_edge(self, edge: 'Edge') -> None:
        """
        Remove an edge from the socket

        Parameters
        ----------
        edge : :py:class:`.edge.Edge`
            Edge to remove from the socket

        Returns
        -------
            None
        """
        if edge in self.edges:
            self.edges.remove(edge)
            self.disconnected.emit()

    def remove_all_edges(self) -> None:
        """
        Remove all edges from the socket

        Returns
        -------
            None
        """
        while len(self.edges) > 0:
            edge = self.edges.pop(0)
            edge.remove()

    def update_edges(self) -> None:
        """
        Update the graphics for all edges connected to this socket

        Returns
        -------
            None
        """
        for edge in self.edges:
            edge.update_positions()

    def __str__(self) -> str:
        """
        Get a string representation of the socket

        Returns
        -------
        str
            Representation of the socket
        """
        return f"<Socket for entry '{self.entry.name}' ({len(self)} connections)>"

    def __len__(self) -> int:
        """
        Get the number of edges connected to this socket.

        Returns
        -------
        int
            Number of edges connected to this socket
        """
        return len(self.edges)

    def get_state(self) -> dict:
        """
        Get the state of the socket as a (JSON-safe) dictionary.

        The dictionary contains:

        - ``id``: The internal ID of the socket

        Returns
        -------
        dict
            JSON-safe dictionary representing socket state
        """
        return {
            'id': self.id
        }

    def set_state(self, state: dict, restore_id: bool = True) -> bool:
        """
        Set the state of this socket from a state dictionary.

        The dictionary contains:

        - ``id``: The internal ID of the socket

        Parameters
        ----------
        state : dict
            Dictionary representation of the desired socket state
        restore_id : bool
            Whether to restore the internal ID or use a new one

        Returns
        -------
        bool
            Whether setting the entry state succeeded.
        """
        if restore_id:
            self.id = state.get('id', self.id)
        return True
